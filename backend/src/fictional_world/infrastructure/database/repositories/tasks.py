"""Task-run repository with SKIP LOCKED claim semantics (S0-ORCH-001, S4-ORCH-001)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from typing import Any, cast
from uuid import UUID

from sqlalchemy import and_, exists, not_, or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from fictional_world.domain.common.enums import TaskState
from fictional_world.domain.common.errors import InvalidStateTransition
from fictional_world.domain.tasks.task_run import TaskRun
from fictional_world.domain.tasks.transitions import LEASED_TASK_STATES, TERMINAL_TASK_STATES
from fictional_world.infrastructure.database.errors import OptimisticConcurrencyError
from fictional_world.infrastructure.database.mappings.records import task_to_record
from fictional_world.infrastructure.database.models import TaskDependencyRow, TaskRunRow


def _json_map(value: Mapping[str, object] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return cast(dict[str, Any], dict(value))


class SqlAlchemyTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, task_id: UUID) -> TaskRun | None:
        row = await self._session.get(TaskRunRow, task_id)
        return task_to_record(row) if row is not None else None

    async def find_by_idempotency_key(self, key: str) -> TaskRun | None:
        result = await self._session.execute(
            select(TaskRunRow).where(TaskRunRow.idempotency_key == key)
        )
        row = result.scalar_one_or_none()
        return task_to_record(row) if row is not None else None

    async def insert(self, task: TaskRun) -> TaskRun:
        row = TaskRunRow(
            id=task.id,
            task_type=task.task_type,
            world_id=task.world_id,
            phase_run_id=task.phase_run_id,
            scene_id=task.scene_id,
            subject_entity_id=task.subject_entity_id,
            state=str(task.state),
            priority=task.priority,
            payload=dict(task.payload),
            idempotency_key=task.idempotency_key,
            attempt_count=task.attempt_count,
            max_attempts=task.max_attempts,
            available_at=task.available_at,
            lease_owner=task.lease_owner,
            lease_expires_at=task.lease_expires_at,
            heartbeat_at=task.heartbeat_at,
            fencing_token=task.fencing_token,
            result_reference=_json_map(task.result_reference),
            error_code=task.error_code,
            error_detail=_json_map(task.error_detail),
            created_at=task.created_at,
            completed_at=task.completed_at,
        )
        self._session.add(row)
        await self._session.flush()
        return task_to_record(row)

    async def add_dependency(self, task_id: UUID, depends_on_task_id: UUID) -> None:
        if task_id == depends_on_task_id:
            raise InvalidStateTransition(
                entity="task_dependency",
                from_state=str(task_id),
                to_state=str(depends_on_task_id),
            )
        self._session.add(TaskDependencyRow(task_id=task_id, depends_on_task_id=depends_on_task_id))
        await self._session.flush()

    async def list_dependencies(self, task_id: UUID) -> Sequence[UUID]:
        result = await self._session.execute(
            select(TaskDependencyRow.depends_on_task_id).where(TaskDependencyRow.task_id == task_id)
        )
        return list(result.scalars().all())

    async def claim_available(
        self,
        *,
        worker_id: str,
        lease_duration: timedelta,
        now: datetime,
        limit: int = 1,
    ) -> Sequence[TaskRun]:
        dep = aliased(TaskRunRow)
        unmet_dependency = exists(
            select(1)
            .select_from(TaskDependencyRow)
            .join(dep, TaskDependencyRow.depends_on_task_id == dep.id)
            .where(
                TaskDependencyRow.task_id == TaskRunRow.id,
                dep.state != TaskState.SUCCEEDED.value,
            )
        )
        claimable = (
            select(TaskRunRow)
            .where(
                TaskRunRow.available_at <= now,
                TaskRunRow.state.notin_([s.value for s in TERMINAL_TASK_STATES]),
                not_(unmet_dependency),
                or_(
                    and_(
                        TaskRunRow.state == TaskState.PENDING.value,
                        or_(
                            TaskRunRow.lease_expires_at.is_(None),
                            TaskRunRow.lease_expires_at <= now,
                        ),
                    ),
                    and_(
                        TaskRunRow.state.in_([s.value for s in LEASED_TASK_STATES]),
                        TaskRunRow.lease_expires_at.is_not(None),
                        TaskRunRow.lease_expires_at <= now,
                    ),
                ),
            )
            .order_by(TaskRunRow.priority.desc(), TaskRunRow.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(claimable)
        rows = list(result.scalars().all())
        if not rows:
            return []

        claimed: list[TaskRun] = []
        for row in rows:
            previous_state = TaskState(row.state)
            if previous_state == TaskState.PENDING:
                row.attempt_count = int(row.attempt_count) + 1
            row.state = TaskState.CLAIMED.value
            row.lease_owner = worker_id
            row.lease_expires_at = now + lease_duration
            row.heartbeat_at = now
            row.fencing_token = int(row.fencing_token) + 1
            claimed.append(task_to_record(row))
        await self._session.flush()
        return claimed

    async def heartbeat(
        self,
        task_id: UUID,
        *,
        worker_id: str,
        lease_duration: timedelta,
        now: datetime,
        fencing_token: int | None = None,
    ) -> TaskRun:
        row = await self._require_lease(task_id, worker_id=worker_id, fencing_token=fencing_token)
        row.heartbeat_at = now
        row.lease_expires_at = now + lease_duration
        await self._session.flush()
        return task_to_record(row)

    async def mark_running(
        self,
        task_id: UUID,
        *,
        worker_id: str,
        now: datetime,
        fencing_token: int | None = None,
    ) -> TaskRun:
        row = await self._require_lease(task_id, worker_id=worker_id, fencing_token=fencing_token)
        if TaskState(row.state) not in LEASED_TASK_STATES:
            raise InvalidStateTransition(
                entity="task_run",
                from_state=row.state,
                to_state=TaskState.RUNNING.value,
            )
        row.state = TaskState.RUNNING.value
        row.heartbeat_at = now
        await self._session.flush()
        return task_to_record(row)

    async def complete_success(
        self,
        task_id: UUID,
        *,
        worker_id: str,
        now: datetime,
        result_reference: Mapping[str, object] | None = None,
        fencing_token: int | None = None,
    ) -> TaskRun:
        row = await self._require_lease(task_id, worker_id=worker_id, fencing_token=fencing_token)
        row.state = TaskState.SUCCEEDED.value
        row.result_reference = _json_map(result_reference)
        row.lease_owner = None
        row.lease_expires_at = None
        row.heartbeat_at = now
        row.completed_at = now
        row.error_code = None
        row.error_detail = None
        await self._session.flush()
        return task_to_record(row)

    async def fail_or_retry(
        self,
        task_id: UUID,
        *,
        worker_id: str,
        now: datetime,
        error_code: str,
        error_detail: Mapping[str, object] | None,
        retry_delay: timedelta,
        fencing_token: int | None = None,
    ) -> TaskRun:
        row = await self._require_lease(task_id, worker_id=worker_id, fencing_token=fencing_token)
        row.error_code = error_code
        row.error_detail = _json_map(error_detail)
        row.lease_owner = None
        row.lease_expires_at = None
        row.heartbeat_at = now
        if int(row.attempt_count) >= int(row.max_attempts):
            row.state = TaskState.DEAD_LETTER.value
            row.completed_at = now
        else:
            row.state = TaskState.PENDING.value
            row.available_at = now + retry_delay
            row.completed_at = None
        await self._session.flush()
        return task_to_record(row)

    async def cancel(self, task_id: UUID, *, now: datetime) -> TaskRun:
        row = await self._session.get(TaskRunRow, task_id, with_for_update=True)
        if row is None:
            raise OptimisticConcurrencyError(
                entity="task_run",
                entity_id=str(task_id),
                expected_version=-1,
            )
        if TaskState(row.state) in TERMINAL_TASK_STATES:
            raise InvalidStateTransition(
                entity="task_run",
                from_state=row.state,
                to_state=TaskState.CANCELLED.value,
            )
        row.state = TaskState.CANCELLED.value
        row.lease_owner = None
        row.lease_expires_at = None
        row.completed_at = now
        await self._session.flush()
        return task_to_record(row)

    async def list_failures_for_world(
        self,
        world_id: UUID,
        *,
        limit: int = 50,
    ) -> Sequence[TaskRun]:
        result = await self._session.execute(
            select(TaskRunRow)
            .where(
                TaskRunRow.world_id == world_id,
                TaskRunRow.state.in_(
                    [
                        TaskState.FAILED.value,
                        TaskState.DEAD_LETTER.value,
                    ]
                ),
            )
            .order_by(TaskRunRow.created_at.desc())
            .limit(limit)
        )
        return [task_to_record(row) for row in result.scalars().all()]

    async def reset_abandoned_leases(
        self,
        *,
        worker_keys: Sequence[str],
        now: datetime,
    ) -> int:
        """Reset tasks claimed by lost workers back to PENDING for re-queuing.

        Returns the number of tasks reset.
        """
        if not worker_keys:
            return 0
        stmt = (
            update(TaskRunRow)
            .where(
                TaskRunRow.lease_owner.in_(worker_keys),
                TaskRunRow.state.in_([s.value for s in LEASED_TASK_STATES]),
            )
            .values(
                state=TaskState.PENDING.value,
                lease_owner=None,
                lease_expires_at=None,
                available_at=now,
            )
            .execution_options(synchronize_session="fetch")
        )
        cursor: CursorResult[tuple[()]] = await self._session.execute(stmt)  # type: ignore[assignment]
        await self._session.flush()
        return int(cursor.rowcount)

    async def _require_lease(
        self,
        task_id: UUID,
        *,
        worker_id: str,
        fencing_token: int | None = None,
    ) -> TaskRunRow:
        """Load a task row under FOR UPDATE and verify the caller still owns the lease.

        When *fencing_token* is provided it must match the value stored in the row;
        this rejects stale workers whose lease was superseded by a fresh claim.
        """
        row = await self._session.get(TaskRunRow, task_id, with_for_update=True)
        if row is None:
            raise OptimisticConcurrencyError(
                entity="task_run",
                entity_id=str(task_id),
                expected_version=-1,
            )
        if TaskState(row.state) in TERMINAL_TASK_STATES:
            raise InvalidStateTransition(
                entity="task_run",
                from_state=row.state,
                to_state="lease_mutation",
            )
        if row.lease_owner != worker_id:
            raise OptimisticConcurrencyError(
                entity="task_run",
                entity_id=str(task_id),
                expected_version=-1,
            )
        if fencing_token is not None and int(row.fencing_token) != fencing_token:
            raise OptimisticConcurrencyError(
                entity="task_run",
                entity_id=str(task_id),
                expected_version=fencing_token,
            )
        return row
