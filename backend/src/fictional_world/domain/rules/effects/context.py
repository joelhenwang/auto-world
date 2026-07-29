"""Minimal world view for Stage 0 effect validation (pure, no ORM)."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from fictional_world.domain.common.enums import ResourceKind


@dataclass(frozen=True, slots=True)
class EntitySnapshot:
    entity_id: UUID
    location_id: UUID | None = None
    resources: dict[ResourceKind, float] = field(default_factory=dict)
    alive: bool = True


@dataclass(frozen=True, slots=True)
class EffectValidationContext:
    """Known entities/locations for validators. Missing keys mean unknown."""

    entities: dict[UUID, EntitySnapshot] = field(default_factory=dict)
    known_location_ids: frozenset[UUID] = field(default_factory=frozenset)
    known_character_ids: frozenset[UUID] = field(default_factory=frozenset)
