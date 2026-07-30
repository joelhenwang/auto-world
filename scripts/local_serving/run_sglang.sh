#!/usr/bin/env bash
# Optional candidate: SGLang (only if stable on pinned ROCm).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export WORLDSIM_BENCH_ENV="${WORLDSIM_BENCH_ENV:-local-sglang}"
exec uv run python -m tools.local_serving_bench \
  --stack sglang \
  --base-url "${WORLDSIM_BENCH_BASE_URL:-}" \
  --model "${WORLDSIM_BENCH_MODEL:-local-model}" \
  --environment-profile "${WORLDSIM_BENCH_ENV}" \
  "$@"
