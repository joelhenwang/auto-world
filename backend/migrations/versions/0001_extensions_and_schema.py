"""Create pgvector/pgcrypto extensions and worldsim schema.

Revision ID: 0001_extensions_and_schema
Revises:
Create Date: 2026-07-29
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0001_extensions_and_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE SCHEMA IF NOT EXISTS worldsim")


def downgrade() -> None:
    # Extensions are shared; leave them installed. Drop only our schema if empty.
    op.execute("DROP SCHEMA IF EXISTS worldsim CASCADE")
