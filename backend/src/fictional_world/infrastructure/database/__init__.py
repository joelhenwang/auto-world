"""Database infrastructure package (S0-DB-001 baseline + S0-DB-002 models + S0-DB-003 UoW)."""

# Ensure ORM tables are registered when the package is imported.
from fictional_world.infrastructure.database import models as models
from fictional_world.infrastructure.database.base import Base
from fictional_world.infrastructure.database.naming import NAMING_CONVENTION, WORLDSIM_SCHEMA
from fictional_world.infrastructure.database.session import (
    create_engine,
    create_session_factory,
    database_url,
    session_scope,
)
from fictional_world.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

__all__ = [
    "NAMING_CONVENTION",
    "WORLDSIM_SCHEMA",
    "Base",
    "SqlAlchemyUnitOfWork",
    "create_engine",
    "create_session_factory",
    "database_url",
    "models",
    "session_scope",
]
