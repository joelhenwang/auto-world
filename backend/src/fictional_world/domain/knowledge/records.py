"""Observation and claim/belief contracts."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.enums import ObservationChannel


class ObservationRecord(StrictContract):
    observation_id: UUID
    observer_id: UUID
    event_id: UUID
    phase_id: UUID
    channels: tuple[ObservationChannel, ...] = Field(min_length=1)
    perceived_summary: str = Field(min_length=1, max_length=2_000)
    visible_effect_keys: tuple[str, ...] = ()
    referenced_entity_ids: tuple[UUID, ...] = ()
    uncertainty: float = Field(ge=0, le=1)
    interpretation: str | None = Field(default=None, max_length=1_500)
    created_at: datetime


class ClaimRecord(StrictContract):
    claim_id: UUID
    event_id: UUID
    speaker_id: UUID
    listener_ids: tuple[UUID, ...] = Field(min_length=1)
    proposition: str = Field(min_length=1, max_length=2_000)
    referenced_entity_ids: tuple[UUID, ...] = ()
    created_at: datetime


class BeliefRecord(StrictContract):
    belief_id: UUID
    owner_character_id: UUID
    proposition: str = Field(min_length=1, max_length=2_000)
    confidence: float = Field(ge=0, le=1)
    source_observation_ids: tuple[UUID, ...] = ()
    source_claim_ids: tuple[UUID, ...] = ()
    supersedes_belief_id: UUID | None = None
    active: bool = True
    created_at: datetime
