"""Integration tests for S0-ORCH-001 budget ledger data operations."""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fictional_world.application.orchestration.budget import BudgetService, ReserveBudgetCommand
from fictional_world.domain.common.enums import BudgetStatus
from fictional_world.domain.common.errors import InvalidStateTransition
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
        await conn.execute(text("TRUNCATE TABLE worldsim.request_budget_ledger CASCADE"))
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield factory
    await engine.dispose()


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_reserve_consume_release_expire(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    now = datetime(2026, 7, 29, 16, 0, tzinfo=UTC)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        service = BudgetService(uow)
        first = await service.reserve(
            ReserveBudgetCommand(
                reservation_key="budget:phase:1",
                required_request_count=2,
                provider_kind="openrouter",
                model_slug="test/model",
                expires_at=now + timedelta(minutes=5),
            )
        )
        duplicate = await service.reserve(
            ReserveBudgetCommand(
                reservation_key="budget:phase:1",
                required_request_count=2,
                provider_kind="openrouter",
                model_slug="test/model",
                expires_at=now + timedelta(minutes=5),
            )
        )
        consumed = await service.consume(first.reservation.id, now=now)
        await uow.commit()
    assert first.already_existed is False
    assert duplicate.already_existed is True
    assert duplicate.reservation.id == first.reservation.id
    assert consumed.status is BudgetStatus.CONSUMED

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        service = BudgetService(uow)
        release_target = await service.reserve(
            ReserveBudgetCommand(
                reservation_key="budget:phase:2",
                required_request_count=1,
                provider_kind="openrouter",
                model_slug="test/model",
                expires_at=now + timedelta(minutes=5),
            )
        )
        released = await service.release(release_target.reservation.id)
        await uow.commit()
    assert released.status is BudgetStatus.RELEASED

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        service = BudgetService(uow)
        with pytest.raises(InvalidStateTransition):
            await service.consume(release_target.reservation.id, now=now)
        await uow.rollback()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        service = BudgetService(uow)
        await service.reserve(
            ReserveBudgetCommand(
                reservation_key="budget:phase:3",
                required_request_count=1,
                provider_kind="openrouter",
                model_slug="test/model",
                expires_at=now - timedelta(seconds=1),
            )
        )
        expired = await service.expire_due(now=now, limit=10)
        await uow.commit()
    assert len(expired) == 1
    assert expired[0].reservation_key == "budget:phase:3"
    assert expired[0].status is BudgetStatus.EXPIRED
