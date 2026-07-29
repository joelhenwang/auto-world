"""Stage 1 REST and WebSocket integration coverage."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fictional_world.application.seed import import_caldris_stage1
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
async def stage1_api(postgres_container: dict[str, str]):
    url = _normalize_url(postgres_container["url"])
    _alembic(url, "upgrade", "head")
    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.execute(text("TRUNCATE TABLE worldsim.world CASCADE"))
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with SqlAlchemyUnitOfWork(factory) as uow:
        seeded = await import_caldris_stage1(uow, root=PACK)
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
async def test_stage1_runtime_reads_and_player_commands(stage1_api) -> None:
    client, _app, world_id = stage1_api

    paused = await client.post(
        f"/api/v1/worlds/{world_id}/pause",
        json={"mode": "after_safe_boundary"},
    )
    assert paused.status_code == 200
    assert paused.json()["status"] == "paused"
    idle = await client.post(f"/api/v1/worlds/{world_id}/resume")
    assert idle.status_code == 200
    assert idle.json()["status"] == "idle"

    advance = await client.post(f"/api/v1/worlds/{world_id}/advance")
    assert advance.status_code == 200
    phase_id = advance.json()["phase_run_id"]
    assert advance.json()["phase_name"] == "dawn"

    timeline = await client.get(f"/api/v1/worlds/{world_id}/timeline")
    assert timeline.status_code == 200
    assert len(timeline.json()) == 1
    assert timeline.json()[0]["event_type"] == "scene.committed"

    scenes = await client.get(
        f"/api/v1/worlds/{world_id}/scenes",
        params={"phase_run_id": phase_id},
    )
    assert scenes.status_code == 200
    assert len(scenes.json()) == 1
    assert set(scenes.json()[0]["participant_ids"]) == {str(MIRA), str(DAIN)}
    assert scenes.json()[0]["canonical_summary"]
    assert "knowledge_scope_hash" not in scenes.text

    characters = await client.get(f"/api/v1/worlds/{world_id}/characters")
    assert characters.status_code == 200
    assert {item["name"] for item in characters.json()} == {
        "Mira Talren",
        "Dain Arcen",
    }
    assert all(
        set(item)
        == {
            "id",
            "name",
            "location_id",
            "life_status",
            "stamina",
            "energy",
            "pain",
            "stress",
            "active_activity_id",
            "state_version",
        }
        for item in characters.json()
    )
    assert "secret" not in characters.text.lower()
    assert "private_belief" not in characters.text.lower()

    acquire_payload = {
        "controller_id": "player-one",
        "idempotency_key": "control:mira:player-one",
    }
    acquire = await client.post(
        f"/api/v1/worlds/{world_id}/characters/{MIRA}/player/acquire",
        json=acquire_payload,
    )
    assert acquire.status_code == 200
    session_id = acquire.json()["id"]
    repeated_acquire = await client.post(
        f"/api/v1/worlds/{world_id}/characters/{MIRA}/player/acquire",
        json=acquire_payload,
    )
    assert repeated_acquire.json()["id"] == session_id
    denied = await client.post(
        f"/api/v1/worlds/{world_id}/characters/{MIRA}/player/acquire",
        json={
            "controller_id": "player-two",
            "idempotency_key": "control:mira:player-two",
        },
    )
    assert denied.status_code == 409

    invalid_action = await client.post(
        f"/api/v1/worlds/{world_id}/characters/{MIRA}/player/action",
        json={
            "session_id": session_id,
            "controller_id": "player-one",
            "idempotency_key": "action:mira:attack",
            "action_family": "attack",
            "description": "Attempt an out-of-scope action.",
        },
    )
    assert invalid_action.status_code == 422

    action_payload = {
        "session_id": session_id,
        "controller_id": "player-one",
        "idempotency_key": "action:mira:ask-dain",
        "action_family": "communicate",
        "description": "Ask Dain about the east bridge.",
        "utterance": "Is the bridge open?",
        "target_entity_ids": [str(DAIN)],
    }
    action = await client.post(
        f"/api/v1/worlds/{world_id}/characters/{MIRA}/player/action",
        json=action_payload,
    )
    assert action.status_code == 202
    assert action.json()["already_existed"] is False
    repeated_action = await client.post(
        f"/api/v1/worlds/{world_id}/characters/{MIRA}/player/action",
        json=action_payload,
    )
    assert repeated_action.status_code == 202
    assert repeated_action.json()["command_id"] == action.json()["command_id"]
    assert repeated_action.json()["already_existed"] is True

    release_payload = {
        "controller_id": "player-one",
        "session_id": session_id,
    }
    released = await client.post(
        f"/api/v1/worlds/{world_id}/characters/{MIRA}/player/release",
        json=release_payload,
    )
    assert released.status_code == 200
    assert released.json()["status"] == "released"
    repeated_release = await client.post(
        f"/api/v1/worlds/{world_id}/characters/{MIRA}/player/release",
        json=release_payload,
    )
    assert repeated_release.status_code == 200
    assert repeated_release.json()["status"] == "released"


@pytest.mark.integration
@pytest.mark.websocket
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_websocket_replays_from_sequence_and_pongs(stage1_api) -> None:
    client, app, world_id = stage1_api
    advance = await client.post(f"/api/v1/worlds/{world_id}/advance")
    assert advance.status_code == 200
    timeline = await client.get(f"/api/v1/worlds/{world_id}/timeline")
    sequence = timeline.json()[0]["sequence"]

    with TestClient(app) as sync_client:
        with sync_client.websocket_connect(
            f"/ws/v1/worlds/{world_id}?after_sequence=0"
        ) as websocket:
            event = websocket.receive_json()
            complete = websocket.receive_json()
            assert event["type"] == "stream_event"
            assert event["sequence"] == sequence
            assert complete == {
                "type": "replay_complete",
                "last_sequence": sequence,
            }
            websocket.send_json({"type": "ping"})
            assert websocket.receive_json() == {
                "type": "pong",
                "last_sequence": sequence,
            }

        with sync_client.websocket_connect(
            f"/ws/v1/worlds/{world_id}?after_sequence={sequence}"
        ) as websocket:
            assert websocket.receive_json() == {
                "type": "replay_complete",
                "last_sequence": sequence,
            }
