"""Status vocabularies for Stage 2 goals, plans, and commitments."""

from __future__ import annotations

from enum import StrEnum


class GoalStatus(StrEnum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class PlanStatus(StrEnum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    SUPERSEDED = "superseded"
    INVALIDATED = "invalidated"


class PlanStepStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    SKIPPED = "skipped"
    INVALIDATED = "invalidated"


class CommitmentStatus(StrEnum):
    PROMISED = "promised"
    ACTIVE = "active"
    FULFILLED = "fulfilled"
    BROKEN = "broken"
    WAIVED = "waived"


class ActivityStatus(StrEnum):
    """Lifecycle for persistent multi-phase activities (handbook ``05``/``09``)."""

    ACTIVE = "active"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"
    INVALIDATED = "invalidated"


class TravelProgressStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    ARRIVED = "arrived"
    INTERRUPTED = "interrupted"
    INVALIDATED = "invalidated"
