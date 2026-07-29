"""SQLAlchemy repository for durable player/user command attempts."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fictional_world.domain.tasks.user_command import UserCommandRecord
from fictional_world.infrastructure.database.models.orchestration import UserCommandRow


def _to_record(row: UserCommandRow) -> UserCommandRecord:
    payload: dict[object, object] = (
        cast(dict[object, object], row.payload) if isinstance(row.payload, dict) else {}
    )
    return UserCommandRecord(
        id=row.id,
        world_id=row.world_id,
        actor_role=row.actor_role,
        command_type=row.command_type,
        payload={str(key): value for key, value in payload.items()},
        target_entity_id=row.target_entity_id,
        requested_phase_boundary=row.requested_phase_boundary,
        idempotency_key=row.idempotency_key,
        permission_decision=row.permission_decision,
        status=row.status,
        resulting_event_id=row.resulting_event_id,
        resulting_task_id=row.resulting_task_id,
        created_at=row.created_at,
        decided_at=row.decided_at,
        completed_at=row.completed_at,
    )


class SqlAlchemyUserCommandRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, command_id: UUID) -> UserCommandRecord | None:
        row = await self._session.get(UserCommandRow, command_id)
        return None if row is None else _to_record(row)

    async def find_by_idempotency_key(self, key: str) -> UserCommandRecord | None:
        result = await self._session.execute(
            select(UserCommandRow).where(UserCommandRow.idempotency_key == key)
        )
        row = result.scalar_one_or_none()
        return None if row is None else _to_record(row)

    async def list_pending_for_world(
        self,
        world_id: UUID,
        *,
        limit: int = 100,
    ) -> Sequence[UserCommandRecord]:
        result = await self._session.execute(
            select(UserCommandRow)
            .where(
                UserCommandRow.world_id == world_id,
                UserCommandRow.status == "pending",
            )
            .order_by(UserCommandRow.created_at.asc())
            .limit(limit)
        )
        return [_to_record(row) for row in result.scalars().all()]

    async def insert(self, command: UserCommandRecord) -> UserCommandRecord:
        row = UserCommandRow(
            id=command.id,
            world_id=command.world_id,
            actor_role=command.actor_role,
            command_type=command.command_type,
            payload=dict(command.payload),
            target_entity_id=command.target_entity_id,
            requested_phase_boundary=command.requested_phase_boundary,
            idempotency_key=command.idempotency_key,
            permission_decision=command.permission_decision,
            status=command.status,
            resulting_event_id=command.resulting_event_id,
            resulting_task_id=command.resulting_task_id,
            decided_at=command.decided_at,
            completed_at=command.completed_at,
        )
        self._session.add(row)
        await self._session.flush()
        return _to_record(row)


__all__ = ["SqlAlchemyUserCommandRepository"]
