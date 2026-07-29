"""SQLAlchemy phase_run repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fictional_world.domain.phases.records import PhaseRunRecord
from fictional_world.infrastructure.database.errors import NotFoundError, OptimisticConcurrencyError
from fictional_world.infrastructure.database.mappings.records import apply_phase, phase_to_record
from fictional_world.infrastructure.database.models import PhaseRunRow


class SqlAlchemyPhaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, phase_run_id: UUID) -> PhaseRunRecord | None:
        row = await self._session.get(PhaseRunRow, phase_run_id)
        return phase_to_record(row) if row is not None else None

    async def find_by_idempotency_key(self, key: str) -> PhaseRunRecord | None:
        result = await self._session.execute(
            select(PhaseRunRow).where(PhaseRunRow.idempotency_key == key)
        )
        row = result.scalar_one_or_none()
        return phase_to_record(row) if row is not None else None

    async def insert(self, phase: PhaseRunRecord) -> PhaseRunRecord:
        row = PhaseRunRow(id=phase.id)
        apply_phase(row, phase)
        self._session.add(row)
        await self._session.flush()
        return phase_to_record(row)

    async def save(self, phase: PhaseRunRecord, *, expected_version: int) -> PhaseRunRecord:
        result = await self._session.execute(
            select(PhaseRunRow).where(PhaseRunRow.id == phase.id).with_for_update()
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise NotFoundError(entity="phase_run", entity_id=str(phase.id))
        if int(row.version) != expected_version:
            raise OptimisticConcurrencyError(
                entity="phase_run",
                entity_id=str(phase.id),
                expected_version=expected_version,
            )
        apply_phase(row, phase)
        row.version = expected_version + 1
        await self._session.flush()
        return phase_to_record(row)
