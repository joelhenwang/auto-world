"""Contract/dry-run tests for Stage 4 local serving bench."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.local_serving_bench.runner import run_benchmark, write_report


@pytest.mark.contract
@pytest.mark.model_fake
def test_dry_run_benchmark_produces_report(tmp_path: Path) -> None:
    report = run_benchmark(stack_id="dry-run", environment_profile="ci-dry-run")
    assert report.environment_profile == "ci-dry-run"
    assert report.corpus_id == "stage4-bench-stage3-rep-v1"
    assert report.summary["total"] == len(report.results)
    assert report.summary["failures"] == 0
    assert report.summary["fanout_count"] >= 4
    assert report.summary["fanout_successes"] == report.summary["fanout_count"]

    json_path, md_path = write_report(report, tmp_path)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["stack_id"] == "dry-run"
    assert "latency_by_role" in payload["summary"]
    assert md_path.read_text(encoding="utf-8").startswith("# Local serving benchmark")


@pytest.mark.contract
def test_candidate_stack_labels_can_dry_simulate_without_url() -> None:
    """Harness must not hard-require a live server to exercise stack labelling."""

    for stack_id in ("vllm", "llamacpp", "transformers", "sglang"):
        report = run_benchmark(
            stack_id=stack_id,
            base_url=None,
            environment_profile="ci-dry-run",
        )
        assert report.summary["failures"] == 0
        assert report.stack_id == stack_id
