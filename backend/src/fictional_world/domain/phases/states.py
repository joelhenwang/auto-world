"""Operational phase_run.state strings (handbook ``07`` §3 Stage 0 surface)."""

from __future__ import annotations

from enum import StrEnum


class PhaseRunState(StrEnum):
    PENDING = "pending"
    ACCEPTING_COMMANDS = "accepting_commands"
    ADVANCING_CLOCK = "advancing_clock"
    APPLYING_WORLD_TICK = "applying_world_tick"
    DIRECTOR_REVIEW = "director_review"
    SNAPSHOT_SEALED = "snapshot_sealed"
    GENERATING_INTENTS = "generating_intents"
    RESOLVING_SCENES = "resolving_scenes"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_PHASE_STATES: frozenset[PhaseRunState] = frozenset(
    {
        PhaseRunState.COMPLETED,
        PhaseRunState.FAILED,
        PhaseRunState.CANCELLED,
    }
)

PAUSE_SAFE_STATES: frozenset[PhaseRunState] = frozenset(
    {
        PhaseRunState.APPLYING_WORLD_TICK,
        PhaseRunState.SNAPSHOT_SEALED,
        PhaseRunState.PAUSED,
    }
)
