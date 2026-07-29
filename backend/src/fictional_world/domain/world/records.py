"""World aggregate persistence records (Stage 0 surface for S0-DB-003)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract


class WorldRecord(StrictContract):
    id: UUID
    slug: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=200)
    status: str = Field(min_length=1, max_length=50)
    language: str = Field(default="en", min_length=1, max_length=32)
    content_rating: str = Field(default="young_adult_soft_dark", min_length=1, max_length=100)
    current_event_sequence: int = Field(default=0, ge=0)
    version: int = Field(default=0, ge=0)
    created_at: datetime | None = None
    ended_at: datetime | None = None


class WorldClockRecord(StrictContract):
    world_id: UUID
    generation_number: int = Field(ge=1, le=3)
    year: int
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    phase_name: str = Field(min_length=1, max_length=50)
    phase_ordinal: int = Field(ge=0, le=9)
    absolute_day_index: int = Field(ge=0)
    absolute_phase_index: int = Field(ge=0)
    resolution_mode: str = Field(min_length=1, max_length=50)
    last_event_id: UUID | None = None
    version: int = Field(default=0, ge=0)
    updated_at: datetime | None = None


class AggregateVersionRecord(StrictContract):
    world_id: UUID
    aggregate_type: str = Field(min_length=1, max_length=100)
    aggregate_id: UUID
    version: int = Field(ge=0)
    updated_at: datetime | None = None
