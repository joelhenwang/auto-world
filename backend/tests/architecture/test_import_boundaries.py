"""Architecture / import-boundary checks (S0-QA-002)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "fictional_world"

FORBIDDEN_IN_DOMAIN = frozenset(
    {
        "fastapi",
        "sqlalchemy",
        "alembic",
        "httpx",
        "uvicorn",
        "langgraph",
        "fictional_world.infrastructure",
        "fictional_world.interfaces",
        "fictional_world.application",
    }
)

FORBIDDEN_IN_APPLICATION = frozenset(
    {
        "fastapi",
        "uvicorn",
        "fictional_world.interfaces",
        "fictional_world.infrastructure.database.models",
        "fictional_world.infrastructure.database.orm",
    }
)


def _iter_py_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if path.is_file())


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.add(node.module)
    return names


def _violations(root: Path, forbidden: frozenset[str]) -> list[str]:
    found: list[str] = []
    for path in _iter_py_files(root):
        for name in _imported_modules(path):
            for ban in forbidden:
                if name == ban or name.startswith(f"{ban}."):
                    found.append(f"{path.relative_to(SRC.parent)}: imports {name}")
    return found


@pytest.mark.architecture
def test_domain_has_no_infrastructure_or_framework_imports() -> None:
    violations = _violations(SRC / "domain", FORBIDDEN_IN_DOMAIN)
    assert violations == []


@pytest.mark.architecture
def test_application_does_not_import_http_or_orm_models() -> None:
    violations = _violations(SRC / "application", FORBIDDEN_IN_APPLICATION)
    assert violations == []
