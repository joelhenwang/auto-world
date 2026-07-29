"""Phase-run and snapshot persistence records."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract

JsonObject = dict[str, Any]


class PhaseRunRecord(StrictContract):
    id: UUID
    world_id: UUID
    absolute_phase_index: int = Field(ge=0)
    phase_name: str = Field(min_length=1, max_length=50)
    resolution_mode: str = Field(min_length=1, max_length=50)
    state: str = Field(min_length=1, max_length=50)
    expected_character_count: int = Field(ge=0)
    completed_character_count: int = Field(default=0, ge=0)
    expected_scene_count: int | None = Field(default=None, ge=0)
    completed_scene_count: int = Field(default=0, ge=0)
    request_reservation_id: UUID | None = None
    idempotency_key: str = Field(min_length=1, max_length=200)
    error_code: str | None = None
    error_detail: dict[str, str | int | float | bool | None] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    version: int = Field(default=0, ge=0)


class PhaseSnapshotCharacterRecord(StrictContract):
    snapshot_id: UUID
    character_id: UUID
    character_state_version: int = Field(ge=0)
    card_version_id: UUID
    location_id: UUID | None = None
    active_activity_id: UUID | None = None
    context_source_hash: str = Field(min_length=1, max_length=128)
    eligibility_status: str = Field(min_length=1, max_length=50)
    eligibility_reason: str | None = Field(default=None, max_length=500)


class PhaseSnapshotRecord(StrictContract):
    id: UUID
    phase_run_id: UUID
    world_id: UUID
    source_event_sequence: int = Field(ge=0)
    world_clock_version: int = Field(ge=0)
    state_manifest: JsonObject = Field(default_factory=dict)
    state_hash: str = Field(min_length=1, max_length=128)
    sealed_at: datetime
    created_at: datetime | None = None
    characters: tuple[PhaseSnapshotCharacterRecord, ...] = ()
