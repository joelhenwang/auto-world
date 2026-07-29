"""Scripted Stage 0 character actions (WAIT / OBSERVE / REST)."""

from __future__ import annotations

from uuid import UUID

from fictional_world.domain.common.enums import MemoryKind, ObservationChannel
from fictional_world.domain.effects.commands import (
    CreateRecentMemoryEffect,
    EffectCommand,
    ObserveEffect,
    RestEffect,
    WaitEffect,
)


def mira_stage0_effects(
    *,
    mira_id: UUID,
    inn_id: UUID | None,
    absolute_phase_index: int = 0,
) -> tuple[EffectCommand, ...]:
    """Deterministic Stage 0 actions for Mira at the Cinder Lantern Inn."""
    targets = (inn_id,) if inn_id is not None else ()
    return (
        WaitEffect(
            effect_key="mira.wait",
            entity_id=mira_id,
            phases=1,
            justification="Stage 0 scripted wait at the inn.",
        ),
        ObserveEffect(
            effect_key="mira.observe",
            observer_id=mira_id,
            target_entity_ids=targets,
            channels=(ObservationChannel.SIGHT,),
            justification="Stage 0 scripted observation of the inn common room.",
        ),
        RestEffect(
            effect_key="mira.rest",
            entity_id=mira_id,
            stamina_recovery=5.0,
            justification="Stage 0 scripted rest between courier work.",
        ),
        CreateRecentMemoryEffect(
            effect_key=f"mira.memory.inn-phase-{absolute_phase_index}",
            owner_character_id=mira_id,
            memory_kind=MemoryKind.EPISODIC,
            text=(
                "Mira rested briefly in the Cinder Lantern Inn after checking "
                f"the route board (phase {absolute_phase_index})."
            ),
            salience=0.4,
            confidence=0.9,
            justification="Stage 0 scripted recent memory from deterministic rest.",
        ),
    )
