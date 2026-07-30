#!/usr/bin/env bash
# Candidate stack runner: vLLM (OpenAI-compatible). Does not select the production pin.
# Usage:
#   export WORLDSIM_BENCH_BASE_URL=http://strix-halo-a:8000
#   export WORLDSIM_BENCH_MODEL=...
#   ./scripts/local_serving/run_vllm.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export WORLDSIM_BENCH_ENV="${WORLDSIM_BENCH_ENV:-local-vllm}"
exec uv run python -m tools.local_serving_bench \
  --stack vllm \
  --base-url "${WORLDSIM_BENCH_BASE_URL:-}" \
  --model "${WORLDSIM_BENCH_MODEL:-local-model}" \
  --environment-profile "${WORLDSIM_BENCH_ENV}" \
  "$@"
