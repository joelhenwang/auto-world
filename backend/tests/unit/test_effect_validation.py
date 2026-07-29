"""Effect validation and projection tests (S0-SIM-001)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from fictional_world.domain.common.enums import MemoryKind, PhaseStage, ResourceKind, RunStatus
from fictional_world.domain.common.errors import InvalidStateTransition
from fictional_world.domain.effects import (
    CreateRecentMemoryEffect,
    MoveEntityEffect,
    SpendResourceEffect,
    WaitEffect,
)
from fictional_world.domain.rules.effects import (
    EffectValidationContext,
    EntitySnapshot,
    project_effect,
    validate_effect,
)
from fictional_world.domain.rules.phase_transitions import (
    assert_phase_stage_advance,
    assert_run_status_transition,
)


@pytest.mark.unit
def test_validate_spend_insufficient() -> None:
    eid = uuid4()
    ctx = EffectValidationContext(
        entities={
            eid: EntitySnapshot(entity_id=eid, resources={ResourceKind.STAMINA: 1.0}),
        }
    )
    effect = SpendResourceEffect(
        effect_key="s1",
        justification="tired",
        entity_id=eid,
        resource=ResourceKind.STAMINA,
        amount=5.0,
    )
    result = validate_effect(effect, context=ctx)
    assert not result.ok
    assert result.issues[0].code == "insufficient_resource"


@pytest.mark.unit
def test_validate_and_project_move() -> None:
    eid = uuid4()
    loc_a, loc_b = uuid4(), uuid4()
    ctx = EffectValidationContext(
        entities={eid: EntitySnapshot(entity_id=eid, location_id=loc_a)},
        known_location_ids=frozenset({loc_a, loc_b}),
    )
    effect = MoveEntityEffect(
        effect_key="m1",
        justification="walk",
        entity_id=eid,
        from_location_id=loc_a,
        to_location_id=loc_b,
    )
    assert validate_effect(effect, context=ctx).ok
    projected = project_effect(effect, context=ctx)
    assert projected.entities[eid].location_id == loc_b


@pytest.mark.unit
def test_wait_and_memory_ok() -> None:
    eid = uuid4()
    ctx = EffectValidationContext(
        entities={eid: EntitySnapshot(entity_id=eid)},
        known_character_ids=frozenset({eid}),
    )
    wait = WaitEffect(effect_key="w1", justification="idle", entity_id=eid)
    assert validate_effect(wait, context=ctx).ok
    mem = CreateRecentMemoryEffect(
        effect_key="mem1",
        justification="note",
        owner_character_id=eid,
        memory_kind=MemoryKind.EPISODIC,
        text="Saw a door.",
        salience=0.5,
        confidence=0.9,
    )
    assert validate_effect(mem, context=ctx).ok
    proj = project_effect(mem, context=ctx)
    assert len(proj.memories) == 1


@pytest.mark.unit
def test_phase_stage_and_run_transitions() -> None:
    assert_phase_stage_advance(current=PhaseStage.ACCEPT_COMMANDS, nxt=PhaseStage.ADVANCE_CLOCK)
    with pytest.raises(InvalidStateTransition):
        assert_phase_stage_advance(current=PhaseStage.ACCEPT_COMMANDS, nxt=PhaseStage.FINALIZE)
    assert_run_status_transition(current=RunStatus.PENDING, nxt=RunStatus.RUNNING)
    with pytest.raises(InvalidStateTransition):
        assert_run_status_transition(current=RunStatus.COMPLETED, nxt=RunStatus.RUNNING)
