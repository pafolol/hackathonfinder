"""Structured output the model must return.

Every field is required (nullable where it may be unknown) because OpenAI's
strict JSON schema mode does not allow optional properties.
"""

from typing import Literal

from pydantic import BaseModel


class FoundFit(BaseModel):
    project_ref: int
    note: str


class FoundOpportunity(BaseModel):
    title: str
    summary: str
    content: str | None
    url: str
    registration_url: str | None
    source_name: str | None
    category: Literal["hackathon", "convocatoria", "aceleradora", "competencia", "fondo", "otro"]
    importance: int
    tags: list[str]
    deadline: str | None
    deadline_note: str | None
    event_start: str | None
    event_end: str | None
    registration_status: str | None
    modality: Literal["presencial", "en_linea", "hibrido"] | None
    city: str | None
    country: str | None
    cost: str | None
    prize_text: str | None
    prize_amount_usd: int | None
    eligibility: str | None
    requirements: list[str]
    fit_projects: list[FoundFit]


class SearchResult(BaseModel):
    opportunities: list[FoundOpportunity]
