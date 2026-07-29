"""Property: absolute_phase_index is strictly monotonic under advances."""

from __future__ import annotations

import pytest

from fictional_world.domain.common.enums import DayPhase
from fictional_world.domain.time import PHASE_ORDER, advance_fictional_clock
from fictional_world.domain.time.fictional_time import FictionalTime


@pytest.mark.property
def test_absolute_phase_monotonic_over_full_day_cycle() -> None:
    time = FictionalTime(
        generation_index=1,
        world_day_index=1,
        phase=DayPhase.DAWN,
        absolute_phase_index=0,
    )
    seen: list[int] = [time.absolute_phase_index]
    for _ in range(len(PHASE_ORDER) * 3):
        time = advance_fictional_clock(time)
        assert time.absolute_phase_index == seen[-1] + 1
        seen.append(time.absolute_phase_index)
    assert time.world_day_index == 4
