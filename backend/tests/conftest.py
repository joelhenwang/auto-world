"""Pytest fixtures for Stage 0 harness (S0-QA-001)."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from fictional_world.testing import FakeClock, FakeModelGateway, SeededRandom, block_network

LIVE_MARKERS = frozenset({"openrouter_live", "local_model_live", "image_live"})


def pytest_configure(config: pytest.Config) -> None:
    for marker in (
        "unit",
        "property",
        "integration",
        "contract",
        "scenario",
        "fault",
        "architecture",
        "model_fake",
        "openrouter_live",
        "local_model_live",
        "image_live",
        "slow",
        "soak",
        "security",
        "migration",
        "api",
        "websocket",
        "requires_docker",
    ):
        config.addinivalue_line("markers", marker)


@pytest.fixture
def fake_clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def seeded_random() -> SeededRandom:
    source = SeededRandom()
    source.seed_script([0.1, 0.2, 0.3])
    return source


@pytest.fixture
def fake_model_gateway() -> FakeModelGateway:
    return FakeModelGateway()


@pytest.fixture(autouse=True)
def network_guard(request: pytest.FixtureRequest) -> Iterator[None]:
    """Block network for ordinary tests; live markers opt out."""

    marker_names = {getattr(marker, "name", "") for marker in request.node.iter_markers()}
    if LIVE_MARKERS.intersection(marker_names):
        yield
        return
    if os.environ.get("WORLDSIM_ALLOW_NETWORK") == "1":
        yield
        return
    # pytest-socket when available
    plugin = request.config.pluginmanager.get_plugin("socket")
    if plugin is not None and hasattr(request.config.option, "disable_socket"):
        yield
        return
    with block_network():
        yield


@pytest.fixture(scope="session")
def postgres_container() -> Iterator[dict[str, str]]:
    """Session-scoped PostgreSQL+pgvector container; skipped without Docker."""

    pytest.importorskip("testcontainers")
    try:
        from testcontainers.postgres import PostgresContainer
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"testcontainers postgres unavailable: {exc}")

    try:
        container = PostgresContainer(
            image="pgvector/pgvector:pg16",
            username="fictional_world",
            password="change-me-local",  # noqa: S106 — local testcontainer placeholder
            dbname="fictional_world_test",
        )
        container.start()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"Docker/postgres container failed to start: {exc}")

    info = {
        "host": str(container.get_container_host_ip()),
        "port": str(container.get_exposed_port(5432)),
        "user": "fictional_world",
        "password": "change-me-local",
        "database": "fictional_world_test",
        "url": str(container.get_connection_url()),
    }
    try:
        yield info
    finally:
        container.stop()
