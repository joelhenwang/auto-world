"""SQLAlchemy World / WorldClock repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fictional_world.domain.seed.records import WorldConfigRecord
from fictional_world.domain.world.records import WorldClockRecord, WorldRecord
from fictional_world.infrastructure.database.errors import NotFoundError, OptimisticConcurrencyError
from fictional_world.infrastructure.database.mappings.records import (
    apply_clock,
    clock_to_record,
    config_to_record,
    world_to_record,
)
from fictional_world.infrastructure.database.models import WorldClockRow, WorldConfigRow, WorldRow


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

    async def update_status(
        self,
        world_id: UUID,
        *,
        status: str,
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
        row.status = status
        row.version = expected_version + 1
        await self._session.flush()
        return world_to_record(row)

    async def insert_config(self, config: WorldConfigRecord) -> WorldConfigRecord:
        row = WorldConfigRow(
            id=config.id,
            world_id=config.world_id,
            config_version=config.config_version,
            is_active=config.is_active,
            effective_from_phase_index=config.effective_from_phase_index,
            detailed_phase_names=list(config.detailed_phase_names),
            max_days=config.max_days,
            max_generations=config.max_generations,
            plot_armour_level=config.plot_armour_level,
            director_privileges=dict(config.director_privileges),
            image_budget_per_day=config.image_budget_per_day,
            macro_simulation_policy=dict(config.macro_simulation_policy),
            content_policy_version=config.content_policy_version,
            created_event_id=config.created_event_id,
        )
        self._session.add(row)
        await self._session.flush()
        return config_to_record(row)

    async def set_config_created_event(
        self, config_id: UUID, *, created_event_id: UUID
    ) -> WorldConfigRecord:
        row = await self._session.get(WorldConfigRow, config_id, with_for_update=True)
        if row is None:
            raise NotFoundError(entity="world_config", entity_id=str(config_id))
        row.created_event_id = created_event_id
        await self._session.flush()
        return config_to_record(row)
