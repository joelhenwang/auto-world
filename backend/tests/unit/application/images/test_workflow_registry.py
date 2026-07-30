"""Unit tests for workflow registry (S4-IMG-001)."""

from __future__ import annotations

import pytest

from fictional_world.infrastructure.comfyui.workflow_registry import WorkflowRegistry


@pytest.mark.unit
def test_registry_loads_stub_v1() -> None:
    reg = WorkflowRegistry()
    wf = reg.load("stub_v1")
    assert isinstance(wf, dict)
    assert "_meta" in wf


@pytest.mark.unit
def test_registry_metadata() -> None:
    reg = WorkflowRegistry()
    meta = reg.metadata("stub_v1")
    assert meta["version"] == "stub_v1"
    assert "supported_asset_classes" in meta


@pytest.mark.unit
def test_registry_hash_deterministic() -> None:
    reg = WorkflowRegistry()
    h1 = reg.hash("stub_v1")
    h2 = reg.hash("stub_v1")
    assert h1 == h2
    assert len(h1) == 64


@pytest.mark.unit
def test_registry_list_versions() -> None:
    reg = WorkflowRegistry()
    versions = reg.list_versions()
    assert "stub_v1" in versions


@pytest.mark.unit
def test_registry_missing_version_raises() -> None:
    reg = WorkflowRegistry()
    with pytest.raises(KeyError, match="nonexistent"):
        reg.load("nonexistent")
