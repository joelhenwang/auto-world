"""Ten-phase calendar helpers (handbook ``07`` §2)."""

from __future__ import annotations

from fictional_world.domain.common.enums import DayPhase
from fictional_world.domain.time.fictional_time import FictionalTime

PHASE_ORDER: tuple[DayPhase, ...] = (
    DayPhase.DAWN,
    DayPhase.SUNRISE,
    DayPhase.MORNING,
    DayPhase.NOON,
    DayPhase.AFTERNOON,
    DayPhase.SUNSET,
    DayPhase.DUSK,
    DayPhase.EVENING,
    DayPhase.NIGHT,
    DayPhase.MIDNIGHT,
)

_PHASE_INDEX = {phase: index for index, phase in enumerate(PHASE_ORDER)}


def phase_index(phase: DayPhase) -> int:
    return _PHASE_INDEX[phase]


def next_phase(phase: DayPhase) -> DayPhase:
    return PHASE_ORDER[(phase_index(phase) + 1) % len(PHASE_ORDER)]


def advance_fictional_clock(current: FictionalTime) -> FictionalTime:
    """Advance one detailed phase; midnight→dawn increments world_day_index."""

    nxt = next_phase(current.phase)
    day = current.world_day_index
    if current.phase is DayPhase.MIDNIGHT and nxt is DayPhase.DAWN:
        day += 1
    return FictionalTime(
        generation_index=current.generation_index,
        world_day_index=day,
        phase=nxt,
        absolute_phase_index=current.absolute_phase_index + 1,
        calendar_label=current.calendar_label,
    )
