"""Integration tests for S0-DB-001 Alembic baseline."""

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
async def test_alembic_baseline_empty_upgrade(postgres_container: dict[str, str]) -> None:
    # testcontainers URL is typically postgresql+psycopg2://... — normalize to psycopg3
    raw = postgres_container["url"]
    url = raw.replace("postgresql+psycopg2://", "postgresql+psycopg://").replace(
        "postgresql://", "postgresql+psycopg://"
    )
    heads = _alembic(url, "heads").stdout.strip().splitlines()
    assert len(heads) == 1
    assert "0001_extensions_and_schema" in heads[0]

    _alembic(url, "upgrade", "head")
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        ext = await conn.execute(
            text("SELECT extname FROM pg_extension WHERE extname IN ('vector', 'pgcrypto')")
        )
        names = {row[0] for row in ext.fetchall()}
        assert "vector" in names
        assert "pgcrypto" in names
        schema = await conn.execute(
            text(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'worldsim'"
            )
        )
        assert schema.first() is not None
        # vector type usable
        await conn.execute(text("SELECT '[1,2,3]'::vector"))
    await engine.dispose()

    _alembic(url, "downgrade", "-1")
    _alembic(url, "upgrade", "head")
