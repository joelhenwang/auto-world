"""Phase domain package."""

from fictional_world.domain.phases.records import (
    PhaseRunRecord,
    PhaseSnapshotCharacterRecord,
    PhaseSnapshotRecord,
)
from fictional_world.domain.phases.states import (
    PAUSE_SAFE_STATES,
    TERMINAL_PHASE_STATES,
    PhaseRunState,
)

__all__ = [
    "PAUSE_SAFE_STATES",
    "TERMINAL_PHASE_STATES",
    "PhaseRunRecord",
    "PhaseRunState",
    "PhaseSnapshotCharacterRecord",
    "PhaseSnapshotRecord",
]
