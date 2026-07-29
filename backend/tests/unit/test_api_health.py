"""API unit tests that do not require PostgreSQL."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from fictional_world.config.settings import ApiSettings, AppSettings, AuthSettings
from fictional_world.interfaces.http.app import create_app
from fictional_world.interfaces.http.middleware import CORRELATION_HEADER


@pytest.fixture
def settings() -> AppSettings:
    return AppSettings(
        api=ApiSettings(bind_host="127.0.0.1", bind_port=8000),
        auth=AuthSettings(enabled=False, allow_insecure_public_bind=False),
    )


@pytest.mark.asyncio
async def test_health_live(settings: AppSettings) -> None:
    engine = MagicMock()
    app = create_app(settings=settings, engine=engine)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert CORRELATION_HEADER in response.headers


@pytest.mark.asyncio
async def test_correlation_id_echo(settings: AppSettings) -> None:
    engine = MagicMock()
    app = create_app(settings=settings, engine=engine)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/live", headers={CORRELATION_HEADER: "corr-test-1"})
    assert response.headers[CORRELATION_HEADER] == "corr-test-1"


@pytest.mark.asyncio
async def test_health_ready_up(settings: AppSettings) -> None:
    conn = AsyncMock()
    conn.__aenter__.return_value = conn
    conn.__aexit__.return_value = None
    conn.execute = AsyncMock(return_value=None)
    engine = MagicMock()
    engine.connect = MagicMock(return_value=conn)
    app = create_app(settings=settings, engine=engine)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["database"] == "up"


@pytest.mark.asyncio
async def test_health_ready_down(settings: AppSettings) -> None:
    conn = AsyncMock()
    conn.__aenter__.return_value = conn
    conn.__aexit__.return_value = None
    conn.execute = AsyncMock(side_effect=RuntimeError("db offline"))
    engine = MagicMock()
    engine.connect = MagicMock(return_value=conn)
    app = create_app(settings=settings, engine=engine)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["database"] == "down"
