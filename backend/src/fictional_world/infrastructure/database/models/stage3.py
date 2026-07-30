"""Stage 3 long-term memory / rules / world ORM tables."""

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
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
    types,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from fictional_world.infrastructure.database.base import Base
from fictional_world.infrastructure.database.naming import WORLDSIM_SCHEMA


class Vector(types.UserDefinedType[object]):
    """pgvector column type without requiring the pgvector Python package."""

    cache_ok = True

    def __init__(self, dim: int) -> None:
        self.dim = dim

    def get_col_spec(self, **_kwargs: object) -> str:
        return f"vector({self.dim})"


class MemoryRow(Base):
    __tablename__ = "memory"
    __table_args__ = (
        UniqueConstraint("owner_character_id", "content_hash", "summary_version"),
        CheckConstraint("salience >= 0 AND salience <= 1", name="salience_range"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="confidence_range"),
        CheckConstraint(
            "emotional_weight >= 0 AND emotional_weight <= 1", name="emotional_weight_range"
        ),
        CheckConstraint("decay_score >= 0 AND decay_score <= 1", name="decay_score_range"),
        CheckConstraint("recall_count >= 0", name="recall_count_nonneg"),
        CheckConstraint("summary_version >= 1", name="summary_version_positive"),
        CheckConstraint("occurred_phase_index >= 0", name="occurred_phase_nonneg"),
        CheckConstraint("created_phase_index >= 0", name="created_phase_nonneg"),
        Index("ix_memory_owner_created", "world_id", "owner_character_id", "created_phase_index"),
        Index(
            "ix_memory_owner_visibility",
            "world_id",
            "owner_character_id",
            "visibility",
            "status",
        ),
        Index("ix_memory_owner_type", "owner_character_id", "memory_type", "status"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
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
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'"))
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    summary_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    goal_relevance: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    emotional_resonance: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    unresolved_commitment: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    referenced_entity_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(Uuid(as_uuid=True)), nullable=False, server_default=text("'{}'::uuid[]")
    )
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class MemorySourceRow(Base):
    __tablename__ = "memory_source"
    __table_args__ = (
        UniqueConstraint("memory_id", "source_kind", "source_id"),
        CheckConstraint("weight >= 0 AND weight <= 1", name="weight_range"),
        CheckConstraint("ordinal >= 0", name="ordinal_nonneg"),
        Index("ix_memory_source_memory", "memory_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    memory_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.memory.id"), nullable=False
    )
    source_kind: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    source_role: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'primary'"))
    weight: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("1.0000")
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))


class EmbeddingModelVersionRow(Base):
    __tablename__ = "embedding_model_version"
    __table_args__ = (
        UniqueConstraint("model_key", "embedding_version"),
        CheckConstraint("dimension > 0", name="dimension_positive"),
        CheckConstraint("embedding_version >= 1", name="embedding_version_positive"),
        Index(
            "uq_embedding_model_version_active",
            "model_key",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    model_key: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    model_slug: Mapped[str] = mapped_column(Text, nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    query_prefix: Mapped[str] = mapped_column(Text, nullable=False)
    passage_prefix: Mapped[str] = mapped_column(Text, nullable=False)
    truncation_policy: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'truncate_tail'")
    )
    embedding_version: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    capability_probe: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class MemoryEmbeddingRow(Base):
    __tablename__ = "memory_embedding"
    __table_args__ = (
        UniqueConstraint(
            "memory_id",
            "embedding_model_key",
            "embedding_version",
            "embedded_content_hash",
        ),
        CheckConstraint("dimension > 0", name="dimension_positive"),
        CheckConstraint("embedding_version >= 1", name="embedding_version_positive"),
        CheckConstraint("prefix_type IN ('query', 'passage')", name="prefix_type"),
        Index("ix_memory_embedding_memory_active", "memory_id", "is_active"),
        Index(
            "ix_memory_embedding_owner_active",
            "world_id",
            "owner_character_id",
            "is_active",
            "embedding_model_key",
            "embedding_version",
        ),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    memory_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.memory.id"), nullable=False
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    owner_character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    embedding_model_key: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_version: Mapped[int] = mapped_column(Integer, nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    prefix_type: Mapped[str] = mapped_column(Text, nullable=False)
    embedded_content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[object] = mapped_column(Vector(2048), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EmbeddingJobRow(Base):
    __tablename__ = "embedding_job"
    __table_args__ = (
        UniqueConstraint("idempotency_key"),
        CheckConstraint("attempt_count >= 0", name="attempt_count_nonneg"),
        CheckConstraint("embedding_version >= 1", name="embedding_version_positive"),
        Index("ix_embedding_job_status", "world_id", "status", "created_at"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    memory_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.memory.id"), nullable=False
    )
    embedding_model_key: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pending'"))
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RetrievalTraceRow(Base):
    __tablename__ = "retrieval_trace"
    __table_args__ = (
        CheckConstraint("request_phase_index >= 0", name="request_phase_nonneg"),
        Index(
            "ix_retrieval_trace_owner_phase",
            "world_id",
            "owner_character_id",
            "request_phase_index",
        ),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    owner_character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    request_phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    filters: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    candidate_memory_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(Uuid(as_uuid=True)), nullable=False, server_default=text("'{}'::uuid[]")
    )
    selected_memory_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(Uuid(as_uuid=True)), nullable=False, server_default=text("'{}'::uuid[]")
    )
    scores: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    embedding_model_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_semantic: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    reranker_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'skipped'")
    )
    model_call_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.model_call.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class MonthlyChapterRow(Base):
    __tablename__ = "monthly_chapter"
    __table_args__ = (
        UniqueConstraint("world_id", "owner_character_id", "month_index", "version_number"),
        CheckConstraint("month_index >= 1", name="month_index_positive"),
        CheckConstraint("end_phase_index >= start_phase_index", name="phase_range"),
        CheckConstraint("version_number >= 1", name="version_number_positive"),
        Index("ix_monthly_chapter_owner", "world_id", "owner_character_id", "month_index"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    owner_character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    month_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    end_phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_extract: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    model_call_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.model_call.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ReflectionRunRow(Base):
    __tablename__ = "reflection_run"
    __table_args__ = (
        UniqueConstraint("idempotency_key"),
        CheckConstraint("month_index >= 1", name="month_index_positive"),
        Index("ix_reflection_run_owner_month", "world_id", "owner_character_id", "month_index"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    owner_character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    month_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pending'"))
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_trait_changes: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    accepted_trait_changes: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    rejected_trait_changes: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    evidence_refs: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    monthly_chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.monthly_chapter.id"),
        nullable=True,
    )
    model_call_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.model_call.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CharacterTraitVersionRow(Base):
    __tablename__ = "character_trait_version"
    __table_args__ = (
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index("ix_character_trait_version_char", "character_id", "trait_key", "version"),
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
    trait_key: Mapped[str] = mapped_column(Text, nullable=False)
    value_before: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    value_after: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    evidence_refs: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    reflection_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.reflection_run.id"),
        nullable=True,
    )
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class StatStateRow(Base):
    __tablename__ = "stat_state"
    __table_args__ = (
        CheckConstraint("current_value >= 0 AND current_value <= 100", name="current_value_range"),
        CheckConstraint(
            "dynamic_potential_cap >= 0 AND dynamic_potential_cap <= 100",
            name="potential_cap_range",
        ),
        CheckConstraint("growth_rate >= 0 AND growth_rate <= 1", name="growth_rate_range"),
        CheckConstraint("adaptability >= 0 AND adaptability <= 1", name="adaptability_range"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index("ix_stat_state_world", "world_id", "character_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        primary_key=True,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    stat_code: Mapped[str] = mapped_column(Text, primary_key=True)
    current_value: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    dynamic_potential_cap: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    growth_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    adaptability: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    last_source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class StatPotentialRow(Base):
    __tablename__ = "stat_potential"
    __table_args__ = (
        UniqueConstraint("character_id", "stat_code"),
        CheckConstraint(
            "base_potential >= 0 AND base_potential <= 100", name="base_potential_range"
        ),
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    stat_code: Mapped[str] = mapped_column(Text, nullable=False)
    base_potential: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    species_modifier: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), nullable=False, server_default=text("0.0000")
    )
    age_modifier: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), nullable=False, server_default=text("0.0000")
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class SkillDefinitionRow(Base):
    __tablename__ = "skill_definition"
    __table_args__ = (
        UniqueConstraint("world_id", "skill_code"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    skill_code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    governing_stats: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    prerequisites: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'"))
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class SkillStateRow(Base):
    __tablename__ = "skill_state"
    __table_args__ = (
        CheckConstraint("proficiency >= 0 AND proficiency <= 100", name="proficiency_range"),
        CheckConstraint("evidence_total >= 0", name="evidence_total_nonneg"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        primary_key=True,
    )
    skill_definition_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.skill_definition.id"),
        primary_key=True,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    proficiency: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), nullable=False, server_default=text("0.0000")
    )
    evidence_total: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), nullable=False, server_default=text("0.0000")
    )
    plateau_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    teacher_character_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=True,
    )
    last_source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SkillProgressEvidenceRow(Base):
    __tablename__ = "skill_progress_evidence"
    __table_args__ = (
        CheckConstraint("evidence_weight >= 0", name="evidence_weight_nonneg"),
        CheckConstraint("difficulty >= 0 AND difficulty <= 1", name="difficulty_range"),
        CheckConstraint(
            "practice_quality >= 0 AND practice_quality <= 1", name="practice_quality_range"
        ),
        Index("ix_skill_progress_evidence_char_skill", "character_id", "skill_definition_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    skill_definition_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.skill_definition.id"),
        nullable=False,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    source_event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=False,
    )
    evidence_weight: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    difficulty: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.5000")
    )
    practice_quality: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.5000")
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SpellDefinitionRow(Base):
    __tablename__ = "spell_definition"
    __table_args__ = (
        UniqueConstraint("world_id", "spell_code"),
        CheckConstraint("mana_cost_min >= 0", name="mana_cost_min_nonneg"),
        CheckConstraint("mana_cost_max >= mana_cost_min", name="mana_cost_range"),
        CheckConstraint("cast_time_beats >= 0", name="cast_time_nonneg"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    spell_code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    school: Mapped[str] = mapped_column(Text, nullable=False)
    elements: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    prerequisites: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    mana_cost_min: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    mana_cost_max: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    cast_time_beats: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    range_desc: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'touch'"))
    target_rules: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    possible_effects: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    failure_modes: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    counters: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    visibility: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'public'"))
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'"))
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class KnownSpellRow(Base):
    __tablename__ = "known_spell"
    __table_args__ = (
        CheckConstraint("proficiency >= 0 AND proficiency <= 100", name="proficiency_range"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        primary_key=True,
    )
    spell_definition_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.spell_definition.id"),
        primary_key=True,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    proficiency: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), nullable=False, server_default=text("0.0000")
    )
    discovery_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class MagicAffinityRow(Base):
    __tablename__ = "magic_affinity"
    __table_args__ = (
        CheckConstraint("affinity >= 0 AND affinity <= 1", name="affinity_range"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        primary_key=True,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    element: Mapped[str] = mapped_column(Text, primary_key=True)
    affinity: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class ItemRow(Base):
    __tablename__ = "item"
    __table_args__ = (
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index("ix_item_world_code", "world_id", "item_code"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    item_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.entity.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    item_kind: Mapped[str] = mapped_column(Text, nullable=False)
    stackable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    properties: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'"))
    created_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class InventoryEntryRow(Base):
    __tablename__ = "inventory_entry"
    __table_args__ = (
        UniqueConstraint("owner_character_id", "item_id"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    owner_character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.item.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    equipped_slot: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class EquipmentStateRow(Base):
    __tablename__ = "equipment_state"
    __table_args__ = (
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        primary_key=True,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    slot: Mapped[str] = mapped_column(Text, primary_key=True)
    inventory_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.inventory_entry.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ConditionRow(Base):
    __tablename__ = "condition"
    __table_args__ = (
        CheckConstraint("severity >= 0 AND severity <= 1", name="severity_range"),
        CheckConstraint("started_phase_index >= 0", name="started_phase_nonneg"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index("ix_condition_char_status", "character_id", "status"),
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
    condition_code: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'"))
    started_phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    expected_end_phase_index: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    modifiers: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    removed_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class InjuryRow(Base):
    __tablename__ = "injury"
    __table_args__ = (
        CheckConstraint("severity >= 0 AND severity <= 1", name="severity_range"),
        CheckConstraint("bleeding >= 0 AND bleeding <= 1", name="bleeding_range"),
        CheckConstraint("pain >= 0 AND pain <= 1", name="pain_range"),
        CheckConstraint("mobility_penalty >= 0 AND mobility_penalty <= 1", name="mobility_range"),
        CheckConstraint(
            "consciousness_impact >= 0 AND consciousness_impact <= 1",
            name="consciousness_range",
        ),
        CheckConstraint("infection_risk >= 0 AND infection_risk <= 1", name="infection_range"),
        CheckConstraint("healing_progress >= 0 AND healing_progress <= 1", name="healing_range"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index("ix_injury_char_status", "character_id", "status"),
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
    body_region: Mapped[str] = mapped_column(Text, nullable=False)
    injury_type: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    bleeding: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    pain: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    mobility_penalty: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    consciousness_impact: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    infection_risk: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    healing_progress: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    treatment: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    permanent_consequence: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'"))
    inflicted_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    healed_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RecoveryPlanRow(Base):
    __tablename__ = "recovery_plan"
    __table_args__ = (
        CheckConstraint("version >= 0", name="version_nonneg"),
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
    injury_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.injury.id"), nullable=True
    )
    condition_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.condition.id"), nullable=True
    )
    plan_status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'"))
    steps: Mapped[object] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    expected_end_phase_index: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class FactionRow(Base):
    __tablename__ = "faction"
    __table_args__ = (
        UniqueConstraint("world_id", "faction_key"),
        CheckConstraint(
            "plot_armour_bias >= -1 AND plot_armour_bias <= 1", name="plot_armour_range"
        ),
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    faction_key: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    faction_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'"))
    leadership: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    territory_location_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(Uuid(as_uuid=True)), nullable=False, server_default=text("'{}'::uuid[]")
    )
    goals: Mapped[object] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    resources: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    plans: Mapped[object] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    plot_armour_bias: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    created_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class FactionMembershipRow(Base):
    __tablename__ = "faction_membership"
    __table_args__ = (
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    faction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.faction.id"),
        primary_key=True,
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        primary_key=True,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'member'"))
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'"))
    joined_phase_index: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class FactionRelationRow(Base):
    __tablename__ = "faction_relation"
    __table_args__ = (
        CheckConstraint("trust >= -1 AND trust <= 1", name="trust_range"),
        CheckConstraint("hostility >= 0 AND hostility <= 1", name="hostility_range"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        CheckConstraint("source_faction_id <> target_faction_id", name="no_self_relation"),
        {"schema": WORLDSIM_SCHEMA},
    )

    source_faction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.faction.id"),
        primary_key=True,
    )
    target_faction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.faction.id"),
        primary_key=True,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    stance: Mapped[str] = mapped_column(Text, nullable=False)
    trust: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    hostility: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    last_source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class FactionStateRow(Base):
    __tablename__ = "faction_state"
    __table_args__ = (
        UniqueConstraint("faction_id", "day_index", "version"),
        CheckConstraint("day_index >= 0", name="day_index_nonneg"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    faction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.faction.id"),
        primary_key=True,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    day_index: Mapped[int] = mapped_column(Integer, primary_key=True)
    indicators: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, primary_key=True, server_default=text("0"))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SettlementIndicatorRow(Base):
    __tablename__ = "settlement_indicator"
    __table_args__ = (
        UniqueConstraint("location_id", "indicator_key", "day_index", "version"),
        CheckConstraint("day_index >= 0", name="day_index_nonneg"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index("ix_settlement_indicator_loc_day", "location_id", "day_index"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.location.entity_id"),
        nullable=False,
    )
    indicator_key: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    day_index: Mapped[int] = mapped_column(Integer, nullable=False)
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ArcRow(Base):
    __tablename__ = "arc"
    __table_args__ = (
        UniqueConstraint("world_id", "arc_key"),
        CheckConstraint("progress >= 0 AND progress <= 1", name="progress_range"),
        CheckConstraint(
            "status IN ('active', 'dormant', 'resolved', 'failed', 'abandoned')",
            name="status",
        ),
        CheckConstraint("arc_scope IN ('major', 'secondary')", name="arc_scope"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index("ix_arc_world_status", "world_id", "status", "arc_scope"),
        Index(
            "uq_arc_one_active_major",
            "world_id",
            unique=True,
            postgresql_where=text("status = 'active' AND arc_scope = 'major'"),
        ),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    arc_key: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    arc_scope: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'major'"))
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'dormant'"))
    premise: Mapped[str] = mapped_column(Text, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    milestones: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    prerequisites: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    closure_conditions: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    participant_entity_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(Uuid(as_uuid=True)), nullable=False, server_default=text("'{}'::uuid[]")
    )
    dominant_genres: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    progress: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    deadline_phase_index: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    start_phase_index: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    end_phase_index: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    director_profile_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TropeUsageRow(Base):
    __tablename__ = "trope_usage"
    __table_args__ = (
        CheckConstraint("phase_index >= 0", name="phase_index_nonneg"),
        CheckConstraint("day_index >= 0", name="day_index_nonneg"),
        Index("ix_trope_usage_world_tag_phase", "world_id", "trope_tag", "phase_index"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    trope_tag: Mapped[str] = mapped_column(Text, nullable=False)
    phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    day_index: Mapped[int] = mapped_column(Integer, nullable=False)
    scene_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.scene.id"), nullable=True
    )
    participant_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(Uuid(as_uuid=True)), nullable=False, server_default=text("'{}'::uuid[]")
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.location.entity_id"),
        nullable=True,
    )
    cooldown_until_phase: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class NoveltySignatureRow(Base):
    __tablename__ = "novelty_signature"
    __table_args__ = (
        CheckConstraint("phase_index >= 0", name="phase_index_nonneg"),
        CheckConstraint("day_index >= 0", name="day_index_nonneg"),
        Index(
            "ix_novelty_signature_world_hash",
            "world_id",
            "signature_kind",
            "signature_hash",
        ),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    signature_kind: Mapped[str] = mapped_column(Text, nullable=False)
    signature_hash: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    day_index: Mapped[int] = mapped_column(Integer, nullable=False)
    participant_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(Uuid(as_uuid=True)), nullable=False, server_default=text("'{}'::uuid[]")
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.location.entity_id"),
        nullable=True,
    )
    action_family: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EvaluatorRunRow(Base):
    __tablename__ = "evaluator_run"
    __table_args__ = (
        UniqueConstraint("idempotency_key"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    target_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'completed'"))
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    findings_summary: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    requested_narration_regen: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    model_call_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.model_call.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class QualityFindingRow(Base):
    __tablename__ = "quality_finding"
    __table_args__ = (
        CheckConstraint("can_mutate_canon = false", name="no_canon_mutation"),
        Index("ix_quality_finding_run", "evaluator_run_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    evaluator_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.evaluator_run.id"),
        nullable=False,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    finding_code: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'info'"))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_refs: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    can_mutate_canon: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ExportRunRow(Base):
    __tablename__ = "export_run"
    __table_args__ = (
        UniqueConstraint("idempotency_key"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    export_kind: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pending'"))
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    artefact_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    manifest: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    month_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MonthRunRow(Base):
    __tablename__ = "month_run"
    __table_args__ = (
        UniqueConstraint("idempotency_key"),
        UniqueConstraint("world_id", "month_index"),
        CheckConstraint("month_index >= 1", name="month_index_positive"),
        CheckConstraint("end_day_index >= start_day_index", name="day_range"),
        Index("ix_month_run_world_status", "world_id", "status"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    month_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pending'"))
    start_day_index: Mapped[int] = mapped_column(Integer, nullable=False)
    end_day_index: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    metrics: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
