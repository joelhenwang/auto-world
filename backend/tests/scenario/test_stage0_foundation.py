"""Stage 0 foundation scenario gate (S0-QA-002)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from tools.scenario_harness import load_scenario, run_stage0_foundation

from fictional_world.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = ROOT / "backend" / "alembic.ini"
PACK = ROOT / "seed" / "worlds" / "caldris-embervale-v1"
SCENARIO = ROOT / "backend" / "tests" / "fixtures" / "stage0_foundation.toml"


def _normalize_url(raw: str) -> str:
    return raw.replace("postgresql+psycopg2://", "postgresql+psycopg://").replace(
        "postgresql://", "postgresql+psycopg://"
    )


def _alembic(url: str, *args: str) -> None:
    env = {**dict(__import__("os").environ), "ALEMBIC_DATABASE_URL": url}
    subprocess.run(
        ["uv", "run", "alembic", "-c", str(ALEMBIC_INI), *args],
        cwd=ROOT,
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )


@pytest.fixture
async def uow_factory(
    postgres_container: dict[str, str],
) -> async_sessionmaker[AsyncSession]:
    url = _normalize_url(postgres_container["url"])
    _alembic(url, "upgrade", "head")
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE worldsim.world CASCADE"))
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield factory
    await engine.dispose()


@pytest.mark.scenario
@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_stage0_foundation_scenario(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    spec = load_scenario(SCENARIO)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        result = await run_stage0_foundation(uow, pack_root=PACK, spec=spec)
    assert result.passed, result.failures
    assert result.world_id is not None
    assert "WORLD_SEEDED" in result.event_timeline
    assert any(item.startswith("advance:0:dawn") for item in result.task_trace)
