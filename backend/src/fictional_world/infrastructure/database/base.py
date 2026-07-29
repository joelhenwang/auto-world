"""Declarative base with deterministic naming convention."""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from fictional_world.infrastructure.database.naming import NAMING_CONVENTION


class Base(DeclarativeBase):
    """ORM declarative base. Domain tables arrive in S0-DB-002."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
