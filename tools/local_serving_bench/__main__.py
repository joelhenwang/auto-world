#!/usr/bin/env python3
"""CLI for S4-BENCH-001 local serving benchmarks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from tools.local_serving_bench.corpus import load_corpus, validate_corpus
    from tools.local_serving_bench.runner import run_benchmark, write_report
    from tools.local_serving_bench.stacks import STACK_IDS

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stack",
        choices=STACK_IDS,
        default="dry-run",
        help="Candidate stack id (default dry-run; no network)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="OpenAI-compatible base URL for live stacks (omit for dry-run)",
    )
    parser.add_argument("--model", default="local-model")
    parser.add_argument(
        "--corpus",
        type=Path,
        default=None,
        help="Path to JSONL corpus (default: Stage 4 frozen corpus)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "docs" / "status" / "evidence" / "stage-4" / "benchmarks",
    )
    parser.add_argument(
        "--environment-profile",
        default=None,
        help="Override environment profile label (default ci-dry-run / env)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate corpus and exit",
    )
    args = parser.parse_args(argv)

    entries = load_corpus(args.corpus)
    errors = validate_corpus(entries)
    if errors:
        print("corpus validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 2
    if args.validate_only:
        print(json.dumps({"ok": True, "entries": len(entries)}, indent=2))
        return 0

    if args.stack != "dry-run" and not args.base_url:
        print(
            f"warning: no --base-url; running dry simulation labelled stack={args.stack}",
            file=sys.stderr,
        )

    report = run_benchmark(
        stack_id=args.stack,
        corpus_path=args.corpus,
        base_url=args.base_url,
        model=args.model,
        environment_profile=args.environment_profile,
    )
    json_path, md_path = write_report(report, args.out_dir)
    payload = {
        "json": str(json_path),
        "markdown": str(md_path),
        "summary": report.summary,
    }
    print(json.dumps(payload, indent=2))
    return 0 if report.summary.get("failures", 1) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
