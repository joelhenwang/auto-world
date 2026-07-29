"""Character ORM tables (handbook ``06`` §7)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
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


class CharacterRow(Base):
    __tablename__ = "character"
    __table_args__ = (
        CheckConstraint(
            "character_kind IN ('focus', 'lineage', 'temporary_npc', 'recurring_npc')",
            name="character_kind",
        ),
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.entity.id"),
        primary_key=True,
    )
    character_kind: Mapped[str] = mapped_column(Text, nullable=False)
    birth_event_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    death_event_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    birth_phase_index: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    death_phase_index: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    biological_age_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    species_code: Mapped[str] = mapped_column(Text, nullable=False)
    sex_or_body_profile: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_card_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character_card_version.id", use_alter=True),
        nullable=True,
    )
    npc_persistence_until_day: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class CharacterCardVersionRow(Base):
    __tablename__ = "character_card_version"
    __table_args__ = (
        UniqueConstraint("character_id", "version_number"),
        UniqueConstraint("character_id", "content_hash"),
        CheckConstraint("version_number >= 1", name="version_number_positive"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    identity: Mapped[object] = mapped_column(JSONB, nullable=False)
    backstory: Mapped[str] = mapped_column(Text, nullable=False)
    appearance: Mapped[object] = mapped_column(JSONB, nullable=False)
    personality_traits: Mapped[object] = mapped_column(JSONB, nullable=False)
    values: Mapped[object] = mapped_column(JSONB, nullable=False)
    fears: Mapped[object] = mapped_column(JSONB, nullable=False)
    desires: Mapped[object] = mapped_column(JSONB, nullable=False)
    boundaries: Mapped[object] = mapped_column(JSONB, nullable=False)
    voice_profile: Mapped[object] = mapped_column(JSONB, nullable=False)
    initial_capabilities: Mapped[object] = mapped_column(JSONB, nullable=False)
    secret_manifest: Mapped[object] = mapped_column(JSONB, nullable=False)
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CharacterStateRow(Base):
    __tablename__ = "character_state"
    __table_args__ = (
        CheckConstraint("stamina BETWEEN 0 AND 100", name="stamina_range"),
        CheckConstraint("mana BETWEEN 0 AND 100", name="mana_range"),
        CheckConstraint("energy BETWEEN 0 AND 100", name="energy_range"),
        CheckConstraint("hunger BETWEEN 0 AND 100", name="hunger_range"),
        CheckConstraint("pain BETWEEN 0 AND 100", name="pain_range"),
        CheckConstraint("stress BETWEEN 0 AND 100", name="stress_range"),
        CheckConstraint("social_need BETWEEN 0 AND 100", name="social_need_range"),
        CheckConstraint("valence BETWEEN -1 AND 1", name="valence_range"),
        CheckConstraint("arousal BETWEEN 0 AND 1", name="arousal_range"),
        CheckConstraint("dominance BETWEEN -1 AND 1", name="dominance_range"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        primary_key=True,
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.location.entity_id"),
        nullable=True,
    )
    life_status: Mapped[str] = mapped_column(Text, nullable=False)
    stamina: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    mana: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    energy: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    hunger: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    pain: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    stress: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    social_need: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    valence: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    arousal: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    dominance: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    active_activity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    current_card_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character_card_version.id"),
        nullable=False,
    )
    last_source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
