"""Integration tests: Stage 0 core schema constraints (S0-DB-002)."""

from __future__ import annotations

import subprocess
import uuid
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = ROOT / "backend" / "alembic.ini"


def _normalize_url(raw: str) -> str:
    return raw.replace("postgresql+psycopg2://", "postgresql+psycopg://").replace(
        "postgresql://", "postgresql+psycopg://"
    )


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


@pytest.fixture
async def migrated_engine(postgres_container: dict[str, str]) -> AsyncEngine:
    url = _normalize_url(postgres_container["url"])
    _alembic(url, "upgrade", "head")
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        # Isolate tests sharing the session-scoped container.
        await conn.execute(text("TRUNCATE TABLE worldsim.world CASCADE"))
    yield engine
    await engine.dispose()


async def _insert_world(
    conn,
    world_id: uuid.UUID,
    slug: str,
    status: str = "archived",
) -> None:
    params = {"id": world_id, "slug": slug, "name": slug, "status": status}
    if status == "ended":
        await conn.execute(
            text(
                """
                INSERT INTO worldsim.world
                  (id, slug, name, status, current_event_sequence, version, ended_at)
                VALUES
                  (:id, :slug, :name, :status, 0, 0, now())
                """
            ),
            params,
        )
        return
    await conn.execute(
        text(
            """
            INSERT INTO worldsim.world
              (id, slug, name, status, current_event_sequence, version)
            VALUES
              (:id, :slug, :name, :status, 0, 0)
            """
        ),
        params,
    )


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_core_tables_exist(migrated_engine: AsyncEngine) -> None:
    async with migrated_engine.connect() as conn:
        rows = await conn.execute(
            text(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'worldsim'
                ORDER BY table_name
                """
            )
        )
        names = {r[0] for r in rows.fetchall()}
    expected = {
        "aggregate_version",
        "character",
        "character_card_version",
        "character_state",
        "entity",
        "event_effect",
        "location",
        "model_call",
        "model_profile",
        "observation",
        "outbox_message",
        "phase_run",
        "phase_snapshot",
        "phase_snapshot_character",
        "recent_memory",
        "request_budget_ledger",
        "task_dependency",
        "task_run",
        "user_command",
        "world",
        "world_clock",
        "world_config",
        "world_event",
    }
    assert expected <= names


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_rejects_duplicate_phase_and_idempotency(migrated_engine: AsyncEngine) -> None:
    world_id = uuid.uuid4()
    async with migrated_engine.begin() as conn:
        await _insert_world(conn, world_id, f"w-{world_id.hex[:8]}")
        await conn.execute(
            text(
                """
                INSERT INTO worldsim.phase_run (
                  id, world_id, absolute_phase_index, phase_name, resolution_mode, state,
                  expected_character_count, idempotency_key
                ) VALUES (
                  :id, :world_id, 1, 'dawn', 'detailed', 'running', 2, :ikey
                )
                """
            ),
            {"id": uuid.uuid4(), "world_id": world_id, "ikey": f"phase-{world_id}-1"},
        )
        with pytest.raises(IntegrityError):
            await conn.execute(
                text(
                    """
                    INSERT INTO worldsim.phase_run (
                      id, world_id, absolute_phase_index, phase_name, resolution_mode, state,
                      expected_character_count, idempotency_key
                    ) VALUES (
                      :id, :world_id, 1, 'dawn', 'detailed', 'completed', 2, :ikey
                    )
                    """
                ),
                {"id": uuid.uuid4(), "world_id": world_id, "ikey": f"phase-{world_id}-dup-index"},
            )


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_rejects_duplicate_event_sequence_and_effect_index(
    migrated_engine: AsyncEngine,
) -> None:
    world_id = uuid.uuid4()
    event_id = uuid.uuid4()
    async with migrated_engine.begin() as conn:
        await _insert_world(conn, world_id, f"ev-{world_id.hex[:8]}")
        await conn.execute(
            text(
                """
                INSERT INTO worldsim.world_event (
                  id, world_id, sequence_number, absolute_phase_index, event_type,
                  canonical_summary, structured_facts, importance, visibility_class,
                  source_kind, idempotency_key, consistency_status
                ) VALUES (
                  :id, :world_id, 1, 0, 'WORLD_TICK', 'tick', '{}'::jsonb, 0.1, 'public',
                  'engine', :ikey, 'consistent'
                )
                """
            ),
            {"id": event_id, "world_id": world_id, "ikey": f"evt-{event_id}"},
        )

    async with migrated_engine.begin() as conn:
        with pytest.raises(IntegrityError):
            await conn.execute(
                text(
                    """
                    INSERT INTO worldsim.world_event (
                      id, world_id, sequence_number, absolute_phase_index, event_type,
                      canonical_summary, structured_facts, importance, visibility_class,
                      source_kind, idempotency_key, consistency_status
                    ) VALUES (
                      :id, :world_id, 1, 0, 'WORLD_TICK', 'dup', '{}'::jsonb, 0.1, 'public',
                      'engine', :ikey, 'consistent'
                    )
                    """
                ),
                {"id": uuid.uuid4(), "world_id": world_id, "ikey": f"evt-dup-{uuid.uuid4()}"},
            )

    async with migrated_engine.begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO worldsim.event_effect (
                  id, world_event_id, effect_index, effect_type, effect_payload,
                  previous_state, resulting_state, validation_manifest
                ) VALUES (
                  :id, :eid, 0, 'wait', '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb
                )
                """
            ),
            {"id": uuid.uuid4(), "eid": event_id},
        )

    async with migrated_engine.begin() as conn:
        with pytest.raises(IntegrityError):
            await conn.execute(
                text(
                    """
                    INSERT INTO worldsim.event_effect (
                      id, world_event_id, effect_index, effect_type, effect_payload,
                      previous_state, resulting_state, validation_manifest
                    ) VALUES (
                      :id, :eid, 0, 'wait', '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb
                    )
                    """
                ),
                {"id": uuid.uuid4(), "eid": event_id},
            )


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_rejects_invalid_resource_ranges(migrated_engine: AsyncEngine) -> None:
    world_id = uuid.uuid4()
    entity_id = uuid.uuid4()
    card_id = uuid.uuid4()
    async with migrated_engine.begin() as conn:
        await _insert_world(conn, world_id, f"rng-{world_id.hex[:8]}")
        await conn.execute(
            text(
                """
                INSERT INTO worldsim.entity
                  (id, world_id, entity_type, canonical_name, normalized_name, lifecycle_status)
                VALUES
                  (:id, :world_id, 'character', 'Alex', 'alex', 'active')
                """
            ),
            {"id": entity_id, "world_id": world_id},
        )
        await conn.execute(
            text(
                """
                INSERT INTO worldsim.character (entity_id, character_kind, species_code, version)
                VALUES (:id, 'focus', 'human', 0)
                """
            ),
            {"id": entity_id},
        )
        await conn.execute(
            text(
                """
                INSERT INTO worldsim.character_card_version (
                  id, character_id, version_number, identity, backstory, appearance,
                  personality_traits, values, fears, desires, boundaries, voice_profile,
                  initial_capabilities, secret_manifest, change_summary, content_hash
                ) VALUES (
                  :id, :cid, 1, '{}'::jsonb, '', '{}'::jsonb, '{}'::jsonb, '{}'::jsonb,
                  '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb,
                  '{}'::jsonb, 'v1', 'hash1'
                )
                """
            ),
            {"id": card_id, "cid": entity_id},
        )
        with pytest.raises(IntegrityError):
            await conn.execute(
                text(
                    """
                    INSERT INTO worldsim.character_state (
                      character_id, life_status, stamina, mana, energy, hunger, pain, stress,
                      social_need, valence, arousal, dominance, current_card_version_id, version
                    ) VALUES (
                      :cid, 'alive', :stamina, 50, 50, 50, 0, 0, 50, 0, 0, 0, :card, 0
                    )
                    """
                ),
                {"cid": entity_id, "stamina": Decimal("150.00"), "card": card_id},
            )


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_rejects_duplicate_user_command_idempotency(migrated_engine: AsyncEngine) -> None:
    world_id = uuid.uuid4()
    key = f"cmd-{uuid.uuid4()}"
    async with migrated_engine.begin() as conn:
        await _insert_world(conn, world_id, f"cmd-{world_id.hex[:8]}")
        await conn.execute(
            text(
                """
                INSERT INTO worldsim.user_command (
                  id, world_id, actor_role, command_type, payload, idempotency_key,
                  permission_decision, status
                ) VALUES (
                  :id, :world_id, 'director', 'pause', '{}'::jsonb, :key, 'allowed', 'accepted'
                )
                """
            ),
            {"id": uuid.uuid4(), "world_id": world_id, "key": key},
        )
        with pytest.raises(IntegrityError):
            await conn.execute(
                text(
                    """
                    INSERT INTO worldsim.user_command (
                      id, world_id, actor_role, command_type, payload, idempotency_key,
                      permission_decision, status
                    ) VALUES (
                      :id, :world_id, 'director', 'pause', '{}'::jsonb, :key, 'allowed', 'accepted'
                    )
                    """
                ),
                {"id": uuid.uuid4(), "world_id": world_id, "key": key},
            )


@pytest.mark.integration
@pytest.mark.migration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_alembic_head_is_0005(postgres_container: dict[str, str]) -> None:
    url = _normalize_url(postgres_container["url"])
    heads = _alembic(url, "heads").stdout.strip().splitlines()
    assert len(heads) == 1
    assert "0006_stage4_distributed_workers" in heads[0]
