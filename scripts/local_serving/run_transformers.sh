#!/usr/bin/env bash
# Candidate stack runner: Transformers/PyTorch OpenAI-compatible shim (conservative baseline).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export WORLDSIM_BENCH_ENV="${WORLDSIM_BENCH_ENV:-local-transformers}"
exec uv run python -m tools.local_serving_bench \
  --stack transformers \
  --base-url "${WORLDSIM_BENCH_BASE_URL:-}" \
  --model "${WORLDSIM_BENCH_MODEL:-local-model}" \
  --environment-profile "${WORLDSIM_BENCH_ENV}" \
  "$@"
