"""Create Stage 3 long-term memory / rules / world tables.

Revision ID: 0005_stage3_long_term_tables
Revises: 0004_stage2_continuity_tables
Create Date: 2026-07-29
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_stage3_long_term_tables"
down_revision: str | None = "0004_stage2_continuity_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


class Vector(sa.types.UserDefinedType):
    """pgvector column type without requiring the pgvector Python package."""

    cache_ok = True

    def __init__(self, dim: int) -> None:
        self.dim = dim

    def get_col_spec(self, **_kwargs: object) -> str:
        return f"vector({self.dim})"


def upgrade() -> None:
    op.create_table(
        "memory",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("owner_character_id", sa.Uuid(), nullable=False),
        sa.Column("memory_type", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("salience", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("emotional_weight", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("visibility", sa.Text(), nullable=False),
        sa.Column("occurred_phase_index", sa.BigInteger(), nullable=False),
        sa.Column("created_phase_index", sa.BigInteger(), nullable=False),
        sa.Column("last_recalled_phase_index", sa.BigInteger(), nullable=True),
        sa.Column("recall_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("decay_score", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("summary_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "goal_relevance",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "emotional_resonance",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "unresolved_commitment",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "referenced_entity_ids",
            postgresql.ARRAY(sa.Uuid()),
            server_default=sa.text("'{}'::uuid[]"),
            nullable=False,
        ),
        sa.Column("source_event_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "salience >= 0 AND salience <= 1", name=op.f("ck_memory_salience_range")
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name=op.f("ck_memory_confidence_range")
        ),
        sa.CheckConstraint(
            "emotional_weight >= 0 AND emotional_weight <= 1",
            name=op.f("ck_memory_emotional_weight_range"),
        ),
        sa.CheckConstraint(
            "decay_score >= 0 AND decay_score <= 1", name=op.f("ck_memory_decay_score_range")
        ),
        sa.CheckConstraint("recall_count >= 0", name=op.f("ck_memory_recall_count_nonneg")),
        sa.CheckConstraint("summary_version >= 1", name=op.f("ck_memory_summary_version_positive")),
        sa.CheckConstraint(
            "occurred_phase_index >= 0", name=op.f("ck_memory_occurred_phase_nonneg")
        ),
        sa.CheckConstraint("created_phase_index >= 0", name=op.f("ck_memory_created_phase_nonneg")),
        sa.UniqueConstraint(
            "owner_character_id",
            "content_hash",
            "summary_version",
            name=op.f("uq_memory_owner_character_id_content_hash_summary_version"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_memory_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_memory_owner_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_memory_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memory")),
        schema="worldsim",
    )
    op.create_index(
        "ix_memory_owner_created",
        "memory",
        ["world_id", "owner_character_id", "created_phase_index"],
        unique=False,
        schema="worldsim",
    )
    op.create_index(
        "ix_memory_owner_visibility",
        "memory",
        ["world_id", "owner_character_id", "visibility", "status"],
        unique=False,
        schema="worldsim",
    )
    op.create_index(
        "ix_memory_owner_type",
        "memory",
        ["owner_character_id", "memory_type", "status"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "memory_source",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("memory_id", sa.Uuid(), nullable=False),
        sa.Column("source_kind", sa.Text(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("source_role", sa.Text(), server_default=sa.text("'primary'"), nullable=False),
        sa.Column(
            "weight",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("1.0000"),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint(
            "weight >= 0 AND weight <= 1", name=op.f("ck_memory_source_weight_range")
        ),
        sa.CheckConstraint("ordinal >= 0", name=op.f("ck_memory_source_ordinal_nonneg")),
        sa.UniqueConstraint(
            "memory_id",
            "source_kind",
            "source_id",
            name=op.f("uq_memory_source_memory_id_source_kind_source_id"),
        ),
        sa.ForeignKeyConstraint(
            ["memory_id"],
            ["worldsim.memory.id"],
            name=op.f("fk_memory_source_memory_id_memory"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memory_source")),
        schema="worldsim",
    )
    op.create_index(
        "ix_memory_source_memory",
        "memory_source",
        ["memory_id"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "embedding_model_version",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("model_key", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("model_slug", sa.Text(), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("query_prefix", sa.Text(), nullable=False),
        sa.Column("passage_prefix", sa.Text(), nullable=False),
        sa.Column(
            "truncation_policy",
            sa.Text(),
            server_default=sa.text("'truncate_tail'"),
            nullable=False,
        ),
        sa.Column("embedding_version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "capability_probe",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "dimension > 0", name=op.f("ck_embedding_model_version_dimension_positive")
        ),
        sa.CheckConstraint(
            "embedding_version >= 1",
            name=op.f("ck_embedding_model_version_embedding_version_positive"),
        ),
        sa.UniqueConstraint(
            "model_key",
            "embedding_version",
            name=op.f("uq_embedding_model_version_model_key_embedding_version"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_embedding_model_version")),
        schema="worldsim",
    )
    op.create_index(
        "uq_embedding_model_version_active",
        "embedding_model_version",
        ["model_key"],
        unique=True,
        schema="worldsim",
        postgresql_where=sa.text("is_active = true"),
    )
    op.create_table(
        "memory_embedding",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("memory_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("owner_character_id", sa.Uuid(), nullable=False),
        sa.Column("embedding_model_key", sa.Text(), nullable=False),
        sa.Column("embedding_version", sa.Integer(), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("prefix_type", sa.Text(), nullable=False),
        sa.Column("embedded_content_hash", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(2048), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("dimension > 0", name=op.f("ck_memory_embedding_dimension_positive")),
        sa.CheckConstraint(
            "embedding_version >= 1", name=op.f("ck_memory_embedding_embedding_version_positive")
        ),
        sa.CheckConstraint(
            "prefix_type IN ('query', 'passage')", name=op.f("ck_memory_embedding_prefix_type")
        ),
        sa.UniqueConstraint(
            "memory_id",
            "embedding_model_key",
            "embedding_version",
            "embedded_content_hash",
            name=op.f(
                "uq_memory_embedding_memory_id_embedding_model_key_embedding_version_embedded_content_hash"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["memory_id"],
            ["worldsim.memory.id"],
            name=op.f("fk_memory_embedding_memory_id_memory"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_memory_embedding_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_memory_embedding_owner_character_id_character"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memory_embedding")),
        schema="worldsim",
    )
    op.create_index(
        "ix_memory_embedding_memory_active",
        "memory_embedding",
        ["memory_id", "is_active"],
        unique=False,
        schema="worldsim",
    )
    op.create_index(
        "ix_memory_embedding_owner_active",
        "memory_embedding",
        ["world_id", "owner_character_id", "is_active", "embedding_model_key", "embedding_version"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "embedding_job",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("memory_id", sa.Uuid(), nullable=False),
        sa.Column("embedding_model_key", sa.Text(), nullable=False),
        sa.Column("embedding_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "attempt_count >= 0", name=op.f("ck_embedding_job_attempt_count_nonneg")
        ),
        sa.CheckConstraint(
            "embedding_version >= 1", name=op.f("ck_embedding_job_embedding_version_positive")
        ),
        sa.UniqueConstraint("idempotency_key", name=op.f("uq_embedding_job_idempotency_key")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_embedding_job_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["memory_id"],
            ["worldsim.memory.id"],
            name=op.f("fk_embedding_job_memory_id_memory"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_embedding_job")),
        schema="worldsim",
    )
    op.create_index(
        "ix_embedding_job_status",
        "embedding_job",
        ["world_id", "status", "created_at"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "retrieval_trace",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("owner_character_id", sa.Uuid(), nullable=False),
        sa.Column("request_phase_index", sa.BigInteger(), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column(
            "filters",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "candidate_memory_ids",
            postgresql.ARRAY(sa.Uuid()),
            server_default=sa.text("'{}'::uuid[]"),
            nullable=False,
        ),
        sa.Column(
            "selected_memory_ids",
            postgresql.ARRAY(sa.Uuid()),
            server_default=sa.text("'{}'::uuid[]"),
            nullable=False,
        ),
        sa.Column(
            "scores",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("embedding_model_key", sa.Text(), nullable=True),
        sa.Column("embedding_version", sa.Integer(), nullable=True),
        sa.Column("used_semantic", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "reranker_status", sa.Text(), server_default=sa.text("'skipped'"), nullable=False
        ),
        sa.Column("model_call_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "request_phase_index >= 0", name=op.f("ck_retrieval_trace_request_phase_nonneg")
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_retrieval_trace_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_retrieval_trace_owner_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["model_call_id"],
            ["worldsim.model_call.id"],
            name=op.f("fk_retrieval_trace_model_call_id_model_call"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_retrieval_trace")),
        schema="worldsim",
    )
    op.create_index(
        "ix_retrieval_trace_owner_phase",
        "retrieval_trace",
        ["world_id", "owner_character_id", "request_phase_index"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "monthly_chapter",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("owner_character_id", sa.Uuid(), nullable=False),
        sa.Column("month_index", sa.Integer(), nullable=False),
        sa.Column("start_phase_index", sa.BigInteger(), nullable=False),
        sa.Column("end_phase_index", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "structured_extract",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("version_number", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("model_call_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "month_index >= 1", name=op.f("ck_monthly_chapter_month_index_positive")
        ),
        sa.CheckConstraint(
            "end_phase_index >= start_phase_index", name=op.f("ck_monthly_chapter_phase_range")
        ),
        sa.CheckConstraint(
            "version_number >= 1", name=op.f("ck_monthly_chapter_version_number_positive")
        ),
        sa.UniqueConstraint(
            "world_id",
            "owner_character_id",
            "month_index",
            "version_number",
            name=op.f("uq_monthly_chapter_world_id_owner_character_id_month_index_version_number"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_monthly_chapter_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_monthly_chapter_owner_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["model_call_id"],
            ["worldsim.model_call.id"],
            name=op.f("fk_monthly_chapter_model_call_id_model_call"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_monthly_chapter")),
        schema="worldsim",
    )
    op.create_index(
        "ix_monthly_chapter_owner",
        "monthly_chapter",
        ["world_id", "owner_character_id", "month_index"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "reflection_run",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("owner_character_id", sa.Uuid(), nullable=False),
        sa.Column("month_index", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column(
            "proposed_trait_changes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "accepted_trait_changes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "rejected_trait_changes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "evidence_refs",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("monthly_chapter_id", sa.Uuid(), nullable=True),
        sa.Column("model_call_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("month_index >= 1", name=op.f("ck_reflection_run_month_index_positive")),
        sa.UniqueConstraint("idempotency_key", name=op.f("uq_reflection_run_idempotency_key")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_reflection_run_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_reflection_run_owner_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["monthly_chapter_id"],
            ["worldsim.monthly_chapter.id"],
            name=op.f("fk_reflection_run_monthly_chapter_id_monthly_chapter"),
        ),
        sa.ForeignKeyConstraint(
            ["model_call_id"],
            ["worldsim.model_call.id"],
            name=op.f("fk_reflection_run_model_call_id_model_call"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reflection_run")),
        schema="worldsim",
    )
    op.create_index(
        "ix_reflection_run_owner_month",
        "reflection_run",
        ["world_id", "owner_character_id", "month_index"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "character_trait_version",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("trait_key", sa.Text(), nullable=False),
        sa.Column("value_before", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("value_after", sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column(
            "evidence_refs",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("reflection_run_id", sa.Uuid(), nullable=True),
        sa.Column("source_event_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_character_trait_version_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_character_trait_version_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_character_trait_version_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["reflection_run_id"],
            ["worldsim.reflection_run.id"],
            name=op.f("fk_character_trait_version_reflection_run_id_reflection_run"),
        ),
        sa.ForeignKeyConstraint(
            ["source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_character_trait_version_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_character_trait_version")),
        schema="worldsim",
    )
    op.create_index(
        "ix_character_trait_version_char",
        "character_trait_version",
        ["character_id", "trait_key", "version"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "stat_state",
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("stat_code", sa.Text(), nullable=False),
        sa.Column("current_value", sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column("dynamic_potential_cap", sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column("growth_rate", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("adaptability", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("last_source_event_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "current_value >= 0 AND current_value <= 100",
            name=op.f("ck_stat_state_current_value_range"),
        ),
        sa.CheckConstraint(
            "dynamic_potential_cap >= 0 AND dynamic_potential_cap <= 100",
            name=op.f("ck_stat_state_potential_cap_range"),
        ),
        sa.CheckConstraint(
            "growth_rate >= 0 AND growth_rate <= 1", name=op.f("ck_stat_state_growth_rate_range")
        ),
        sa.CheckConstraint(
            "adaptability >= 0 AND adaptability <= 1", name=op.f("ck_stat_state_adaptability_range")
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_stat_state_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_stat_state_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_stat_state_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["last_source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_stat_state_last_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("character_id", "stat_code", name=op.f("pk_stat_state")),
        schema="worldsim",
    )
    op.create_index(
        "ix_stat_state_world",
        "stat_state",
        ["world_id", "character_id"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "stat_potential",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("stat_code", sa.Text(), nullable=False),
        sa.Column("base_potential", sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column(
            "species_modifier",
            sa.Numeric(precision=8, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "age_modifier",
            sa.Numeric(precision=8, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint(
            "base_potential >= 0 AND base_potential <= 100",
            name=op.f("ck_stat_potential_base_potential_range"),
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_stat_potential_version_nonneg")),
        sa.UniqueConstraint(
            "character_id", "stat_code", name=op.f("uq_stat_potential_character_id_stat_code")
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_stat_potential_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_stat_potential_world_id_world"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stat_potential")),
        schema="worldsim",
    )
    op.create_table(
        "skill_definition",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("skill_code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column(
            "governing_stats",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "prerequisites",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint("version >= 0", name=op.f("ck_skill_definition_version_nonneg")),
        sa.UniqueConstraint(
            "world_id", "skill_code", name=op.f("uq_skill_definition_world_id_skill_code")
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_skill_definition_world_id_world"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skill_definition")),
        schema="worldsim",
    )
    op.create_table(
        "skill_state",
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("skill_definition_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column(
            "proficiency",
            sa.Numeric(precision=8, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "evidence_total",
            sa.Numeric(precision=8, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column("plateau_flag", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("teacher_character_id", sa.Uuid(), nullable=True),
        sa.Column("last_source_event_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "proficiency >= 0 AND proficiency <= 100", name=op.f("ck_skill_state_proficiency_range")
        ),
        sa.CheckConstraint(
            "evidence_total >= 0", name=op.f("ck_skill_state_evidence_total_nonneg")
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_skill_state_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_skill_state_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["skill_definition_id"],
            ["worldsim.skill_definition.id"],
            name=op.f("fk_skill_state_skill_definition_id_skill_definition"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_skill_state_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["teacher_character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_skill_state_teacher_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["last_source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_skill_state_last_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("character_id", "skill_definition_id", name=op.f("pk_skill_state")),
        schema="worldsim",
    )
    op.create_table(
        "skill_progress_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("skill_definition_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("source_event_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_weight", sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column(
            "difficulty",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.5000"),
            nullable=False,
        ),
        sa.Column(
            "practice_quality",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.5000"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "evidence_weight >= 0", name=op.f("ck_skill_progress_evidence_evidence_weight_nonneg")
        ),
        sa.CheckConstraint(
            "difficulty >= 0 AND difficulty <= 1",
            name=op.f("ck_skill_progress_evidence_difficulty_range"),
        ),
        sa.CheckConstraint(
            "practice_quality >= 0 AND practice_quality <= 1",
            name=op.f("ck_skill_progress_evidence_practice_quality_range"),
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_skill_progress_evidence_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["skill_definition_id"],
            ["worldsim.skill_definition.id"],
            name=op.f("fk_skill_progress_evidence_skill_definition_id_skill_definition"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_skill_progress_evidence_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_skill_progress_evidence_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skill_progress_evidence")),
        schema="worldsim",
    )
    op.create_index(
        "ix_skill_progress_evidence_char_skill",
        "skill_progress_evidence",
        ["character_id", "skill_definition_id"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "spell_definition",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("spell_code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("school", sa.Text(), nullable=False),
        sa.Column(
            "elements",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "prerequisites",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("mana_cost_min", sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column("mana_cost_max", sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column("cast_time_beats", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("range_desc", sa.Text(), server_default=sa.text("'touch'"), nullable=False),
        sa.Column(
            "target_rules",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "possible_effects",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "failure_modes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "counters",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("visibility", sa.Text(), server_default=sa.text("'public'"), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint(
            "mana_cost_min >= 0", name=op.f("ck_spell_definition_mana_cost_min_nonneg")
        ),
        sa.CheckConstraint(
            "mana_cost_max >= mana_cost_min", name=op.f("ck_spell_definition_mana_cost_range")
        ),
        sa.CheckConstraint(
            "cast_time_beats >= 0", name=op.f("ck_spell_definition_cast_time_nonneg")
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_spell_definition_version_nonneg")),
        sa.UniqueConstraint(
            "world_id", "spell_code", name=op.f("uq_spell_definition_world_id_spell_code")
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_spell_definition_world_id_world"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_spell_definition")),
        schema="worldsim",
    )
    op.create_table(
        "known_spell",
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("spell_definition_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column(
            "proficiency",
            sa.Numeric(precision=8, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column("discovery_event_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "proficiency >= 0 AND proficiency <= 100", name=op.f("ck_known_spell_proficiency_range")
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_known_spell_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_known_spell_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["spell_definition_id"],
            ["worldsim.spell_definition.id"],
            name=op.f("fk_known_spell_spell_definition_id_spell_definition"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_known_spell_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["discovery_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_known_spell_discovery_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("character_id", "spell_definition_id", name=op.f("pk_known_spell")),
        schema="worldsim",
    )
    op.create_table(
        "magic_affinity",
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("element", sa.Text(), nullable=False),
        sa.Column("affinity", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint(
            "affinity >= 0 AND affinity <= 1", name=op.f("ck_magic_affinity_affinity_range")
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_magic_affinity_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_magic_affinity_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_magic_affinity_world_id_world"),
        ),
        sa.PrimaryKeyConstraint("character_id", "element", name=op.f("pk_magic_affinity")),
        schema="worldsim",
    )
    op.create_table(
        "item",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("item_code", sa.Text(), nullable=True),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("item_kind", sa.Text(), nullable=False),
        sa.Column("stackable", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "properties",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column("created_event_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint("version >= 0", name=op.f("ck_item_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_item_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["entity_id"],
            ["worldsim.entity.id"],
            name=op.f("fk_item_entity_id_entity"),
        ),
        sa.ForeignKeyConstraint(
            ["created_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_item_created_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_item")),
        schema="worldsim",
    )
    op.create_index(
        "ix_item_world_code",
        "item",
        ["world_id", "item_code"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "inventory_entry",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("owner_character_id", sa.Uuid(), nullable=False),
        sa.Column("item_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("equipped_slot", sa.Text(), nullable=True),
        sa.Column("last_source_event_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_inventory_entry_quantity_positive")),
        sa.CheckConstraint("version >= 0", name=op.f("ck_inventory_entry_version_nonneg")),
        sa.UniqueConstraint(
            "owner_character_id",
            "item_id",
            name=op.f("uq_inventory_entry_owner_character_id_item_id"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_inventory_entry_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_inventory_entry_owner_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["item_id"],
            ["worldsim.item.id"],
            name=op.f("fk_inventory_entry_item_id_item"),
        ),
        sa.ForeignKeyConstraint(
            ["last_source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_inventory_entry_last_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_inventory_entry")),
        schema="worldsim",
    )
    op.create_table(
        "equipment_state",
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("slot", sa.Text(), nullable=False),
        sa.Column("inventory_entry_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_equipment_state_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_equipment_state_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_equipment_state_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["inventory_entry_id"],
            ["worldsim.inventory_entry.id"],
            name=op.f("fk_equipment_state_inventory_entry_id_inventory_entry"),
        ),
        sa.PrimaryKeyConstraint("character_id", "slot", name=op.f("pk_equipment_state")),
        schema="worldsim",
    )
    op.create_table(
        "condition",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("condition_code", sa.Text(), nullable=False),
        sa.Column("severity", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column("started_phase_index", sa.BigInteger(), nullable=False),
        sa.Column("expected_end_phase_index", sa.BigInteger(), nullable=True),
        sa.Column(
            "modifiers",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("source_event_id", sa.Uuid(), nullable=True),
        sa.Column("removed_event_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint(
            "severity >= 0 AND severity <= 1", name=op.f("ck_condition_severity_range")
        ),
        sa.CheckConstraint(
            "started_phase_index >= 0", name=op.f("ck_condition_started_phase_nonneg")
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_condition_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_condition_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_condition_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_condition_source_event_id_world_event"),
        ),
        sa.ForeignKeyConstraint(
            ["removed_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_condition_removed_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_condition")),
        schema="worldsim",
    )
    op.create_index(
        "ix_condition_char_status",
        "condition",
        ["character_id", "status"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "injury",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("body_region", sa.Text(), nullable=False),
        sa.Column("injury_type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column(
            "bleeding",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "pain",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "mobility_penalty",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "consciousness_impact",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "infection_risk",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "healing_progress",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "treatment",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "permanent_consequence", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column("inflicted_event_id", sa.Uuid(), nullable=True),
        sa.Column("healed_event_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "severity >= 0 AND severity <= 1", name=op.f("ck_injury_severity_range")
        ),
        sa.CheckConstraint(
            "bleeding >= 0 AND bleeding <= 1", name=op.f("ck_injury_bleeding_range")
        ),
        sa.CheckConstraint("pain >= 0 AND pain <= 1", name=op.f("ck_injury_pain_range")),
        sa.CheckConstraint(
            "mobility_penalty >= 0 AND mobility_penalty <= 1", name=op.f("ck_injury_mobility_range")
        ),
        sa.CheckConstraint(
            "consciousness_impact >= 0 AND consciousness_impact <= 1",
            name=op.f("ck_injury_consciousness_range"),
        ),
        sa.CheckConstraint(
            "infection_risk >= 0 AND infection_risk <= 1", name=op.f("ck_injury_infection_range")
        ),
        sa.CheckConstraint(
            "healing_progress >= 0 AND healing_progress <= 1", name=op.f("ck_injury_healing_range")
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_injury_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_injury_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_injury_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["inflicted_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_injury_inflicted_event_id_world_event"),
        ),
        sa.ForeignKeyConstraint(
            ["healed_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_injury_healed_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_injury")),
        schema="worldsim",
    )
    op.create_index(
        "ix_injury_char_status",
        "injury",
        ["character_id", "status"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "recovery_plan",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("injury_id", sa.Uuid(), nullable=True),
        sa.Column("condition_id", sa.Uuid(), nullable=True),
        sa.Column("plan_status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column(
            "steps",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("expected_end_phase_index", sa.BigInteger(), nullable=True),
        sa.Column("source_event_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint("version >= 0", name=op.f("ck_recovery_plan_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_recovery_plan_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_recovery_plan_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["injury_id"],
            ["worldsim.injury.id"],
            name=op.f("fk_recovery_plan_injury_id_injury"),
        ),
        sa.ForeignKeyConstraint(
            ["condition_id"],
            ["worldsim.condition.id"],
            name=op.f("fk_recovery_plan_condition_id_condition"),
        ),
        sa.ForeignKeyConstraint(
            ["source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_recovery_plan_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recovery_plan")),
        schema="worldsim",
    )
    op.create_table(
        "faction",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("faction_key", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("faction_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column(
            "leadership",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "territory_location_ids",
            postgresql.ARRAY(sa.Uuid()),
            server_default=sa.text("'{}'::uuid[]"),
            nullable=False,
        ),
        sa.Column(
            "goals",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "resources",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "plans",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "plot_armour_bias",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column("created_event_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "plot_armour_bias >= -1 AND plot_armour_bias <= 1",
            name=op.f("ck_faction_plot_armour_range"),
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_faction_version_nonneg")),
        sa.UniqueConstraint(
            "world_id", "faction_key", name=op.f("uq_faction_world_id_faction_key")
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_faction_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["created_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_faction_created_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_faction")),
        schema="worldsim",
    )
    op.create_table(
        "faction_membership",
        sa.Column("faction_id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.Text(), server_default=sa.text("'member'"), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column("joined_phase_index", sa.BigInteger(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint("version >= 0", name=op.f("ck_faction_membership_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["faction_id"],
            ["worldsim.faction.id"],
            name=op.f("fk_faction_membership_faction_id_faction"),
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_faction_membership_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_faction_membership_world_id_world"),
        ),
        sa.PrimaryKeyConstraint("faction_id", "character_id", name=op.f("pk_faction_membership")),
        schema="worldsim",
    )
    op.create_table(
        "faction_relation",
        sa.Column("source_faction_id", sa.Uuid(), nullable=False),
        sa.Column("target_faction_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("stance", sa.Text(), nullable=False),
        sa.Column(
            "trust",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "hostility",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column("last_source_event_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint(
            "trust >= -1 AND trust <= 1", name=op.f("ck_faction_relation_trust_range")
        ),
        sa.CheckConstraint(
            "hostility >= 0 AND hostility <= 1", name=op.f("ck_faction_relation_hostility_range")
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_faction_relation_version_nonneg")),
        sa.CheckConstraint(
            "source_faction_id <> target_faction_id",
            name=op.f("ck_faction_relation_no_self_relation"),
        ),
        sa.ForeignKeyConstraint(
            ["source_faction_id"],
            ["worldsim.faction.id"],
            name=op.f("fk_faction_relation_source_faction_id_faction"),
        ),
        sa.ForeignKeyConstraint(
            ["target_faction_id"],
            ["worldsim.faction.id"],
            name=op.f("fk_faction_relation_target_faction_id_faction"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_faction_relation_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["last_source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_faction_relation_last_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint(
            "source_faction_id", "target_faction_id", name=op.f("pk_faction_relation")
        ),
        schema="worldsim",
    )
    op.create_table(
        "faction_state",
        sa.Column("faction_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("day_index", sa.Integer(), nullable=False),
        sa.Column(
            "indicators",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source_event_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("day_index >= 0", name=op.f("ck_faction_state_day_index_nonneg")),
        sa.CheckConstraint("version >= 0", name=op.f("ck_faction_state_version_nonneg")),
        sa.UniqueConstraint(
            "faction_id",
            "day_index",
            "version",
            name=op.f("uq_faction_state_faction_id_day_index_version"),
        ),
        sa.ForeignKeyConstraint(
            ["faction_id"],
            ["worldsim.faction.id"],
            name=op.f("fk_faction_state_faction_id_faction"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_faction_state_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_faction_state_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint(
            "faction_id", "day_index", "version", name=op.f("pk_faction_state")
        ),
        schema="worldsim",
    )
    op.create_table(
        "settlement_indicator",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("indicator_key", sa.Text(), nullable=False),
        sa.Column("value", sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column("day_index", sa.Integer(), nullable=False),
        sa.Column("source_event_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("day_index >= 0", name=op.f("ck_settlement_indicator_day_index_nonneg")),
        sa.CheckConstraint("version >= 0", name=op.f("ck_settlement_indicator_version_nonneg")),
        sa.UniqueConstraint(
            "location_id",
            "indicator_key",
            "day_index",
            "version",
            name=op.f("uq_settlement_indicator_location_id_indicator_key_day_index_version"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_settlement_indicator_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["worldsim.location.entity_id"],
            name=op.f("fk_settlement_indicator_location_id_location"),
        ),
        sa.ForeignKeyConstraint(
            ["source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_settlement_indicator_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_settlement_indicator")),
        schema="worldsim",
    )
    op.create_index(
        "ix_settlement_indicator_loc_day",
        "settlement_indicator",
        ["location_id", "day_index"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "arc",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("arc_key", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("arc_scope", sa.Text(), server_default=sa.text("'major'"), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'dormant'"), nullable=False),
        sa.Column("premise", sa.Text(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column(
            "milestones",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "prerequisites",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "closure_conditions",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "participant_entity_ids",
            postgresql.ARRAY(sa.Uuid()),
            server_default=sa.text("'{}'::uuid[]"),
            nullable=False,
        ),
        sa.Column(
            "dominant_genres",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "progress",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column("deadline_phase_index", sa.BigInteger(), nullable=True),
        sa.Column("start_phase_index", sa.BigInteger(), nullable=True),
        sa.Column("end_phase_index", sa.BigInteger(), nullable=True),
        sa.Column("director_profile_key", sa.Text(), nullable=True),
        sa.Column("source_event_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("progress >= 0 AND progress <= 1", name=op.f("ck_arc_progress_range")),
        sa.CheckConstraint(
            "status IN ('active', 'dormant', 'resolved', 'failed', 'abandoned')",
            name=op.f("ck_arc_status"),
        ),
        sa.CheckConstraint("arc_scope IN ('major', 'secondary')", name=op.f("ck_arc_arc_scope")),
        sa.CheckConstraint("version >= 0", name=op.f("ck_arc_version_nonneg")),
        sa.UniqueConstraint("world_id", "arc_key", name=op.f("uq_arc_world_id_arc_key")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_arc_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_arc_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_arc")),
        schema="worldsim",
    )
    op.create_index(
        "ix_arc_world_status",
        "arc",
        ["world_id", "status", "arc_scope"],
        unique=False,
        schema="worldsim",
    )
    op.create_index(
        "uq_arc_one_active_major",
        "arc",
        ["world_id"],
        unique=True,
        schema="worldsim",
        postgresql_where=sa.text("status = 'active' AND arc_scope = 'major'"),
    )
    op.create_table(
        "trope_usage",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("trope_tag", sa.Text(), nullable=False),
        sa.Column("phase_index", sa.BigInteger(), nullable=False),
        sa.Column("day_index", sa.Integer(), nullable=False),
        sa.Column("scene_id", sa.Uuid(), nullable=True),
        sa.Column(
            "participant_ids",
            postgresql.ARRAY(sa.Uuid()),
            server_default=sa.text("'{}'::uuid[]"),
            nullable=False,
        ),
        sa.Column("location_id", sa.Uuid(), nullable=True),
        sa.Column("cooldown_until_phase", sa.BigInteger(), nullable=True),
        sa.Column("content_hash", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("phase_index >= 0", name=op.f("ck_trope_usage_phase_index_nonneg")),
        sa.CheckConstraint("day_index >= 0", name=op.f("ck_trope_usage_day_index_nonneg")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_trope_usage_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["scene_id"],
            ["worldsim.scene.id"],
            name=op.f("fk_trope_usage_scene_id_scene"),
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["worldsim.location.entity_id"],
            name=op.f("fk_trope_usage_location_id_location"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trope_usage")),
        schema="worldsim",
    )
    op.create_index(
        "ix_trope_usage_world_tag_phase",
        "trope_usage",
        ["world_id", "trope_tag", "phase_index"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "novelty_signature",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("signature_kind", sa.Text(), nullable=False),
        sa.Column("signature_hash", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=True),
        sa.Column("phase_index", sa.BigInteger(), nullable=False),
        sa.Column("day_index", sa.Integer(), nullable=False),
        sa.Column(
            "participant_ids",
            postgresql.ARRAY(sa.Uuid()),
            server_default=sa.text("'{}'::uuid[]"),
            nullable=False,
        ),
        sa.Column("location_id", sa.Uuid(), nullable=True),
        sa.Column("action_family", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "phase_index >= 0", name=op.f("ck_novelty_signature_phase_index_nonneg")
        ),
        sa.CheckConstraint("day_index >= 0", name=op.f("ck_novelty_signature_day_index_nonneg")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_novelty_signature_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["worldsim.location.entity_id"],
            name=op.f("fk_novelty_signature_location_id_location"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_novelty_signature")),
        schema="worldsim",
    )
    op.create_index(
        "ix_novelty_signature_world_hash",
        "novelty_signature",
        ["world_id", "signature_kind", "signature_hash"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "evaluator_run",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("target_ref", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), server_default=sa.text("'completed'"), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column(
            "findings_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "requested_narration_regen",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("model_call_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("idempotency_key", name=op.f("uq_evaluator_run_idempotency_key")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_evaluator_run_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["model_call_id"],
            ["worldsim.model_call.id"],
            name=op.f("fk_evaluator_run_model_call_id_model_call"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluator_run")),
        schema="worldsim",
    )
    op.create_table(
        "quality_finding",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("evaluator_run_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("finding_code", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), server_default=sa.text("'info'"), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "evidence_refs",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "can_mutate_canon", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "can_mutate_canon = false", name=op.f("ck_quality_finding_no_canon_mutation")
        ),
        sa.ForeignKeyConstraint(
            ["evaluator_run_id"],
            ["worldsim.evaluator_run.id"],
            name=op.f("fk_quality_finding_evaluator_run_id_evaluator_run"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_quality_finding_world_id_world"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quality_finding")),
        schema="worldsim",
    )
    op.create_index(
        "ix_quality_finding_run",
        "quality_finding",
        ["evaluator_run_id"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "export_run",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("export_kind", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("artefact_uri", sa.Text(), nullable=True),
        sa.Column(
            "manifest",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("month_index", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("idempotency_key", name=op.f("uq_export_run_idempotency_key")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_export_run_world_id_world"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_export_run")),
        schema="worldsim",
    )
    op.create_table(
        "month_run",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("month_index", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("start_day_index", sa.Integer(), nullable=False),
        sa.Column("end_day_index", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column(
            "metrics",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("month_index >= 1", name=op.f("ck_month_run_month_index_positive")),
        sa.CheckConstraint("end_day_index >= start_day_index", name=op.f("ck_month_run_day_range")),
        sa.UniqueConstraint("idempotency_key", name=op.f("uq_month_run_idempotency_key")),
        sa.UniqueConstraint(
            "world_id", "month_index", name=op.f("uq_month_run_world_id_month_index")
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_month_run_world_id_world"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_month_run")),
        schema="worldsim",
    )
    op.create_index(
        "ix_month_run_world_status",
        "month_run",
        ["world_id", "status"],
        unique=False,
        schema="worldsim",
    )


def downgrade() -> None:
    op.drop_index("ix_month_run_world_status", table_name="month_run", schema="worldsim")
    op.drop_index("ix_quality_finding_run", table_name="quality_finding", schema="worldsim")
    op.drop_index(
        "ix_novelty_signature_world_hash", table_name="novelty_signature", schema="worldsim"
    )
    op.drop_index("ix_trope_usage_world_tag_phase", table_name="trope_usage", schema="worldsim")
    op.drop_index(
        "uq_arc_one_active_major",
        table_name="arc",
        schema="worldsim",
        postgresql_where=sa.text("status = 'active' AND arc_scope = 'major'"),
    )
    op.drop_index("ix_arc_world_status", table_name="arc", schema="worldsim")
    op.drop_index(
        "ix_settlement_indicator_loc_day", table_name="settlement_indicator", schema="worldsim"
    )
    op.drop_index("ix_injury_char_status", table_name="injury", schema="worldsim")
    op.drop_index("ix_condition_char_status", table_name="condition", schema="worldsim")
    op.drop_index("ix_item_world_code", table_name="item", schema="worldsim")
    op.drop_index(
        "ix_skill_progress_evidence_char_skill",
        table_name="skill_progress_evidence",
        schema="worldsim",
    )
    op.drop_index("ix_stat_state_world", table_name="stat_state", schema="worldsim")
    op.drop_index(
        "ix_character_trait_version_char", table_name="character_trait_version", schema="worldsim"
    )
    op.drop_index("ix_reflection_run_owner_month", table_name="reflection_run", schema="worldsim")
    op.drop_index("ix_monthly_chapter_owner", table_name="monthly_chapter", schema="worldsim")
    op.drop_index("ix_retrieval_trace_owner_phase", table_name="retrieval_trace", schema="worldsim")
    op.drop_index("ix_embedding_job_status", table_name="embedding_job", schema="worldsim")
    op.drop_index(
        "ix_memory_embedding_owner_active", table_name="memory_embedding", schema="worldsim"
    )
    op.drop_index(
        "ix_memory_embedding_memory_active", table_name="memory_embedding", schema="worldsim"
    )
    op.drop_index(
        "uq_embedding_model_version_active",
        table_name="embedding_model_version",
        schema="worldsim",
        postgresql_where=sa.text("is_active = true"),
    )
    op.drop_index("ix_memory_source_memory", table_name="memory_source", schema="worldsim")
    op.drop_index("ix_memory_owner_type", table_name="memory", schema="worldsim")
    op.drop_index("ix_memory_owner_visibility", table_name="memory", schema="worldsim")
    op.drop_index("ix_memory_owner_created", table_name="memory", schema="worldsim")
    op.drop_table("month_run", schema="worldsim")
    op.drop_table("export_run", schema="worldsim")
    op.drop_table("quality_finding", schema="worldsim")
    op.drop_table("evaluator_run", schema="worldsim")
    op.drop_table("novelty_signature", schema="worldsim")
    op.drop_table("trope_usage", schema="worldsim")
    op.drop_table("arc", schema="worldsim")
    op.drop_table("settlement_indicator", schema="worldsim")
    op.drop_table("faction_state", schema="worldsim")
    op.drop_table("faction_relation", schema="worldsim")
    op.drop_table("faction_membership", schema="worldsim")
    op.drop_table("faction", schema="worldsim")
    op.drop_table("recovery_plan", schema="worldsim")
    op.drop_table("injury", schema="worldsim")
    op.drop_table("condition", schema="worldsim")
    op.drop_table("equipment_state", schema="worldsim")
    op.drop_table("inventory_entry", schema="worldsim")
    op.drop_table("item", schema="worldsim")
    op.drop_table("magic_affinity", schema="worldsim")
    op.drop_table("known_spell", schema="worldsim")
    op.drop_table("spell_definition", schema="worldsim")
    op.drop_table("skill_progress_evidence", schema="worldsim")
    op.drop_table("skill_state", schema="worldsim")
    op.drop_table("skill_definition", schema="worldsim")
    op.drop_table("stat_potential", schema="worldsim")
    op.drop_table("stat_state", schema="worldsim")
    op.drop_table("character_trait_version", schema="worldsim")
    op.drop_table("reflection_run", schema="worldsim")
    op.drop_table("monthly_chapter", schema="worldsim")
    op.drop_table("retrieval_trace", schema="worldsim")
    op.drop_table("embedding_job", schema="worldsim")
    op.drop_table("memory_embedding", schema="worldsim")
    op.drop_table("embedding_model_version", schema="worldsim")
    op.drop_table("memory_source", schema="worldsim")
    op.drop_table("memory", schema="worldsim")
