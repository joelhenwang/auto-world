# `S4-BENCH-001` — Workload corpus and local serving benchmark

**Stage:** 4  
**Workstream:** MODEL / OPS / QA  
**Status:** COMPLETE  
**Priority:** P0  
**Owner:** parent coding agent  
**Reviewer(s):** Stage 4 parent / QA  
**Branch/worktree:** `cursor/s4-integration-8b4a`  
**Upstream commit:** `05db78a` (main)  
**Target merge order:** first Stage 4 package; before S4-MODEL-001/002

---

## 1. Objective

```text
Freeze a Stage 3 representative JSONL request corpus and ship a repeatable local
serving benchmark harness (inventory, candidate-stack runners, metrics, selection ADR)
so Stage 4 may select a serving stack without hard-coding frameworks before evidence.
```

## 2. Why this task exists

- Requirements: handbook `29` §6–§7 S4-BENCH-001; `12` local migration
- Stage gate: serving-stack selection ADR from benchmarks (`29` §9 / §10)
- Risks mitigated: pinning an unsupported stack on gfx1151/ROCm; confusing hardware
  failures with domain regressions
- Upstream: Stage 3 GATE_PASS; Downstream: S4-MODEL-001/002, S4-OPS-001, S4-QA-001

## 3. Required reading

1. `AGENTS.md`
2. `29_STAGE_4_LOCAL_DISTRIBUTION_AND_IMAGES.md` §6–§7
3. `12_MODEL_GATEWAY_OPENROUTER_AND_LOCAL_MIGRATION.md`
4. `docs/status/CONTRACT_FREEZE.md` (Stages 0–3)
5. Current gateway under `backend/src/fictional_world/infrastructure/model_gateway/`
6. This kickoff handoff: `docs/handoffs/2026-07-30_S4-KICKOFF.md`

## 4. Frozen contracts

| Contract | Version/hash/commit | Owner | Allowed change |
|---|---|---|---|
| Stage 0–3 freeze | `CONTRACT_FREEZE.md` | parent | none (additive Stage 4 only) |
| Migration head | `0005_stage3_long_term_tables` | S3 | new revisions only (not this task) |
| Prompt/corpus Stage 1–3 | fixtures + prompts | MODEL | **do not edit** to favour one server |
| Gateway protocols | `application/models/protocols.py` | MODEL | read-only this task |

## 5. Scope

### In scope

- Frozen JSONL corpus under `backend/tests/fixtures/benchmarks/stage4/`
- Hardware inventory for Halo A/B + RTX 4060 Ti
- Benchmark runner under `tools/local_serving_bench/`
- Candidate-stack runner scripts (vLLM, llama.cpp, Transformers, optional SGLang)
- Machine-readable + human-readable results under `docs/status/evidence/stage-4/benchmarks/`
- Selection ADR with rejected alternatives + rollback
- Unit/contract tests for corpus + dry-run runner (default CI offline)

### Explicitly out of scope

- Hard-coding production pin without ADR
- Editing domain prompts for benchmark favouritism
- Local adapter/routing implementation (S4-MODEL-001/002)
- Temporal, MinIO, ComfyUI, admin API/UI
- Live OpenRouter in default CI

## 6. File/path ownership

### Writable

```text
docs/tasks/active/S4-BENCH-001_workload-benchmark.md
docs/handoffs/*S4*
docs/status/CURRENT_STAGE.md
docs/status/INTEGRATION_STATUS.md
docs/status/SESSION_LOG.md
docs/status/OPEN_DECISIONS.md
docs/status/evidence/stage-4/benchmarks/**
docs/ops/hardware/**
docs/adr/ADR-0002_*.md
backend/tests/fixtures/benchmarks/stage4/**
backend/tests/unit/benchmark/**
backend/tests/contract/benchmark/**
tools/local_serving_bench/**
scripts/local_serving/**
```

### Read-only dependencies

```text
backend/src/fictional_world/application/models/**
backend/src/fictional_world/infrastructure/model_gateway/**
backend/prompts/**
backend/tests/fixtures/model_corpus/**
docs/status/CONTRACT_FREEZE.md
docs/status/evidence/stage-3/**
```

## 7. Data and migration ownership

```text
No database change: yes
```

## 8. Interface inputs and outputs

### Inputs

```text
Frozen Stage 3 role mix (character/reaction/director/resolver/narrator/summaries/
evaluation/embeddings/concurrency fan-out) + hardware inventory YAML
```

### Outputs

```text
JSONL corpus, bench JSON/MD reports, candidate runner scripts, ADR-0002
```

### Errors/fallbacks

```text
Missing live servers → dry-run / recorded mode; never call OpenRouter from default CI
```

## 9. Required tests

- Corpus schema/contract tests (roles, case kinds, expected schemas)
- Dry-run benchmark runner produces valid metrics JSON offline
- Marker `local_model_live` reserved for real endpoint runs (deselected by default)

## 10. Acceptance criteria

- [x] JSONL corpus frozen with expected schemas and quality labels
- [x] Hardware inventory documented for three-host topology
- [x] Repeatable scripts for each candidate stack
- [x] Results machine-readable + human-readable
- [x] Selection ADR with rejected alternatives and rollback
- [x] Offline tests pass; no live OpenRouter in default suite
- [x] Domain prompts unchanged

## 11. Non-goals / stop conditions

Stop if handbook requires real Halo hardware for ADR acceptance and environment cannot
provide it — then ADR must be provisional with explicit live confirmation path, not a
silent hard-code.
