"""Worker and host registry repositories (S4-ORCH-001)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from fictional_world.domain.tasks.workers import HostRecord, WorkerRecord
from fictional_world.infrastructure.database.errors import NotFoundError
from fictional_world.infrastructure.database.mappings.records import (
    host_to_record,
    worker_to_record,
)
from fictional_world.infrastructure.database.models.workers import (
    HostRegistryRow,
    WorkerRegistryRow,
)


class SqlAlchemyHostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, host_id: UUID) -> HostRecord | None:
        row = await self._session.get(HostRegistryRow, host_id)
        return host_to_record(row) if row is not None else None

    async def find_by_key(self, host_key: str) -> HostRecord | None:
        result = await self._session.execute(
            select(HostRegistryRow).where(HostRegistryRow.host_key == host_key)
        )
        row = result.scalar_one_or_none()
        return host_to_record(row) if row is not None else None

    async def register(
        self,
        *,
        host_key: str,
        capabilities: Sequence[str] = (),
        now: datetime,
    ) -> HostRecord:
        """Upsert a host by host_key; returns the current record."""
        stmt = (
            pg_insert(HostRegistryRow)
            .values(
                id=uuid4(),
                host_key=host_key,
                capabilities=list(capabilities),
                status="active",
                first_seen_at=now,
                last_seen_at=now,
            )
            .on_conflict_do_update(
                index_elements=["host_key"],
                set_={
                    "last_seen_at": now,
                    "capabilities": list(capabilities),
                    "status": "active",
                },
            )
            .returning(HostRegistryRow)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one()
        return host_to_record(row)

    async def update_last_seen(self, host_id: UUID, *, now: datetime) -> HostRecord:
        row = await self._session.get(HostRegistryRow, host_id, with_for_update=True)
        if row is None:
            raise NotFoundError(entity="host_registry", entity_id=str(host_id))
        row.last_seen_at = now
        await self._session.flush()
        return host_to_record(row)

    async def mark_lost(self, host_id: UUID) -> HostRecord:
        row = await self._session.get(HostRegistryRow, host_id, with_for_update=True)
        if row is None:
            raise NotFoundError(entity="host_registry", entity_id=str(host_id))
        row.status = "lost"
        await self._session.flush()
        return host_to_record(row)


class SqlAlchemyWorkerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, worker_id: UUID) -> WorkerRecord | None:
        row = await self._session.get(WorkerRegistryRow, worker_id)
        return worker_to_record(row) if row is not None else None

    async def find_by_key(self, worker_key: str) -> WorkerRecord | None:
        result = await self._session.execute(
            select(WorkerRegistryRow).where(WorkerRegistryRow.worker_key == worker_key)
        )
        row = result.scalar_one_or_none()
        return worker_to_record(row) if row is not None else None

    async def register(
        self,
        *,
        host_id: UUID,
        worker_key: str,
        capabilities: Sequence[str] = (),
        now: datetime,
    ) -> WorkerRecord:
        """Upsert a worker by worker_key; returns the current record."""
        stmt = (
            pg_insert(WorkerRegistryRow)
            .values(
                id=uuid4(),
                host_id=host_id,
                worker_key=worker_key,
                capabilities=list(capabilities),
                status="active",
                heartbeat_at=now,
                registered_at=now,
                drain_requested_at=None,
                last_task_claimed_at=None,
                is_draining=False,
            )
            .on_conflict_do_update(
                index_elements=["worker_key"],
                set_={
                    "host_id": host_id,
                    "capabilities": list(capabilities),
                    "status": "active",
                    "heartbeat_at": now,
                    "is_draining": False,
                },
            )
            .returning(WorkerRegistryRow)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one()
        return worker_to_record(row)

    async def heartbeat(self, worker_id: UUID, *, now: datetime) -> WorkerRecord:
        """Refresh heartbeat timestamp; does not change draining state."""
        row = await self._session.get(WorkerRegistryRow, worker_id, with_for_update=True)
        if row is None:
            raise NotFoundError(entity="worker_registry", entity_id=str(worker_id))
        row.heartbeat_at = now
        if row.status == "lost":
            row.status = "draining" if row.is_draining else "active"
        await self._session.flush()
        return worker_to_record(row)

    async def drain(self, worker_id: UUID, *, now: datetime) -> WorkerRecord:
        """Request graceful drain; transitions status to 'draining'."""
        row = await self._session.get(WorkerRegistryRow, worker_id, with_for_update=True)
        if row is None:
            raise NotFoundError(entity="worker_registry", entity_id=str(worker_id))
        row.is_draining = True
        row.drain_requested_at = now
        if row.status == "active":
            row.status = "draining"
        await self._session.flush()
        return worker_to_record(row)

    async def mark_drained(self, worker_id: UUID) -> WorkerRecord:
        """Mark worker as fully drained (no tasks held)."""
        row = await self._session.get(WorkerRegistryRow, worker_id, with_for_update=True)
        if row is None:
            raise NotFoundError(entity="worker_registry", entity_id=str(worker_id))
        row.status = "drained"
        await self._session.flush()
        return worker_to_record(row)

    async def mark_lost(self, worker_id: UUID) -> WorkerRecord:
        row = await self._session.get(WorkerRegistryRow, worker_id, with_for_update=True)
        if row is None:
            raise NotFoundError(entity="worker_registry", entity_id=str(worker_id))
        row.status = "lost"
        await self._session.flush()
        return worker_to_record(row)

    async def find_lost(
        self,
        *,
        now: datetime,
        heartbeat_grace: timedelta,
    ) -> Sequence[WorkerRecord]:
        """Return workers whose heartbeat has expired and are not yet lost/drained."""
        cutoff = now - heartbeat_grace
        result = await self._session.execute(
            select(WorkerRegistryRow)
            .where(
                and_(
                    WorkerRegistryRow.status.in_(["active", "draining"]),
                    WorkerRegistryRow.heartbeat_at < cutoff,
                )
            )
            .with_for_update(skip_locked=True)
        )
        return [worker_to_record(r) for r in result.scalars().all()]

    async def note_task_claimed(self, worker_key: str, *, now: datetime) -> None:
        """Update last_task_claimed_at for the worker identified by worker_key."""
        result = await self._session.execute(
            select(WorkerRegistryRow)
            .where(WorkerRegistryRow.worker_key == worker_key)
            .with_for_update(skip_locked=True)
        )
        row = result.scalar_one_or_none()
        if row is not None:
            row.last_task_claimed_at = now
            await self._session.flush()
