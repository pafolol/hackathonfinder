import asyncio
from datetime import date, timedelta

from sqlalchemy import select

from app import db
from app.models import Opportunity, Project, SearchRun
from app.schemas import Preferences
from app.search import runner
from app.search.prompt import build_input
from app.search.schema import FoundFit, FoundOpportunity, SearchResult

TODAY = runner.today_local()


def found(**overrides) -> FoundOpportunity:
    data = dict(
        title="Hackathon de IA",
        summary="Hackathon de 48 horas.",
        content=None,
        url="https://www.ejemplo.mx/hack/?utm_source=openai",
        registration_url=None,
        source_name="Ejemplo",
        category="hackathon",
        importance=9,
        tags=["IA", " "],
        deadline=(TODAY + timedelta(days=10)).isoformat(),
        deadline_note=None,
        event_start=None,
        event_end=None,
        registration_status="abierto",
        modality="hibrido",
        city="Guadalajara",
        country="México",
        cost="Gratis",
        prize_text="Hasta $5,000 USD",
        prize_amount_usd=5000,
        eligibility=None,
        requirements=["Equipo de 3"],
        fit_projects=[],
    )
    data.update(overrides)
    return FoundOpportunity(**data)


def test_dedupe_key_ignores_tracking_scheme_and_www():
    a = runner.dedupe_key("https://www.ejemplo.mx/hack/?utm_source=openai&b=2&a=1#top")
    b = runner.dedupe_key("http://ejemplo.mx/hack?a=1&b=2")
    assert a == b == "ejemplo.mx/hack?a=1&b=2"


def test_prompt_includes_context_and_numbers_projects():
    projects = [Project(name="AgroSense", description="Sensores IoT", stage="MVP", technologies=["IoT"])]
    known = [Opportunity(title="Ya vista", url="https://ya.mx")]
    prefs = Preferences(keywords=["agrotech"], min_prize_usd=1000, excluded_sources=["spam.com"])
    text, refs = build_input("Perfil del área GDL", prefs, projects, known, date(2026, 10, 3))
    assert refs[1].name == "AgroSense"
    for expected in (
        "2026-10-03", "Perfil del área GDL", "1. AgroSense", "Etapa: MVP",
        "agrotech", "1000 USD", "spam.com", "Ya vista — https://ya.mx",
    ):
        assert expected in text


async def _run_and_project():
    async with db.SessionLocal() as session:
        project = Project(name="AgroSense", description="", technologies=[])
        session.add(project)
        await session.commit()
        run = await runner.create_run(session, "manual")
    return run, project


async def test_save_results_filters_dedupes_and_links():
    run, project = await _run_and_project()
    result = SearchResult(
        opportunities=[
            found(fit_projects=[FoundFit(project_ref=1, note="Encaja por IoT"), FoundFit(project_ref=99, note="x")]),
            found(title="Duplicado", url="https://ejemplo.mx/hack"),
            found(title="Cerrada", url="https://ejemplo.mx/vieja", deadline=(TODAY - timedelta(days=1)).isoformat()),
            found(title="Sin enlace", url="n/a"),
        ]
    )
    async with db.SessionLocal() as session:
        counts = await runner.save_results(session, run, result, {1: project}, TODAY)
        await session.commit()
    assert counts == (1, 1)

    async with db.SessionLocal() as session:
        opp = (await session.scalars(select(Opportunity))).one()
    assert opp.url == "https://www.ejemplo.mx/hack/"
    assert opp.importance == 5
    assert opp.tags == ["IA"]
    assert [(f.project.name, f.note) for f in opp.fits] == [("AgroSense", "Encaja por IoT")]


async def test_refound_item_updates_but_keeps_review_state():
    run, project = await _run_and_project()
    async with db.SessionLocal() as session:
        await runner.save_results(
            session, run, SearchResult(opportunities=[found(fit_projects=[FoundFit(project_ref=1, note="a")])]),
            {1: project}, TODAY,
        )
        await session.commit()
    async with db.SessionLocal() as session:
        opp = (await session.scalars(select(Opportunity))).one()
        opp.review_status = "revisada"
        opp.is_saved = True
        await session.commit()

    async with db.SessionLocal() as session:
        counts = await runner.save_results(
            session, run, SearchResult(opportunities=[found(prize_text="Hasta $8,000 USD", fit_projects=[])]),
            {1: project}, TODAY,
        )
        await session.commit()
    assert counts == (1, 0)

    async with db.SessionLocal() as session:
        opp = (await session.scalars(select(Opportunity))).one()
    assert (opp.prize_text, opp.review_status, opp.is_saved, opp.fits) == ("Hasta $8,000 USD", "revisada", True, [])


async def _wait_for_run(client, run_id):
    for _ in range(100):
        run = (await client.get(f"/api/runs/{run_id}")).json()
        if run["status"] != "en_curso":
            return run
        await asyncio.sleep(0.02)
    raise AssertionError("la búsqueda no terminó")


async def test_run_endpoint_end_to_end(client, monkeypatch):
    project = (await client.post("/api/projects", json={"name": "AgroSense"})).json()
    seen_inputs = []

    async def fake_openai(user_input):
        seen_inputs.append(user_input)
        return SearchResult(
            opportunities=[
                found(fit_projects=[FoundFit(project_ref=1, note="Encaja")]),
                found(title="Fondo semilla", url="https://fondo.org/semilla", category="fondo", deadline=None),
            ]
        ), 1234

    monkeypatch.setattr(runner, "call_openai", fake_openai)

    started = await client.post("/api/runs")
    assert started.status_code == 202
    run = await _wait_for_run(client, started.json()["id"])
    assert (run["status"], run["items_found"], run["items_new"], run["total_tokens"]) == ("ok", 2, 2, 1234)
    assert "1. AgroSense" in seen_inputs[0]

    items = (await client.get("/api/opportunities")).json()
    assert [i["title"] for i in items] == ["Hackathon de IA", "Fondo semilla"]  # sin fecha límite al final
    assert items[0]["fit_projects"][0]["name"] == "AgroSense"

    by_project = (await client.get("/api/opportunities", params={"project_id": project["id"]})).json()
    assert len(by_project) == 1
    assert len((await client.get("/api/opportunities", params={"q": "semilla"})).json()) == 1
    assert len((await client.get("/api/opportunities", params={"category": "fondo"})).json()) == 1

    opp_id = items[0]["id"]
    patched = await client.patch(f"/api/opportunities/{opp_id}", json={"review_status": "descartada"})
    assert patched.json()["review_status"] == "descartada"
    assert len((await client.get("/api/opportunities")).json()) == 1

    # A second run finds the same things: nothing new, and the known list is sent to the model.
    second = await _wait_for_run(client, (await client.post("/api/runs")).json()["id"])
    assert (second["items_found"], second["items_new"]) == (2, 0)
    assert "https://fondo.org/semilla" in seen_inputs[1]


async def test_failed_run_is_recorded(client):
    # No OPENAI_API_KEY configured in tests.
    run = await _wait_for_run(client, (await client.post("/api/runs")).json()["id"])
    assert run["status"] == "error"
    assert "OPENAI_API_KEY" in run["error"]
    async with db.SessionLocal() as session:
        assert (await session.scalars(select(SearchRun))).one().finished_at is not None
