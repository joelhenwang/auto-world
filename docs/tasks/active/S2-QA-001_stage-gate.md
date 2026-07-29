# `S2-QA-001` — Stage 2 gate and evidence

**Stage:** 2  
**Workstream:** QA  
**Status:** READY  
**Depends:** S2-ORCH-001, S2-API-001, S2-UI-001  
**AGENTS conceptual branch:** `task/S2-QA-001-stage-gate`

## Objective

```text
Prove stage2-seven-day-world-v1 completes seven full days for four characters
with leakage/fault/continuity checks and evidence under docs/status/evidence/stage-2/.
```

## Deliverables

- Deterministic scenario + fake corpus
- Gate script `scripts/run_stage2_gate.py`
- Evidence bundle + stage-gate-report.md Decision PASS/FAIL
- Freeze Stage 2 contracts in CONTRACT_FREEZE.md
