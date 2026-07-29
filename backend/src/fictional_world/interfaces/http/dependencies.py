"""FastAPI dependency injection."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.config.settings import AppSettings
from fictional_world.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def get_settings(request: Request) -> AppSettings:
    return cast(AppSettings, request.app.state.settings)


def get_engine(request: Request) -> AsyncEngine:
    return cast(AsyncEngine, request.app.state.engine)


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    return cast(async_sessionmaker[AsyncSession], request.app.state.session_factory)


async def get_uow(
    factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> AsyncIterator[UnitOfWork]:
    async with SqlAlchemyUnitOfWork(factory) as uow:
        yield cast(UnitOfWork, uow)


SettingsDep = Annotated[AppSettings, Depends(get_settings)]
EngineDep = Annotated[AsyncEngine, Depends(get_engine)]
UowDep = Annotated[UnitOfWork, Depends(get_uow)]
