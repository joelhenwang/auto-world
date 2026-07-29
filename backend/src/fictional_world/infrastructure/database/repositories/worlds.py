"""SQLAlchemy World / WorldClock repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fictional_world.domain.world.records import WorldClockRecord, WorldRecord
from fictional_world.infrastructure.database.errors import NotFoundError, OptimisticConcurrencyError
from fictional_world.infrastructure.database.mappings.records import (
    apply_clock,
    clock_to_record,
    world_to_record,
)
from fictional_world.infrastructure.database.models import WorldClockRow, WorldRow


class SqlAlchemyWorldRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, world_id: UUID) -> WorldRecord | None:
        row = await self._session.get(WorldRow, world_id)
        return world_to_record(row) if row is not None else None

    async def get_by_slug(self, slug: str) -> WorldRecord | None:
        result = await self._session.execute(select(WorldRow).where(WorldRow.slug == slug))
        row = result.scalar_one_or_none()
        return world_to_record(row) if row is not None else None

    async def insert(self, world: WorldRecord) -> WorldRecord:
        row = WorldRow(
            id=world.id,
            slug=world.slug,
            name=world.name,
            status=world.status,
            language=world.language,
            content_rating=world.content_rating,
            current_event_sequence=world.current_event_sequence,
            version=world.version,
            ended_at=world.ended_at,
        )
        self._session.add(row)
        await self._session.flush()
        return world_to_record(row)

    async def lock_for_event_sequence(self, world_id: UUID) -> WorldRecord:
        result = await self._session.execute(
            select(WorldRow).where(WorldRow.id == world_id).with_for_update()
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise NotFoundError(entity="world", entity_id=str(world_id))
        return world_to_record(row)

    async def advance_event_sequence(
        self,
        world_id: UUID,
        *,
        next_sequence: int,
        expected_version: int,
    ) -> WorldRecord:
        result = await self._session.execute(
            select(WorldRow).where(WorldRow.id == world_id).with_for_update()
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise NotFoundError(entity="world", entity_id=str(world_id))
        if int(row.version) != expected_version:
            raise OptimisticConcurrencyError(
                entity="world",
                entity_id=str(world_id),
                expected_version=expected_version,
            )
        row.current_event_sequence = next_sequence
        row.version = expected_version + 1
        await self._session.flush()
        return world_to_record(row)

    async def get_clock(self, world_id: UUID) -> WorldClockRecord | None:
        row = await self._session.get(WorldClockRow, world_id)
        return clock_to_record(row) if row is not None else None

    async def upsert_clock(
        self,
        clock: WorldClockRecord,
        *,
        expected_version: int | None,
    ) -> WorldClockRecord:
        row = await self._session.get(WorldClockRow, clock.world_id)
        if row is None:
            if expected_version is not None:
                raise NotFoundError(entity="world_clock", entity_id=str(clock.world_id))
            row = WorldClockRow(world_id=clock.world_id)
            apply_clock(row, clock)
            self._session.add(row)
        else:
            if expected_version is None or int(row.version) != expected_version:
                raise OptimisticConcurrencyError(
                    entity="world_clock",
                    entity_id=str(clock.world_id),
                    expected_version=expected_version if expected_version is not None else -1,
                )
            apply_clock(row, clock)
            row.version = expected_version + 1
        await self._session.flush()
        return clock_to_record(row)
