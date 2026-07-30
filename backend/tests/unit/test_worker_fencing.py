"""Unit tests for fencing-token logic and worker domain records (S4-ORCH-001).

These tests exercise pure domain/transition logic without a database.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from fictional_world.domain.common.enums import TaskState
from fictional_world.domain.tasks.transitions import (
    LEASED_TASK_STATES,
    TERMINAL_TASK_STATES,
    is_claimable_row,
    is_terminal,
    lease_is_expired,
)
from fictional_world.domain.tasks.workers import HostRecord, WorkerRecord

# ---------------------------------------------------------------------------
# TaskRun fencing_token field
# ---------------------------------------------------------------------------


def test_task_run_has_fencing_token_default() -> None:
    from fictional_world.domain.tasks.task_run import TaskRun

    now = datetime(2026, 7, 30, 0, 0, tzinfo=UTC)
    task = TaskRun(
        id=uuid4(),
        task_type="test",
        state=TaskState.PENDING,
        priority=0,
        idempotency_key="k:1",
        available_at=now,
        created_at=now,
    )
    assert task.fencing_token == 0


def test_task_run_fencing_token_explicit() -> None:
    from fictional_world.domain.tasks.task_run import TaskRun

    now = datetime(2026, 7, 30, 0, 0, tzinfo=UTC)
    task = TaskRun(
        id=uuid4(),
        task_type="test",
        state=TaskState.CLAIMED,
        priority=0,
        idempotency_key="k:2",
        available_at=now,
        created_at=now,
        fencing_token=7,
    )
    assert task.fencing_token == 7


def test_task_run_fencing_token_must_be_nonneg() -> None:
    import pydantic

    from fictional_world.domain.tasks.task_run import TaskRun

    now = datetime(2026, 7, 30, 0, 0, tzinfo=UTC)
    with pytest.raises(pydantic.ValidationError):
        TaskRun(
            id=uuid4(),
            task_type="test",
            state=TaskState.PENDING,
            priority=0,
            idempotency_key="k:3",
            available_at=now,
            created_at=now,
            fencing_token=-1,
        )


# ---------------------------------------------------------------------------
# HostRecord / WorkerRecord domain DTOs
# ---------------------------------------------------------------------------


def test_host_record_default_status() -> None:
    now = datetime(2026, 7, 30, 0, 0, tzinfo=UTC)
    host = HostRecord(
        id=uuid4(),
        host_key="host-a",
        first_seen_at=now,
        last_seen_at=now,
    )
    assert host.status == "active"
    assert host.capabilities == ()


def test_worker_record_default_status() -> None:
    now = datetime(2026, 7, 30, 0, 0, tzinfo=UTC)
    worker = WorkerRecord(
        id=uuid4(),
        host_id=uuid4(),
        worker_key="worker-a",
        heartbeat_at=now,
        registered_at=now,
    )
    assert worker.status == "active"
    assert worker.capabilities == ()
    assert worker.drain_requested_at is None


# ---------------------------------------------------------------------------
# Transition helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "state",
    [TaskState.SUCCEEDED, TaskState.FAILED, TaskState.DEAD_LETTER, TaskState.CANCELLED],
)
def test_is_terminal_returns_true_for_terminal_states(state: TaskState) -> None:
    assert is_terminal(state) is True


@pytest.mark.parametrize(
    "state",
    [TaskState.PENDING, TaskState.CLAIMED, TaskState.RUNNING],
)
def test_is_terminal_returns_false_for_non_terminal(state: TaskState) -> None:
    assert is_terminal(state) is False


def test_leased_states_set() -> None:
    assert TaskState.CLAIMED in LEASED_TASK_STATES
    assert TaskState.RUNNING in LEASED_TASK_STATES


def test_lease_expired_when_none() -> None:
    now = datetime(2026, 7, 30, tzinfo=UTC)
    assert lease_is_expired(lease_expires_at=None, now=now) is True


def test_lease_not_expired_when_future() -> None:
    now = datetime(2026, 7, 30, tzinfo=UTC)
    future = now + timedelta(seconds=30)
    assert lease_is_expired(lease_expires_at=future, now=now) is False


def test_is_claimable_row_pending_no_lease() -> None:
    now = datetime(2026, 7, 30, tzinfo=UTC)
    assert (
        is_claimable_row(
            state=TaskState.PENDING,
            available_at=now,
            lease_expires_at=None,
            now=now,
        )
        is True
    )


def test_is_claimable_row_pending_not_yet_available() -> None:
    now = datetime(2026, 7, 30, tzinfo=UTC)
    future = now + timedelta(minutes=5)
    assert (
        is_claimable_row(
            state=TaskState.PENDING,
            available_at=future,
            lease_expires_at=None,
            now=now,
        )
        is False
    )


def test_is_claimable_row_claimed_with_expired_lease() -> None:
    now = datetime(2026, 7, 30, tzinfo=UTC)
    past = now - timedelta(seconds=1)
    assert (
        is_claimable_row(
            state=TaskState.CLAIMED,
            available_at=now,
            lease_expires_at=past,
            now=now,
        )
        is True
    )


def test_is_claimable_row_claimed_with_active_lease() -> None:
    now = datetime(2026, 7, 30, tzinfo=UTC)
    future = now + timedelta(seconds=60)
    assert (
        is_claimable_row(
            state=TaskState.CLAIMED,
            available_at=now,
            lease_expires_at=future,
            now=now,
        )
        is False
    )


def test_terminal_not_claimable() -> None:
    now = datetime(2026, 7, 30, tzinfo=UTC)
    for state in TERMINAL_TASK_STATES:
        assert (
            is_claimable_row(
                state=state,
                available_at=now,
                lease_expires_at=None,
                now=now,
            )
            is False
        )
