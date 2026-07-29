"""Create Stage 2 continuity / knowledge / travel / narrative tables.

Revision ID: 0004_stage2_continuity_tables
Revises: 0003_stage1_action_scene_tables
Create Date: 2026-07-29
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_stage2_continuity_tables"
down_revision: str | None = "0003_stage1_action_scene_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "route",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("origin_location_id", sa.Uuid(), nullable=False),
        sa.Column("destination_location_id", sa.Uuid(), nullable=False),
        sa.Column("is_bidirectional", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("distance_units", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("base_duration_phases", sa.Integer(), nullable=False),
        sa.Column(
            "allowed_travel_modes",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "terrain_tags",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "danger_level",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "seasonal_modifiers",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column("created_event_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint(
            "distance_units > 0",
            name=op.f("ck_route_distance_units_positive"),
        ),
        sa.CheckConstraint(
            "base_duration_phases > 0",
            name=op.f("ck_route_base_duration_phases_positive"),
        ),
        sa.CheckConstraint(
            "danger_level >= 0 AND danger_level <= 1",
            name=op.f("ck_route_danger_level_range"),
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_route_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_route_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["origin_location_id"],
            ["worldsim.location.entity_id"],
            name=op.f("fk_route_origin_location_id_location"),
        ),
        sa.ForeignKeyConstraint(
            ["destination_location_id"],
            ["worldsim.location.entity_id"],
            name=op.f("fk_route_destination_location_id_location"),
        ),
        sa.ForeignKeyConstraint(
            ["created_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_route_created_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_route")),
        schema="worldsim",
    )
    op.create_index(
        "uq_route_active_identity",
        "route",
        ["world_id", "origin_location_id", "destination_location_id"],
        unique=True,
        schema="worldsim",
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index("ix_route_world", "route", ["world_id"], unique=False, schema="worldsim")

    op.create_table(
        "goal",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("owner_character_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column(
            "priority",
            sa.Numeric(precision=8, scale=4),
            server_default=sa.text("0.5000"),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column("horizon", sa.Text(), nullable=True),
        sa.Column(
            "success_conditions",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "failure_conditions",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "allows_alternative_plans",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
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
        sa.CheckConstraint("version >= 0", name=op.f("ck_goal_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_goal_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_goal_owner_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_goal_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_goal")),
        schema="worldsim",
    )
    op.create_index(
        "ix_goal_owner",
        "goal",
        ["world_id", "owner_character_id"],
        unique=False,
        schema="worldsim",
    )

    op.create_table(
        "plan",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("goal_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("owner_character_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("expected_horizon", sa.Text(), nullable=True),
        sa.Column(
            "commitment_level",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.5000"),
            nullable=False,
        ),
        sa.Column("revision_number", sa.Integer(), server_default=sa.text("1"), nullable=False),
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
        sa.CheckConstraint(
            "commitment_level >= 0 AND commitment_level <= 1",
            name=op.f("ck_plan_commitment_level_range"),
        ),
        sa.CheckConstraint(
            "revision_number >= 1",
            name=op.f("ck_plan_revision_number_positive"),
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_plan_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["goal_id"],
            ["worldsim.goal.id"],
            name=op.f("fk_plan_goal_id_goal"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_plan_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_plan_owner_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_plan_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plan")),
        schema="worldsim",
    )
    op.create_index(
        "uq_plan_one_active_primary_per_goal",
        "plan",
        ["goal_id"],
        unique=True,
        schema="worldsim",
        postgresql_where=sa.text("is_primary AND status = 'active'"),
    )
    op.create_index("ix_plan_goal", "plan", ["goal_id"], unique=False, schema="worldsim")

    op.create_table(
        "commitment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("debtor_character_id", sa.Uuid(), nullable=False),
        sa.Column("beneficiary_character_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "due_condition",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column("created_event_id", sa.Uuid(), nullable=True),
        sa.Column("fulfilled_event_id", sa.Uuid(), nullable=True),
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
        sa.CheckConstraint("version >= 0", name=op.f("ck_commitment_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_commitment_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["debtor_character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_commitment_debtor_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["beneficiary_character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_commitment_beneficiary_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["created_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_commitment_created_event_id_world_event"),
        ),
        sa.ForeignKeyConstraint(
            ["fulfilled_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_commitment_fulfilled_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_commitment")),
        schema="worldsim",
    )
    op.create_index(
        "ix_commitment_debtor",
        "commitment",
        ["world_id", "debtor_character_id"],
        unique=False,
        schema="worldsim",
    )

    op.create_table(
        "relationship_edge",
        sa.Column("source_character_id", sa.Uuid(), nullable=False),
        sa.Column("target_character_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column(
            "familiarity",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "trust",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "affection",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "attraction",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "respect",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "fear",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "resentment",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "dependency",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "loyalty",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "perceived_reciprocity",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column("last_meaningful_interaction_phase", sa.BigInteger(), nullable=True),
        sa.Column("last_source_event_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "source_character_id <> target_character_id",
            name=op.f("ck_relationship_edge_source_ne_target"),
        ),
        sa.CheckConstraint(
            "familiarity >= 0 AND familiarity <= 1",
            name=op.f("ck_relationship_edge_familiarity_range"),
        ),
        sa.CheckConstraint(
            "trust >= -1 AND trust <= 1",
            name=op.f("ck_relationship_edge_trust_range"),
        ),
        sa.CheckConstraint(
            "affection >= -1 AND affection <= 1",
            name=op.f("ck_relationship_edge_affection_range"),
        ),
        sa.CheckConstraint(
            "attraction >= -1 AND attraction <= 1",
            name=op.f("ck_relationship_edge_attraction_range"),
        ),
        sa.CheckConstraint(
            "respect >= -1 AND respect <= 1",
            name=op.f("ck_relationship_edge_respect_range"),
        ),
        sa.CheckConstraint(
            "fear >= -1 AND fear <= 1",
            name=op.f("ck_relationship_edge_fear_range"),
        ),
        sa.CheckConstraint(
            "resentment >= -1 AND resentment <= 1",
            name=op.f("ck_relationship_edge_resentment_range"),
        ),
        sa.CheckConstraint(
            "dependency >= -1 AND dependency <= 1",
            name=op.f("ck_relationship_edge_dependency_range"),
        ),
        sa.CheckConstraint(
            "loyalty >= -1 AND loyalty <= 1",
            name=op.f("ck_relationship_edge_loyalty_range"),
        ),
        sa.CheckConstraint(
            "perceived_reciprocity >= -1 AND perceived_reciprocity <= 1",
            name=op.f("ck_relationship_edge_perceived_reciprocity_range"),
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_relationship_edge_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["source_character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_relationship_edge_source_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["target_character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_relationship_edge_target_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_relationship_edge_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["last_source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_relationship_edge_last_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint(
            "source_character_id",
            "target_character_id",
            name=op.f("pk_relationship_edge"),
        ),
        schema="worldsim",
    )
    op.create_index(
        "ix_relationship_edge_world_source",
        "relationship_edge",
        ["world_id", "source_character_id"],
        unique=False,
        schema="worldsim",
    )

    op.create_table(
        "relationship_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("source_character_id", sa.Uuid(), nullable=False),
        sa.Column("target_character_id", sa.Uuid(), nullable=False),
        sa.Column("source_event_id", sa.Uuid(), nullable=False),
        sa.Column("dimension", sa.Text(), nullable=False),
        sa.Column("signed_strength", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("perceived", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("decay_policy", sa.Text(), server_default=sa.text("'default'"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "signed_strength >= -1 AND signed_strength <= 1",
            name=op.f("ck_relationship_evidence_signed_strength_range"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_relationship_evidence_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["source_character_id", "target_character_id"],
            [
                "worldsim.relationship_edge.source_character_id",
                "worldsim.relationship_edge.target_character_id",
            ],
            name=op.f("fk_relationship_evidence_edge_relationship_edge"),
        ),
        sa.ForeignKeyConstraint(
            ["source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_relationship_evidence_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_relationship_evidence")),
        schema="worldsim",
    )
    op.create_index(
        "ix_relationship_evidence_edge",
        "relationship_evidence",
        ["source_character_id", "target_character_id"],
        unique=False,
        schema="worldsim",
    )

    op.create_table(
        "claim",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("source_event_id", sa.Uuid(), nullable=False),
        sa.Column("speaker_id", sa.Uuid(), nullable=False),
        sa.Column("proposition_key", sa.Text(), nullable=True),
        sa.Column("proposition_text", sa.Text(), nullable=False),
        sa.Column("truth_status", sa.Text(), server_default=sa.text("'unknown'"), nullable=False),
        sa.Column("intent_class", sa.Text(), nullable=True),
        sa.Column("confidence_expressed", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "confidence_expressed IS NULL OR (confidence_expressed >= 0 AND confidence_expressed <= 1)",
            name=op.f("ck_claim_confidence_expressed_range"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_claim_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_claim_source_event_id_world_event"),
        ),
        sa.ForeignKeyConstraint(
            ["speaker_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_claim_speaker_id_character"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_claim")),
        schema="worldsim",
    )
    op.create_index("ix_claim_world", "claim", ["world_id"], unique=False, schema="worldsim")
    op.create_index(
        "ix_claim_speaker",
        "claim",
        ["speaker_id", "created_at"],
        unique=False,
        schema="worldsim",
    )

    op.create_table(
        "claim_listener",
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("listener_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["claim_id"],
            ["worldsim.claim.id"],
            name=op.f("fk_claim_listener_claim_id_claim"),
        ),
        sa.ForeignKeyConstraint(
            ["listener_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_claim_listener_listener_id_character"),
        ),
        sa.PrimaryKeyConstraint("claim_id", "listener_id", name=op.f("pk_claim_listener")),
        schema="worldsim",
    )

    op.create_table(
        "belief",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("proposition_key", sa.Text(), nullable=False),
        sa.Column("belief_text", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column("first_source_observation_id", sa.Uuid(), nullable=True),
        sa.Column("last_source_event_id", sa.Uuid(), nullable=True),
        sa.Column(
            "evidence_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name=op.f("ck_belief_confidence_range"),
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_belief_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_belief_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_belief_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["first_source_observation_id"],
            ["worldsim.observation.id"],
            name=op.f("fk_belief_first_source_observation_id_observation"),
        ),
        sa.ForeignKeyConstraint(
            ["last_source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_belief_last_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_belief")),
        sa.UniqueConstraint(
            "character_id",
            "proposition_key",
            name=op.f("uq_belief_character_id_proposition_key"),
        ),
        schema="worldsim",
    )
    op.create_index(
        "ix_belief_character",
        "belief",
        ["character_id", "status"],
        unique=False,
        schema="worldsim",
    )

    op.create_table(
        "belief_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("belief_id", sa.Uuid(), nullable=False),
        sa.Column("source_kind", sa.Text(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("signed_weight", sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "source_kind IN ('observation', 'claim', 'event')",
            name=op.f("ck_belief_evidence_source_kind"),
        ),
        sa.ForeignKeyConstraint(
            ["belief_id"],
            ["worldsim.belief.id"],
            name=op.f("fk_belief_evidence_belief_id_belief"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_belief_evidence")),
        sa.UniqueConstraint(
            "belief_id",
            "source_kind",
            "source_id",
            name=op.f("uq_belief_evidence_belief_id_source_kind_source_id"),
        ),
        schema="worldsim",
    )

    op.create_table(
        "secret_access",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("secret_key", sa.Text(), nullable=False),
        sa.Column("owner_character_id", sa.Uuid(), nullable=False),
        sa.Column("holder_character_id", sa.Uuid(), nullable=False),
        sa.Column("access_level", sa.Text(), nullable=False),
        sa.Column("granted_event_id", sa.Uuid(), nullable=True),
        sa.Column("revoked_event_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_secret_access_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_secret_access_owner_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["holder_character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_secret_access_holder_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["granted_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_secret_access_granted_event_id_world_event"),
        ),
        sa.ForeignKeyConstraint(
            ["revoked_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_secret_access_revoked_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_secret_access")),
        sa.UniqueConstraint(
            "world_id",
            "secret_key",
            "holder_character_id",
            name=op.f("uq_secret_access_world_id_secret_key_holder_character_id"),
        ),
        schema="worldsim",
    )

    op.create_table(
        "hook",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("hook_key", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'dormant'"), nullable=False),
        sa.Column("premise", sa.Text(), nullable=False),
        sa.Column(
            "prerequisites",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("scheduled_window", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "involved_entity_ids",
            postgresql.ARRAY(sa.Uuid()),
            server_default=sa.text("'{}'::uuid[]"),
            nullable=False,
        ),
        sa.Column(
            "disclosure_state",
            sa.Text(),
            server_default=sa.text("'hidden'"),
            nullable=False,
        ),
        sa.Column("cooldown_until_phase", sa.BigInteger(), nullable=True),
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
        sa.CheckConstraint(
            "status IN ('active', 'dormant', 'resolved', 'abandoned')",
            name=op.f("ck_hook_status"),
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_hook_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_hook_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_hook_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_hook")),
        sa.UniqueConstraint("world_id", "hook_key", name=op.f("uq_hook_world_id_hook_key")),
        schema="worldsim",
    )
    op.create_index(
        "ix_hook_world_status", "hook", ["world_id", "status"], unique=False, schema="worldsim"
    )

    op.create_table(
        "activity",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("owner_entity_id", sa.Uuid(), nullable=False),
        sa.Column("activity_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column("origin_location_id", sa.Uuid(), nullable=True),
        sa.Column("destination_location_id", sa.Uuid(), nullable=True),
        sa.Column("route_id", sa.Uuid(), nullable=True),
        sa.Column("started_phase_index", sa.BigInteger(), nullable=False),
        sa.Column("expected_end_phase_index", sa.BigInteger(), nullable=True),
        sa.Column(
            "progress",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "interruption_conditions",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "activity_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("last_source_event_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint(
            "progress >= 0 AND progress <= 1",
            name=op.f("ck_activity_progress_range"),
        ),
        sa.CheckConstraint(
            "(activity_type <> 'travel') OR (route_id IS NOT NULL)",
            name=op.f("ck_activity_travel_requires_route"),
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_activity_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_activity_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_entity_id"],
            ["worldsim.entity.id"],
            name=op.f("fk_activity_owner_entity_id_entity"),
        ),
        sa.ForeignKeyConstraint(
            ["origin_location_id"],
            ["worldsim.location.entity_id"],
            name=op.f("fk_activity_origin_location_id_location"),
        ),
        sa.ForeignKeyConstraint(
            ["destination_location_id"],
            ["worldsim.location.entity_id"],
            name=op.f("fk_activity_destination_location_id_location"),
        ),
        sa.ForeignKeyConstraint(
            ["route_id"],
            ["worldsim.route.id"],
            name=op.f("fk_activity_route_id_route"),
        ),
        sa.ForeignKeyConstraint(
            ["last_source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_activity_last_source_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_activity")),
        schema="worldsim",
    )
    op.create_index(
        "uq_activity_one_active_per_owner",
        "activity",
        ["owner_entity_id"],
        unique=True,
        schema="worldsim",
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "ix_activity_world_owner",
        "activity",
        ["world_id", "owner_entity_id"],
        unique=False,
        schema="worldsim",
    )

    op.create_table(
        "plan_step",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("target_entity_id", sa.Uuid(), nullable=True),
        sa.Column("target_location_id", sa.Uuid(), nullable=True),
        sa.Column("activity_id", sa.Uuid(), nullable=True),
        sa.Column(
            "prerequisites",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("expected_duration_phases", sa.Integer(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint("step_index >= 0", name=op.f("ck_plan_step_step_index_nonneg")),
        sa.CheckConstraint(
            "expected_duration_phases IS NULL OR expected_duration_phases >= 0",
            name=op.f("ck_plan_step_expected_duration_nonneg"),
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_plan_step_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["worldsim.plan.id"],
            name=op.f("fk_plan_step_plan_id_plan"),
        ),
        sa.ForeignKeyConstraint(
            ["target_entity_id"],
            ["worldsim.entity.id"],
            name=op.f("fk_plan_step_target_entity_id_entity"),
        ),
        sa.ForeignKeyConstraint(
            ["target_location_id"],
            ["worldsim.location.entity_id"],
            name=op.f("fk_plan_step_target_location_id_location"),
        ),
        sa.ForeignKeyConstraint(
            ["activity_id"],
            ["worldsim.activity.id"],
            name=op.f("fk_plan_step_activity_id_activity"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plan_step")),
        sa.UniqueConstraint(
            "plan_id",
            "step_index",
            name=op.f("uq_plan_step_plan_id_step_index"),
        ),
        schema="worldsim",
    )

    op.create_table(
        "activity_participant",
        sa.Column("activity_id", sa.Uuid(), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("joined_phase_index", sa.BigInteger(), nullable=False),
        sa.Column("left_phase_index", sa.BigInteger(), nullable=True),
        sa.CheckConstraint(
            "joined_phase_index >= 0",
            name=op.f("ck_activity_participant_joined_phase_nonneg"),
        ),
        sa.ForeignKeyConstraint(
            ["activity_id"],
            ["worldsim.activity.id"],
            name=op.f("fk_activity_participant_activity_id_activity"),
        ),
        sa.ForeignKeyConstraint(
            ["entity_id"],
            ["worldsim.entity.id"],
            name=op.f("fk_activity_participant_entity_id_entity"),
        ),
        sa.PrimaryKeyConstraint(
            "activity_id",
            "entity_id",
            name=op.f("pk_activity_participant"),
        ),
        schema="worldsim",
    )

    op.create_table(
        "travel_progress",
        sa.Column("activity_id", sa.Uuid(), nullable=False),
        sa.Column("route_id", sa.Uuid(), nullable=False),
        sa.Column(
            "distance_completed",
            sa.Numeric(precision=12, scale=4),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("phases_elapsed", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "current_segment_index",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("last_tick_phase_index", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'in_progress'"), nullable=False),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint(
            "distance_completed >= 0",
            name=op.f("ck_travel_progress_distance_completed_nonneg"),
        ),
        sa.CheckConstraint(
            "phases_elapsed >= 0",
            name=op.f("ck_travel_progress_phases_elapsed_nonneg"),
        ),
        sa.CheckConstraint(
            "current_segment_index >= 0",
            name=op.f("ck_travel_progress_current_segment_index_nonneg"),
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_travel_progress_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["activity_id"],
            ["worldsim.activity.id"],
            name=op.f("fk_travel_progress_activity_id_activity"),
        ),
        sa.ForeignKeyConstraint(
            ["route_id"],
            ["worldsim.route.id"],
            name=op.f("fk_travel_progress_route_id_route"),
        ),
        sa.PrimaryKeyConstraint("activity_id", name=op.f("pk_travel_progress")),
        schema="worldsim",
    )

    op.create_table(
        "narrative_metric",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("metric_key", sa.Text(), nullable=False),
        sa.Column("metric_value", sa.Numeric(precision=16, scale=6), nullable=False),
        sa.Column("window_start_phase", sa.BigInteger(), nullable=False),
        sa.Column("window_end_phase", sa.BigInteger(), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_narrative_metric_world_id_world"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_narrative_metric")),
        schema="worldsim",
    )
    op.create_index(
        "ix_narrative_metric_world_key_recorded",
        "narrative_metric",
        ["world_id", "metric_key", "recorded_at"],
        unique=False,
        schema="worldsim",
    )

    op.create_table(
        "npc_profile",
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column(
            "role_tags",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "compact_card",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("source_hook_id", sa.Uuid(), nullable=True),
        sa.Column("similarity_fingerprint", sa.Text(), nullable=False),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_npc_profile_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_npc_profile_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_npc_profile_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["source_hook_id"],
            ["worldsim.hook.id"],
            name=op.f("fk_npc_profile_source_hook_id_hook"),
        ),
        sa.PrimaryKeyConstraint("character_id", name=op.f("pk_npc_profile")),
        schema="worldsim",
    )

    op.create_table(
        "npc_lifecycle",
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("lifecycle_status", sa.Text(), nullable=False),
        sa.Column("activated_phase_index", sa.BigInteger(), nullable=True),
        sa.Column("archive_phase_index", sa.BigInteger(), nullable=True),
        sa.Column("ttl_until_phase", sa.BigInteger(), nullable=True),
        sa.Column(
            "relevance_score",
            sa.Numeric(precision=5, scale=4),
            server_default=sa.text("0.5000"),
            nullable=False,
        ),
        sa.Column("archive_summary", sa.Text(), nullable=True),
        sa.Column("last_scene_phase_index", sa.BigInteger(), nullable=True),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "lifecycle_status IN ('proposed', 'active', 'archived', 'retained')",
            name=op.f("ck_npc_lifecycle_lifecycle_status"),
        ),
        sa.CheckConstraint(
            "lifecycle_status <> 'archived' OR archive_phase_index IS NOT NULL",
            name=op.f("ck_npc_lifecycle_archived_requires_archive_phase"),
        ),
        sa.CheckConstraint(
            "relevance_score >= 0 AND relevance_score <= 1",
            name=op.f("ck_npc_lifecycle_relevance_score_range"),
        ),
        sa.CheckConstraint("version >= 0", name=op.f("ck_npc_lifecycle_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_npc_lifecycle_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_npc_lifecycle_world_id_world"),
        ),
        sa.PrimaryKeyConstraint("character_id", name=op.f("pk_npc_lifecycle")),
        schema="worldsim",
    )

    op.create_table(
        "summary",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("owner_character_id", sa.Uuid(), nullable=True),
        sa.Column("summary_type", sa.Text(), nullable=False),
        sa.Column("start_phase_index", sa.BigInteger(), nullable=False),
        sa.Column("end_phase_index", sa.BigInteger(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "structured_extract",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("perspective", sa.Text(), nullable=False),
        sa.Column("version_number", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("model_call_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "version_number >= 1",
            name=op.f("ck_summary_version_number_positive"),
        ),
        sa.CheckConstraint(
            "end_phase_index >= start_phase_index",
            name=op.f("ck_summary_phase_range"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_summary_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_summary_owner_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["model_call_id"],
            ["worldsim.model_call.id"],
            name=op.f("fk_summary_model_call_id_model_call"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_summary")),
        schema="worldsim",
    )
    op.create_index(
        "uq_summary_owned_identity",
        "summary",
        [
            "world_id",
            "owner_character_id",
            "summary_type",
            "start_phase_index",
            "end_phase_index",
            "version_number",
        ],
        unique=True,
        schema="worldsim",
        postgresql_where=sa.text("owner_character_id IS NOT NULL"),
    )
    op.create_index(
        "uq_summary_unowned_identity",
        "summary",
        [
            "world_id",
            "summary_type",
            "start_phase_index",
            "end_phase_index",
            "version_number",
        ],
        unique=True,
        schema="worldsim",
        postgresql_where=sa.text("owner_character_id IS NULL"),
    )

    op.create_table(
        "summary_source",
        sa.Column("summary_id", sa.Uuid(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("source_kind", sa.Text(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("ordinal >= 0", name=op.f("ck_summary_source_ordinal_nonneg")),
        sa.ForeignKeyConstraint(
            ["summary_id"],
            ["worldsim.summary.id"],
            name=op.f("fk_summary_source_summary_id_summary"),
        ),
        sa.PrimaryKeyConstraint("summary_id", "ordinal", name=op.f("pk_summary_source")),
        schema="worldsim",
    )

    op.create_table(
        "diary_entry",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("owner_character_id", sa.Uuid(), nullable=False),
        sa.Column("day_index", sa.BigInteger(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("summary_id", sa.Uuid(), nullable=True),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint("day_index >= 0", name=op.f("ck_diary_entry_day_index_nonneg")),
        sa.CheckConstraint("version >= 0", name=op.f("ck_diary_entry_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_diary_entry_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_character_id"],
            ["worldsim.character.entity_id"],
            name=op.f("fk_diary_entry_owner_character_id_character"),
        ),
        sa.ForeignKeyConstraint(
            ["summary_id"],
            ["worldsim.summary.id"],
            name=op.f("fk_diary_entry_summary_id_summary"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_diary_entry")),
        sa.UniqueConstraint(
            "world_id",
            "owner_character_id",
            "day_index",
            name=op.f("uq_diary_entry_world_id_owner_character_id_day_index"),
        ),
        schema="worldsim",
    )

    op.create_table(
        "day_run",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("day_index", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recovery_snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint("day_index >= 0", name=op.f("ck_day_run_day_index_nonneg")),
        sa.CheckConstraint("version >= 0", name=op.f("ck_day_run_version_nonneg")),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_day_run_world_id_world"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_day_run")),
        sa.UniqueConstraint("idempotency_key", name=op.f("uq_day_run_idempotency_key")),
        sa.UniqueConstraint(
            "world_id",
            "day_index",
            name=op.f("uq_day_run_world_id_day_index"),
        ),
        schema="worldsim",
    )

    op.create_table(
        "daily_audit",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("day_run_id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column(
            "hard_violation_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "soft_violation_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "findings",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "hard_violation_count >= 0",
            name=op.f("ck_daily_audit_hard_violation_count_nonneg"),
        ),
        sa.CheckConstraint(
            "soft_violation_count >= 0",
            name=op.f("ck_daily_audit_soft_violation_count_nonneg"),
        ),
        sa.ForeignKeyConstraint(
            ["day_run_id"],
            ["worldsim.day_run.id"],
            name=op.f("fk_daily_audit_day_run_id_day_run"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_daily_audit_world_id_world"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_daily_audit")),
        sa.UniqueConstraint("day_run_id", name=op.f("uq_daily_audit_day_run_id")),
        schema="worldsim",
    )

    op.create_table(
        "scheduled_effect",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("due_phase_index", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'pending'"), nullable=False),
        sa.Column(
            "effect_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("source_event_id", sa.Uuid(), nullable=True),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("applied_event_id", sa.Uuid(), nullable=True),
        sa.CheckConstraint(
            "due_phase_index >= 0",
            name=op.f("ck_scheduled_effect_due_phase_index_nonneg"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_scheduled_effect_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["source_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_scheduled_effect_source_event_id_world_event"),
        ),
        sa.ForeignKeyConstraint(
            ["applied_event_id"],
            ["worldsim.world_event.id"],
            name=op.f("fk_scheduled_effect_applied_event_id_world_event"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scheduled_effect")),
        sa.UniqueConstraint(
            "idempotency_key",
            name=op.f("uq_scheduled_effect_idempotency_key"),
        ),
        schema="worldsim",
    )
    op.create_index(
        "ix_scheduled_effect_due",
        "scheduled_effect",
        ["world_id", "due_phase_index", "status"],
        unique=False,
        schema="worldsim",
    )

    # Additive FKs / columns on Stage 0-1 tables
    op.create_foreign_key(
        op.f("fk_character_state_active_activity_id_activity"),
        "character_state",
        "activity",
        ["active_activity_id"],
        ["id"],
        source_schema="worldsim",
        referent_schema="worldsim",
    )
    op.create_foreign_key(
        op.f("fk_action_proposal_continuation_activity_id_activity"),
        "action_proposal",
        "activity",
        ["continuation_activity_id"],
        ["id"],
        source_schema="worldsim",
        referent_schema="worldsim",
    )
    op.add_column(
        "scene",
        sa.Column("continuation_id", sa.Uuid(), nullable=True),
        schema="worldsim",
    )
    op.add_column(
        "scene",
        sa.Column("director_hook_id", sa.Uuid(), nullable=True),
        schema="worldsim",
    )
    op.add_column(
        "scene",
        sa.Column(
            "observer_eligibility",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        schema="worldsim",
    )
    op.create_foreign_key(
        op.f("fk_scene_director_hook_id_hook"),
        "scene",
        "hook",
        ["director_hook_id"],
        ["id"],
        source_schema="worldsim",
        referent_schema="worldsim",
    )
    op.add_column(
        "world_event",
        sa.Column("director_provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema="worldsim",
    )
    op.add_column(
        "world_event",
        sa.Column("npc_provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema="worldsim",
    )


def downgrade() -> None:
    op.drop_column("world_event", "npc_provenance", schema="worldsim")
    op.drop_column("world_event", "director_provenance", schema="worldsim")
    op.drop_constraint(
        op.f("fk_scene_director_hook_id_hook"),
        "scene",
        schema="worldsim",
        type_="foreignkey",
    )
    op.drop_column("scene", "observer_eligibility", schema="worldsim")
    op.drop_column("scene", "director_hook_id", schema="worldsim")
    op.drop_column("scene", "continuation_id", schema="worldsim")
    op.drop_constraint(
        op.f("fk_action_proposal_continuation_activity_id_activity"),
        "action_proposal",
        schema="worldsim",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_character_state_active_activity_id_activity"),
        "character_state",
        schema="worldsim",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_scheduled_effect_due",
        table_name="scheduled_effect",
        schema="worldsim",
    )
    op.drop_table("scheduled_effect", schema="worldsim")
    op.drop_table("daily_audit", schema="worldsim")
    op.drop_table("day_run", schema="worldsim")
    op.drop_table("diary_entry", schema="worldsim")
    op.drop_table("summary_source", schema="worldsim")
    op.drop_index(
        "uq_summary_unowned_identity",
        table_name="summary",
        schema="worldsim",
        postgresql_where=sa.text("owner_character_id IS NULL"),
    )
    op.drop_index(
        "uq_summary_owned_identity",
        table_name="summary",
        schema="worldsim",
        postgresql_where=sa.text("owner_character_id IS NOT NULL"),
    )
    op.drop_table("summary", schema="worldsim")
    op.drop_table("npc_lifecycle", schema="worldsim")
    op.drop_table("npc_profile", schema="worldsim")
    op.drop_index(
        "ix_narrative_metric_world_key_recorded",
        table_name="narrative_metric",
        schema="worldsim",
    )
    op.drop_table("narrative_metric", schema="worldsim")
    op.drop_table("travel_progress", schema="worldsim")
    op.drop_table("activity_participant", schema="worldsim")
    op.drop_table("plan_step", schema="worldsim")
    op.drop_index(
        "uq_activity_one_active_per_owner",
        table_name="activity",
        schema="worldsim",
        postgresql_where=sa.text("status = 'active'"),
    )
    op.drop_index("ix_activity_world_owner", table_name="activity", schema="worldsim")
    op.drop_table("activity", schema="worldsim")
    op.drop_index("ix_hook_world_status", table_name="hook", schema="worldsim")
    op.drop_table("hook", schema="worldsim")
    op.drop_table("secret_access", schema="worldsim")
    op.drop_table("belief_evidence", schema="worldsim")
    op.drop_index("ix_belief_character", table_name="belief", schema="worldsim")
    op.drop_table("belief", schema="worldsim")
    op.drop_table("claim_listener", schema="worldsim")
    op.drop_index("ix_claim_speaker", table_name="claim", schema="worldsim")
    op.drop_index("ix_claim_world", table_name="claim", schema="worldsim")
    op.drop_table("claim", schema="worldsim")
    op.drop_index(
        "ix_relationship_evidence_edge",
        table_name="relationship_evidence",
        schema="worldsim",
    )
    op.drop_table("relationship_evidence", schema="worldsim")
    op.drop_index(
        "ix_relationship_edge_world_source",
        table_name="relationship_edge",
        schema="worldsim",
    )
    op.drop_table("relationship_edge", schema="worldsim")
    op.drop_index("ix_commitment_debtor", table_name="commitment", schema="worldsim")
    op.drop_table("commitment", schema="worldsim")
    op.drop_index(
        "uq_plan_one_active_primary_per_goal",
        table_name="plan",
        schema="worldsim",
        postgresql_where=sa.text("is_primary AND status = 'active'"),
    )
    op.drop_index("ix_plan_goal", table_name="plan", schema="worldsim")
    op.drop_table("plan", schema="worldsim")
    op.drop_index("ix_goal_owner", table_name="goal", schema="worldsim")
    op.drop_table("goal", schema="worldsim")
    op.drop_index(
        "uq_route_active_identity",
        table_name="route",
        schema="worldsim",
        postgresql_where=sa.text("status = 'active'"),
    )
    op.drop_index("ix_route_world", table_name="route", schema="worldsim")
    op.drop_table("route", schema="worldsim")
