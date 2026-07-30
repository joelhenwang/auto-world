#!/usr/bin/env bash
# Offline dry-run of the Stage 4 benchmark harness (default CI path).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export WORLDSIM_BENCH_ENV="${WORLDSIM_BENCH_ENV:-ci-dry-run}"
exec uv run python -m tools.local_serving_bench \
  --stack dry-run \
  --environment-profile "${WORLDSIM_BENCH_ENV}" \
  "$@"
