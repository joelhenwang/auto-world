"""SQLAlchemy repository implementations for Stage 0 aggregates."""

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

__all__ = [
    "SqlAlchemyAggregateVersionRepository",
    "SqlAlchemyBudgetRepository",
    "SqlAlchemyCharacterRepository",
    "SqlAlchemyEventRepository",
    "SqlAlchemyObservationRepository",
    "SqlAlchemyOutboxRepository",
    "SqlAlchemyPhaseRepository",
    "SqlAlchemyPhaseSnapshotRepository",
    "SqlAlchemyRecentMemoryRepository",
    "SqlAlchemyTaskRepository",
    "SqlAlchemyWorldRepository",
]
