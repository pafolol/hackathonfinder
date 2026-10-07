from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_session
from app.models import SearchConfig
from app.schemas import ContextIn, ContextOut, Preferences, Schedule
from app.search import scheduler
from app.search.runner import get_config

router = APIRouter(prefix="/context", tags=["context"], dependencies=[Depends(get_current_user)])


def _out(config: SearchConfig) -> ContextOut:
    return ContextOut(
        profile_text=config.profile_text,
        preferences=Preferences.model_validate(config.preferences or {}),
        schedule=Schedule.model_validate(config.schedule or {}),
        updated_at=config.updated_at,
        next_run_at=scheduler.next_run_at(),
    )


@router.get("", response_model=ContextOut)
async def read_context(session: AsyncSession = Depends(get_session)):
    return _out(await get_config(session))


@router.put("", response_model=ContextOut)
async def write_context(body: ContextIn, session: AsyncSession = Depends(get_session)):
    try:
        ZoneInfo(body.schedule.timezone)
    except (ZoneInfoNotFoundError, ValueError):
        raise HTTPException(422, "Zona horaria no válida")
    config = await get_config(session)
    config.profile_text = body.profile_text.strip()
    config.preferences = body.preferences.model_dump()
    config.schedule = body.schedule.model_dump()
    await session.commit()
    scheduler.apply_schedule(body.schedule)
    return _out(config)
