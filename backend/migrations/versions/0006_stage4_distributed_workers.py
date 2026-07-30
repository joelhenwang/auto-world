"""Stage 4 distributed-worker registry and fencing tokens.

Adds:
- worldsim.host_registry   — physical/virtual machines
- worldsim.worker_registry — worker processes on each host
- worldsim.task_run.fencing_token (bigint) — monotonically-increasing
  claim counter; stale workers are rejected when the stored token has
  been superseded by a fresh claim.

Revision ID: 0006_stage4_distributed_workers
Revises: 0005_stage3_long_term_tables
Create Date: 2026-07-30
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_stage4_distributed_workers"
down_revision: str | None = "0005_stage3_long_term_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "host_registry",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("host_key", sa.Text(), nullable=False),
        sa.Column(
            "capabilities",
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
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('active', 'lost', 'decommissioned')",
            name=op.f("ck_host_registry_status"),
        ),
        sa.UniqueConstraint("host_key", name=op.f("uq_host_registry_host_key")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_host_registry")),
        schema="worldsim",
    )
    op.create_index(
        "ix_host_registry_status",
        "host_registry",
        ["status"],
        unique=False,
        schema="worldsim",
    )
    op.create_table(
        "worker_registry",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("host_id", sa.Uuid(), nullable=False),
        sa.Column("worker_key", sa.Text(), nullable=False),
        sa.Column(
            "capabilities",
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
            "heartbeat_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("drain_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_task_claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_draining",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('active', 'draining', 'drained', 'lost')",
            name=op.f("ck_worker_registry_status"),
        ),
        sa.ForeignKeyConstraint(
            ["host_id"],
            ["worldsim.host_registry.id"],
            name=op.f("fk_worker_registry_host_id_host_registry"),
        ),
        sa.UniqueConstraint("worker_key", name=op.f("uq_worker_registry_worker_key")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_worker_registry")),
        schema="worldsim",
    )
    op.create_index(
        "ix_worker_registry_host_status",
        "worker_registry",
        ["host_id", "status"],
        unique=False,
        schema="worldsim",
    )
    op.create_index(
        "ix_worker_registry_heartbeat",
        "worker_registry",
        ["status", "heartbeat_at"],
        unique=False,
        schema="worldsim",
    )
    op.add_column(
        "task_run",
        sa.Column(
            "fencing_token",
            sa.BigInteger(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        schema="worldsim",
    )


def downgrade() -> None:
    op.drop_column("task_run", "fencing_token", schema="worldsim")
    op.drop_index(
        "ix_worker_registry_heartbeat",
        table_name="worker_registry",
        schema="worldsim",
    )
    op.drop_index(
        "ix_worker_registry_host_status",
        table_name="worker_registry",
        schema="worldsim",
    )
    op.drop_table("worker_registry", schema="worldsim")
    op.drop_index(
        "ix_host_registry_status",
        table_name="host_registry",
        schema="worldsim",
    )
    op.drop_table("host_registry", schema="worldsim")
