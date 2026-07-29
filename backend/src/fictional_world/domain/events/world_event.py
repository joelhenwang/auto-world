"""Committed world event contract."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.effects.commands import EffectCommand
from fictional_world.domain.events.provenance import Provenance
from fictional_world.domain.time.fictional_time import FictionalTime


class CommittedWorldEvent(StrictContract):
    event_id: UUID
    sequence_number: int = Field(ge=1)
    world_id: UUID
    phase_id: UUID
    scene_id: UUID | None
    fictional_time: FictionalTime
    event_type: str = Field(min_length=1, max_length=100)
    initiator_id: UUID | None
    participant_ids: tuple[UUID, ...] = ()
    location_id: UUID | None
    canonical_summary: str = Field(min_length=1, max_length=2_000)
    effects: tuple[EffectCommand, ...] = ()
    provenance: Provenance
    committed_at: datetime
