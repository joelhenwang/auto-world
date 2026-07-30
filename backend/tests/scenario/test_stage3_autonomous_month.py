"""Deterministic Stage 3 thirty-day scenario gate."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from tools.scenario_harness import load_scenario, run_stage3_thirty_day

from fictional_world.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = ROOT / "backend" / "alembic.ini"
PACK = ROOT / "seed" / "worlds" / "caldris-embervale-v1"
SCENARIO = ROOT / "backend" / "tests" / "fixtures" / "stage3_autonomous_month.toml"


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
    async with engine.begin() as connection:
        await connection.execute(text("TRUNCATE TABLE worldsim.world CASCADE"))
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield factory
    await engine.dispose()


@pytest.mark.scenario
@pytest.mark.integration
@pytest.mark.model_fake
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_stage3_autonomous_month(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    spec = load_scenario(SCENARIO)
    result = await run_stage3_thirty_day(
        lambda: SqlAlchemyUnitOfWork(uow_factory),
        pack_root=PACK,
        spec=spec,
    )

    assert result.passed, result.failures
    assert result.world_id is not None
    assert len([item for item in result.task_trace if item.startswith("day:")]) == 30
    assert any(item.startswith("month:") for item in result.task_trace)
    assert len(result.state_hashes) == 300
