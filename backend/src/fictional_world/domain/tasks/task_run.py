"""Task-run domain DTO (handbook ``06`` §17.1 surface for Stage 0)."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.enums import TaskState

# Bounded JSON-ish payload without recursive type aliases (Pydantic recursion).
JsonScalar = str | int | float | bool | None
JsonObject = dict[str, JsonScalar | list[JsonScalar] | dict[str, JsonScalar]]


class TaskRun(StrictContract):
    id: UUID
    task_type: str = Field(min_length=1, max_length=200)
    world_id: UUID | None = None
    phase_run_id: UUID | None = None
    scene_id: UUID | None = None
    subject_entity_id: UUID | None = None
    state: TaskState
    priority: int = Field(ge=0)
    payload: JsonObject = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=1, max_length=200)
    attempt_count: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=3, ge=1)
    available_at: datetime
    lease_owner: str | None = Field(default=None, max_length=200)
    lease_expires_at: datetime | None = None
    heartbeat_at: datetime | None = None
    result_reference: Mapping[str, JsonScalar] | None = None
    error_code: str | None = Field(default=None, max_length=100)
    error_detail: JsonObject | None = None
    created_at: datetime
    completed_at: datetime | None = None
