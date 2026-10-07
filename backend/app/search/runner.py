import asyncio
import logging
import uuid
from datetime import date, datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

from openai import AsyncOpenAI, BadRequestError
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app import db
from app.config import get_settings
from app.models import Opportunity, OpportunityProject, Project, SearchConfig, SearchRun, utcnow
from app.schemas import Preferences, Schedule
from app.search.prompt import INSTRUCTIONS, build_input
from app.search.schema import FoundOpportunity, SearchResult

log = logging.getLogger(__name__)

LOCAL_TZ = ZoneInfo("America/Mexico_City")
KNOWN_LIMIT = 150
_TRACKING_PARAMS = {"fbclid", "gclid", "ref", "source"}
_TRACKING_PREFIXES = ("utm_", "mc_")

_run_lock = asyncio.Lock()
_tasks: set[asyncio.Task] = set()


def is_running() -> bool:
    return _run_lock.locked()


def today_local() -> date:
    return datetime.now(LOCAL_TZ).date()


async def get_config(session: AsyncSession) -> SearchConfig:
    config = await session.get(SearchConfig, 1)
    if config is None:
        config = SearchConfig(
            id=1,
            profile_text="",
            preferences=Preferences().model_dump(),
            schedule=Schedule().model_dump(),
        )
        session.add(config)
        await session.commit()
    return config


# --- URL handling ---

def _is_tracking(key: str) -> bool:
    key = key.lower()
    return key in _TRACKING_PARAMS or key.startswith(_TRACKING_PREFIXES)


def clean_url(url: str) -> str:
    """Drop tracking parameters (web search results come back with utm_source=openai)."""
    parts = urlsplit(url.strip())
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if not _is_tracking(k)])
    return urlunsplit(parts._replace(query=query, fragment=""))


def dedupe_key(url: str) -> str:
    parts = urlsplit(clean_url(url))
    host = parts.netloc.lower().removeprefix("www.")
    query = urlencode(sorted(parse_qsl(parts.query)))
    return (host + parts.path.rstrip("/") + ("?" + query if query else ""))[:600]


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def _blank_to_none(value: str | None) -> str | None:
    return value.strip() or None if value else None


# --- saving ---

def _apply(opp: Opportunity, item: FoundOpportunity, url: str) -> None:
    opp.title = item.title.strip()[:400]
    opp.summary = item.summary.strip()
    opp.content = _blank_to_none(item.content)
    opp.url = url
    reg_url = _blank_to_none(item.registration_url)
    opp.registration_url = clean_url(reg_url) if reg_url and reg_url.startswith("http") else None
    opp.source_name = _blank_to_none(item.source_name)
    opp.category = item.category
    opp.importance = min(5, max(1, item.importance))
    opp.tags = [t.strip() for t in item.tags if t.strip()]
    opp.deadline = _parse_date(item.deadline)
    opp.deadline_note = _blank_to_none(item.deadline_note)
    opp.event_start = _parse_date(item.event_start)
    opp.event_end = _parse_date(item.event_end)
    opp.registration_status = _blank_to_none(item.registration_status)
    opp.modality = item.modality
    opp.city = _blank_to_none(item.city)
    opp.country = _blank_to_none(item.country)
    opp.cost = _blank_to_none(item.cost)
    opp.prize_text = _blank_to_none(item.prize_text)
    opp.prize_amount_usd = item.prize_amount_usd if item.prize_amount_usd and item.prize_amount_usd > 0 else None
    opp.eligibility = _blank_to_none(item.eligibility)
    opp.requirements = [r.strip() for r in item.requirements if r.strip()]


async def save_results(
    session: AsyncSession,
    run: SearchRun,
    result: SearchResult,
    refs: dict[int, Project],
    today: date,
) -> tuple[int, int]:
    """Upsert the found opportunities. Returns (valid items, newly inserted)."""
    found = new = 0
    seen: set[str] = set()
    for item in result.opportunities:
        url = item.url.strip()
        if not url.startswith(("http://", "https://")) or not item.title.strip():
            continue
        deadline = _parse_date(item.deadline)
        if deadline and deadline < today:
            continue
        url = clean_url(url)
        key = dedupe_key(url)
        if key in seen:
            continue
        seen.add(key)

        opp = await session.scalar(select(Opportunity).where(Opportunity.dedupe_key == key))
        if opp is None:
            opp = Opportunity(dedupe_key=key, run_id=run.id, fits=[])
            session.add(opp)
            new += 1
        # A re-found item refreshes its data but keeps review_status / is_saved.
        _apply(opp, item, url)

        notes: dict[uuid.UUID, str | None] = {}
        for fit in item.fit_projects:
            project = refs.get(fit.project_ref)
            if project is not None:
                notes[project.id] = _blank_to_none(fit.note)
        existing = {f.project_id: f for f in opp.fits}
        opp.fits = [
            _with_note(existing.get(pid) or OpportunityProject(project_id=pid), note)
            for pid, note in notes.items()
        ]
        found += 1
    await session.flush()
    return found, new


def _with_note(fit: OpportunityProject, note: str | None) -> OpportunityProject:
    fit.note = note
    return fit


# --- OpenAI ---

async def call_openai(user_input: str) -> tuple[SearchResult, int | None]:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("Falta OPENAI_API_KEY en el archivo .env del backend")
    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=900, max_retries=1)
    tools = [
        {
            "type": "web_search",
            "user_location": {"type": "approximate", "country": "MX", "region": "Jalisco", "city": "Guadalajara"},
        }
    ]
    tokens = 0
    try:
        response = await client.responses.parse(
            model=settings.openai_model,
            instructions=INSTRUCTIONS,
            input=user_input,
            tools=tools,
            text_format=SearchResult,
        )
    except BadRequestError as exc:
        # Some models can't combine web search with structured output: search first, structure after.
        log.warning("Búsqueda con salida estructurada rechazada (%s); usando dos pasos", exc)
        raw = await client.responses.create(
            model=settings.openai_model, instructions=INSTRUCTIONS, input=user_input, tools=tools
        )
        tokens += raw.usage.total_tokens if raw.usage else 0
        response = await client.responses.parse(
            model=settings.openai_model,
            instructions=(
                "Convierte el siguiente reporte al esquema indicado sin agregar ni inventar datos. "
                "Lo que no aparezca en el reporte va en null."
            ),
            input=raw.output_text,
            text_format=SearchResult,
        )
    tokens += response.usage.total_tokens if response.usage else 0
    if response.output_parsed is None:
        raise RuntimeError("El modelo no devolvió un resultado con el formato esperado")
    return response.output_parsed, tokens or None


# --- runs ---

async def create_run(session: AsyncSession, trigger: str, user_id: uuid.UUID | None = None) -> SearchRun:
    run = SearchRun(trigger=trigger, triggered_by=user_id)
    session.add(run)
    await session.commit()
    return run


def launch(run_id: uuid.UUID) -> None:
    task = asyncio.create_task(execute_run(run_id))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def execute_run(run_id: uuid.UUID) -> None:
    async with _run_lock:
        async with db.SessionLocal() as session:
            try:
                run = await session.get(SearchRun, run_id)
                config = await get_config(session)
                prefs = Preferences.model_validate(config.preferences or {})
                today = today_local()
                projects = list(
                    await session.scalars(select(Project).where(Project.is_active).order_by(Project.name))
                )
                known = list(
                    await session.scalars(
                        select(Opportunity)
                        .where(or_(Opportunity.deadline.is_(None), Opportunity.deadline >= today))
                        .order_by(Opportunity.discovered_at.desc())
                        .limit(KNOWN_LIMIT)
                    )
                )
                user_input, refs = build_input(config.profile_text, prefs, projects, known, today)
                result, tokens = await call_openai(user_input)
                run.items_found, run.items_new = await save_results(session, run, result, refs, today)
                run.total_tokens = tokens
                run.status = "ok"
                run.finished_at = utcnow()
                await session.commit()
            except Exception as exc:
                log.exception("La búsqueda %s falló", run_id)
                await session.rollback()
                await session.execute(
                    update(SearchRun)
                    .where(SearchRun.id == run_id)
                    .values(status="error", error=str(exc)[:2000], finished_at=utcnow())
                )
                await session.commit()


async def fail_interrupted_runs(session: AsyncSession) -> None:
    """Runs left en_curso by a previous process can never finish."""
    await session.execute(
        update(SearchRun)
        .where(SearchRun.status == "en_curso")
        .values(status="error", error="El servidor se reinició durante la búsqueda", finished_at=utcnow())
    )
    await session.commit()
