"""Unit tests for Stage 4 benchmark corpus (S4-BENCH-001)."""

from __future__ import annotations

import pytest
from tools.local_serving_bench.corpus import (
    REQUIRED_CASE_KINDS,
    REQUIRED_ROLES,
    load_corpus,
    load_manifest,
    validate_corpus,
)


@pytest.mark.unit
def test_stage4_benchmark_corpus_covers_required_roles_and_cases() -> None:
    entries = load_corpus()
    errors = validate_corpus(entries)
    assert errors == []
    roles = {entry.role for entry in entries}
    kinds = {entry.case_kind for entry in entries}
    assert roles >= REQUIRED_ROLES
    assert kinds >= REQUIRED_CASE_KINDS
    fanout = [entry for entry in entries if entry.case_kind == "concurrency_fanout"]
    assert len(fanout) >= 4
    assert {entry.fanout_group for entry in fanout} == {"phase-fanout-4"}


@pytest.mark.unit
def test_stage4_benchmark_manifest_matches_corpus() -> None:
    entries = load_corpus()
    manifest = load_manifest()
    assert manifest["corpus_id"] == "stage4-bench-stage3-rep-v1"
    assert manifest["entry_count"] == len(entries)
    assert manifest["source_stage"] == 3
    assert manifest["scenario_ref"] == "stage3-autonomous-month-v1"
