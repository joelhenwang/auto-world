"""World aggregate ORM tables (handbook ``06`` §5)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from fictional_world.infrastructure.database.base import Base
from fictional_world.infrastructure.database.naming import WORLDSIM_SCHEMA


class WorldRow(Base):
    __tablename__ = "world"
    __table_args__ = (
        CheckConstraint(
            "status IN ('initializing', 'active', 'paused', 'ended', 'archived')",
            name="status",
        ),
        CheckConstraint("current_event_sequence >= 0", name="event_sequence_nonneg"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        CheckConstraint(
            "(status = 'ended' AND ended_at IS NOT NULL) OR (status <> 'ended')",
            name="ended_status_consistency",
        ),
        Index(
            "uq_world_one_live",
            text("(true)"),
            unique=True,
            postgresql_where=text("status IN ('initializing', 'active', 'paused')"),
        ),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'en'"))
    content_rating: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'young_adult_soft_dark'")
    )
    current_event_sequence: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0")
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorldConfigRow(Base):
    __tablename__ = "world_config"
    __table_args__ = (
        UniqueConstraint("world_id", "config_version"),
        Index(
            "uq_world_config_one_active",
            "world_id",
            unique=True,
            postgresql_where=text("is_active"),
        ),
        CheckConstraint("config_version >= 1", name="config_version_positive"),
        CheckConstraint("max_days >= 1", name="max_days_positive"),
        CheckConstraint("max_generations BETWEEN 1 AND 3", name="max_generations_range"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"),
        nullable=False,
    )
    config_version: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    effective_from_phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    detailed_phase_names: Mapped[object] = mapped_column(JSONB, nullable=False)
    max_days: Mapped[int] = mapped_column(Integer, nullable=False)
    max_generations: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("3")
    )
    plot_armour_level: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    director_privileges: Mapped[object] = mapped_column(JSONB, nullable=False)
    image_budget_per_day: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    macro_simulation_policy: Mapped[object] = mapped_column(JSONB, nullable=False)
    content_policy_version: Mapped[str] = mapped_column(Text, nullable=False)
    created_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id", use_alter=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class WorldClockRow(Base):
    __tablename__ = "world_clock"
    __table_args__ = (
        CheckConstraint("generation_number BETWEEN 1 AND 3", name="generation_range"),
        CheckConstraint("month BETWEEN 1 AND 12", name="month_range"),
        CheckConstraint("day BETWEEN 1 AND 31", name="day_range"),
        CheckConstraint("phase_ordinal BETWEEN 0 AND 9", name="phase_ordinal_range"),
        CheckConstraint("absolute_day_index >= 0", name="absolute_day_nonneg"),
        CheckConstraint("absolute_phase_index >= 0", name="absolute_phase_nonneg"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        CheckConstraint(
            "resolution_mode IN ('detailed', 'day', 'week', 'month', 'year')",
            name="resolution_mode",
        ),
        CheckConstraint(
            "phase_name IN ("
            "'dawn','sunrise','morning','noon','afternoon',"
            "'sunset','dusk','evening','night','midnight'"
            ") OR resolution_mode <> 'detailed'",
            name="detailed_phase_name",
        ),
        {"schema": WORLDSIM_SCHEMA},
    )

    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"),
        primary_key=True,
    )
    generation_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    day: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    phase_name: Mapped[str] = mapped_column(Text, nullable=False)
    phase_ordinal: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    absolute_day_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    absolute_phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    resolution_mode: Mapped[str] = mapped_column(Text, nullable=False)
    last_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id", use_alter=True),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
