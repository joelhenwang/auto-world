"""Event and effect persistence records for repository boundaries."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract

# Bounded JSONB audit blobs — nested objects allowed (Stage 0 persistence DTOs).
JsonObject = dict[str, Any]


class EventEffectRecord(StrictContract):
    id: UUID
    world_event_id: UUID
    effect_index: int = Field(ge=0)
    effect_type: str = Field(min_length=1, max_length=100)
    target_entity_id: UUID | None = None
    effect_payload: JsonObject = Field(default_factory=dict)
    previous_state: JsonObject = Field(default_factory=dict)
    resulting_state: JsonObject = Field(default_factory=dict)
    target_version_before: int | None = None
    target_version_after: int | None = None
    source_attempt_ids: tuple[UUID, ...] = ()
    validation_manifest: JsonObject = Field(default_factory=dict)


class WorldEventRecord(StrictContract):
    id: UUID
    world_id: UUID
    sequence_number: int = Field(ge=1)
    absolute_phase_index: int = Field(ge=0)
    phase_run_id: UUID | None = None
    scene_id: UUID | None = None
    event_type: str = Field(min_length=1, max_length=100)
    initiator_entity_id: UUID | None = None
    location_id: UUID | None = None
    canonical_summary: str = Field(min_length=1, max_length=2_000)
    structured_facts: JsonObject = Field(default_factory=dict)
    importance: Decimal
    visibility_class: str = Field(min_length=1, max_length=50)
    source_kind: str = Field(min_length=1, max_length=50)
    source_model_profile_id: UUID | None = None
    prompt_version_id: UUID | None = None
    random_seed: int | None = None
    idempotency_key: str = Field(min_length=1, max_length=200)
    supersedes_event_id: UUID | None = None
    consistency_status: str = Field(min_length=1, max_length=50)
    committed_at: datetime | None = None
    director_provenance: JsonObject | None = None
    npc_provenance: JsonObject | None = None
    effects: tuple[EventEffectRecord, ...] = ()


class OutboxMessageRecord(StrictContract):
    id: UUID
    world_event_id: UUID | None = None
    message_type: str = Field(min_length=1, max_length=100)
    payload: JsonObject = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=1, max_length=200)
    state: str = Field(min_length=1, max_length=50)
    attempt_count: int = Field(default=0, ge=0)
    available_at: datetime | None = None
    claimed_by: str | None = None
    claim_expires_at: datetime | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None
