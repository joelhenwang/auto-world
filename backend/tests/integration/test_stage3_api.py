"""Stage 3 REST API integration coverage (read projections)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fictional_world.application.seed import import_caldris_stage2
from fictional_world.config.settings import AppSettings
from fictional_world.domain.seed.ids import seed_uuid
from fictional_world.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from fictional_world.interfaces.http.app import create_app

ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = ROOT / "backend" / "alembic.ini"
PACK = ROOT / "seed" / "worlds" / "caldris-embervale-v1"
MIRA = seed_uuid("character/mira-talren")
DAIN = seed_uuid("character/dain-arcen")


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
async def stage3_api(postgres_container: dict[str, str]):
    url = _normalize_url(postgres_container["url"])
    _alembic(url, "upgrade", "head")
    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.execute(text("TRUNCATE TABLE worldsim.world CASCADE"))
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with SqlAlchemyUnitOfWork(factory) as uow:
        seeded = await import_caldris_stage2(uow, root=PACK)
        await uow.commit()
    app = create_app(settings=AppSettings(), engine=engine)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, app, seeded.world_id
    await engine.dispose()


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_stage3_month_runs_memories_arcs_factions_exports(stage3_api) -> None:
    client, _app, world_id = stage3_api

    month_runs = await client.get(f"/api/v1/worlds/{world_id}/month-runs")
    assert month_runs.status_code == 200
    assert month_runs.json() == []

    mira_memories = await client.get(f"/api/v1/worlds/{world_id}/characters/{MIRA}/memories")
    assert mira_memories.status_code == 200
    assert mira_memories.json() == []
    assert all(item["owner_character_id"] == str(MIRA) for item in mira_memories.json())

    dain_memories = await client.get(f"/api/v1/worlds/{world_id}/characters/{DAIN}/memories")
    assert dain_memories.status_code == 200
    assert all(item["owner_character_id"] == str(DAIN) for item in dain_memories.json())

    arcs = await client.get(f"/api/v1/worlds/{world_id}/arcs")
    assert arcs.status_code == 200
    assert arcs.json() == []

    factions = await client.get(f"/api/v1/worlds/{world_id}/factions")
    assert factions.status_code == 200
    assert factions.json() == []

    exports = await client.get(f"/api/v1/worlds/{world_id}/exports")
    assert exports.status_code == 200
    assert exports.json() == {"items": []}

    # Stage 2 day-progress remains available (additive Stage 3 routes).
    progress = await client.get(f"/api/v1/worlds/{world_id}/day-progress")
    assert progress.status_code == 200
    assert progress.json()["day_index"] == 0
