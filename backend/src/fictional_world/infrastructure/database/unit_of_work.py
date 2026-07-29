"""SQLAlchemy unit of work (transaction owner)."""

from __future__ import annotations

from types import TracebackType
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fictional_world.infrastructure.database.repositories.budgets import (
    SqlAlchemyBudgetRepository,
)
from fictional_world.infrastructure.database.repositories.characters import (
    SqlAlchemyCharacterRepository,
)
from fictional_world.infrastructure.database.repositories.events import SqlAlchemyEventRepository
from fictional_world.infrastructure.database.repositories.phases import SqlAlchemyPhaseRepository
from fictional_world.infrastructure.database.repositories.snapshots import (
    SqlAlchemyPhaseSnapshotRepository,
)
from fictional_world.infrastructure.database.repositories.support import (
    SqlAlchemyAggregateVersionRepository,
    SqlAlchemyObservationRepository,
    SqlAlchemyOutboxRepository,
    SqlAlchemyRecentMemoryRepository,
)
from fictional_world.infrastructure.database.repositories.tasks import SqlAlchemyTaskRepository
from fictional_world.infrastructure.database.repositories.worlds import SqlAlchemyWorldRepository


class SqlAlchemyUnitOfWork:
    """One AsyncSession-scoped unit of work. Call ``commit`` explicitly on success."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self.session: AsyncSession | None = None
        self.worlds = cast(SqlAlchemyWorldRepository, None)
        self.characters = cast(SqlAlchemyCharacterRepository, None)
        self.phases = cast(SqlAlchemyPhaseRepository, None)
        self.snapshots = cast(SqlAlchemyPhaseSnapshotRepository, None)
        self.events = cast(SqlAlchemyEventRepository, None)
        self.observations = cast(SqlAlchemyObservationRepository, None)
        self.recent_memories = cast(SqlAlchemyRecentMemoryRepository, None)
        self.aggregate_versions = cast(SqlAlchemyAggregateVersionRepository, None)
        self.outbox = cast(SqlAlchemyOutboxRepository, None)
        self.tasks = cast(SqlAlchemyTaskRepository, None)
        self.budgets = cast(SqlAlchemyBudgetRepository, None)

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self.session = self._session_factory()
        self.worlds = SqlAlchemyWorldRepository(self.session)
        self.characters = SqlAlchemyCharacterRepository(self.session)
        self.phases = SqlAlchemyPhaseRepository(self.session)
        self.snapshots = SqlAlchemyPhaseSnapshotRepository(self.session)
        self.events = SqlAlchemyEventRepository(self.session)
        self.observations = SqlAlchemyObservationRepository(self.session)
        self.recent_memories = SqlAlchemyRecentMemoryRepository(self.session)
        self.aggregate_versions = SqlAlchemyAggregateVersionRepository(self.session)
        self.outbox = SqlAlchemyOutboxRepository(self.session)
        self.tasks = SqlAlchemyTaskRepository(self.session)
        self.budgets = SqlAlchemyBudgetRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self.session is None:
            return
        try:
            if exc_type is not None:
                await self.session.rollback()
        finally:
            await self.session.close()
            self.session = None

    async def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("unit of work is not active")
        await self.session.commit()

    async def rollback(self) -> None:
        if self.session is None:
            raise RuntimeError("unit of work is not active")
        await self.session.rollback()
