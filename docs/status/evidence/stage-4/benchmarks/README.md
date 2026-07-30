# Stage 4 benchmark evidence

**Task:** S4-BENCH-001  
**Corpus:** `stage4-bench-stage3-rep-v1`  
**ADR:** `docs/adr/ADR-0002_local_serving_stack_selection.md`

## How to regenerate (offline)

```bash
chmod +x scripts/local_serving/*.sh
./scripts/local_serving/run_dry_run.sh
# Optional labelled dry simulations (still offline without --base-url):
./scripts/local_serving/run_llamacpp.sh
./scripts/local_serving/run_vllm.sh
./scripts/local_serving/run_transformers.sh
```

## Live hardware (opt-in)

```bash
export WORLDSIM_BENCH_BASE_URL=http://strix-halo-a:8000
export WORLDSIM_BENCH_MODEL=...
export WORLDSIM_BENCH_ENV=strix-halo-a
export WORLDSIM_ALLOW_NETWORK=1
uv run pytest -o addopts='' -m local_model_live
./scripts/local_serving/run_llamacpp.sh --base-url "$WORLDSIM_BENCH_BASE_URL"
```

Never send private local-only worlds to OpenRouter from these scripts without policy approval.
