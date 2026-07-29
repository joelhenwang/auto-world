"""SQLAlchemy world_event / event_effect repository."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fictional_world.domain.events.persistence import EventEffectRecord, WorldEventRecord
from fictional_world.infrastructure.database.mappings.records import (
    effect_to_record,
    event_to_record,
)
from fictional_world.infrastructure.database.models import EventEffectRow, WorldEventRow


class SqlAlchemyEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, event_id: UUID) -> WorldEventRecord | None:
        row = await self._session.get(WorldEventRow, event_id)
        if row is None:
            return None
        effects = await self._effects_for(event_id)
        return event_to_record(row, effects)

    async def find_by_idempotency_key(self, key: str) -> WorldEventRecord | None:
        result = await self._session.execute(
            select(WorldEventRow).where(WorldEventRow.idempotency_key == key)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        effects = await self._effects_for(row.id)
        return event_to_record(row, effects)

    async def list_for_world(
        self,
        world_id: UUID,
        *,
        after_sequence: int | None = None,
        limit: int = 100,
    ) -> Sequence[WorldEventRecord]:
        stmt = select(WorldEventRow).where(WorldEventRow.world_id == world_id)
        if after_sequence is not None:
            stmt = stmt.where(WorldEventRow.sequence_number > after_sequence)
        stmt = stmt.order_by(WorldEventRow.sequence_number.asc()).limit(limit)
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())
        return [event_to_record(row) for row in rows]

    async def insert(self, event: WorldEventRecord) -> WorldEventRecord:
        row = WorldEventRow(
            id=event.id,
            world_id=event.world_id,
            sequence_number=event.sequence_number,
            absolute_phase_index=event.absolute_phase_index,
            phase_run_id=event.phase_run_id,
            scene_id=event.scene_id,
            event_type=event.event_type,
            initiator_entity_id=event.initiator_entity_id,
            location_id=event.location_id,
            canonical_summary=event.canonical_summary,
            structured_facts=dict(event.structured_facts),
            importance=event.importance,
            visibility_class=event.visibility_class,
            source_kind=event.source_kind,
            source_model_profile_id=event.source_model_profile_id,
            prompt_version_id=event.prompt_version_id,
            random_seed=event.random_seed,
            idempotency_key=event.idempotency_key,
            supersedes_event_id=event.supersedes_event_id,
            consistency_status=event.consistency_status,
            director_provenance=event.director_provenance,
            npc_provenance=event.npc_provenance,
        )
        self._session.add(row)
        await self._session.flush()
        effect_rows: list[EventEffectRow] = []
        if event.effects:
            effect_rows = list(await self._insert_effect_rows(event.effects))
        return event_to_record(row, effect_rows)

    async def insert_effects(
        self, effects: Sequence[EventEffectRecord]
    ) -> Sequence[EventEffectRecord]:
        rows = await self._insert_effect_rows(effects)
        return [effect_to_record(row) for row in rows]

    async def _insert_effect_rows(
        self, effects: Sequence[EventEffectRecord]
    ) -> list[EventEffectRow]:
        rows: list[EventEffectRow] = []
        for effect in effects:
            row = EventEffectRow(
                id=effect.id,
                world_event_id=effect.world_event_id,
                effect_index=effect.effect_index,
                effect_type=effect.effect_type,
                target_entity_id=effect.target_entity_id,
                effect_payload=dict(effect.effect_payload),
                previous_state=dict(effect.previous_state),
                resulting_state=dict(effect.resulting_state),
                target_version_before=effect.target_version_before,
                target_version_after=effect.target_version_after,
                source_attempt_ids=list(effect.source_attempt_ids) or None,
                validation_manifest=dict(effect.validation_manifest),
            )
            self._session.add(row)
            rows.append(row)
        await self._session.flush()
        return rows

    async def _effects_for(self, event_id: UUID) -> list[EventEffectRow]:
        result = await self._session.execute(
            select(EventEffectRow)
            .where(EventEffectRow.world_event_id == event_id)
            .order_by(EventEffectRow.effect_index.asc())
        )
        return list(result.scalars().all())
