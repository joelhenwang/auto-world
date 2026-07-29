"""Request budget ledger repository."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fictional_world.domain.common.enums import BudgetStatus
from fictional_world.domain.common.errors import InvalidStateTransition
from fictional_world.domain.tasks.budget import RequestBudgetRecord
from fictional_world.infrastructure.database.errors import OptimisticConcurrencyError
from fictional_world.infrastructure.database.mappings.records import budget_to_record
from fictional_world.infrastructure.database.models import RequestBudgetLedgerRow


class SqlAlchemyBudgetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, reservation_id: UUID) -> RequestBudgetRecord | None:
        row = await self._session.get(RequestBudgetLedgerRow, reservation_id)
        return budget_to_record(row) if row is not None else None

    async def find_by_reservation_key(self, key: str) -> RequestBudgetRecord | None:
        result = await self._session.execute(
            select(RequestBudgetLedgerRow).where(RequestBudgetLedgerRow.reservation_key == key)
        )
        row = result.scalar_one_or_none()
        return budget_to_record(row) if row is not None else None

    async def reserve(self, record: RequestBudgetRecord) -> RequestBudgetRecord:
        existing = await self.find_by_reservation_key(record.reservation_key)
        if existing is not None:
            return existing
        row = RequestBudgetLedgerRow(
            id=record.id,
            reservation_key=record.reservation_key,
            required_request_count=record.required_request_count,
            provider_kind=record.provider_kind,
            model_slug=record.model_slug,
            status=str(record.status),
            world_id=record.world_id,
            phase_run_id=record.phase_run_id,
            task_run_id=record.task_run_id,
            expires_at=record.expires_at,
            consumed_at=record.consumed_at,
        )
        if record.reserved_at is not None:
            row.reserved_at = record.reserved_at
        self._session.add(row)
        await self._session.flush()
        return budget_to_record(row)

    async def consume(self, reservation_id: UUID, *, now: datetime) -> RequestBudgetRecord:
        row = await self._require(reservation_id)
        if BudgetStatus(row.status) != BudgetStatus.RESERVED:
            raise InvalidStateTransition(
                entity="request_budget_ledger",
                from_state=row.status,
                to_state=BudgetStatus.CONSUMED.value,
            )
        row.status = BudgetStatus.CONSUMED.value
        row.consumed_at = now
        await self._session.flush()
        return budget_to_record(row)

    async def release(self, reservation_id: UUID) -> RequestBudgetRecord:
        row = await self._require(reservation_id)
        if BudgetStatus(row.status) != BudgetStatus.RESERVED:
            raise InvalidStateTransition(
                entity="request_budget_ledger",
                from_state=row.status,
                to_state=BudgetStatus.RELEASED.value,
            )
        row.status = BudgetStatus.RELEASED.value
        await self._session.flush()
        return budget_to_record(row)

    async def expire_due(self, *, now: datetime, limit: int = 100) -> Sequence[RequestBudgetRecord]:
        result = await self._session.execute(
            select(RequestBudgetLedgerRow)
            .where(
                RequestBudgetLedgerRow.status == BudgetStatus.RESERVED.value,
                RequestBudgetLedgerRow.expires_at <= now,
            )
            .order_by(RequestBudgetLedgerRow.expires_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        rows = list(result.scalars().all())
        expired: list[RequestBudgetRecord] = []
        for row in rows:
            row.status = BudgetStatus.EXPIRED.value
            expired.append(budget_to_record(row))
        await self._session.flush()
        return expired

    async def _require(self, reservation_id: UUID) -> RequestBudgetLedgerRow:
        row = await self._session.get(RequestBudgetLedgerRow, reservation_id, with_for_update=True)
        if row is None:
            raise OptimisticConcurrencyError(
                entity="request_budget_ledger",
                entity_id=str(reservation_id),
                expected_version=-1,
            )
        return row
