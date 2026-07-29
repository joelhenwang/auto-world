"""Observation persistence record aligned to ``observation`` table."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract

JsonObject = dict[str, str | int | float | bool | list[str] | dict[str, str] | None]


class ObservationPersistenceRecord(StrictContract):
    id: UUID
    world_event_id: UUID
    observer_id: UUID
    observation_type: str = Field(min_length=1, max_length=100)
    perceived_summary: str = Field(min_length=1, max_length=2_000)
    perceived_facts: JsonObject = Field(default_factory=dict)
    omitted_fact_keys: tuple[str, ...] = ()
    confidence: Decimal
    visibility_reason: str = Field(min_length=1, max_length=200)
    source_sense_tags: tuple[str, ...] = ()
    content_hash: str = Field(min_length=1, max_length=128)
    created_at: datetime | None = None
