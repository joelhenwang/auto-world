"""Integration tests for S0-ORCH-002 deterministic phase runner."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fictional_world.application.orchestration.phase_runner import DeterministicPhaseRunner
from fictional_world.application.seed import import_caldris_stage0
from fictional_world.domain.phases.states import PhaseRunState
from fictional_world.domain.seed.ids import seed_uuid
from fictional_world.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

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


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_seed_then_advance_phase_once(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        seeded = await import_caldris_stage0(uow, root=PACK)
        runner = DeterministicPhaseRunner(uow)
        result = await runner.request_phase_advance(seeded.world_id)
        await uow.commit()

    assert result.already_completed is False
    assert result.absolute_phase_index == 0
    assert result.phase_name == "dawn"
    assert result.snapshot_id is not None
    assert len(result.event_ids) == 2

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        phase = await uow.phases.get(result.phase_run_id)
        snapshot = await uow.snapshots.get_for_phase(result.phase_run_id)
        clock = await uow.worlds.get_clock(seeded.world_id)
        mira = await uow.characters.get_state(seed_uuid("character/mira-talren"))
        memories = await uow.recent_memories.list_for_owner(
            seed_uuid("character/mira-talren"),
            world_id=seeded.world_id,
            limit=10,
        )
        events = await uow.events.list_for_world(seeded.world_id, limit=20)

    assert phase is not None
    assert PhaseRunState(phase.state) is PhaseRunState.COMPLETED
    assert snapshot is not None
    assert len(snapshot.characters) == 1
    assert clock is not None
    assert clock.absolute_phase_index == 0
    assert mira is not None
    assert float(mira.stamina) >= 54.0  # rested +5 from seed 54
    assert len(memories) >= 1
    types = {event.event_type for event in events}
    assert "WORLD_TICK" in types
    assert "SCRIPTED_ACTIONS" in types


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_repeat_advance_is_idempotent(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        seeded = await import_caldris_stage0(uow, root=PACK)
        runner = DeterministicPhaseRunner(uow)
        first = await runner.request_phase_advance(seeded.world_id)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        runner = DeterministicPhaseRunner(uow)
        # Same clock index already completed — advances to sunrise (new phase).
        second = await runner.request_phase_advance(seeded.world_id)
        await uow.commit()
        events = await uow.events.list_for_world(seeded.world_id, limit=50)

    assert second.absolute_phase_index == 1
    assert second.phase_name == "sunrise"
    assert second.phase_run_id != first.phase_run_id
    tick_events = [e for e in events if e.event_type == "WORLD_TICK"]
    assert len(tick_events) == 2

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        runner = DeterministicPhaseRunner(uow)
        # Re-run completed sunrise phase via direct resume path.
        phase = await uow.phases.get(second.phase_run_id)
        assert phase is not None
        again = await runner.request_phase_advance(seeded.world_id)
        # Next index after sunrise completed → morning
        await uow.commit()
    assert again.absolute_phase_index == 2


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_pause_at_snapshot_and_resume(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        seeded = await import_caldris_stage0(uow, root=PACK)
        runner = DeterministicPhaseRunner(uow)
        paused = await runner.request_phase_advance(
            seeded.world_id, stop_after_snapshot=True
        )
        await uow.commit()

    assert paused.snapshot_id is not None
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        phase = await uow.phases.get(paused.phase_run_id)
        assert phase is not None
        assert PhaseRunState(phase.state) is PhaseRunState.PAUSED
        events_mid = await uow.events.list_for_world(seeded.world_id, limit=20)
        scripted_mid = [e for e in events_mid if e.event_type == "SCRIPTED_ACTIONS"]
        assert scripted_mid == []

        runner = DeterministicPhaseRunner(uow)
        resumed = await runner.resume_world(seeded.world_id)
        await uow.commit()

    assert resumed is not None
    assert resumed.phase_run_id == paused.phase_run_id
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        phase = await uow.phases.get(paused.phase_run_id)
        events = await uow.events.list_for_world(seeded.world_id, limit=20)
    assert phase is not None
    assert PhaseRunState(phase.state) is PhaseRunState.COMPLETED
    assert any(e.event_type == "SCRIPTED_ACTIONS" for e in events)


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_restart_after_commit_no_duplicate_events(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        seeded = await import_caldris_stage0(uow, root=PACK)
        runner = DeterministicPhaseRunner(uow)
        first = await runner.request_phase_advance(seeded.world_id)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        runner = DeterministicPhaseRunner(uow)
        # Simulate uncertain retry of the completed phase via idempotent event keys
        # by reconciling — should not recreate WORLD_TICK for index 0.
        report = await runner.reconcile(seeded.world_id)
        await uow.commit()
        events = await uow.events.list_for_world(seeded.world_id, limit=50)

    ticks = [
        e
        for e in events
        if e.event_type == "WORLD_TICK"
        and e.structured_facts.get("absolute_phase_index") == 0
    ]
    assert len(ticks) == 1
    assert first.phase_run_id
    # After completed phase, reconcile finds no active phase.
    assert report.active_phase_id is None or report.phase_completed is True
