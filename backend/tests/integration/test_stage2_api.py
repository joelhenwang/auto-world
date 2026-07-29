"""Stage 2 REST API integration coverage."""

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
MIRA_PRIVATE_BELIEF_SNIPPET = "father's disappearance"


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
async def stage2_api(postgres_container: dict[str, str]):
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
async def test_stage2_day_progress_beliefs_isolation_and_run_day(stage2_api) -> None:
    client, _app, world_id = stage2_api

    progress = await client.get(f"/api/v1/worlds/{world_id}/day-progress")
    assert progress.status_code == 200
    body = progress.json()
    assert body["day_index"] == 0
    assert body["phase_name"] == "dawn"
    assert body["completed_day_count"] == 0
    assert body["day_run"] is None

    map_state = await client.get(f"/api/v1/worlds/{world_id}/map")
    assert map_state.status_code == 200
    assert len(map_state.json()["locations"]) >= 4
    assert len(map_state.json()["routes"]) >= 1

    mira_beliefs = await client.get(f"/api/v1/worlds/{world_id}/characters/{MIRA}/beliefs")
    assert mira_beliefs.status_code == 200
    mira_texts = " ".join(item["belief_text"] for item in mira_beliefs.json())
    assert MIRA_PRIVATE_BELIEF_SNIPPET in mira_texts
    assert all(item["character_id"] == str(MIRA) for item in mira_beliefs.json())

    dain_beliefs = await client.get(f"/api/v1/worlds/{world_id}/characters/{DAIN}/beliefs")
    assert dain_beliefs.status_code == 200
    dain_payload = dain_beliefs.text.casefold()
    assert MIRA_PRIVATE_BELIEF_SNIPPET.casefold() not in dain_payload
    assert "falsified north-route" not in dain_payload
    assert all(item["character_id"] == str(DAIN) for item in dain_beliefs.json())

    detail = await client.get(f"/api/v1/worlds/{world_id}/characters/{MIRA}")
    assert detail.status_code == 200
    assert detail.json()["name"]
    assert "goals" in detail.json()
    assert "secret_manifest" not in detail.text

    denied = await client.get(f"/api/v1/worlds/{world_id}/director", params={"mode": "player"})
    assert denied.status_code == 403
    allowed = await client.get(
        f"/api/v1/worlds/{world_id}/director",
        headers={"X-Observer-Mode": "watcher"},
    )
    assert allowed.status_code == 200
    assert "hooks" in allowed.json()
    assert "metrics" in allowed.json()

    failures = await client.get(f"/api/v1/worlds/{world_id}/tasks/failures")
    assert failures.status_code == 200
    assert failures.json() == []

    run_day = await client.post(f"/api/v1/worlds/{world_id}/run-day")
    assert run_day.status_code == 200, run_day.text
    day_body = run_day.json()
    assert day_body["day_index"] == 0
    assert day_body["day_run_id"] is not None
    assert len(day_body["phase_results"]) == 10

    after = await client.get(f"/api/v1/worlds/{world_id}/day-progress")
    assert after.status_code == 200
    assert after.json()["completed_day_count"] >= 1

    diaries = await client.get(f"/api/v1/worlds/{world_id}/characters/{MIRA}/diaries")
    assert diaries.status_code == 200
    assert len(diaries.json()["diaries"]) >= 1

    dain_diaries = await client.get(f"/api/v1/worlds/{world_id}/characters/{DAIN}/diaries")
    assert dain_diaries.status_code == 200
    assert MIRA_PRIVATE_BELIEF_SNIPPET.casefold() not in dain_diaries.text.casefold()

    advance = await client.post(f"/api/v1/worlds/{world_id}/advance")
    assert advance.status_code == 200
    assert advance.json()["phase_name"]
