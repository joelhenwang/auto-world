"""Observation / claim / belief / secret persistence records."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract

JsonObject = dict[str, Any]


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


class ClaimPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    source_event_id: UUID
    speaker_id: UUID
    proposition_key: str | None = Field(default=None, max_length=200)
    proposition_text: str = Field(min_length=1, max_length=4_000)
    truth_status: str = Field(default="unknown", min_length=1, max_length=50)
    intent_class: str | None = Field(default=None, max_length=100)
    confidence_expressed: Decimal | None = None
    created_at: datetime | None = None
    listener_ids: tuple[UUID, ...] = ()


class BeliefPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    character_id: UUID
    proposition_key: str = Field(min_length=1, max_length=200)
    belief_text: str = Field(min_length=1, max_length=4_000)
    confidence: Decimal
    status: str = Field(default="active", min_length=1, max_length=50)
    first_source_observation_id: UUID | None = None
    last_source_event_id: UUID | None = None
    evidence_summary: JsonObject = Field(default_factory=dict)
    version: int = Field(default=0, ge=0)
    updated_at: datetime | None = None
    created_at: datetime | None = None


class SecretAccessPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    secret_key: str = Field(min_length=1, max_length=200)
    owner_character_id: UUID
    holder_character_id: UUID
    access_level: str = Field(min_length=1, max_length=50)
    granted_event_id: UUID | None = None
    revoked_event_id: UUID | None = None
    created_at: datetime | None = None
