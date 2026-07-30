"""Integration tests for S4-ORCH-001 distributed workers.

Tests cover:
- Host/worker registration (idempotent upsert)
- Worker heartbeat
- Worker drain
- Reconciliation of abandoned leases
- Fencing token: stale worker cannot complete after lease superseded

Requires PostgreSQL via testcontainers.
"""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fictional_world.application.orchestration.reconcile import ReconcileAbandonedService
from fictional_world.application.orchestration.task_queue import (
    CreateTaskCommand,
    TaskQueueService,
)
from fictional_world.application.orchestration.worker_lifecycle import (
    RegisterWorkerCommand,
    WorkerLifecycleService,
)
from fictional_world.domain.common.errors import ConcurrencyConflict
from fictional_world.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = ROOT / "backend" / "alembic.ini"


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
        await conn.execute(text("TRUNCATE TABLE worldsim.task_run CASCADE"))
        await conn.execute(text("TRUNCATE TABLE worldsim.worker_registry CASCADE"))
        await conn.execute(text("TRUNCATE TABLE worldsim.host_registry CASCADE"))
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield factory
    await engine.dispose()


# ---------------------------------------------------------------------------
# Host / worker registration
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_register_worker_is_idempotent(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    now = datetime(2026, 7, 30, 10, 0, tzinfo=UTC)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        svc = WorkerLifecycleService(uow)
        r1 = await svc.register(
            RegisterWorkerCommand(
                host_key="host-1",
                worker_key="worker-1",
                host_capabilities=["gpu"],
                worker_capabilities=["embed"],
            ),
            now=now,
        )
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        svc = WorkerLifecycleService(uow)
        r2 = await svc.register(
            RegisterWorkerCommand(
                host_key="host-1",
                worker_key="worker-1",
                host_capabilities=["gpu"],
                worker_capabilities=["embed"],
            ),
            now=now + timedelta(seconds=5),
        )
        await uow.commit()

    assert r1.host.id == r2.host.id
    assert r1.worker.id == r2.worker.id
    assert r2.host_already_existed is True
    assert r2.worker_already_existed is True


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_worker_heartbeat(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    t0 = datetime(2026, 7, 30, 11, 0, tzinfo=UTC)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        svc = WorkerLifecycleService(uow)
        result = await svc.register(
            RegisterWorkerCommand(host_key="host-hb", worker_key="worker-hb"),
            now=t0,
        )
        await uow.commit()

    t1 = t0 + timedelta(seconds=30)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        svc = WorkerLifecycleService(uow)
        updated = await svc.heartbeat(result.worker.id, now=t1)
        await uow.commit()

    assert updated.heartbeat_at == t1
    assert updated.status == "active"


# ---------------------------------------------------------------------------
# Drain
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_worker_drain_transitions_status(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    t0 = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        svc = WorkerLifecycleService(uow)
        result = await svc.register(
            RegisterWorkerCommand(host_key="host-d", worker_key="worker-d"),
            now=t0,
        )
        await uow.commit()

    t1 = t0 + timedelta(minutes=1)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        svc = WorkerLifecycleService(uow)
        drained = await svc.drain(result.worker.id, now=t1)
        await uow.commit()

    assert drained.status == "draining"
    assert drained.drain_requested_at == t1


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_reconcile_resets_lost_worker_tasks(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    t0 = datetime(2026, 7, 30, 13, 0, tzinfo=UTC)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        # Register worker with key matching the worker_id used when claiming
        lifecycle = WorkerLifecycleService(uow)
        await lifecycle.register(
            RegisterWorkerCommand(
                host_key="host-r",
                worker_key="stale-worker",
            ),
            now=t0,
        )
        # Create and claim a task by that worker
        queue = TaskQueueService(uow)
        await queue.create(
            CreateTaskCommand(
                task_type="reconcile_test",
                idempotency_key="task:reconcile:1",
                available_at=t0,
            )
        )
        tasks = await queue.claim(
            worker_id="stale-worker",
            lease_duration=timedelta(seconds=90),
            now=t0,
            limit=1,
        )
        assert len(tasks) == 1
        await uow.commit()

    # Advance time past grace period without any heartbeat
    t_late = t0 + timedelta(minutes=10)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        reconciler = ReconcileAbandonedService(uow)
        result = await reconciler.reconcile(
            now=t_late,
            heartbeat_grace=timedelta(minutes=5),
        )
        await uow.commit()

    assert result.workers_marked_lost >= 1
    assert result.tasks_reset >= 1

    # Task should now be claimable again
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        queue = TaskQueueService(uow)
        reclaimed = await queue.claim(
            worker_id="fresh-worker",
            lease_duration=timedelta(seconds=90),
            now=t_late,
            limit=1,
        )
        await uow.commit()

    assert len(reclaimed) == 1
    assert reclaimed[0].lease_owner == "fresh-worker"


# ---------------------------------------------------------------------------
# Fencing token: stale worker cannot complete
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_stale_worker_cannot_complete_after_fencing_token_superseded(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    """S4-ORCH-001 core acceptance criterion.

    Scenario:
    1. Worker A claims task (fencing_token=1).
    2. Worker A's lease expires.
    3. Worker B reclaims the task (fencing_token=2).
    4. Worker A wakes up and tries to complete with its stale token (1).
       → Should be rejected with ConcurrencyConflict.
    5. Worker B completes with correct token (2).
       → Should succeed.
    """
    t0 = datetime(2026, 7, 30, 14, 0, tzinfo=UTC)
    lease_duration = timedelta(seconds=30)

    # Step 1: Worker A claims task
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        queue = TaskQueueService(uow)
        await queue.create(
            CreateTaskCommand(
                task_type="fence_test",
                idempotency_key="task:fence:1",
                available_at=t0,
            )
        )
        claimed_by_a = await queue.claim(
            worker_id="worker-a",
            lease_duration=lease_duration,
            now=t0,
            limit=1,
        )
        await uow.commit()

    assert len(claimed_by_a) == 1
    token_a = claimed_by_a[0].fencing_token
    assert token_a == 1  # first claim increments from 0 to 1
    task_id = claimed_by_a[0].id

    # Step 2 + 3: Lease expires, Worker B reclaims
    t_expired = t0 + timedelta(seconds=60)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        queue = TaskQueueService(uow)
        claimed_by_b = await queue.claim(
            worker_id="worker-b",
            lease_duration=timedelta(seconds=90),
            now=t_expired,
            limit=1,
        )
        await uow.commit()

    assert len(claimed_by_b) == 1
    token_b = claimed_by_b[0].fencing_token
    assert token_b == 2  # second claim increments to 2
    assert token_b > token_a

    # Step 4: Stale Worker A tries to complete with old token → REJECTED
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        queue = TaskQueueService(uow)
        with pytest.raises(ConcurrencyConflict):
            await queue.complete(
                task_id,
                worker_id="worker-b",  # correct owner but wrong token
                fencing_token=token_a,  # stale token
                now=t_expired + timedelta(seconds=1),
            )
        await uow.rollback()

    # Step 5: Worker B completes with correct token → SUCCESS
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        queue = TaskQueueService(uow)
        completed = await queue.complete(
            task_id,
            worker_id="worker-b",
            fencing_token=token_b,
            now=t_expired + timedelta(seconds=2),
        )
        await uow.commit()

    from fictional_world.domain.common.enums import TaskState

    assert completed.state is TaskState.SUCCEEDED


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_fencing_token_increments_on_each_claim(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Each re-claim should produce a strictly higher fencing token."""
    t0 = datetime(2026, 7, 30, 15, 0, tzinfo=UTC)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        queue = TaskQueueService(uow)
        await queue.create(
            CreateTaskCommand(
                task_type="token_increment",
                idempotency_key="task:incr:1",
                available_at=t0,
                max_attempts=10,
            )
        )
        c1 = await queue.claim(
            worker_id="w1",
            lease_duration=timedelta(seconds=1),
            now=t0,
            limit=1,
        )
        await uow.commit()

    t1 = t0 + timedelta(seconds=5)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        queue = TaskQueueService(uow)
        c2 = await queue.claim(
            worker_id="w2",
            lease_duration=timedelta(seconds=1),
            now=t1,
            limit=1,
        )
        await uow.commit()

    t2 = t1 + timedelta(seconds=5)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        queue = TaskQueueService(uow)
        c3 = await queue.claim(
            worker_id="w3",
            lease_duration=timedelta(seconds=90),
            now=t2,
            limit=1,
        )
        await uow.commit()

    assert c1[0].fencing_token == 1
    assert c2[0].fencing_token == 2
    assert c3[0].fencing_token == 3


# ---------------------------------------------------------------------------
# Migration round-trip
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_migration_0006_upgrade_downgrade_upgrade(
    postgres_container: dict[str, str],
) -> None:
    """Verify migration 0006 can upgrade, downgrade, and re-upgrade cleanly."""
    url = _normalize_url(postgres_container["url"])
    # already at head from the uow_factory fixture, but we test downgrade here
    _alembic(url, "downgrade", "0005_stage3_long_term_tables")
    _alembic(url, "upgrade", "head")
    # If we get here without exception the migration is clean.
