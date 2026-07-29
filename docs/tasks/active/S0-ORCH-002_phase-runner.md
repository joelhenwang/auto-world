# `S0-ORCH-002` — Deterministic phase runner

**Stage:** 0 | **Workstream:** ORCH | **Status:** IN_REVIEW | **Priority:** P0  
**Owner:** parent agent | **Branch:** `cursor/s0-orch002-phase-runner-09ce`  
**Upstream:** `9b3177d` | **Depends:** S0-SIM-002, S0-ORCH-001, S0-CONTENT-001  
**AGENTS conceptual branch:** `task/S0-ORCH-002-phase-runner`

## Objective

`WorldOrchestrator` Postgres adapter: create phase, advance clock/world tick, seal snapshot, scripted Mira WAIT/OBSERVE/REST, finalize; resume from durable state without duplicates.

## Assumptions

1. First advance runs the seeded clock phase (dawn/index 0); later advances bump the calendar.
2. Snapshot seal is insert-once per phase_run (unique FK).
3. Director/user-commands/images stubbed as successful no-ops with durable tasks.
4. No LangGraph / live models.

## Writable

- `backend/src/fictional_world/application/orchestration/**`
- `backend/src/fictional_world/domain/phases/**`
- ports/repos/mappings/UoW for snapshots + phase queries
- `backend/tests/integration/test_phase_runner*`
- `backend/tests/unit/test_phase_runner*`
- task/status/handoff docs

## Non-goals

- API routes (S0-API-001)
- Full QA scenario gate (S0-QA-002)
- Temporal / multi-character scenes / Director LLM

## Tests

Restart at boundaries; no duplicate phase/event; pause/resume; scripted effects on Caldris seed.
