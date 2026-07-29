"""End-to-end Stage 1 dawn → morning → evening orchestration tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fictional_world.application.orchestration.phase_runner import DeterministicPhaseRunner
from fictional_world.application.seed import import_caldris_stage1
from fictional_world.domain.common.enums import BudgetStatus
from fictional_world.domain.phases.states import PhaseRunState
from fictional_world.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from fictional_world.testing import Stage1FakeModelGateway

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
    async with engine.begin() as connection:
        await connection.execute(text("TRUNCATE TABLE worldsim.world CASCADE"))
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield factory
    await engine.dispose()


@pytest.mark.integration
@pytest.mark.scenario
@pytest.mark.model_fake
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_stage1_first_day_uses_sealed_snapshots_and_restart_safe_tasks(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        seeded = await import_caldris_stage1(uow, root=PACK)
        await uow.commit()

    results = []
    call_count = 0
    for _ in range(3):
        async with SqlAlchemyUnitOfWork(uow_factory) as uow:

            def assert_no_open_transaction() -> None:
                assert uow.session is not None
                assert not uow.session.in_transaction()

            gateway = Stage1FakeModelGateway(before_generate=assert_no_open_transaction)
            runner = DeterministicPhaseRunner(
                uow,
                model_gateway=gateway,
                stage1=True,
            )
            results.append(await runner.request_phase_advance(seeded.world_id))
            call_count += len(gateway.calls)
            await uow.commit()

    assert [result.phase_name for result in results] == ["dawn", "morning", "evening"]
    assert [result.absolute_phase_index for result in results] == [0, 2, 7]
    assert all(len(result.event_ids) == 2 for result in results)
    assert call_count == 10

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        assert uow.session is not None
        clock = await uow.worlds.get_clock(seeded.world_id)
        assert clock is not None
        assert clock.phase_name == "evening"
        assert clock.absolute_phase_index == 7

        for result in results:
            phase = await uow.phases.get(result.phase_run_id)
            snapshot = await uow.snapshots.get_for_phase(result.phase_run_id)
            proposals = await uow.action_proposals.list_for_phase(result.phase_run_id)
            scenes = await uow.scenes.list_for_phase(result.phase_run_id)
            assert phase is not None
            assert PhaseRunState(phase.state) is PhaseRunState.COMPLETED
            assert phase.expected_character_count == 2
            assert phase.completed_character_count == 2
            assert phase.completed_scene_count == phase.expected_scene_count == 1
            assert phase.request_reservation_id is not None
            reservation = await uow.budgets.get(phase.request_reservation_id)
            assert reservation is not None
            assert reservation.status is BudgetStatus.CONSUMED
            assert snapshot is not None
            assert len(snapshot.characters) == 2
            assert len(proposals) == 2
            assert {proposal.snapshot_id for proposal in proposals} == {snapshot.id}
            assert len(scenes) == 1
            assert scenes[0].snapshot_id == snapshot.id
            assert len(scenes[0].participants) == 2
            scope_hashes = {
                participant.knowledge_scope_hash for participant in scenes[0].participants
            }
            assert None not in scope_hashes
            assert len(scope_hashes) == 2

        counts = (
            await uow.session.execute(
                text(
                    """
                    SELECT
                      (SELECT count(*) FROM worldsim.phase_run),
                      (SELECT count(*) FROM worldsim.phase_snapshot),
                      (SELECT count(*) FROM worldsim.action_proposal),
                      (SELECT count(*) FROM worldsim.scene),
                      (SELECT count(*) FROM worldsim.reaction_proposal),
                      (SELECT count(*) FROM worldsim.scene_resolution),
                      (SELECT count(*) FROM worldsim.scene_run),
                      (SELECT count(*) FROM worldsim.stream_event),
                      (SELECT count(*) FROM worldsim.observation),
                      (SELECT count(*) FROM worldsim.recent_memory),
                      (SELECT count(*) FROM worldsim.task_run WHERE state = 'succeeded')
                    """
                )
            )
        ).one()
        # Two deterministic OBSERVE effects add focused observations beyond the
        # six participant-scoped scene observations.
        assert tuple(counts) == (3, 3, 6, 3, 3, 3, 3, 3, 8, 6, 30)


@pytest.mark.integration
@pytest.mark.model_fake
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_stage1_pause_after_snapshot_resumes_same_phase(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        seeded = await import_caldris_stage1(uow, root=PACK)
        paused = await DeterministicPhaseRunner(
            uow,
            model_gateway=Stage1FakeModelGateway(),
            stage1=True,
        ).request_phase_advance(seeded.world_id, stop_after_snapshot=True)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        phase = await uow.phases.get(paused.phase_run_id)
        assert phase is not None
        assert PhaseRunState(phase.state) is PhaseRunState.PAUSED
        gateway = Stage1FakeModelGateway()
        resumed = await DeterministicPhaseRunner(
            uow,
            model_gateway=gateway,
            stage1=True,
        ).resume_world(seeded.world_id)
        await uow.commit()

    assert resumed is not None
    assert resumed.phase_run_id == paused.phase_run_id
    assert resumed.snapshot_id == paused.snapshot_id
    assert resumed.phase_name == "dawn"
    assert len(gateway.calls) == 3

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        proposals = await uow.action_proposals.list_for_phase(paused.phase_run_id)
        events = await uow.events.list_for_world(seeded.world_id, limit=20)
        assert len(proposals) == 2
        dawn_ticks = [
            event
            for event in events
            if event.event_type == "WORLD_TICK"
            and event.absolute_phase_index == paused.absolute_phase_index
        ]
        assert len(dawn_ticks) == 1
