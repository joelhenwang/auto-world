"""Observation ORM (handbook ``06`` §11.1)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from fictional_world.infrastructure.database.base import Base
from fictional_world.infrastructure.database.naming import WORLDSIM_SCHEMA


class ObservationRow(Base):
    __tablename__ = "observation"
    __table_args__ = (
        UniqueConstraint(
            "world_event_id",
            "observer_id",
            "observation_type",
            "content_hash",
        ),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="confidence_range"),
        Index("ix_observation_observer_event", "observer_id", "world_event_id"),
        Index("ix_observation_observer_created", "observer_id", "created_at"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=False,
    )
    observer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    observation_type: Mapped[str] = mapped_column(Text, nullable=False)
    perceived_summary: Mapped[str] = mapped_column(Text, nullable=False)
    perceived_facts: Mapped[object] = mapped_column(JSONB, nullable=False)
    omitted_fact_keys: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    visibility_reason: Mapped[str] = mapped_column(Text, nullable=False)
    source_sense_tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
