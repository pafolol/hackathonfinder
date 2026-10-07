import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_session
from app.models import Opportunity, OpportunityProject
from app.schemas import Category, FitProjectOut, OpportunityOut, OpportunityUpdate, ReviewStatus
from app.search.runner import today_local

router = APIRouter(prefix="/opportunities", tags=["opportunities"], dependencies=[Depends(get_current_user)])

_COLUMNS = [f for f in OpportunityOut.model_fields if f != "fit_projects"]


def to_out(opp: Opportunity) -> OpportunityOut:
    fits = sorted(opp.fits, key=lambda f: f.project.name.lower())
    return OpportunityOut(
        **{field: getattr(opp, field) for field in _COLUMNS},
        fit_projects=[FitProjectOut(project_id=f.project_id, name=f.project.name, note=f.note) for f in fits],
    )


async def _get(session: AsyncSession, opportunity_id: uuid.UUID) -> Opportunity:
    opp = await session.get(Opportunity, opportunity_id)
    if opp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Oportunidad no encontrada")
    return opp


@router.get("", response_model=list[OpportunityOut])
async def list_opportunities(
    category: Category | None = None,
    review_status: ReviewStatus | None = None,
    saved: bool | None = None,
    project_id: uuid.UUID | None = None,
    q: str | None = None,
    include_closed: bool = False,
    sort: Literal["deadline", "discovered"] = "deadline",
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Opportunity)
    if category:
        stmt = stmt.where(Opportunity.category == category)
    if review_status:
        stmt = stmt.where(Opportunity.review_status == review_status)
    else:
        stmt = stmt.where(Opportunity.review_status != "descartada")
    if saved is not None:
        stmt = stmt.where(Opportunity.is_saved == saved)
    if project_id:
        stmt = stmt.where(
            Opportunity.id.in_(
                select(OpportunityProject.opportunity_id).where(OpportunityProject.project_id == project_id)
            )
        )
    if not include_closed:
        stmt = stmt.where(or_(Opportunity.deadline.is_(None), Opportunity.deadline >= today_local()))
    for term in (q or "").split():
        like = f"%{term}%"
        stmt = stmt.where(
            or_(
                Opportunity.title.ilike(like),
                Opportunity.summary.ilike(like),
                Opportunity.source_name.ilike(like),
                Opportunity.city.ilike(like),
            )
        )
    if sort == "deadline":
        # Soonest deadline first; items without a published deadline go last.
        stmt = stmt.order_by(Opportunity.deadline.is_(None), Opportunity.deadline, Opportunity.importance.desc())
    else:
        stmt = stmt.order_by(Opportunity.discovered_at.desc())
    return [to_out(o) for o in await session.scalars(stmt.limit(300))]


@router.get("/{opportunity_id}", response_model=OpportunityOut)
async def get_opportunity(opportunity_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    return to_out(await _get(session, opportunity_id))


@router.patch("/{opportunity_id}", response_model=OpportunityOut)
async def update_opportunity(
    opportunity_id: uuid.UUID, body: OpportunityUpdate, session: AsyncSession = Depends(get_session)
):
    opp = await _get(session, opportunity_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(opp, field, value)
    await session.commit()
    return to_out(opp)


@router.delete("/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_opportunity(opportunity_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    await session.delete(await _get(session, opportunity_id))
    await session.commit()
