"""Integration tests for S0-ORCH-001 outbox claim/dispatch."""

from __future__ import annotations

import subprocess
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fictional_world.application.orchestration.outbox_dispatcher import OutboxDispatcher
from fictional_world.domain.common.enums import OutboxState
from fictional_world.domain.events.persistence import OutboxMessageRecord
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
        await conn.execute(text("TRUNCATE TABLE worldsim.outbox_message CASCADE"))
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield factory
    await engine.dispose()


def _pending(key: str, *, available_at: datetime) -> OutboxMessageRecord:
    return OutboxMessageRecord(
        id=uuid.uuid4(),
        message_type="event.committed",
        payload={"event_id": key},
        idempotency_key=key,
        state=OutboxState.PENDING.value,
        attempt_count=0,
        available_at=available_at,
    )


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_outbox_claim_dispatch_and_idempotent_complete(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    now = datetime(2026, 7, 29, 11, 0, tzinfo=UTC)
    seen: list[str] = []

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await uow.outbox.insert(_pending("outbox:a", available_at=now))
        await uow.outbox.insert(_pending("outbox:b", available_at=now))
        await uow.commit()

    async def handler(message: OutboxMessageRecord) -> None:
        # At-least-once consumers must tolerate duplicate delivery by key.
        if message.idempotency_key in seen:
            return
        seen.append(message.idempotency_key)

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        dispatcher = OutboxDispatcher(uow)
        result = await dispatcher.dispatch_once(
            worker_id="consumer-1",
            handler=handler,
            now=now,
            limit=10,
        )
        # Simulate at-least-once re-ack after uncertain commit.
        for message_id in result.completed_ids:
            again = await dispatcher.complete(message_id, worker_id="consumer-1", now=now)
            assert again.state == OutboxState.COMPLETED.value
        await uow.commit()

    assert sorted(seen) == ["outbox:a", "outbox:b"]

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        dispatcher = OutboxDispatcher(uow)
        empty = await dispatcher.claim(worker_id="consumer-2", now=now, limit=10)
        await uow.commit()
    assert empty == []


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_outbox_expired_claim_reclaimed(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    t0 = datetime(2026, 7, 29, 10, 0, tzinfo=UTC)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await uow.outbox.insert(_pending("outbox:expire", available_at=t0))
        dispatcher = OutboxDispatcher(uow)
        first = await dispatcher.claim(
            worker_id="slow",
            lease_duration=timedelta(seconds=10),
            now=t0,
            limit=1,
        )
        await uow.commit()
    assert len(first) == 1

    later = t0 + timedelta(seconds=30)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        dispatcher = OutboxDispatcher(uow)
        second = await dispatcher.claim(
            worker_id="fast",
            lease_duration=timedelta(seconds=60),
            now=later,
            limit=1,
        )
        await uow.commit()
    assert len(second) == 1
    assert second[0].idempotency_key == "outbox:expire"
    assert second[0].claimed_by == "fast"
    assert second[0].attempt_count == 2
