"""Shared input contracts for the observation→claim→belief pipeline."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.knowledge.visibility import ObserverEligibility

JsonObject = dict[str, Any]


class ObserverPresence(StrictContract):
    """Spatial/sensory presence of one potential observer relative to an event."""

    character_id: UUID
    co_located: bool = False
    line_of_sight: bool = False
    hearing_range: bool = False
    attention: bool = True
    concealment_blocks_sight: bool = False
    close_range: bool = False
    known_magic_sense: bool = False
    precise_close: bool = False
    # Explicit override used by tests / callers that already classified eligibility.
    eligibility_override: ObserverEligibility | None = None


class EventObservationInput(StrictContract):
    """Canonical event facts ready for observer-specific observation derivation."""

    world_event_id: UUID
    structured_facts: JsonObject = Field(default_factory=dict)
    canonical_summary: str = Field(min_length=1, max_length=2_000)
    public_summary: str | None = Field(default=None, max_length=2_000)
    auditory_summary: str | None = Field(default=None, max_length=2_000)
    partial_summary: str | None = Field(default=None, max_length=2_000)


class PerspectiveKnowledge(StrictContract):
    """Beliefs and secrets allowed for one character's perspective package."""

    character_id: UUID
    beliefs: tuple[dict[str, Any], ...] = ()
    secret_keys: tuple[str, ...] = ()
    secret_summaries: tuple[dict[str, Any], ...] = ()


__all__ = [
    "EventObservationInput",
    "ObserverPresence",
    "PerspectiveKnowledge",
]
