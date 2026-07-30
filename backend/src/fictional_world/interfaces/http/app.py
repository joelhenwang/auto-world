"""FastAPI application factory (S0-API-001)."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from fictional_world import __version__
from fictional_world.config import AppSettings, settings_from_profile, validate_settings
from fictional_world.infrastructure.database.session import create_engine, create_session_factory
from fictional_world.interfaces.http.middleware import CorrelationIdMiddleware
from fictional_world.interfaces.http.routes import (
    admin_stage4,
    health,
    stage1,
    stage2,
    stage3,
    websocket,
    worlds,
)
from fictional_world.observability.logging import configure_logging


def load_settings(*, profile: str | None = None) -> AppSettings:
    """Load TOML profile, then overlay environment / ``.env`` via ``AppSettings``."""

    env = AppSettings()
    name = profile or env.profile
    settings = settings_from_profile(name).model_copy(
        update={
            "environment": env.environment,
            "profile": name,
            "api": env.api,
            "database": env.database,
            "auth": env.auth,
            "model_gateway": env.model_gateway,
            "openrouter": env.openrouter,
            "memory": env.memory,
            "features": env.features,
            "observability": env.observability,
        }
    )
    validate_settings(settings)
    return settings


def create_app(
    *,
    settings: AppSettings | None = None,
    engine: AsyncEngine | None = None,
) -> FastAPI:
    """Build the Stage 0 API. Optional engine injection supports tests."""

    app_settings = settings if settings is not None else load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        configure_logging(level=app_settings.observability.log_level)
        own_engine = engine is None
        app.state.settings = app_settings
        if engine is None:
            app.state.engine = create_engine(app_settings.database)
        else:
            app.state.engine = engine
        app.state.session_factory = create_session_factory(app.state.engine)
        try:
            yield
        finally:
            if own_engine:
                await app.state.engine.dispose()

    application = FastAPI(
        title="Fictional World API",
        version=__version__,
        lifespan=lifespan,
    )
    application.add_middleware(CorrelationIdMiddleware)
    application.include_router(health.router)
    application.include_router(worlds.router)
    application.include_router(stage1.router)
    application.include_router(stage2.router)
    application.include_router(stage3.router)
    application.include_router(websocket.router)
    application.include_router(admin_stage4.router)
    application.state.settings = app_settings
    if engine is not None:
        application.state.engine = engine
        application.state.session_factory = create_session_factory(engine)
    return application


# ASGI entry for `uvicorn fictional_world.interfaces.http.app:app`.
app = create_app()
