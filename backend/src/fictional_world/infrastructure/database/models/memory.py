"""Stage 0 recent_memory table (handbook ``06`` §12.1 subset).

Full long-term ``memory`` ORM lives in ``stage3.MemoryRow``.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from fictional_world.infrastructure.database.base import Base
from fictional_world.infrastructure.database.naming import WORLDSIM_SCHEMA


class RecentMemoryRow(Base):
    """Stage-0 memory surface; full ``memory`` table is ``MemoryRow`` in ``stage3``."""

    __tablename__ = "recent_memory"
    __table_args__ = (
        UniqueConstraint(
            "owner_character_id",
            "content_hash",
            "summary_version",
        ),
        CheckConstraint("salience >= 0 AND salience <= 1", name="salience_range"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="confidence_range"),
        CheckConstraint(
            "emotional_weight >= 0 AND emotional_weight <= 1", name="emotional_weight_range"
        ),
        CheckConstraint("decay_score >= 0 AND decay_score <= 1", name="decay_score_range"),
        CheckConstraint("recall_count >= 0", name="recall_count_nonneg"),
        CheckConstraint("summary_version >= 1", name="summary_version_positive"),
        Index("ix_recent_memory_owner_created", "owner_character_id", "created_at"),
        Index("ix_recent_memory_world_owner", "world_id", "owner_character_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"),
        nullable=False,
    )
    owner_character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    memory_type: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    salience: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    emotional_weight: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    visibility: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    last_recalled_phase_index: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    recall_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    decay_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    summary_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    source_observation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.observation.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
