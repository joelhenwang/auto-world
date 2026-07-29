"""Durable user command record for player action attempts."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract


class UserCommandRecord(StrictContract):
    id: UUID
    world_id: UUID
    actor_role: str = Field(min_length=1, max_length=50)
    command_type: str = Field(min_length=1, max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)
    target_entity_id: UUID | None = None
    requested_phase_boundary: str | None = Field(default=None, max_length=50)
    idempotency_key: str = Field(min_length=1, max_length=200)
    permission_decision: str = Field(min_length=1, max_length=50)
    status: str = Field(min_length=1, max_length=50)
    resulting_event_id: UUID | None = None
    resulting_task_id: UUID | None = None
    created_at: datetime | None = None
    decided_at: datetime | None = None
    completed_at: datetime | None = None


__all__ = ["UserCommandRecord"]
