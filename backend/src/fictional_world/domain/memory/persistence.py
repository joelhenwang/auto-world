"""Recent-memory persistence record aligned to ``recent_memory`` table."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract


class RecentMemoryRecord(StrictContract):
    id: UUID
    world_id: UUID
    owner_character_id: UUID
    memory_type: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1, max_length=4_000)
    salience: Decimal
    confidence: Decimal
    emotional_weight: Decimal
    visibility: str = Field(min_length=1, max_length=50)
    occurred_phase_index: int = Field(ge=0)
    created_phase_index: int = Field(ge=0)
    last_recalled_phase_index: int | None = Field(default=None, ge=0)
    recall_count: int = Field(default=0, ge=0)
    decay_score: Decimal
    status: str = Field(min_length=1, max_length=50)
    content_hash: str = Field(min_length=1, max_length=128)
    summary_version: int = Field(default=1, ge=1)
    source_event_id: UUID | None = None
    source_observation_id: UUID | None = None
    created_at: datetime | None = None
