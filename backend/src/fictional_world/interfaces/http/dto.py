"""HTTP response/request DTOs for Stage 0 API."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
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


class PauseWorldRequest(ApiModel):
    mode: Literal["after_safe_boundary", "immediate"] = "after_safe_boundary"


class RuntimeCommandResponse(ApiModel):
    world_id: UUID
    status: str
    phase: AdvancePhaseResponse | None = None


class StreamEventRead(ApiModel):
    id: UUID
    world_id: UUID
    sequence: int
    event_type: str
    occurred_at: datetime
    fictional_time: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    schema_version: str
    phase_run_id: UUID | None = None
    scene_id: UUID | None = None
    world_event_id: UUID | None = None
    perspective_scope: str


class SceneSummaryRead(ApiModel):
    id: UUID
    phase_run_id: UUID
    snapshot_id: UUID
    location_id: UUID | None
    scene_type: str
    state: str
    priority_score: Decimal
    beat_budget: int
    participant_ids: list[UUID]
    resolution_level: str | None = None
    canonical_summary: str | None = None
    narration: str | None = None


class CharacterSummaryRead(ApiModel):
    id: UUID
    name: str
    location_id: UUID | None
    life_status: str
    stamina: Decimal
    energy: Decimal
    pain: Decimal
    stress: Decimal
    active_activity_id: UUID | None
    state_version: int


class AcquirePlayerControlRequest(ApiModel):
    controller_id: str = Field(min_length=1, max_length=200)
    idempotency_key: str = Field(min_length=1, max_length=200)


class ReleasePlayerControlRequest(ApiModel):
    controller_id: str = Field(min_length=1, max_length=200)
    session_id: UUID


class PlayerControlRead(ApiModel):
    id: UUID
    world_id: UUID
    character_id: UUID
    controller_id: str
    status: str
    acquired_at: datetime
    released_at: datetime | None
    waiting_input: bool
    phase_run_id: UUID | None
    version: int


class PlayerActionRequest(ApiModel):
    session_id: UUID
    controller_id: str = Field(min_length=1, max_length=200)
    idempotency_key: str = Field(min_length=1, max_length=200)
    action_family: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=2_000)
    utterance: str | None = Field(default=None, max_length=1_000)
    target_entity_ids: list[UUID] = Field(default_factory=list)
    target_location_id: UUID | None = None


class PlayerActionResponse(ApiModel):
    command_id: UUID
    status: str
    already_existed: bool
