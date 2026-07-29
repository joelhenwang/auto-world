"""Calendar and fictional clock tests (S0-SIM-001)."""

from __future__ import annotations

import pytest

from fictional_world.domain.common.enums import DayPhase
from fictional_world.domain.time import PHASE_ORDER, advance_fictional_clock, next_phase
from fictional_world.domain.time.fictional_time import FictionalTime


@pytest.mark.unit
def test_phase_order_has_ten() -> None:
    assert len(PHASE_ORDER) == 10
    assert PHASE_ORDER[0] is DayPhase.DAWN
    assert PHASE_ORDER[-1] is DayPhase.MIDNIGHT


@pytest.mark.unit
def test_midnight_to_dawn_increments_day() -> None:
    current = FictionalTime(
        generation_index=1,
        world_day_index=3,
        phase=DayPhase.MIDNIGHT,
        absolute_phase_index=29,
    )
    nxt = advance_fictional_clock(current)
    assert nxt.phase is DayPhase.DAWN
    assert nxt.world_day_index == 4
    assert nxt.absolute_phase_index == 30


@pytest.mark.unit
def test_non_midnight_keeps_day() -> None:
    current = FictionalTime(
        generation_index=1,
        world_day_index=1,
        phase=DayPhase.DAWN,
        absolute_phase_index=0,
    )
    nxt = advance_fictional_clock(current)
    assert nxt.phase is next_phase(DayPhase.DAWN)
    assert nxt.world_day_index == 1
    assert nxt.absolute_phase_index == 1
