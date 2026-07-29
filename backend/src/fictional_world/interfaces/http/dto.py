"""HTTP response/request DTOs for Stage 0 API."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthLiveResponse(ApiModel):
    status: str = "ok"


class HealthReadyResponse(ApiModel):
    status: str
    database: str
    detail: str | None = None


class WorldRead(ApiModel):
    id: UUID
    slug: str
    name: str
    status: str
    current_event_sequence: int
    version: int


class ClockRead(ApiModel):
    world_id: UUID
    generation_number: int
    year: int
    month: int
    day: int
    phase_name: str
    phase_ordinal: int
    absolute_day_index: int
    absolute_phase_index: int
    resolution_mode: str
    version: int


class PhaseRead(ApiModel):
    id: UUID
    world_id: UUID
    absolute_phase_index: int
    phase_name: str
    state: str
    resolution_mode: str
    expected_character_count: int
    completed_character_count: int
    version: int
    started_at: datetime | None = None
    completed_at: datetime | None = None


class EventRead(ApiModel):
    id: UUID
    world_id: UUID
    sequence_number: int
    absolute_phase_index: int
    phase_run_id: UUID | None
    event_type: str
    canonical_summary: str
    structured_facts: dict[str, Any] = Field(default_factory=dict)
    importance: Decimal
    visibility_class: str
    source_kind: str
    idempotency_key: str
    committed_at: datetime | None = None


class AdvancePhaseResponse(ApiModel):
    phase_run_id: UUID
    absolute_phase_index: int
    phase_name: str
    already_completed: bool
    snapshot_id: UUID | None
    event_ids: list[UUID]


class ReconcileResponse(ApiModel):
    world_id: UUID
    active_phase_id: UUID | None
    tasks_created: int
    phase_completed: bool
    notes: list[str]
