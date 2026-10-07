import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_session
from app.models import Project
from app.schemas import ProjectIn, ProjectOut

router = APIRouter(prefix="/projects", tags=["projects"], dependencies=[Depends(get_current_user)])


def _clean(body: ProjectIn) -> dict:
    data = body.model_dump()
    data["name"] = data["name"].strip()
    data["technologies"] = [t.strip() for t in data["technologies"] if t.strip()]
    for field in ("stage", "sector", "team", "url"):
        data[field] = (data[field] or "").strip() or None
    return data


async def _get(session: AsyncSession, project_id: uuid.UUID) -> Project:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado")
    return project


@router.get("", response_model=list[ProjectOut])
async def list_projects(session: AsyncSession = Depends(get_session)):
    return list(await session.scalars(select(Project).order_by(Project.is_active.desc(), Project.name)))


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(body: ProjectIn, session: AsyncSession = Depends(get_session)):
    project = Project(**_clean(body))
    session.add(project)
    await session.commit()
    return project


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(project_id: uuid.UUID, body: ProjectIn, session: AsyncSession = Depends(get_session)):
    project = await _get(session, project_id)
    for field, value in _clean(body).items():
        setattr(project, field, value)
    await session.commit()
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    await session.delete(await _get(session, project_id))
    await session.commit()
