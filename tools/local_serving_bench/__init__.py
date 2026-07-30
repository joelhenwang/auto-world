"""Local serving benchmark harness (S4-BENCH-001).

Default mode is offline dry-run against a scripted fake endpoint. Live stacks are
opt-in via ``--base-url`` and pytest marker ``local_model_live``.
"""

from __future__ import annotations

from tools.local_serving_bench.corpus import CorpusEntry, load_corpus, load_manifest
from tools.local_serving_bench.metrics import BenchReport, BenchResult, summarize
from tools.local_serving_bench.runner import run_benchmark

__all__ = [
    "BenchReport",
    "BenchResult",
    "CorpusEntry",
    "load_corpus",
    "load_manifest",
    "run_benchmark",
    "summarize",
]
