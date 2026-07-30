"""Worker lifecycle application service (S4-ORCH-001).

Handles host/worker registration, heartbeating, and graceful drain.
The service is stateless; it delegates all persistence to the UnitOfWork.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.domain.common.errors import DomainError
from fictional_world.domain.tasks.workers import HostRecord, WorkerRecord


class WorkerError(DomainError):
    """Raised for worker lifecycle rule failures."""


@dataclass(frozen=True, slots=True)
class RegisterWorkerCommand:
    host_key: str
    worker_key: str
    host_capabilities: Sequence[str] = ()
    worker_capabilities: Sequence[str] = ()


@dataclass(frozen=True, slots=True)
class RegisterWorkerResult:
    host: HostRecord
    worker: WorkerRecord
    host_already_existed: bool
    worker_already_existed: bool


class WorkerLifecycleService:
    """Register hosts/workers, send heartbeats, and request drain."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def register(
        self,
        command: RegisterWorkerCommand,
        *,
        now: datetime | None = None,
    ) -> RegisterWorkerResult:
        """Upsert a host and worker; returns both records."""
        ts = now or datetime.now(UTC)
        existing_host = await self._uow.hosts.find_by_key(command.host_key)
        host = await self._uow.hosts.register(
            host_key=command.host_key,
            capabilities=list(command.host_capabilities),
            now=ts,
        )
        existing_worker = await self._uow.workers.find_by_key(command.worker_key)
        worker = await self._uow.workers.register(
            host_id=host.id,
            worker_key=command.worker_key,
            capabilities=list(command.worker_capabilities),
            now=ts,
        )
        return RegisterWorkerResult(
            host=host,
            worker=worker,
            host_already_existed=existing_host is not None,
            worker_already_existed=existing_worker is not None,
        )

    async def heartbeat(
        self,
        worker_id: UUID,
        *,
        now: datetime | None = None,
    ) -> WorkerRecord:
        """Refresh a worker heartbeat; returns the updated record."""
        ts = now or datetime.now(UTC)
        return await self._uow.workers.heartbeat(worker_id, now=ts)

    async def heartbeat_by_key(
        self,
        worker_key: str,
        *,
        now: datetime | None = None,
    ) -> WorkerRecord:
        """Refresh heartbeat by worker_key string."""
        ts = now or datetime.now(UTC)
        worker = await self._uow.workers.find_by_key(worker_key)
        if worker is None:
            raise WorkerError(f"worker not found: {worker_key!r}")
        return await self._uow.workers.heartbeat(worker.id, now=ts)

    async def drain(
        self,
        worker_id: UUID,
        *,
        now: datetime | None = None,
    ) -> WorkerRecord:
        """Request graceful drain for a worker."""
        ts = now or datetime.now(UTC)
        return await self._uow.workers.drain(worker_id, now=ts)

    async def drain_by_key(
        self,
        worker_key: str,
        *,
        now: datetime | None = None,
    ) -> WorkerRecord:
        """Request graceful drain by worker_key string."""
        ts = now or datetime.now(UTC)
        worker = await self._uow.workers.find_by_key(worker_key)
        if worker is None:
            raise WorkerError(f"worker not found: {worker_key!r}")
        return await self._uow.workers.drain(worker.id, now=ts)

    async def mark_drained(self, worker_id: UUID) -> WorkerRecord:
        """Confirm a worker has fully released all task leases."""
        return await self._uow.workers.mark_drained(worker_id)
