"""Postgres testcontainer fixture self-test."""

from __future__ import annotations

import pytest


@pytest.mark.integration
@pytest.mark.requires_docker
def test_postgres_container_fixture(postgres_container: dict[str, str]) -> None:
    assert postgres_container["database"] == "fictional_world_test"
    assert postgres_container["port"]
    assert "postgresql" in postgres_container["url"]
