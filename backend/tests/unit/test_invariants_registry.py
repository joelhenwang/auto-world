"""Invariant registry tests."""

from __future__ import annotations

from uuid import uuid4

import pytest

from fictional_world.domain.common.enums import DayPhase, ResourceKind
from fictional_world.domain.rules.effects import EffectValidationContext, EntitySnapshot
from fictional_world.domain.rules.invariants import INVARIANT_REGISTRY, get_invariant
from fictional_world.domain.time.fictional_time import FictionalTime


@pytest.mark.unit
def test_registry_contains_stage0_invariants() -> None:
    assert "resources_non_negative" in INVARIANT_REGISTRY
    assert "absolute_phase_monotonic" in INVARIANT_REGISTRY
    spec = get_invariant("resources_non_negative")
    eid = uuid4()
    ctx = EffectValidationContext(
        entities={eid: EntitySnapshot(entity_id=eid, resources={ResourceKind.MANA: -1.0})}
    )
    result = spec.check(ctx)
    assert not result.ok


@pytest.mark.unit
def test_absolute_phase_invariant() -> None:
    prev = FictionalTime(
        generation_index=1, world_day_index=1, phase=DayPhase.DAWN, absolute_phase_index=5
    )
    cur = FictionalTime(
        generation_index=1, world_day_index=1, phase=DayPhase.SUNRISE, absolute_phase_index=4
    )
    result = get_invariant("absolute_phase_monotonic").check(prev, cur)
    assert not result.ok
