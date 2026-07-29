# Current Stage

**Updated:** 2026-07-29T20:14:53Z
**Updated by:** integration subagent
**Repository:** autonomous-fictional-world  
**Current branch:** `cursor/s1-integration-5704`
**Stage:** 1 — First Complete Three-Phase Day | **Status:** GATE_PASS_PENDING_REVIEW

## Current objective

Parent-review and merge the completed Stage 1 vertical slice. The deterministic
S1-QA-001 gate passes at ; evidence is under
`docs/status/evidence/stage-1/`.

Active characters: Mira Talren + Dain Arcen. Enabled phases: dawn → morning → evening.

## Active tasks

| Task ID | Status | Notes |
|---|---|---|
| S0-QA-002 | VERIFIED on main | Stage 0 GATE_PASS; contracts FROZEN |
| S1-DB-001 | VERIFIED | migration `0003`, scene/stream repositories |
| S1-KNOW-001 | VERIFIED | sealed perspective context + leakage tests |
| S1-MODEL-001 | VERIFIED | prompts/schemas/fake corpus |
| S1-GRAPH-001 | VERIFIED | bounded character decision pipeline |
| S1-SIM-001 | VERIFIED | activation/scene assembly |
| S1-GRAPH-002 | VERIFIED | reaction/resolution pipelines |
| S1-SIM-002 | VERIFIED | atomic idempotent scene commit |
| S1-ORCH-001 | VERIFIED | first-day workflow, budget, pause/resume |
| S1-API-001 | VERIFIED | REST/OpenAPI/WebSocket/player commands |
| S1-UI-001 | VERIFIED | Vue runtime client; tests/build green |
| S1-QA-001 | GATE_PASS | 154 offline tests; fake scenario + live smoke pass |

## Stage 0 freeze (do not break)

- Canon = PostgreSQL + committed `world_event`; models propose only
- Idempotency on all externally retried ops
- No DB transaction across remote model calls
- Character knowledge isolation
- Default tests: no live OpenRouter (`openrouter_live` opt-in)
- Additive contract changes only; new Alembic revisions

## Latest verified baseline

```bash
sudo chmod 666 /var/run/docker.sock
uv run python scripts/run_stage1_gate.py
# PASS: 154 passed, 2 live tests deselected; frontend 5 passed + build
uv run pytest -o addopts='' -m openrouter_live \
  backend/tests/live/test_stage1_openrouter.py \
  backend/tests/unit/test_openrouter_errors.py
# PASS: 2 passed
```

Evidence: `docs/status/evidence/stage-1/stage-gate-report.md`
