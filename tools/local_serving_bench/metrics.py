"""Benchmark metrics and report shapes."""

from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, cast


@dataclass(slots=True)
class BenchResult:
    request_id: str
    role: str
    case_kind: str
    stack_id: str
    success: bool
    latency_ms: float
    error: str | None = None
    structured_valid: bool | None = None
    cancelled: bool = False
    output_chars: int = 0
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BenchReport:
    """Machine-readable benchmark report."""

    report_id: str
    stack_id: str
    environment_profile: str
    corpus_id: str
    started_at: str
    finished_at: str
    host_record: dict[str, Any]
    software_versions: dict[str, str]
    results: list[BenchResult] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "stack_id": self.stack_id,
            "environment_profile": self.environment_profile,
            "corpus_id": self.corpus_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "host_record": self.host_record,
            "software_versions": self.software_versions,
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary,
        }


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def summarize(results: list[BenchResult]) -> dict[str, Any]:
    by_role: dict[str, list[BenchResult]] = {}
    for result in results:
        by_role.setdefault(result.role, []).append(result)

    def _latency_stats(items: list[BenchResult]) -> dict[str, float]:
        values = [item.latency_ms for item in items if item.success]
        if not values:
            return {"count": 0.0, "p50_ms": 0.0, "p95_ms": 0.0, "mean_ms": 0.0}
        ordered = sorted(values)
        p95_index = min(len(ordered) - 1, max(0, round(0.95 * (len(ordered) - 1))))
        return {
            "count": float(len(values)),
            "p50_ms": float(statistics.median(ordered)),
            "p95_ms": float(ordered[p95_index]),
            "mean_ms": float(statistics.fmean(ordered)),
        }

    role_stats = {role: _latency_stats(items) for role, items in sorted(by_role.items())}
    successes = sum(1 for item in results if item.success)
    structured = [item for item in results if item.structured_valid is not None]
    structured_ok = sum(1 for item in structured if item.structured_valid)
    fanout = [item for item in results if item.case_kind == "concurrency_fanout"]
    return {
        "total": len(results),
        "successes": successes,
        "failures": len(results) - successes,
        "structured_checked": len(structured),
        "structured_valid": structured_ok,
        "fanout_count": len(fanout),
        "fanout_successes": sum(1 for item in fanout if item.success),
        "latency_by_role": role_stats,
        "overall_latency": _latency_stats(results),
    }


def render_markdown(report: BenchReport) -> str:
    lines = [
        f"# Local serving benchmark — `{report.stack_id}`",
        "",
        f"- report_id: `{report.report_id}`",
        f"- environment: `{report.environment_profile}`",
        f"- corpus: `{report.corpus_id}`",
        f"- started: {report.started_at}",
        f"- finished: {report.finished_at}",
        "",
        "## Summary",
        "",
        f"- total: {report.summary.get('total')}",
        f"- successes: {report.summary.get('successes')}",
        f"- failures: {report.summary.get('failures')}",
        f"- structured_valid: {report.summary.get('structured_valid')}/"
        f"{report.summary.get('structured_checked')}",
        f"- fanout_successes: {report.summary.get('fanout_successes')}/"
        f"{report.summary.get('fanout_count')}",
        "",
        "## Latency by role (successful)",
        "",
        "| Role | n | p50 ms | p95 ms | mean ms |",
        "|---|---:|---:|---:|---:|",
    ]
    latency_raw = report.summary.get("latency_by_role", {})
    latency: dict[str, Any] = {}
    if isinstance(latency_raw, dict):
        typed_latency = cast(dict[object, object], latency_raw)
        for key_obj, val_obj in typed_latency.items():
            latency[str(key_obj)] = val_obj
    for role, stats_obj in latency.items():
        if not isinstance(stats_obj, dict):
            continue
        stats = cast(dict[str, Any], stats_obj)
        lines.append(
            f"| {role} | {int(stats['count'])} | {stats['p50_ms']:.1f} | "
            f"{stats['p95_ms']:.1f} | {stats['mean_ms']:.1f} |"
        )
    lines.extend(["", "## Host / software", "", "```json"])
    host_blob = {
        "host_record": report.host_record,
        "software": report.software_versions,
    }
    lines.append(json_dumps(host_blob))
    lines.extend(["```", ""])
    return "\n".join(lines)


def json_dumps(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, indent=2, sort_keys=True)
