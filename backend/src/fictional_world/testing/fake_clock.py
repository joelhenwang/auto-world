"""Deterministic operational clock for tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


@dataclass
class FakeClock:
    """Controllable wall-clock; tests never sleep for fictional phases."""

    _now: datetime = field(default_factory=lambda: datetime(2026, 1, 1, tzinfo=UTC))

    def now(self) -> datetime:
        return self._now

    def set(self, instant: datetime) -> None:
        if instant.tzinfo is None:
            msg = "FakeClock requires timezone-aware datetimes"
            raise ValueError(msg)
        self._now = instant.astimezone(UTC)

    def advance(self, *, seconds: float = 0, minutes: float = 0, hours: float = 0) -> datetime:
        delta = timedelta(seconds=seconds, minutes=minutes, hours=hours)
        self._now = self._now + delta
        return self._now
