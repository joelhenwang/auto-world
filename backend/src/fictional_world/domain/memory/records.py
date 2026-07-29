"""Memory and embedding metadata contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.enums import MemoryKind, Visibility


class MemoryRecord(StrictContract):
    memory_id: UUID
    owner_character_id: UUID
    kind: MemoryKind
    text: str = Field(min_length=1, max_length=4_000)
    salience: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    source_event_ids: tuple[UUID, ...] = ()
    source_observation_ids: tuple[UUID, ...] = ()
    source_claim_ids: tuple[UUID, ...] = ()
    referenced_entity_ids: tuple[UUID, ...] = ()
    visibility: Visibility = Visibility.PRIVATE
    created_absolute_phase_index: int = Field(ge=0)
    last_recalled_absolute_phase_index: int | None = Field(default=None, ge=0)
    active: bool = True
    created_at: datetime


class EmbeddingMetadata(StrictContract):
    embedding_id: UUID
    owner_object_id: UUID
    owner_object_type: Literal["memory", "summary", "event", "lore"]
    model_slug: str
    dimensions: Literal[2048] = 2048
    prefix_type: Literal["query", "passage"]
    content_hash: str = Field(min_length=32, max_length=128)
    created_at: datetime
