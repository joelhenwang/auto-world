"""Observation, recent-memory, aggregate-version, and outbox repositories."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fictional_world.domain.events.persistence import OutboxMessageRecord
from fictional_world.domain.knowledge.persistence import ObservationPersistenceRecord
from fictional_world.domain.memory.persistence import RecentMemoryRecord
from fictional_world.domain.world.records import AggregateVersionRecord
from fictional_world.infrastructure.database.errors import OptimisticConcurrencyError
from fictional_world.infrastructure.database.mappings.records import (
    aggregate_version_to_record,
    memory_to_record,
    observation_to_record,
    outbox_to_record,
    parse_aggregate_key,
)
from fictional_world.infrastructure.database.models import (
    AggregateVersionRow,
    ObservationRow,
    OutboxMessageRow,
    RecentMemoryRow,
)


class SqlAlchemyObservationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert_many(
        self, observations: Sequence[ObservationPersistenceRecord]
    ) -> Sequence[ObservationPersistenceRecord]:
        rows: list[ObservationRow] = []
        for obs in observations:
            row = ObservationRow(
                id=obs.id,
                world_event_id=obs.world_event_id,
                observer_id=obs.observer_id,
                observation_type=obs.observation_type,
                perceived_summary=obs.perceived_summary,
                perceived_facts=dict(obs.perceived_facts),
                omitted_fact_keys=list(obs.omitted_fact_keys) or None,
                confidence=obs.confidence,
                visibility_reason=obs.visibility_reason,
                source_sense_tags=list(obs.source_sense_tags) or None,
                content_hash=obs.content_hash,
            )
            self._session.add(row)
            rows.append(row)
        await self._session.flush()
        return [observation_to_record(row) for row in rows]

    async def list_for_observer(
        self,
        observer_id: UUID,
        *,
        limit: int = 50,
    ) -> Sequence[ObservationPersistenceRecord]:
        result = await self._session.execute(
            select(ObservationRow)
            .where(ObservationRow.observer_id == observer_id)
            .order_by(ObservationRow.created_at.desc())
            .limit(limit)
        )
        return [observation_to_record(row) for row in result.scalars().all()]


class SqlAlchemyRecentMemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert(self, memory: RecentMemoryRecord) -> RecentMemoryRecord:
        row = RecentMemoryRow(
            id=memory.id,
            world_id=memory.world_id,
            owner_character_id=memory.owner_character_id,
            memory_type=memory.memory_type,
            content=memory.content,
            salience=memory.salience,
            confidence=memory.confidence,
            emotional_weight=memory.emotional_weight,
            visibility=memory.visibility,
            occurred_phase_index=memory.occurred_phase_index,
            created_phase_index=memory.created_phase_index,
            last_recalled_phase_index=memory.last_recalled_phase_index,
            recall_count=memory.recall_count,
            decay_score=memory.decay_score,
            status=memory.status,
            content_hash=memory.content_hash,
            summary_version=memory.summary_version,
            source_event_id=memory.source_event_id,
            source_observation_id=memory.source_observation_id,
        )
        self._session.add(row)
        await self._session.flush()
        return memory_to_record(row)

    async def list_for_owner(
        self,
        owner_character_id: UUID,
        *,
        world_id: UUID,
        limit: int = 50,
    ) -> Sequence[RecentMemoryRecord]:
        result = await self._session.execute(
            select(RecentMemoryRow)
            .where(
                RecentMemoryRow.owner_character_id == owner_character_id,
                RecentMemoryRow.world_id == world_id,
            )
            .order_by(RecentMemoryRow.created_at.desc())
            .limit(limit)
        )
        return [memory_to_record(row) for row in result.scalars().all()]


class SqlAlchemyAggregateVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self,
        world_id: UUID,
        aggregate_type: str,
        aggregate_id: UUID,
    ) -> AggregateVersionRecord | None:
        row = await self._session.get(AggregateVersionRow, (world_id, aggregate_type, aggregate_id))
        return aggregate_version_to_record(row) if row is not None else None

    async def upsert(
        self,
        record: AggregateVersionRecord,
        *,
        expected_version: int | None,
    ) -> AggregateVersionRecord:
        row = await self._session.get(
            AggregateVersionRow,
            (record.world_id, record.aggregate_type, record.aggregate_id),
            with_for_update=True,
        )
        if row is None:
            if expected_version is not None:
                raise OptimisticConcurrencyError(
                    entity=record.aggregate_type,
                    entity_id=str(record.aggregate_id),
                    expected_version=expected_version,
                )
            row = AggregateVersionRow(
                world_id=record.world_id,
                aggregate_type=record.aggregate_type,
                aggregate_id=record.aggregate_id,
                version=record.version,
            )
            self._session.add(row)
        else:
            if expected_version is None or int(row.version) != expected_version:
                raise OptimisticConcurrencyError(
                    entity=record.aggregate_type,
                    entity_id=str(record.aggregate_id),
                    expected_version=expected_version if expected_version is not None else -1,
                )
            row.version = record.version
        await self._session.flush()
        return aggregate_version_to_record(row)

    async def verify(self, world_id: UUID, expected: Mapping[str, int]) -> None:
        for key, version in expected.items():
            aggregate_type, aggregate_id = parse_aggregate_key(key)
            row = await self.get(world_id, aggregate_type, aggregate_id)
            current = 0 if row is None else row.version
            if current != version:
                raise OptimisticConcurrencyError(
                    entity=aggregate_type,
                    entity_id=str(aggregate_id),
                    expected_version=version,
                )


class SqlAlchemyOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert(self, message: OutboxMessageRecord) -> OutboxMessageRecord:
        row = OutboxMessageRow(
            id=message.id,
            world_event_id=message.world_event_id,
            message_type=message.message_type,
            payload=dict(message.payload),
            idempotency_key=message.idempotency_key,
            state=message.state,
            attempt_count=message.attempt_count,
            claimed_by=message.claimed_by,
            claim_expires_at=message.claim_expires_at,
            completed_at=message.completed_at,
        )
        self._session.add(row)
        await self._session.flush()
        return outbox_to_record(row)

    async def find_by_idempotency_key(self, key: str) -> OutboxMessageRecord | None:
        result = await self._session.execute(
            select(OutboxMessageRow).where(OutboxMessageRow.idempotency_key == key)
        )
        row = result.scalar_one_or_none()
        return outbox_to_record(row) if row is not None else None

    async def insert_many(
        self, messages: Sequence[OutboxMessageRecord]
    ) -> Sequence[OutboxMessageRecord]:
        return [await self.insert(message) for message in messages]
