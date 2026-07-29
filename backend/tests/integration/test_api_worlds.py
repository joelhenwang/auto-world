"""Integration tests for Stage 0 HTTP API (S0-API-001)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fictional_world.application.seed import import_caldris_stage0
from fictional_world.config.settings import AppSettings
from fictional_world.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from fictional_world.interfaces.http.app import create_app

ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = ROOT / "backend" / "alembic.ini"
PACK = ROOT / "seed" / "worlds" / "caldris-embervale-v1"


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
async def api_client(postgres_container: dict[str, str]):
    url = _normalize_url(postgres_container["url"])
    _alembic(url, "upgrade", "head")
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE worldsim.world CASCADE"))
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with SqlAlchemyUnitOfWork(factory) as uow:
        seeded = await import_caldris_stage0(uow, root=PACK)
        await uow.commit()

    settings = AppSettings()
    app = create_app(settings=settings, engine=engine)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, seeded.world_id
    await engine.dispose()


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_world_reads_and_advance(api_client) -> None:
    client, world_id = api_client
    world = await client.get(f"/worlds/{world_id}")
    assert world.status_code == 200
    assert world.json()["slug"]

    clock = await client.get(f"/worlds/{world_id}/clock")
    assert clock.status_code == 200
    assert clock.json()["phase_name"] == "dawn"
    assert clock.json()["absolute_phase_index"] == 0

    advance = await client.post(f"/worlds/{world_id}/commands/advance-phase")
    assert advance.status_code == 200
    body = advance.json()
    assert body["absolute_phase_index"] == 0
    assert body["phase_name"] == "dawn"
    assert body["snapshot_id"] is not None
    assert len(body["event_ids"]) == 2

    events = await client.get(f"/worlds/{world_id}/events")
    assert events.status_code == 200
    types = {row["event_type"] for row in events.json()}
    assert "WORLD_TICK" in types
    assert "SCRIPTED_ACTIONS" in types

    phase = await client.get(f"/worlds/{world_id}/phases/0")
    assert phase.status_code == 200
    assert phase.json()["state"] == "completed"

    # Second advance moves calendar.
    again = await client.post(f"/worlds/{world_id}/commands/advance-phase")
    assert again.status_code == 200
    assert again.json()["absolute_phase_index"] == 1
    assert again.json()["phase_name"] == "sunrise"


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_missing_world_404(api_client) -> None:
    client, _world_id = api_client
    missing = "00000000-0000-0000-0000-000000000099"
    response = await client.get(f"/worlds/{missing}")
    assert response.status_code == 404
