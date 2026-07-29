"""Database infrastructure package (S0-DB-001 baseline)."""

from fictional_world.infrastructure.database.base import Base
from fictional_world.infrastructure.database.naming import NAMING_CONVENTION, WORLDSIM_SCHEMA
from fictional_world.infrastructure.database.session import (
    create_engine,
    create_session_factory,
    database_url,
    session_scope,
)

__all__ = [
    "NAMING_CONVENTION",
    "WORLDSIM_SCHEMA",
    "Base",
    "create_engine",
    "create_session_factory",
    "database_url",
    "session_scope",
]
