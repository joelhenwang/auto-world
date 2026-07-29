"""SQLAlchemy phase_snapshot repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fictional_world.domain.phases.records import PhaseSnapshotRecord
from fictional_world.infrastructure.database.mappings.records import snapshot_to_record
from fictional_world.infrastructure.database.models import (
    PhaseSnapshotCharacterRow,
    PhaseSnapshotRow,
)


class SqlAlchemyPhaseSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, snapshot_id: UUID) -> PhaseSnapshotRecord | None:
        row = await self._session.get(PhaseSnapshotRow, snapshot_id)
        if row is None:
            return None
        return await self._hydrate(row)

    async def get_for_phase(self, phase_run_id: UUID) -> PhaseSnapshotRecord | None:
        result = await self._session.execute(
            select(PhaseSnapshotRow).where(PhaseSnapshotRow.phase_run_id == phase_run_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return await self._hydrate(row)

    async def insert(self, snapshot: PhaseSnapshotRecord) -> PhaseSnapshotRecord:
        existing = await self.get_for_phase(snapshot.phase_run_id)
        if existing is not None:
            return existing
        row = PhaseSnapshotRow(
            id=snapshot.id,
            phase_run_id=snapshot.phase_run_id,
            world_id=snapshot.world_id,
            source_event_sequence=snapshot.source_event_sequence,
            world_clock_version=snapshot.world_clock_version,
            state_manifest=dict(snapshot.state_manifest),
            state_hash=snapshot.state_hash,
            sealed_at=snapshot.sealed_at,
        )
        self._session.add(row)
        for character in snapshot.characters:
            self._session.add(
                PhaseSnapshotCharacterRow(
                    snapshot_id=snapshot.id,
                    character_id=character.character_id,
                    character_state_version=character.character_state_version,
                    card_version_id=character.card_version_id,
                    location_id=character.location_id,
                    active_activity_id=character.active_activity_id,
                    context_source_hash=character.context_source_hash,
                    eligibility_status=character.eligibility_status,
                    eligibility_reason=character.eligibility_reason,
                )
            )
        await self._session.flush()
        return await self._hydrate(row)

    async def _hydrate(self, row: PhaseSnapshotRow) -> PhaseSnapshotRecord:
        result = await self._session.execute(
            select(PhaseSnapshotCharacterRow).where(
                PhaseSnapshotCharacterRow.snapshot_id == row.id
            )
        )
        characters = list(result.scalars().all())
        return snapshot_to_record(row, characters)
