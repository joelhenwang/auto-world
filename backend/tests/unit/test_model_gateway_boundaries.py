"""Architecture: application.models must not import provider SDKs."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

FORBIDDEN = frozenset({"openai", "httpx", "openrouter", "anthropic", "requests"})
MODELS_ROOT = (
    Path(__file__).resolve().parents[2] / "src" / "fictional_world" / "application" / "models"
)


@pytest.mark.unit
def test_no_provider_sdk_imports_in_application_models() -> None:
    offenders: list[str] = []
    for path in MODELS_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root in FORBIDDEN:
                        offenders.append(f"{path.name}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".", 1)[0]
                if root in FORBIDDEN:
                    offenders.append(f"{path.name}: from {node.module}")
    assert not offenders, offenders
