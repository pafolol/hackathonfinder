import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_session
from app.models import SearchRun, User
from app.schemas import RunOut
from app.search import runner

router = APIRouter(prefix="/runs", tags=["runs"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[RunOut])
async def list_runs(session: AsyncSession = Depends(get_session)):
    return list(await session.scalars(select(SearchRun).order_by(SearchRun.started_at.desc()).limit(50)))


@router.get("/{run_id}", response_model=RunOut)
async def get_run(run_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    run = await session.get(SearchRun, run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Búsqueda no encontrada")
    return run


@router.post("", response_model=RunOut, status_code=status.HTTP_202_ACCEPTED)
async def start_run(session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    running = await session.scalar(select(SearchRun).where(SearchRun.status == "en_curso"))
    if runner.is_running() or running is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya hay una búsqueda en curso")
    run = await runner.create_run(session, "manual", user.id)
    runner.launch(run.id)
    return run
