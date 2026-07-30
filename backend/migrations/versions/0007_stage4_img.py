"""Stage 4 object storage metadata and image pipeline tables.

Adds:
- worldsim.asset_object   — binary asset envelope (S3-backed binary lives outside DB)
- worldsim.image_job      — ComfyUI image generation jobs with idempotency key
- worldsim.visual_profile — versioned visual style profiles (character/location/world)
- worldsim.gallery_item   — display record linking job → asset with QC metadata

Images are NEVER canonical and NEVER block phase execution (handbook 16 §2).

Revision ID: 0007_stage4_img
Revises: 0006_stage4_distributed_workers
Create Date: 2026-07-30
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_stage4_img"
down_revision: str | None = "0006_stage4_distributed_workers"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # asset_object
    # ------------------------------------------------------------------
    op.create_table(
        "asset_object",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("bucket", sa.Text(), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=False),
        sa.Column(
            "byte_size",
            sa.BigInteger(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("checksum_sha256", sa.Text(), nullable=False),
        sa.Column("width_px", sa.Integer(), nullable=True),
        sa.Column("height_px", sa.Integer(), nullable=True),
        sa.Column(
            "asset_class",
            sa.Text(),
            server_default=sa.text("'UNKNOWN'"),
            nullable=False,
        ),
        sa.Column("source_job_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            "extra_meta",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "byte_size >= 0",
            name=op.f("ck_asset_object_byte_size_nonneg"),
        ),
        sa.CheckConstraint(
            "status IN ('active', 'deleted', 'orphan')",
            name=op.f("ck_asset_object_status"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_asset_object_version_pos"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_asset_object_world_id_world"),
        ),
        sa.UniqueConstraint(
            "bucket",
            "object_key",
            name=op.f("uq_asset_object_bucket_object_key"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_asset_object")),
        schema="worldsim",
    )
    op.create_index(
        "ix_asset_object_world_class",
        "asset_object",
        ["world_id", "asset_class"],
        unique=False,
        schema="worldsim",
    )
    op.create_index(
        "ix_asset_object_job",
        "asset_object",
        ["source_job_id"],
        unique=False,
        schema="worldsim",
    )

    # ------------------------------------------------------------------
    # image_job
    # ------------------------------------------------------------------
    op.create_table(
        "image_job",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("source_event_id", sa.Uuid(), nullable=True),
        sa.Column("source_scene_id", sa.Uuid(), nullable=True),
        sa.Column(
            "asset_class",
            sa.Text(),
            server_default=sa.text("'EVENT_CG'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'queued'"),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.Integer(),
            server_default=sa.text("50"),
            nullable=False,
        ),
        sa.Column(
            "generation_number",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column(
            "attempt",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "max_attempts",
            sa.Integer(),
            server_default=sa.text("3"),
            nullable=False,
        ),
        sa.Column("workflow_profile_id", sa.Uuid(), nullable=True),
        sa.Column("workflow_version", sa.Text(), nullable=True),
        sa.Column("external_prompt_id", sa.Text(), nullable=True),
        sa.Column("seed", sa.BigInteger(), nullable=True),
        sa.Column("width_px", sa.Integer(), nullable=True),
        sa.Column("height_px", sa.Integer(), nullable=True),
        sa.Column(
            "prompt_spec",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "visual_profile_versions",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("error_class", sa.Text(), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('queued','running','succeeded','failed','rejected',"
            "'approved','cancelled','dead_letter')",
            name=op.f("ck_image_job_status"),
        ),
        sa.CheckConstraint(
            "priority >= 0 AND priority <= 100",
            name=op.f("ck_image_job_priority"),
        ),
        sa.CheckConstraint(
            "generation_number >= 1",
            name=op.f("ck_image_job_generation_number_pos"),
        ),
        sa.CheckConstraint(
            "attempt >= 0",
            name=op.f("ck_image_job_attempt_nonneg"),
        ),
        sa.CheckConstraint(
            "max_attempts >= 1",
            name=op.f("ck_image_job_max_attempts_pos"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_image_job_version_pos"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_image_job_world_id_world"),
        ),
        sa.UniqueConstraint(
            "world_id",
            "idempotency_key",
            name=op.f("uq_image_job_world_idempotency_key"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_image_job")),
        schema="worldsim",
    )
    op.create_index(
        "ix_image_job_world_status",
        "image_job",
        ["world_id", "status"],
        unique=False,
        schema="worldsim",
    )
    op.create_index(
        "ix_image_job_source_event",
        "image_job",
        ["source_event_id"],
        unique=False,
        schema="worldsim",
    )
    op.create_index(
        "ix_image_job_source_scene",
        "image_job",
        ["source_scene_id"],
        unique=False,
        schema="worldsim",
    )

    # ------------------------------------------------------------------
    # visual_profile
    # ------------------------------------------------------------------
    op.create_table(
        "visual_profile",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("subject_type", sa.Text(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column(
            "profile_version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column("valid_from_event_id", sa.Uuid(), nullable=True),
        sa.Column("supersedes_profile_id", sa.Uuid(), nullable=True),
        sa.Column(
            "style_spec",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "negative_constraints",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "reference_asset_ids",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "subject_type IN ('character', 'location', 'world')",
            name=op.f("ck_visual_profile_subject_type"),
        ),
        sa.CheckConstraint(
            "profile_version >= 1",
            name=op.f("ck_visual_profile_version_pos"),
        ),
        sa.CheckConstraint(
            "status IN ('active', 'superseded', 'draft')",
            name=op.f("ck_visual_profile_status"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_visual_profile_optimistic_version_pos"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_visual_profile_world_id_world"),
        ),
        sa.UniqueConstraint(
            "world_id",
            "subject_type",
            "subject_id",
            "profile_version",
            name=op.f("uq_visual_profile_world_subject_version"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_visual_profile")),
        schema="worldsim",
    )
    op.create_index(
        "ix_visual_profile_world_subject",
        "visual_profile",
        ["world_id", "subject_type", "subject_id"],
        unique=False,
        schema="worldsim",
    )
    op.create_index(
        "ix_visual_profile_world_subject_active",
        "visual_profile",
        ["world_id", "subject_type", "subject_id", "status"],
        unique=False,
        schema="worldsim",
    )

    # ------------------------------------------------------------------
    # gallery_item
    # ------------------------------------------------------------------
    op.create_table(
        "gallery_item",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("image_job_id", sa.Uuid(), nullable=False),
        sa.Column("asset_object_id", sa.Uuid(), nullable=False),
        sa.Column("source_event_id", sa.Uuid(), nullable=True),
        sa.Column("source_scene_id", sa.Uuid(), nullable=True),
        sa.Column(
            "asset_class",
            sa.Text(),
            server_default=sa.text("'EVENT_CG'"),
            nullable=False,
        ),
        sa.Column(
            "display_status",
            sa.Text(),
            server_default=sa.text("'auto_selected'"),
            nullable=False,
        ),
        sa.Column(
            "is_canonical_illustration",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "qc_passed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "qc_report",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "display_status IN ('auto_selected','user_selected','rejected','hidden','superseded')",
            name=op.f("ck_gallery_item_display_status"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_gallery_item_version_pos"),
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worldsim.world.id"],
            name=op.f("fk_gallery_item_world_id_world"),
        ),
        sa.ForeignKeyConstraint(
            ["image_job_id"],
            ["worldsim.image_job.id"],
            name=op.f("fk_gallery_item_image_job_id_image_job"),
        ),
        sa.ForeignKeyConstraint(
            ["asset_object_id"],
            ["worldsim.asset_object.id"],
            name=op.f("fk_gallery_item_asset_object_id_asset_object"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_gallery_item")),
        schema="worldsim",
    )
    op.create_index(
        "ix_gallery_item_world_event",
        "gallery_item",
        ["world_id", "source_event_id"],
        unique=False,
        schema="worldsim",
    )
    op.create_index(
        "ix_gallery_item_world_status",
        "gallery_item",
        ["world_id", "display_status"],
        unique=False,
        schema="worldsim",
    )
    op.create_index(
        "ix_gallery_item_job",
        "gallery_item",
        ["image_job_id"],
        unique=False,
        schema="worldsim",
    )


def downgrade() -> None:
    op.drop_index("ix_gallery_item_job", table_name="gallery_item", schema="worldsim")
    op.drop_index("ix_gallery_item_world_status", table_name="gallery_item", schema="worldsim")
    op.drop_index("ix_gallery_item_world_event", table_name="gallery_item", schema="worldsim")
    op.drop_table("gallery_item", schema="worldsim")

    op.drop_index(
        "ix_visual_profile_world_subject_active",
        table_name="visual_profile",
        schema="worldsim",
    )
    op.drop_index("ix_visual_profile_world_subject", table_name="visual_profile", schema="worldsim")
    op.drop_table("visual_profile", schema="worldsim")

    op.drop_index("ix_image_job_source_scene", table_name="image_job", schema="worldsim")
    op.drop_index("ix_image_job_source_event", table_name="image_job", schema="worldsim")
    op.drop_index("ix_image_job_world_status", table_name="image_job", schema="worldsim")
    op.drop_table("image_job", schema="worldsim")

    op.drop_index("ix_asset_object_job", table_name="asset_object", schema="worldsim")
    op.drop_index("ix_asset_object_world_class", table_name="asset_object", schema="worldsim")
    op.drop_table("asset_object", schema="worldsim")
