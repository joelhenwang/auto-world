# `S2-QA-001` — Stage 2 gate and evidence

**Stage:** 2  
**Workstream:** QA  
**Status:** COMPLETE  
**Depends:** S2-ORCH-001, S2-API-001, S2-UI-001  
**AGENTS conceptual branch:** `task/S2-QA-001-stage-gate`  
**Branch:** `cursor/s2-qa-001-gate-085f`

## Objective

```text
Prove stage2-seven-day-world-v1 completes seven full days for four characters
with leakage/fault/continuity checks and evidence under docs/status/evidence/stage-2/.
```

## Deliverables

- Deterministic scenario + fake corpus (existing ORCH scenario retained)
- Gate script `scripts/run_stage2_gate.py`
- Evidence bundle + stage-gate-report.md Decision PASS/FAIL
- Leakage corpus >=100 assertions (`test_leakage_corpus.py`)
- Day-boundary restart idempotency test
- Human review worksheet stub
- Freeze Stage 2 contracts in CONTRACT_FREEZE.md

## Acceptance

- `uv run python scripts/run_stage2_gate.py` exits 0
- `docs/status/evidence/stage-2/stage-gate-report.md` shows **Decision: PASS**
- Stage 1 gate remains runnable

## Handoff

`docs/handoffs/2026-07-29_S2-QA-001.md`
