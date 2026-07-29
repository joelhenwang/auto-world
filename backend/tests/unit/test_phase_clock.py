"""Unit tests for Stage 0 clock advance helper."""

from __future__ import annotations

from fictional_world.application.orchestration.clock import advance_world_clock
from fictional_world.domain.common.enums import DayPhase
from fictional_world.domain.world.records import WorldClockRecord


def _clock(**overrides: object) -> WorldClockRecord:
    base = {
        "world_id": __import__("uuid").uuid4(),
        "generation_number": 1,
        "year": 412,
        "month": 3,
        "day": 12,
        "phase_name": DayPhase.DAWN.value,
        "phase_ordinal": 0,
        "absolute_day_index": 0,
        "absolute_phase_index": 0,
        "resolution_mode": "detailed",
        "version": 0,
    }
    base.update(overrides)
    return WorldClockRecord(**base)  # type: ignore[arg-type]


def test_advance_dawn_to_sunrise() -> None:
    nxt = advance_world_clock(_clock())
    assert nxt.phase_name == DayPhase.SUNRISE.value
    assert nxt.phase_ordinal == 1
    assert nxt.absolute_phase_index == 1
    assert nxt.day == 12


def test_advance_midnight_rolls_day() -> None:
    nxt = advance_world_clock(
        _clock(
            phase_name=DayPhase.MIDNIGHT.value,
            phase_ordinal=9,
            absolute_phase_index=9,
        )
    )
    assert nxt.phase_name == DayPhase.DAWN.value
    assert nxt.day == 13
    assert nxt.absolute_day_index == 1
    assert nxt.absolute_phase_index == 10
