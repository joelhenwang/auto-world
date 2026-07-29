"""Phase-run persistence record aligned to ``phase_run`` table."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract


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
