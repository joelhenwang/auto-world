"""Observation / claim / belief ORM (handbook ``06`` §11)."""

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
    Numeric,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
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


class ClaimRow(Base):
    __tablename__ = "claim"
    __table_args__ = (
        CheckConstraint(
            "confidence_expressed IS NULL OR "
            "(confidence_expressed >= 0 AND confidence_expressed <= 1)",
            name="confidence_expressed_range",
        ),
        Index("ix_claim_world", "world_id"),
        Index("ix_claim_speaker", "speaker_id", "created_at"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    source_event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=False,
    )
    speaker_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    proposition_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposition_text: Mapped[str] = mapped_column(Text, nullable=False)
    truth_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'unknown'")
    )
    intent_class: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_expressed: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ClaimListenerRow(Base):
    __tablename__ = "claim_listener"
    __table_args__ = ({"schema": WORLDSIM_SCHEMA},)

    claim_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.claim.id"),
        primary_key=True,
    )
    listener_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        primary_key=True,
    )


class BeliefRow(Base):
    __tablename__ = "belief"
    __table_args__ = (
        UniqueConstraint("character_id", "proposition_key"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="confidence_range"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index("ix_belief_character", "character_id", "status"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    proposition_key: Mapped[str] = mapped_column(Text, nullable=False)
    belief_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'"))
    first_source_observation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.observation.id"),
        nullable=True,
    )
    last_source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    evidence_summary: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class BeliefEvidenceRow(Base):
    __tablename__ = "belief_evidence"
    __table_args__ = (
        UniqueConstraint("belief_id", "source_kind", "source_id"),
        CheckConstraint(
            "source_kind IN ('observation', 'claim', 'event')",
            name="source_kind",
        ),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    belief_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.belief.id"), nullable=False
    )
    source_kind: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    signed_weight: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SecretAccessRow(Base):
    __tablename__ = "secret_access"
    __table_args__ = (
        UniqueConstraint("world_id", "secret_key", "holder_character_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    secret_key: Mapped[str] = mapped_column(Text, nullable=False)
    owner_character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    holder_character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    access_level: Mapped[str] = mapped_column(Text, nullable=False)
    granted_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    revoked_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
