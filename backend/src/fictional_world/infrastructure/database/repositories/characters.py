"""SQLAlchemy character / entity / state repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fictional_world.domain.characters.records import (
    CharacterRecord,
    CharacterStateRecord,
    EntityRecord,
)
from fictional_world.infrastructure.database.errors import NotFoundError, OptimisticConcurrencyError
from fictional_world.infrastructure.database.mappings.records import (
    apply_character_state,
    character_state_to_record,
    character_to_record,
    entity_to_record,
)
from fictional_world.infrastructure.database.models import (
    CharacterRow,
    CharacterStateRow,
    EntityRow,
)


class SqlAlchemyCharacterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert_entity(self, entity: EntityRecord) -> EntityRecord:
        row = EntityRow(
            id=entity.id,
            world_id=entity.world_id,
            entity_type=entity.entity_type,
            canonical_name=entity.canonical_name,
            normalized_name=entity.normalized_name,
            lifecycle_status=entity.lifecycle_status,
            created_event_id=entity.created_event_id,
            archived_event_id=entity.archived_event_id,
            archived_at=entity.archived_at,
        )
        self._session.add(row)
        await self._session.flush()
        return entity_to_record(row)

    async def insert_character(self, character: CharacterRecord) -> CharacterRecord:
        row = CharacterRow(
            entity_id=character.entity_id,
            character_kind=character.character_kind,
            species_code=character.species_code,
            current_card_version_id=character.current_card_version_id,
            version=character.version,
        )
        self._session.add(row)
        await self._session.flush()
        return character_to_record(row)

    async def get_state(self, character_id: UUID) -> CharacterStateRecord | None:
        row = await self._session.get(CharacterStateRow, character_id)
        return character_state_to_record(row) if row is not None else None

    async def get_state_for_update(self, character_id: UUID) -> CharacterStateRecord:
        result = await self._session.execute(
            select(CharacterStateRow)
            .where(CharacterStateRow.character_id == character_id)
            .with_for_update()
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise NotFoundError(entity="character_state", entity_id=str(character_id))
        return character_state_to_record(row)

    async def insert_state(self, state: CharacterStateRecord) -> CharacterStateRecord:
        row = CharacterStateRow(character_id=state.character_id)
        apply_character_state(row, state)
        self._session.add(row)
        await self._session.flush()
        return character_state_to_record(row)

    async def save_state(
        self,
        state: CharacterStateRecord,
        *,
        expected_version: int,
    ) -> CharacterStateRecord:
        result = await self._session.execute(
            select(CharacterStateRow)
            .where(CharacterStateRow.character_id == state.character_id)
            .with_for_update()
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise NotFoundError(entity="character_state", entity_id=str(state.character_id))
        if int(row.version) != expected_version:
            raise OptimisticConcurrencyError(
                entity="character_state",
                entity_id=str(state.character_id),
                expected_version=expected_version,
            )
        apply_character_state(row, state)
        row.version = expected_version + 1
        await self._session.flush()
        return character_state_to_record(row)
