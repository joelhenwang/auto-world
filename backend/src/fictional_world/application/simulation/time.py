"""Stage 2 ten-phase calendar profile helpers (S2-SIM-001)."""

from __future__ import annotations

from enum import StrEnum

from fictional_world.domain.common.enums import DayPhase
from fictional_world.domain.time.calendar import PHASE_ORDER, advance_fictional_clock, next_phase
from fictional_world.domain.time.fictional_time import FictionalTime

# Stage 1 vertical slice (orchestration also filters to these).
STAGE1_PHASE_PROFILE: tuple[DayPhase, ...] = (
    DayPhase.DAWN,
    DayPhase.MORNING,
    DayPhase.EVENING,
)

# Stage 2 enables the full canonical day (handbook ``07`` §2 / ``05`` §16).
STAGE2_PHASE_PROFILE: tuple[DayPhase, ...] = PHASE_ORDER

STAGE1_ENABLED_PHASE_NAMES: frozenset[str] = frozenset(
    phase.value for phase in STAGE1_PHASE_PROFILE
)
STAGE2_ENABLED_PHASE_NAMES: frozenset[str] = frozenset(
    phase.value for phase in STAGE2_PHASE_PROFILE
)


class PhaseProfile(StrEnum):
    STAGE1 = "stage1"
    STAGE2 = "stage2"


def phase_profile_names(profile: PhaseProfile | str) -> tuple[str, ...]:
    """Return ordered phase name strings for a simulation profile."""

    resolved = PhaseProfile(profile)
    if resolved is PhaseProfile.STAGE1:
        return tuple(phase.value for phase in STAGE1_PHASE_PROFILE)
    return tuple(phase.value for phase in STAGE2_PHASE_PROFILE)


def enabled_phase_names(profile: PhaseProfile | str) -> frozenset[str]:
    resolved = PhaseProfile(profile)
    if resolved is PhaseProfile.STAGE1:
        return STAGE1_ENABLED_PHASE_NAMES
    return STAGE2_ENABLED_PHASE_NAMES


def is_phase_enabled(phase: DayPhase | str, *, profile: PhaseProfile | str) -> bool:
    name = phase.value if isinstance(phase, DayPhase) else str(phase).strip().casefold()
    return name in enabled_phase_names(profile)


def full_day_phase_sequence() -> tuple[DayPhase, ...]:
    """Canonical Stage 2 day: all ten detailed phases in order."""

    return STAGE2_PHASE_PROFILE


def walk_full_day(start: FictionalTime) -> tuple[FictionalTime, ...]:
    """Advance through one full ten-phase day starting at ``start`` (inclusive).

    Returns eleven clock values: the starting phase plus ten advances that land
    on the same phase of the next calendar day when ``start`` is dawn.
    """

    clocks: list[FictionalTime] = [start]
    current = start
    for _ in range(len(PHASE_ORDER)):
        current = advance_fictional_clock(current)
        clocks.append(current)
    return tuple(clocks)


__all__ = [
    "PHASE_ORDER",
    "STAGE1_ENABLED_PHASE_NAMES",
    "STAGE1_PHASE_PROFILE",
    "STAGE2_ENABLED_PHASE_NAMES",
    "STAGE2_PHASE_PROFILE",
    "PhaseProfile",
    "advance_fictional_clock",
    "enabled_phase_names",
    "full_day_phase_sequence",
    "is_phase_enabled",
    "next_phase",
    "phase_profile_names",
    "walk_full_day",
]
