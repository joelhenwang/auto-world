"""Task queue application service (S0-ORCH-001)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.domain.common.enums import TaskState
from fictional_world.domain.common.errors import DomainError
from fictional_world.domain.tasks.task_run import JsonObject, TaskRun


class TaskQueueError(DomainError):
    """Raised for task-queue rule failures."""


@dataclass(frozen=True, slots=True)
class CreateTaskCommand:
    task_type: str
    idempotency_key: str
    payload: JsonObject | None = None
    world_id: UUID | None = None
    phase_run_id: UUID | None = None
    scene_id: UUID | None = None
    subject_entity_id: UUID | None = None
    priority: int = 0
    max_attempts: int = 3
    available_at: datetime | None = None
    depends_on: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class CreateTaskResult:
    task: TaskRun
    already_existed: bool


class TaskQueueService:
    """Create, claim, heartbeat, complete, and dead-letter durable tasks."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def create(self, command: CreateTaskCommand) -> CreateTaskResult:
        existing = await self._uow.tasks.find_by_idempotency_key(command.idempotency_key)
        if existing is not None:
            return CreateTaskResult(task=existing, already_existed=True)

        now = datetime.now(UTC)
        task = TaskRun(
            id=uuid4(),
            task_type=command.task_type,
            world_id=command.world_id,
            phase_run_id=command.phase_run_id,
            scene_id=command.scene_id,
            subject_entity_id=command.subject_entity_id,
            state=TaskState.PENDING,
            priority=command.priority,
            payload=dict(command.payload or {}),
            idempotency_key=command.idempotency_key,
            attempt_count=0,
            max_attempts=command.max_attempts,
            available_at=command.available_at or now,
            created_at=now,
        )
        try:
            inserted = await self._uow.tasks.insert(task)
            for dep_id in command.depends_on:
                await self._uow.tasks.add_dependency(inserted.id, dep_id)
        except IntegrityError:
            await self._uow.rollback()
            recovered = await self._uow.tasks.find_by_idempotency_key(command.idempotency_key)
            if recovered is None:
                raise
            return CreateTaskResult(task=recovered, already_existed=True)
        return CreateTaskResult(task=inserted, already_existed=False)

    async def claim(
        self,
        *,
        worker_id: str,
        lease_duration: timedelta = timedelta(seconds=90),
        now: datetime | None = None,
        limit: int = 1,
    ) -> Sequence[TaskRun]:
        return await self._uow.tasks.claim_available(
            worker_id=worker_id,
            lease_duration=lease_duration,
            now=now or datetime.now(UTC),
            limit=limit,
        )

    async def heartbeat(
        self,
        task_id: UUID,
        *,
        worker_id: str,
        lease_duration: timedelta = timedelta(seconds=90),
        now: datetime | None = None,
    ) -> TaskRun:
        return await self._uow.tasks.heartbeat(
            task_id,
            worker_id=worker_id,
            lease_duration=lease_duration,
            now=now or datetime.now(UTC),
        )

    async def mark_running(
        self, task_id: UUID, *, worker_id: str, now: datetime | None = None
    ) -> TaskRun:
        return await self._uow.tasks.mark_running(
            task_id, worker_id=worker_id, now=now or datetime.now(UTC)
        )

    async def complete(
        self,
        task_id: UUID,
        *,
        worker_id: str,
        result_reference: Mapping[str, object] | None = None,
        now: datetime | None = None,
    ) -> TaskRun:
        return await self._uow.tasks.complete_success(
            task_id,
            worker_id=worker_id,
            now=now or datetime.now(UTC),
            result_reference=result_reference,
        )

    async def fail(
        self,
        task_id: UUID,
        *,
        worker_id: str,
        error_code: str,
        error_detail: Mapping[str, object] | None = None,
        retry_delay: timedelta = timedelta(seconds=5),
        now: datetime | None = None,
    ) -> TaskRun:
        return await self._uow.tasks.fail_or_retry(
            task_id,
            worker_id=worker_id,
            now=now or datetime.now(UTC),
            error_code=error_code,
            error_detail=error_detail,
            retry_delay=retry_delay,
        )
