"""Status and scope vocabularies for Stage 3 arcs and Stage 2 hooks."""

from __future__ import annotations

from enum import StrEnum


class ArcStatus(StrEnum):
    ACTIVE = "active"
    DORMANT = "dormant"
    RESOLVED = "resolved"
    FAILED = "failed"
    ABANDONED = "abandoned"


class ArcScope(StrEnum):
    MAJOR = "major"
    SECONDARY = "secondary"


class HookStatus(StrEnum):
    ACTIVE = "active"
    DORMANT = "dormant"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"


# Arc statuses that close an arc (terminal).
ARC_TERMINAL_STATUSES: frozenset[ArcStatus] = frozenset(
    {ArcStatus.RESOLVED, ArcStatus.FAILED, ArcStatus.ABANDONED}
)

# Hook statuses counted toward the active secondary-hook slot budget.
ACTIVE_HOOK_STATUS = HookStatus.ACTIVE
