#!/usr/bin/env bash
# Candidate stack runner: llama.cpp server (OpenAI-compatible). Does not select the production pin.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export WORLDSIM_BENCH_ENV="${WORLDSIM_BENCH_ENV:-local-llamacpp}"
exec uv run python -m tools.local_serving_bench \
  --stack llamacpp \
  --base-url "${WORLDSIM_BENCH_BASE_URL:-}" \
  --model "${WORLDSIM_BENCH_MODEL:-local-model}" \
  --environment-profile "${WORLDSIM_BENCH_ENV}" \
  "$@"
