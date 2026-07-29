"""Domain common package exports."""

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.errors import (
    ConcurrencyConflict,
    DomainError,
    InsufficientResource,
    InvalidAction,
    InvalidStateTransition,
    SecretAccessDenied,
    UnknownTarget,
)
from fictional_world.domain.common.ids import (
    CharacterId,
    EventId,
    MemoryId,
    ObservationId,
    PhaseId,
    SceneId,
    SnapshotId,
    TaskId,
    WorldId,
)
from fictional_world.domain.common.result import ValidationIssue, ValidationResult

__all__ = [
    "CharacterId",
    "ConcurrencyConflict",
    "DomainError",
    "EventId",
    "InsufficientResource",
    "InvalidAction",
    "InvalidStateTransition",
    "MemoryId",
    "ObservationId",
    "PhaseId",
    "SceneId",
    "SecretAccessDenied",
    "SnapshotId",
    "StrictContract",
    "TaskId",
    "UnknownTarget",
    "ValidationIssue",
    "ValidationResult",
    "WorldId",
]
