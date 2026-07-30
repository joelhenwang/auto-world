"""Integration tests for migration 0007 — image/storage tables (S4-STORAGE-001)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = ROOT / "backend" / "alembic.ini"


def _alembic(url: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**dict(__import__("os").environ), "ALEMBIC_DATABASE_URL": url}
    return subprocess.run(
        ["uv", "run", "alembic", "-c", str(ALEMBIC_INI), *args],
        cwd=ROOT,
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )


@pytest.mark.integration
@pytest.mark.migration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_migration_0007_adds_image_tables(postgres_container: dict[str, str]) -> None:
    raw = postgres_container["url"]
    url = raw.replace("postgresql+psycopg2://", "postgresql+psycopg://").replace(
        "postgresql://", "postgresql+psycopg://"
    )
    _alembic(url, "upgrade", "head")

    engine = create_async_engine(url)
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'worldsim' "
                "AND table_name IN ('asset_object','image_job','visual_profile','gallery_item')"
            )
        )
        tables = {row[0] for row in result.fetchall()}
        assert tables == {"asset_object", "image_job", "visual_profile", "gallery_item"}

        # Verify idempotency_key uniqueness constraint exists on image_job
        result = await conn.execute(
            text(
                "SELECT constraint_name FROM information_schema.table_constraints "
                "WHERE table_schema = 'worldsim' AND table_name = 'image_job' "
                "AND constraint_type = 'UNIQUE'"
            )
        )
        constraint_names = {row[0] for row in result.fetchall()}
        assert any("idempotency_key" in name for name in constraint_names)

        # Verify visual_profile unique constraint
        result = await conn.execute(
            text(
                "SELECT constraint_name FROM information_schema.table_constraints "
                "WHERE table_schema = 'worldsim' AND table_name = 'visual_profile' "
                "AND constraint_type = 'UNIQUE'"
            )
        )
        vp_constraints = {row[0] for row in result.fetchall()}
        assert len(vp_constraints) >= 1

    await engine.dispose()

    # Verify roundtrip downgrade/upgrade
    _alembic(url, "downgrade", "-1")
    _alembic(url, "upgrade", "head")
    await engine.dispose()
