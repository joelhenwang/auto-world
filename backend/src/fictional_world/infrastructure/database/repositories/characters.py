"""SQLAlchemy character / entity / state repository."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fictional_world.domain.characters.records import (
    CharacterRecord,
    CharacterStateRecord,
    EntityRecord,
)
from fictional_world.domain.seed.records import CharacterCardVersionRecord, LocationRecord
from fictional_world.infrastructure.database.errors import NotFoundError, OptimisticConcurrencyError
from fictional_world.infrastructure.database.mappings.records import (
    apply_character_state,
    card_to_record,
    character_state_to_record,
    character_to_record,
    entity_to_record,
    location_to_record,
)
from fictional_world.infrastructure.database.models import (
    CharacterCardVersionRow,
    CharacterRow,
    CharacterStateRow,
    EntityRow,
    LocationRow,
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

    async def insert_location(self, location: LocationRecord) -> LocationRecord:
        row = LocationRow(
            entity_id=location.entity_id,
            parent_location_id=location.parent_location_id,
            location_type=location.location_type,
            region_code=location.region_code,
            coordinate_x=location.coordinate_x,
            coordinate_y=location.coordinate_y,
            elevation=location.elevation,
            capacity=location.capacity,
            owner_entity_id=location.owner_entity_id,
            environment_tags=list(location.environment_tags) or None,
            canonical_description=location.canonical_description,
            visual_profile_version=location.visual_profile_version,
            version=location.version,
        )
        self._session.add(row)
        await self._session.flush()
        return location_to_record(row)

    async def get_location(self, entity_id: UUID) -> LocationRecord | None:
        row = await self._session.get(LocationRow, entity_id)
        return location_to_record(row) if row is not None else None

    async def insert_card(self, card: CharacterCardVersionRecord) -> CharacterCardVersionRecord:
        row = CharacterCardVersionRow(
            id=card.id,
            character_id=card.character_id,
            version_number=card.version_number,
            identity=dict(card.identity),
            backstory=card.backstory,
            appearance=dict(card.appearance),
            personality_traits=dict(card.personality_traits),
            values=dict(card.values),
            fears=dict(card.fears),
            desires=dict(card.desires),
            boundaries=dict(card.boundaries),
            voice_profile=dict(card.voice_profile),
            initial_capabilities=dict(card.initial_capabilities),
            secret_manifest=dict(card.secret_manifest),
            change_summary=card.change_summary,
            source_event_id=card.source_event_id,
            content_hash=card.content_hash,
        )
        self._session.add(row)
        await self._session.flush()
        return card_to_record(row)

    async def get_card(self, card_id: UUID) -> CharacterCardVersionRecord | None:
        row = await self._session.get(CharacterCardVersionRow, card_id)
        return card_to_record(row) if row is not None else None

    async def set_character_card(
        self, character_id: UUID, *, card_version_id: UUID
    ) -> CharacterRecord:
        row = await self._session.get(CharacterRow, character_id, with_for_update=True)
        if row is None:
            raise NotFoundError(entity="character", entity_id=str(character_id))
        row.current_card_version_id = card_version_id
        await self._session.flush()
        return character_to_record(row)

    async def set_entity_created_event(
        self, entity_id: UUID, *, created_event_id: UUID
    ) -> EntityRecord:
        row = await self._session.get(EntityRow, entity_id, with_for_update=True)
        if row is None:
            raise NotFoundError(entity="entity", entity_id=str(entity_id))
        row.created_event_id = created_event_id
        await self._session.flush()
        return entity_to_record(row)

    async def list_character_ids_for_world(self, world_id: UUID) -> Sequence[UUID]:
        result = await self._session.execute(
            select(CharacterRow.entity_id)
            .join(EntityRow, EntityRow.id == CharacterRow.entity_id)
            .where(EntityRow.world_id == world_id)
            .order_by(CharacterRow.entity_id.asc())
        )
        return list(result.scalars().all())
