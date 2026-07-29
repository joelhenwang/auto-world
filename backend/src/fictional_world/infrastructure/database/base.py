"""Declarative base with deterministic naming convention."""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from fictional_world.infrastructure.database.naming import NAMING_CONVENTION


class Base(DeclarativeBase):
    """ORM declarative base for worldsim schema tables."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION, schema="worldsim")
