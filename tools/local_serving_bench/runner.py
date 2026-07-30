"""Benchmark execution."""

from __future__ import annotations

import asyncio
import os
import platform
import uuid
from pathlib import Path
from typing import Any

from tools.local_serving_bench.corpus import CorpusEntry, load_corpus, load_manifest
from tools.local_serving_bench.metrics import (
    BenchReport,
    BenchResult,
    render_markdown,
    summarize,
    utc_now_iso,
)
from tools.local_serving_bench.stacks import StackAdapter, build_adapter


def collect_host_record() -> dict[str, Any]:
    return {
        "hostname": platform.node(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "environment_profile": os.environ.get("WORLDSIM_BENCH_ENV", "ci-dry-run"),
    }


def collect_software_versions(stack_id: str) -> dict[str, str]:
    versions = {
        "stack_id": stack_id,
        "platform": platform.platform(),
        "python": platform.python_version(),
    }
    for key in (
        "WORLDSIM_BENCH_SERVER_VERSION",
        "WORLDSIM_BENCH_MODEL_ID",
        "WORLDSIM_BENCH_QUANT",
        "WORLDSIM_BENCH_ROCM",
        "WORLDSIM_BENCH_CUDA",
    ):
        value = os.environ.get(key)
        if value:
            versions[key.removeprefix("WORLDSIM_BENCH_").lower()] = value
    return versions


async def _run_one(adapter: StackAdapter, entry: CorpusEntry) -> BenchResult:
    try:
        success, output, meta = await adapter.execute(entry)
    except Exception as exc:
        return BenchResult(
            request_id=entry.request_id,
            role=entry.role,
            case_kind=entry.case_kind,
            stack_id=adapter.stack_id,
            success=False,
            latency_ms=0.0,
            error=str(exc),
        )
    latency = float(meta.get("latency_ms") or 0.0)
    cancelled = bool(meta.get("cancelled"))
    structured = meta.get("structured_valid")
    structured_valid = bool(structured) if structured is not None else None
    # Cancellation cases are successful when cancellation is observed.
    if entry.case_kind == "cancellation":
        return BenchResult(
            request_id=entry.request_id,
            role=entry.role,
            case_kind=entry.case_kind,
            stack_id=adapter.stack_id,
            success=cancelled or not success,
            latency_ms=latency,
            cancelled=True,
            notes="cancellation observed" if cancelled or not success else "not cancelled",
        )
    # Malformed cases succeed when the runner captures non-JSON without crashing.
    if entry.case_kind == "malformed":
        return BenchResult(
            request_id=entry.request_id,
            role=entry.role,
            case_kind=entry.case_kind,
            stack_id=adapter.stack_id,
            success=True,
            latency_ms=latency,
            structured_valid=False,
            output_chars=len(output),
            notes="malformed tolerance probe",
        )
    return BenchResult(
        request_id=entry.request_id,
        role=entry.role,
        case_kind=entry.case_kind,
        stack_id=adapter.stack_id,
        success=success,
        latency_ms=latency,
        error=None if success else output,
        structured_valid=structured_valid,
        output_chars=len(output) if success else 0,
    )


async def _run_entries(adapter: StackAdapter, entries: list[CorpusEntry]) -> list[BenchResult]:
    results: list[BenchResult] = []
    # Fan-out groups run concurrently; other entries sequentially.
    pending = list(entries)
    while pending:
        entry = pending.pop(0)
        group = entry.fanout_group
        if group is None:
            results.append(await _run_one(adapter, entry))
            continue
        cohort = [entry]
        rest: list[CorpusEntry] = []
        for item in pending:
            if item.fanout_group == group:
                cohort.append(item)
            else:
                rest.append(item)
        pending = rest
        cohort_results = await asyncio.gather(*[_run_one(adapter, item) for item in cohort])
        results.extend(cohort_results)
    return results


def run_benchmark(
    *,
    stack_id: str,
    corpus_path: Path | None = None,
    base_url: str | None = None,
    model: str = "local-model",
    environment_profile: str | None = None,
) -> BenchReport:
    entries = load_corpus(corpus_path)
    manifest = load_manifest(
        corpus_path.with_name("manifest.json") if corpus_path is not None else None
    )
    adapter = build_adapter(stack_id=stack_id, base_url=base_url, model=model)
    started = utc_now_iso()
    results = asyncio.run(_run_entries(adapter, entries))
    finished = utc_now_iso()
    host = collect_host_record()
    if environment_profile:
        host["environment_profile"] = environment_profile
    report = BenchReport(
        report_id=f"bench-{stack_id}-{uuid.uuid4().hex[:10]}",
        stack_id=stack_id,
        environment_profile=str(host.get("environment_profile") or "ci-dry-run"),
        corpus_id=str(manifest.get("corpus_id") or "unknown"),
        started_at=started,
        finished_at=finished,
        host_record=host,
        software_versions=collect_software_versions(stack_id),
        results=results,
        summary=summarize(results),
    )
    return report


def write_report(report: BenchReport, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{report.stack_id}-{report.report_id}.json"
    md_path = out_dir / f"{report.stack_id}-{report.report_id}.md"
    import json

    json_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path
