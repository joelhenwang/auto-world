"""SQLAlchemy repository implementations for Stage 0 aggregates."""

from fictional_world.infrastructure.database.repositories.characters import (
    SqlAlchemyCharacterRepository,
)
from fictional_world.infrastructure.database.repositories.events import SqlAlchemyEventRepository
from fictional_world.infrastructure.database.repositories.phases import SqlAlchemyPhaseRepository
from fictional_world.infrastructure.database.repositories.support import (
    SqlAlchemyAggregateVersionRepository,
    SqlAlchemyObservationRepository,
    SqlAlchemyOutboxRepository,
    SqlAlchemyRecentMemoryRepository,
)
from fictional_world.infrastructure.database.repositories.worlds import SqlAlchemyWorldRepository

__all__ = [
    "SqlAlchemyAggregateVersionRepository",
    "SqlAlchemyCharacterRepository",
    "SqlAlchemyEventRepository",
    "SqlAlchemyObservationRepository",
    "SqlAlchemyOutboxRepository",
    "SqlAlchemyPhaseRepository",
    "SqlAlchemyRecentMemoryRepository",
    "SqlAlchemyWorldRepository",
]
