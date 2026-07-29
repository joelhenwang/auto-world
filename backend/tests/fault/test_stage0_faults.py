"""Fault-injection coverage for Stage 0 gate (S0-QA-002)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fictional_world.application.orchestration.phase_runner import DeterministicPhaseRunner
from fictional_world.application.seed import import_caldris_stage0
from fictional_world.domain.phases.records import PhaseSnapshotRecord
from fictional_world.domain.phases.states import PhaseRunState
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


@pytest.mark.fault
@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_crash_after_snapshot_then_resume_no_duplicate_tick(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    """After commit-before-ack at snapshot boundary, resume must not duplicate WORLD_TICK."""

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        seeded = await import_caldris_stage0(uow, root=PACK)
        runner = DeterministicPhaseRunner(uow)
        paused = await runner.request_phase_advance(seeded.world_id, stop_after_snapshot=True)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        runner = DeterministicPhaseRunner(uow)
        resumed = await runner.resume_world(seeded.world_id)
        await uow.commit()
        events = await uow.events.list_for_world(seeded.world_id, limit=50)
        phase = await uow.phases.get(paused.phase_run_id)

    assert resumed is not None
    assert phase is not None
    assert PhaseRunState(phase.state) is PhaseRunState.COMPLETED
    ticks = [
        event
        for event in events
        if event.event_type == "WORLD_TICK"
        and event.structured_facts.get("absolute_phase_index") == 0
    ]
    assert len(ticks) == 1


@pytest.mark.fault
@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_snapshot_insert_once_is_idempotent(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        seeded = await import_caldris_stage0(uow, root=PACK)
        runner = DeterministicPhaseRunner(uow)
        result = await runner.request_phase_advance(seeded.world_id)
        await uow.commit()
        assert result.snapshot_id is not None
        first = await uow.snapshots.get(result.snapshot_id)
        assert first is not None
        # Re-insert with a different hash must return the sealed snapshot unchanged.
        again = await uow.snapshots.insert(
            PhaseSnapshotRecord(
                id=first.id,
                phase_run_id=first.phase_run_id,
                world_id=first.world_id,
                source_event_sequence=first.source_event_sequence,
                world_clock_version=first.world_clock_version,
                state_manifest={"tampered": True},
                state_hash="0" * 64,
                sealed_at=first.sealed_at,
                characters=(),
            )
        )
        await uow.commit()

    assert again.state_hash == first.state_hash
    assert again.state_manifest == first.state_manifest
    assert "tampered" not in again.state_manifest
