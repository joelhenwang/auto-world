"""Repository and unit-of-work ports (handbook ``19`` §12)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID

from fictional_world.domain.characters.records import (
    CharacterRecord,
    CharacterStateRecord,
    EntityRecord,
)
from fictional_world.domain.events.persistence import (
    EventEffectRecord,
    OutboxMessageRecord,
    WorldEventRecord,
)
from fictional_world.domain.knowledge.persistence import ObservationPersistenceRecord
from fictional_world.domain.memory.persistence import RecentMemoryRecord
from fictional_world.domain.phases.records import PhaseRunRecord
from fictional_world.domain.tasks.budget import RequestBudgetRecord
from fictional_world.domain.tasks.task_run import TaskRun
from fictional_world.domain.world.records import (
    AggregateVersionRecord,
    WorldClockRecord,
    WorldRecord,
)


class WorldRepository(Protocol):
    async def get(self, world_id: UUID) -> WorldRecord | None: ...

    async def get_by_slug(self, slug: str) -> WorldRecord | None: ...

    async def insert(self, world: WorldRecord) -> WorldRecord: ...

    async def lock_for_event_sequence(self, world_id: UUID) -> WorldRecord: ...

    async def advance_event_sequence(
        self,
        world_id: UUID,
        *,
        next_sequence: int,
        expected_version: int,
    ) -> WorldRecord: ...

    async def get_clock(self, world_id: UUID) -> WorldClockRecord | None: ...

    async def upsert_clock(
        self, clock: WorldClockRecord, *, expected_version: int | None
    ) -> WorldClockRecord: ...


class CharacterRepository(Protocol):
    async def insert_entity(self, entity: EntityRecord) -> EntityRecord: ...

    async def insert_character(self, character: CharacterRecord) -> CharacterRecord: ...

    async def get_state(self, character_id: UUID) -> CharacterStateRecord | None: ...

    async def get_state_for_update(self, character_id: UUID) -> CharacterStateRecord: ...

    async def insert_state(self, state: CharacterStateRecord) -> CharacterStateRecord: ...

    async def save_state(
        self,
        state: CharacterStateRecord,
        *,
        expected_version: int,
    ) -> CharacterStateRecord: ...


class PhaseRepository(Protocol):
    async def get(self, phase_run_id: UUID) -> PhaseRunRecord | None: ...

    async def find_by_idempotency_key(self, key: str) -> PhaseRunRecord | None: ...

    async def insert(self, phase: PhaseRunRecord) -> PhaseRunRecord: ...

    async def save(
        self,
        phase: PhaseRunRecord,
        *,
        expected_version: int,
    ) -> PhaseRunRecord: ...


class EventRepository(Protocol):
    async def get(self, event_id: UUID) -> WorldEventRecord | None: ...

    async def find_by_idempotency_key(self, key: str) -> WorldEventRecord | None: ...

    async def list_for_world(
        self,
        world_id: UUID,
        *,
        after_sequence: int | None = None,
        limit: int = 100,
    ) -> Sequence[WorldEventRecord]: ...

    async def insert(self, event: WorldEventRecord) -> WorldEventRecord: ...

    async def insert_effects(
        self, effects: Sequence[EventEffectRecord]
    ) -> Sequence[EventEffectRecord]: ...


class ObservationRepository(Protocol):
    async def insert_many(
        self, observations: Sequence[ObservationPersistenceRecord]
    ) -> Sequence[ObservationPersistenceRecord]: ...

    async def list_for_observer(
        self,
        observer_id: UUID,
        *,
        limit: int = 50,
    ) -> Sequence[ObservationPersistenceRecord]: ...


class RecentMemoryRepository(Protocol):
    async def insert(self, memory: RecentMemoryRecord) -> RecentMemoryRecord: ...

    async def list_for_owner(
        self,
        owner_character_id: UUID,
        *,
        world_id: UUID,
        limit: int = 50,
    ) -> Sequence[RecentMemoryRecord]: ...


class AggregateVersionRepository(Protocol):
    async def get(
        self,
        world_id: UUID,
        aggregate_type: str,
        aggregate_id: UUID,
    ) -> AggregateVersionRecord | None: ...

    async def upsert(
        self,
        record: AggregateVersionRecord,
        *,
        expected_version: int | None,
    ) -> AggregateVersionRecord: ...

    async def verify(
        self,
        world_id: UUID,
        expected: Mapping[str, int],
    ) -> None:
        """``expected`` maps ``aggregate_type:aggregate_id`` -> version."""
        ...


class OutboxRepository(Protocol):
    async def insert(self, message: OutboxMessageRecord) -> OutboxMessageRecord: ...

    async def find_by_idempotency_key(self, key: str) -> OutboxMessageRecord | None: ...

    async def get(self, message_id: UUID) -> OutboxMessageRecord | None: ...

    async def insert_many(
        self, messages: Sequence[OutboxMessageRecord]
    ) -> Sequence[OutboxMessageRecord]: ...

    async def claim_available(
        self,
        *,
        worker_id: str,
        lease_duration: timedelta,
        now: datetime,
        limit: int = 1,
    ) -> Sequence[OutboxMessageRecord]: ...

    async def complete(
        self,
        message_id: UUID,
        *,
        worker_id: str,
        now: datetime,
    ) -> OutboxMessageRecord: ...


class TaskRepository(Protocol):
    async def get(self, task_id: UUID) -> TaskRun | None: ...

    async def find_by_idempotency_key(self, key: str) -> TaskRun | None: ...

    async def insert(self, task: TaskRun) -> TaskRun: ...

    async def add_dependency(self, task_id: UUID, depends_on_task_id: UUID) -> None: ...

    async def list_dependencies(self, task_id: UUID) -> Sequence[UUID]: ...

    async def claim_available(
        self,
        *,
        worker_id: str,
        lease_duration: timedelta,
        now: datetime,
        limit: int = 1,
    ) -> Sequence[TaskRun]: ...

    async def heartbeat(
        self,
        task_id: UUID,
        *,
        worker_id: str,
        lease_duration: timedelta,
        now: datetime,
    ) -> TaskRun: ...

    async def mark_running(self, task_id: UUID, *, worker_id: str, now: datetime) -> TaskRun: ...

    async def complete_success(
        self,
        task_id: UUID,
        *,
        worker_id: str,
        now: datetime,
        result_reference: Mapping[str, object] | None = None,
    ) -> TaskRun: ...

    async def fail_or_retry(
        self,
        task_id: UUID,
        *,
        worker_id: str,
        now: datetime,
        error_code: str,
        error_detail: Mapping[str, object] | None,
        retry_delay: timedelta,
    ) -> TaskRun: ...

    async def cancel(self, task_id: UUID, *, now: datetime) -> TaskRun: ...


class BudgetRepository(Protocol):
    async def get(self, reservation_id: UUID) -> RequestBudgetRecord | None: ...

    async def find_by_reservation_key(self, key: str) -> RequestBudgetRecord | None: ...

    async def reserve(self, record: RequestBudgetRecord) -> RequestBudgetRecord: ...

    async def consume(self, reservation_id: UUID, *, now: datetime) -> RequestBudgetRecord: ...

    async def release(self, reservation_id: UUID) -> RequestBudgetRecord: ...

    async def expire_due(
        self, *, now: datetime, limit: int = 100
    ) -> Sequence[RequestBudgetRecord]: ...


class UnitOfWork(Protocol):
    worlds: WorldRepository
    characters: CharacterRepository
    phases: PhaseRepository
    events: EventRepository
    observations: ObservationRepository
    recent_memories: RecentMemoryRepository
    aggregate_versions: AggregateVersionRepository
    outbox: OutboxRepository
    tasks: TaskRepository
    budgets: BudgetRepository

    async def __aenter__(self) -> UnitOfWork: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
