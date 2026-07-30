"""Benchmark corpus loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class CorpusEntry:
    """One frozen benchmark request line."""

    raw: dict[str, Any]

    @property
    def request_id(self) -> str:
        return str(self.raw["request_id"])

    @property
    def role(self) -> str:
        return str(self.raw["role"])

    @property
    def case_kind(self) -> str:
        return str(self.raw["case_kind"])

    @property
    def expected_schema(self) -> str | None:
        value = self.raw.get("expected_schema")
        return str(value) if value is not None else None

    @property
    def fanout_group(self) -> str | None:
        value = self.raw.get("fanout_group")
        return str(value) if value is not None else None


REQUIRED_ROLES = frozenset(
    {
        "character_decision",
        "character_reaction",
        "director_proposal",
        "resolver",
        "scene_narrator",
        "daily_summarizer",
        "monthly_reflector",
        "quality_evaluator",
        "embedding",
    }
)

REQUIRED_CASE_KINDS = frozenset(
    {
        "valid",
        "malformed",
        "long_context",
        "unicode",
        "cancellation",
        "concurrency_fanout",
    }
)


def default_corpus_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    return (
        root
        / "backend"
        / "tests"
        / "fixtures"
        / "benchmarks"
        / "stage4"
        / "stage3_representative_requests.jsonl"
    )


def default_manifest_path() -> Path:
    return default_corpus_path().with_name("manifest.json")


def load_corpus(path: Path | None = None) -> list[CorpusEntry]:
    corpus_path = path or default_corpus_path()
    entries: list[CorpusEntry] = []
    for line in corpus_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        entries.append(CorpusEntry(raw=json.loads(line)))
    return entries


def load_manifest(path: Path | None = None) -> dict[str, Any]:
    manifest_path = path or default_manifest_path()
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def validate_corpus(entries: list[CorpusEntry]) -> list[str]:
    """Return human-readable validation errors (empty if ok)."""

    errors: list[str] = []
    roles = {e.role for e in entries}
    kinds = {e.case_kind for e in entries}
    missing_roles = REQUIRED_ROLES - roles
    missing_kinds = REQUIRED_CASE_KINDS - kinds
    if missing_roles:
        errors.append(f"missing roles: {sorted(missing_roles)}")
    if missing_kinds:
        errors.append(f"missing case_kinds: {sorted(missing_kinds)}")
    fanouts = [e for e in entries if e.case_kind == "concurrency_fanout"]
    if len(fanouts) < 4:
        errors.append("concurrency_fanout requires at least 4 entries")
    for entry in entries:
        if "request_id" not in entry.raw or "role" not in entry.raw:
            errors.append(f"entry missing request_id/role: {entry.raw!r}")
        if entry.role != "embedding" and "messages" not in entry.raw:
            errors.append(f"{entry.request_id}: text roles require messages")
        if entry.role == "embedding" and "texts" not in entry.raw:
            errors.append(f"{entry.request_id}: embedding roles require texts")
    return errors
