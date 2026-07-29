"""Pure in-memory projectors for Stage 0 effects."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from uuid import UUID

from fictional_world.domain.common.enums import ResourceKind
from fictional_world.domain.effects.commands import (
    CreateRecentMemoryEffect,
    EffectBase,
    MoveEntityEffect,
    RestEffect,
    SpendResourceEffect,
    WaitEffect,
)
from fictional_world.domain.rules.effects.context import EffectValidationContext, EntitySnapshot


@dataclass(frozen=True, slots=True)
class ProjectedMemory:
    owner_character_id: UUID
    text: str
    memory_kind: str
    salience: float
    confidence: float


@dataclass(frozen=True, slots=True)
class EffectProjection:
    entities: dict[UUID, EntitySnapshot] = field(default_factory=dict)
    memories: tuple[ProjectedMemory, ...] = ()
    noop_keys: tuple[str, ...] = ()


def project_effect(
    effect: EffectBase,
    *,
    context: EffectValidationContext,
) -> EffectProjection:
    entities = dict(context.entities)
    memories: list[ProjectedMemory] = []
    noops: list[str] = []

    if isinstance(effect, WaitEffect):
        noops.append(effect.effect_key)
    elif isinstance(effect, RestEffect):
        snap = entities.get(effect.entity_id)
        if snap is not None:
            resources = dict(snap.resources)
            stamina = resources.get(ResourceKind.STAMINA, 0.0) + effect.stamina_recovery
            resources[ResourceKind.STAMINA] = min(100.0, stamina)
            entities[effect.entity_id] = replace(snap, resources=resources)
    elif isinstance(effect, MoveEntityEffect):
        snap = entities.get(effect.entity_id)
        if snap is not None:
            entities[effect.entity_id] = replace(snap, location_id=effect.to_location_id)
    elif isinstance(effect, SpendResourceEffect):
        snap = entities.get(effect.entity_id)
        if snap is not None:
            resources = dict(snap.resources)
            resources[effect.resource] = resources.get(effect.resource, 0.0) - effect.amount
            entities[effect.entity_id] = replace(snap, resources=resources)
    elif isinstance(effect, CreateRecentMemoryEffect):
        memories.append(
            ProjectedMemory(
                owner_character_id=effect.owner_character_id,
                text=effect.text,
                memory_kind=effect.memory_kind.value,
                salience=effect.salience,
                confidence=effect.confidence,
            )
        )
    else:
        noops.append(getattr(effect, "effect_key", "unknown"))

    return EffectProjection(
        entities=entities,
        memories=tuple(memories),
        noop_keys=tuple(noops),
    )
