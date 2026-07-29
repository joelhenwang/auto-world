# `S0-QA-002` — Stage 0 gate and review

**Stage:** 0 | **Workstream:** QA | **Status:** IN_REVIEW | **Priority:** P0  
**Owner:** parent agent | **Branch:** `cursor/s0-qa002-stage-gate-09ce`  
**Upstream:** `b45b6d5` | **Depends:** all Stage 0 tasks  
**AGENTS conceptual branch:** `task/S0-QA-002-stage-gate`

## Objective

Produce the Stage 0 promotion evidence: deterministic foundation scenario, fault-injection coverage, architecture/security checks, gate report, and contract freeze update.

## Writable

- `tools/scenario_harness/**`
- `backend/tests/scenario/**`, `backend/tests/fault/**`, `backend/tests/architecture/**`, `backend/tests/security/**`
- `backend/tests/fixtures/stage0_foundation*.toml`
- `scripts/run_stage0_gate.py` (and related evidence helpers)
- `docs/status/evidence/stage-0/**`
- `docs/status/CONTRACT_FREEZE.md`, `CURRENT_STAGE.md`, handoff/task docs

## Non-goals

- Stage 1 character graphs / WebSocket
- Live OpenRouter as a hard gate (opt-in only)
- Soak / multi-day scenarios

## Gate

Handbook `25` §8 hard exit checklist with evidence paths.
