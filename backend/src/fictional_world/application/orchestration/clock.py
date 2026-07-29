"""World clock advance helpers for Stage 0 orchestration."""

from __future__ import annotations

from fictional_world.domain.common.enums import DayPhase
from fictional_world.domain.time.calendar import next_phase, phase_index
from fictional_world.domain.world.records import WorldClockRecord

_DAYS_PER_MONTH = 30
_MONTHS_PER_YEAR = 8  # Turning Calendar (Caldris)


def advance_world_clock(clock: WorldClockRecord) -> WorldClockRecord:
    """Advance one detailed day-phase on a persistence clock record."""
    current = DayPhase(clock.phase_name)
    nxt = next_phase(current)
    day = clock.day
    month = clock.month
    year = clock.year
    abs_day = clock.absolute_day_index
    if current is DayPhase.MIDNIGHT and nxt is DayPhase.DAWN:
        day += 1
        abs_day += 1
        if day > _DAYS_PER_MONTH:
            day = 1
            month += 1
            if month > _MONTHS_PER_YEAR:
                month = 1
                year += 1
    return clock.model_copy(
        update={
            "phase_name": nxt.value,
            "phase_ordinal": phase_index(nxt),
            "absolute_phase_index": clock.absolute_phase_index + 1,
            "absolute_day_index": abs_day,
            "day": day,
            "month": month,
            "year": year,
        }
    )
