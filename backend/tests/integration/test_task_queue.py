"""Integration tests for S0-ORCH-001 task claim/lease/retry/dead-letter."""

from __future__ import annotations

import asyncio
import subprocess
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fictional_world.application.orchestration.task_queue import (
    CreateTaskCommand,
    TaskQueueService,
)
from fictional_world.domain.common.enums import TaskState
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
        await conn.execute(text("TRUNCATE TABLE worldsim.request_budget_ledger CASCADE"))
        await conn.execute(text("TRUNCATE TABLE worldsim.outbox_message CASCADE"))
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield factory
    await engine.dispose()


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_create_is_idempotent(uow_factory: async_sessionmaker[AsyncSession]) -> None:
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        service = TaskQueueService(uow)
        first = await service.create(
            CreateTaskCommand(task_type="demo", idempotency_key="task:demo:1")
        )
        second = await service.create(
            CreateTaskCommand(task_type="demo", idempotency_key="task:demo:1")
        )
        await uow.commit()
    assert first.already_existed is False
    assert second.already_existed is True
    assert first.task.id == second.task.id


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_two_workers_cannot_claim_same_task(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        service = TaskQueueService(uow)
        created = await service.create(
            CreateTaskCommand(task_type="race", idempotency_key="task:race:1", priority=10)
        )
        await uow.commit()
        task_id = created.task.id

    async def claim_as(worker: str) -> list[uuid.UUID]:
        async with SqlAlchemyUnitOfWork(uow_factory) as uow:
            service = TaskQueueService(uow)
            claimed = await service.claim(worker_id=worker, limit=1)
            await uow.commit()
            return [row.id for row in claimed]

    left, right = await asyncio.gather(claim_as("worker-a"), claim_as("worker-b"))
    winners = left + right
    assert len(winners) == 1
    assert winners[0] == task_id


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_dependency_blocks_claim_until_parent_succeeds(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    t0 = datetime(2026, 7, 29, 14, 0, tzinfo=UTC)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        service = TaskQueueService(uow)
        parent = await service.create(
            CreateTaskCommand(
                task_type="parent",
                idempotency_key="task:dep:parent",
                available_at=t0,
            )
        )
        child = await service.create(
            CreateTaskCommand(
                task_type="child",
                idempotency_key="task:dep:child",
                available_at=t0,
                depends_on=(parent.task.id,),
            )
        )
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        service = TaskQueueService(uow)
        claimed = await service.claim(worker_id="w1", now=t0, limit=5)
        assert [t.id for t in claimed] == [parent.task.id]
        await service.complete(parent.task.id, worker_id="w1", now=t0)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        service = TaskQueueService(uow)
        claimed = await service.claim(worker_id="w2", now=t0, limit=5)
        assert [t.id for t in claimed] == [child.task.id]
        await uow.commit()


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_expired_lease_can_be_reclaimed(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    t0 = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        service = TaskQueueService(uow)
        created = await service.create(
            CreateTaskCommand(
                task_type="expire",
                idempotency_key="task:expire:1",
                available_at=t0,
            )
        )
        claimed = await service.claim(
            worker_id="stale",
            lease_duration=timedelta(seconds=30),
            now=t0,
            limit=1,
        )
        assert len(claimed) == 1
        await uow.commit()

    later = t0 + timedelta(seconds=60)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        service = TaskQueueService(uow)
        reclaimed = await service.claim(
            worker_id="fresh",
            lease_duration=timedelta(seconds=90),
            now=later,
            limit=1,
        )
        await uow.commit()
    assert len(reclaimed) == 1
    assert reclaimed[0].id == created.task.id
    assert reclaimed[0].lease_owner == "fresh"


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_terminal_tasks_never_reclaimed(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    t0 = datetime(2026, 7, 29, 18, 0, tzinfo=UTC)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        service = TaskQueueService(uow)
        created = await service.create(
            CreateTaskCommand(
                task_type="done",
                idempotency_key="task:done:1",
                available_at=t0,
            )
        )
        claimed = await service.claim(worker_id="w1", now=t0, limit=1)
        assert len(claimed) == 1
        await service.complete(created.task.id, worker_id="w1", now=t0)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        service = TaskQueueService(uow)
        again = await service.claim(worker_id="w2", now=t0 + timedelta(hours=1), limit=1)
        await uow.commit()
    assert again == []


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_retry_then_dead_letter(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    t0 = datetime(2026, 7, 29, 19, 0, tzinfo=UTC)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        service = TaskQueueService(uow)
        created = await service.create(
            CreateTaskCommand(
                task_type="flaky",
                idempotency_key="task:flaky:1",
                max_attempts=2,
                available_at=t0,
            )
        )
        claimed = await service.claim(worker_id="w1", now=t0, limit=1)
        assert claimed[0].attempt_count == 1
        retried = await service.fail(
            created.task.id,
            worker_id="w1",
            error_code="boom",
            error_detail={"reason": "temp"},
            retry_delay=timedelta(seconds=0),
            now=t0,
        )
        assert retried.state is TaskState.PENDING
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        service = TaskQueueService(uow)
        claimed = await service.claim(worker_id="w1", now=t0, limit=1)
        assert claimed[0].attempt_count == 2
        dead = await service.fail(
            created.task.id,
            worker_id="w1",
            error_code="boom",
            error_detail={"reason": "fatal"},
            retry_delay=timedelta(seconds=0),
            now=t0,
        )
        await uow.commit()
    assert dead.state is TaskState.DEAD_LETTER
    assert dead.error_code == "boom"

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        service = TaskQueueService(uow)
        again = await service.claim(worker_id="w2", now=t0 + timedelta(hours=1), limit=1)
        await uow.commit()
    assert again == []


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_heartbeat_extends_lease(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    t0 = datetime(2026, 7, 29, 15, 0, tzinfo=UTC)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        service = TaskQueueService(uow)
        created = await service.create(
            CreateTaskCommand(task_type="hb", idempotency_key="task:hb:1", available_at=t0)
        )
        await service.claim(worker_id="w1", lease_duration=timedelta(seconds=30), now=t0, limit=1)
        beat = await service.heartbeat(
            created.task.id,
            worker_id="w1",
            lease_duration=timedelta(seconds=120),
            now=t0 + timedelta(seconds=10),
        )
        await uow.commit()
    assert beat.lease_expires_at == t0 + timedelta(seconds=130)
