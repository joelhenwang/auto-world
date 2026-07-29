"""Pure task-state helpers for Stage 0 orchestration."""

from __future__ import annotations

from datetime import datetime

from fictional_world.domain.common.enums import TaskState

TERMINAL_TASK_STATES: frozenset[TaskState] = frozenset(
    {
        TaskState.SUCCEEDED,
        TaskState.FAILED,
        TaskState.DEAD_LETTER,
        TaskState.CANCELLED,
    }
)

LEASED_TASK_STATES: frozenset[TaskState] = frozenset(
    {
        TaskState.CLAIMED,
        TaskState.RUNNING,
    }
)


def is_terminal(state: TaskState | str) -> bool:
    return TaskState(state) in TERMINAL_TASK_STATES


def lease_is_expired(*, lease_expires_at: datetime | None, now: datetime) -> bool:
    if lease_expires_at is None:
        return True
    return lease_expires_at <= now


def is_claimable_row(
    *,
    state: TaskState | str,
    available_at: datetime,
    lease_expires_at: datetime | None,
    now: datetime,
) -> bool:
    """Whether a row may be claimed ignoring dependency checks."""
    current = TaskState(state)
    if current in TERMINAL_TASK_STATES:
        return False
    if available_at > now:
        return False
    if current == TaskState.PENDING:
        return lease_is_expired(lease_expires_at=lease_expires_at, now=now)
    if current in LEASED_TASK_STATES:
        return lease_is_expired(lease_expires_at=lease_expires_at, now=now)
    return False
