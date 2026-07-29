"""Entity and location ORM tables (handbook ``06`` §6)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from fictional_world.infrastructure.database.base import Base
from fictional_world.infrastructure.database.naming import WORLDSIM_SCHEMA


class EntityRow(Base):
    __tablename__ = "entity"
    __table_args__ = (
        Index("ix_entity_world_type_name", "world_id", "entity_type", "normalized_name"),
        Index("ix_entity_world_lifecycle", "world_id", "lifecycle_status"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(Text, nullable=False)
    created_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id", use_alter=True),
        nullable=True,
    )
    archived_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id", use_alter=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LocationRow(Base):
    __tablename__ = "location"
    __table_args__ = ({"schema": WORLDSIM_SCHEMA},)

    entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.entity.id"),
        primary_key=True,
    )
    parent_location_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.location.entity_id"),
        nullable=True,
    )
    location_type: Mapped[str] = mapped_column(Text, nullable=False)
    region_code: Mapped[str] = mapped_column(Text, nullable=False)
    coordinate_x: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    coordinate_y: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    elevation: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    owner_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.entity.id"),
        nullable=True,
    )
    environment_tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    canonical_description: Mapped[str] = mapped_column(Text, nullable=False)
    visual_profile_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
