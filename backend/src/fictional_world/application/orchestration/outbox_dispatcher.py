"""Outbox claim/dispatch interface (S0-ORCH-001)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.domain.events.persistence import OutboxMessageRecord


class OutboxHandler(Protocol):
    def __call__(self, message: OutboxMessageRecord) -> Awaitable[None]: ...


@dataclass(frozen=True, slots=True)
class DispatchResult:
    claimed: tuple[OutboxMessageRecord, ...]
    completed_ids: tuple[UUID, ...]


class OutboxDispatcher:
    """Claim pending outbox rows, invoke a handler, then ack completion.

    Delivery is at-least-once. Handlers must be idempotent on ``idempotency_key``.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def claim(
        self,
        *,
        worker_id: str,
        lease_duration: timedelta = timedelta(seconds=90),
        now: datetime | None = None,
        limit: int = 10,
    ) -> Sequence[OutboxMessageRecord]:
        return await self._uow.outbox.claim_available(
            worker_id=worker_id,
            lease_duration=lease_duration,
            now=now or datetime.now(UTC),
            limit=limit,
        )

    async def complete(
        self,
        message_id: UUID,
        *,
        worker_id: str,
        now: datetime | None = None,
    ) -> OutboxMessageRecord:
        return await self._uow.outbox.complete(
            message_id, worker_id=worker_id, now=now or datetime.now(UTC)
        )

    async def dispatch_once(
        self,
        *,
        worker_id: str,
        handler: Callable[[OutboxMessageRecord], Awaitable[None]],
        lease_duration: timedelta = timedelta(seconds=90),
        now: datetime | None = None,
        limit: int = 10,
    ) -> DispatchResult:
        """Claim a batch, run handler, complete on success.

        Caller commits the UoW after this method returns. Handlers must be
        idempotent; do not hold the UoW open across long remote I/O.
        """
        clock = now or datetime.now(UTC)
        claimed = await self.claim(
            worker_id=worker_id,
            lease_duration=lease_duration,
            now=clock,
            limit=limit,
        )
        completed: list[UUID] = []
        for message in claimed:
            await handler(message)
            done = await self.complete(message.id, worker_id=worker_id, now=clock)
            completed.append(done.id)
        return DispatchResult(claimed=tuple(claimed), completed_ids=tuple(completed))
