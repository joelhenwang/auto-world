"""Async engine and session factory (handbook ``19`` §10)."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from fictional_world.config.settings import DatabaseSettings


def database_url(settings: DatabaseSettings) -> str:
    """Build a Psycopg 3 async SQLAlchemy URL."""

    return (
        f"postgresql+psycopg://{settings.user}:{settings.password}"
        f"@{settings.host}:{settings.port}/{settings.name}"
    )


def create_engine(settings: DatabaseSettings, *, echo: bool = False) -> AsyncEngine:
    """Create an async engine. Do not hold connections across model inference."""

    return create_async_engine(
        database_url(settings),
        echo=echo,
        pool_pre_ping=True,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """One AsyncSession per application unit of work."""

    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@asynccontextmanager
async def session_scope(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession]:
    """Open a session and roll back on error; caller owns commit."""

    session = factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
