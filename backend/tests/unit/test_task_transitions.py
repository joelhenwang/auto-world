"""Unit tests for Stage 0 task claimability helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fictional_world.domain.common.enums import TaskState
from fictional_world.domain.tasks.transitions import is_claimable_row, is_terminal


def test_terminal_states() -> None:
    assert is_terminal(TaskState.SUCCEEDED)
    assert is_terminal(TaskState.DEAD_LETTER)
    assert not is_terminal(TaskState.PENDING)
    assert not is_terminal(TaskState.CLAIMED)


def test_pending_claimable_without_lease() -> None:
    now = datetime(2026, 7, 29, tzinfo=UTC)
    assert is_claimable_row(
        state=TaskState.PENDING,
        available_at=now - timedelta(seconds=1),
        lease_expires_at=None,
        now=now,
    )


def test_pending_not_claimable_before_available_at() -> None:
    now = datetime(2026, 7, 29, tzinfo=UTC)
    assert not is_claimable_row(
        state=TaskState.PENDING,
        available_at=now + timedelta(seconds=30),
        lease_expires_at=None,
        now=now,
    )


def test_claimed_reclaimable_only_when_expired() -> None:
    now = datetime(2026, 7, 29, tzinfo=UTC)
    assert not is_claimable_row(
        state=TaskState.CLAIMED,
        available_at=now - timedelta(hours=1),
        lease_expires_at=now + timedelta(seconds=30),
        now=now,
    )
    assert is_claimable_row(
        state=TaskState.CLAIMED,
        available_at=now - timedelta(hours=1),
        lease_expires_at=now - timedelta(seconds=1),
        now=now,
    )


def test_succeeded_never_claimable() -> None:
    now = datetime(2026, 7, 29, tzinfo=UTC)
    assert not is_claimable_row(
        state=TaskState.SUCCEEDED,
        available_at=now - timedelta(hours=1),
        lease_expires_at=None,
        now=now,
    )
