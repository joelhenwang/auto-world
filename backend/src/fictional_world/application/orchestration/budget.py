"""Budget reservation data operations (S0-ORCH-001)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.domain.common.enums import BudgetStatus
from fictional_world.domain.tasks.budget import RequestBudgetRecord


@dataclass(frozen=True, slots=True)
class ReserveBudgetCommand:
    reservation_key: str
    required_request_count: int
    provider_kind: str
    model_slug: str
    expires_at: datetime
    world_id: UUID | None = None
    phase_run_id: UUID | None = None
    task_run_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ReserveBudgetResult:
    reservation: RequestBudgetRecord
    already_existed: bool


class BudgetService:
    """Data-layer reserve / consume / release / expire against ``request_budget_ledger``."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def reserve(self, command: ReserveBudgetCommand) -> ReserveBudgetResult:
        existing = await self._uow.budgets.find_by_reservation_key(command.reservation_key)
        if existing is not None:
            return ReserveBudgetResult(reservation=existing, already_existed=True)

        record = RequestBudgetRecord(
            id=uuid4(),
            reservation_key=command.reservation_key,
            required_request_count=command.required_request_count,
            provider_kind=command.provider_kind,
            model_slug=command.model_slug,
            status=BudgetStatus.RESERVED,
            world_id=command.world_id,
            phase_run_id=command.phase_run_id,
            task_run_id=command.task_run_id,
            reserved_at=datetime.now(UTC),
            expires_at=command.expires_at,
        )
        try:
            inserted = await self._uow.budgets.reserve(record)
        except IntegrityError:
            await self._uow.rollback()
            recovered = await self._uow.budgets.find_by_reservation_key(command.reservation_key)
            if recovered is None:
                raise
            return ReserveBudgetResult(reservation=recovered, already_existed=True)
        return ReserveBudgetResult(
            reservation=inserted,
            already_existed=inserted.id != record.id,
        )

    async def consume(
        self, reservation_id: UUID, *, now: datetime | None = None
    ) -> RequestBudgetRecord:
        return await self._uow.budgets.consume(reservation_id, now=now or datetime.now(UTC))

    async def release(self, reservation_id: UUID) -> RequestBudgetRecord:
        return await self._uow.budgets.release(reservation_id)

    async def expire_due(
        self, *, now: datetime | None = None, limit: int = 100
    ) -> Sequence[RequestBudgetRecord]:
        return await self._uow.budgets.expire_due(now=now or datetime.now(UTC), limit=limit)

    async def reserve_for_duration(
        self,
        *,
        reservation_key: str,
        required_request_count: int,
        provider_kind: str,
        model_slug: str,
        ttl: timedelta,
        world_id: UUID | None = None,
        phase_run_id: UUID | None = None,
        task_run_id: UUID | None = None,
        now: datetime | None = None,
    ) -> ReserveBudgetResult:
        clock = now or datetime.now(UTC)
        return await self.reserve(
            ReserveBudgetCommand(
                reservation_key=reservation_key,
                required_request_count=required_request_count,
                provider_kind=provider_kind,
                model_slug=model_slug,
                expires_at=clock + ttl,
                world_id=world_id,
                phase_run_id=phase_run_id,
                task_run_id=task_run_id,
            )
        )
