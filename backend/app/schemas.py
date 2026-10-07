import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Category = Literal["hackathon", "convocatoria", "aceleradora", "competencia", "fondo", "otro"]
ReviewStatus = Literal["nueva", "revisada", "descartada"]
Role = Literal["admin", "staff"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- auth / users ---

class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORMModel):
    id: uuid.UUID
    email: str
    name: str
    role: Role
    is_active: bool
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=200)
    role: Role = "staff"


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=200)


# --- projects ---

class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    stage: str | None = None
    sector: str | None = None
    technologies: list[str] = []
    team: str | None = None
    url: str | None = None
    is_active: bool = True


class ProjectOut(ORMModel, ProjectIn):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# --- context ---

class Preferences(BaseModel):
    types: list[Category] = ["hackathon", "convocatoria", "aceleradora", "competencia", "fondo"]
    regions: list[str] = ["México", "Latinoamérica", "Global (en línea)"]
    modalities: list[Literal["presencial", "en_linea", "hibrido"]] = ["presencial", "en_linea", "hibrido"]
    min_prize_usd: int | None = Field(default=None, ge=0)
    deadline_window_days: int = Field(default=120, ge=7, le=730)
    keywords: list[str] = []
    priority_sources: list[str] = []
    excluded_sources: list[str] = []
    max_results: int = Field(default=15, ge=1, le=40)


class Schedule(BaseModel):
    enabled: bool = False
    frequency: Literal["daily", "weekly"] = "weekly"
    weekday: int = Field(default=0, ge=0, le=6)  # 0 = lunes
    hour: int = Field(default=8, ge=0, le=23)
    timezone: str = "America/Mexico_City"


class ContextIn(BaseModel):
    profile_text: str = ""
    preferences: Preferences = Preferences()
    schedule: Schedule = Schedule()


class ContextOut(ContextIn):
    updated_at: datetime | None = None
    next_run_at: datetime | None = None


# --- runs ---

class RunOut(ORMModel):
    id: uuid.UUID
    trigger: str
    triggered_by: uuid.UUID | None
    status: str
    started_at: datetime
    finished_at: datetime | None
    items_found: int
    items_new: int
    error: str | None
    total_tokens: int | None


# --- opportunities ---

class FitProjectOut(BaseModel):
    project_id: uuid.UUID
    name: str
    note: str | None


class OpportunityOut(BaseModel):
    id: uuid.UUID
    title: str
    summary: str
    content: str | None
    url: str
    registration_url: str | None
    source_name: str | None
    category: str
    importance: int
    tags: list[str]
    deadline: date | None
    deadline_note: str | None
    event_start: date | None
    event_end: date | None
    registration_status: str | None
    modality: str | None
    city: str | None
    country: str | None
    cost: str | None
    prize_text: str | None
    prize_amount_usd: int | None
    eligibility: str | None
    requirements: list[str]
    extra: dict[str, Any]
    review_status: str
    is_saved: bool
    discovered_at: datetime
    fit_projects: list[FitProjectOut]


class OpportunityUpdate(BaseModel):
    review_status: ReviewStatus | None = None
    is_saved: bool | None = None
    importance: int | None = Field(default=None, ge=1, le=5)
