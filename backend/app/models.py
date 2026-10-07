import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# JSONB on Postgres, plain JSON elsewhere (tests run on SQLite).
JSONType = JSON().with_variant(JSONB(), "postgresql")

CATEGORIES = ("hackathon", "convocatoria", "aceleradora", "competencia", "fondo", "otro")
REVIEW_STATUSES = ("nueva", "revisada", "descartada")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="staff")  # admin | staff
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    stage: Mapped[str | None] = mapped_column(String(60))
    sector: Mapped[str | None] = mapped_column(String(120))
    technologies: Mapped[list[str]] = mapped_column(JSONType, default=list)
    team: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SearchConfig(Base):
    """Single row (id = 1): the context that steers every search."""

    __tablename__ = "search_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_text: Mapped[str] = mapped_column(Text, default="")
    preferences: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    schedule: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SearchRun(Base):
    __tablename__ = "search_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    trigger: Mapped[str] = mapped_column(String(20))  # manual | programada
    triggered_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(20), default="en_curso")  # en_curso | ok | error
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    items_found: Mapped[int] = mapped_column(Integer, default=0)
    items_new: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    total_tokens: Mapped[int | None] = mapped_column(Integer)


class Opportunity(Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        Index("ix_opportunities_discovered_at", "discovered_at"),
        Index("ix_opportunities_deadline", "deadline"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(400))
    summary: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(1000))
    registration_url: Mapped[str | None] = mapped_column(String(1000))
    source_name: Mapped[str | None] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(30), default="otro")
    importance: Mapped[int] = mapped_column(Integer, default=3)
    tags: Mapped[list[str]] = mapped_column(JSONType, default=list)

    deadline: Mapped[date | None] = mapped_column(Date)
    deadline_note: Mapped[str | None] = mapped_column(Text)
    event_start: Mapped[date | None] = mapped_column(Date)
    event_end: Mapped[date | None] = mapped_column(Date)
    registration_status: Mapped[str | None] = mapped_column(String(60))
    modality: Mapped[str | None] = mapped_column(String(30))  # presencial | en_linea | hibrido
    city: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str | None] = mapped_column(String(120))
    cost: Mapped[str | None] = mapped_column(String(200))
    prize_text: Mapped[str | None] = mapped_column(Text)
    prize_amount_usd: Mapped[int | None] = mapped_column(Integer)
    eligibility: Mapped[str | None] = mapped_column(Text)
    requirements: Mapped[list[str]] = mapped_column(JSONType, default=list)
    extra: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)

    dedupe_key: Mapped[str] = mapped_column(String(600), unique=True)
    review_status: Mapped[str] = mapped_column(String(20), default="nueva")
    is_saved: Mapped[bool] = mapped_column(Boolean, default=False)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("search_runs.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    fits: Mapped[list["OpportunityProject"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan", lazy="selectin"
    )


class OpportunityProject(Base):
    """Why a given project is a good candidate for an opportunity."""

    __tablename__ = "opportunity_projects"

    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), primary_key=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    note: Mapped[str | None] = mapped_column(Text)

    opportunity: Mapped[Opportunity] = relationship(back_populates="fits")
    project: Mapped[Project] = relationship(lazy="joined")
