# `S0-SIM-002` — Atomic event commit service

**Stage:** 0 | **Workstream:** SIM | **Status:** IN_PROGRESS | **Priority:** P0  
**Owner:** parent agent | **Branch:** `cursor/s0-sim002-event-commit-09ce`  
**Upstream:** `2bd15f0` | **Depends:** S0-DB-003, S0-SIM-001  
**AGENTS conceptual branch:** `task/S0-SIM-002-event-commit`

## Objective

Atomic operation commit: idempotency check, expected-version verify, validate effects, insert event/effects/observations/recent-memory/outbox, apply Stage-0 projections, advance world sequence; return existing result on retry.

## Writable

- `backend/src/fictional_world/application/simulation/**`
- `backend/tests/integration/test_event_commit*`
- `backend/tests/unit/test_event_commit*` (if needed)
- task/status/handoff docs

## Non-goals

- Scene table / full scene state machine (no scene tables in Stage 0 schema)
- Task/outbox claim workers (S0-ORCH-001)
- Seed importer (S0-CONTENT-001)
- Model calls inside the transaction

## Tests

Rollback on validation/conflict; duplicate idempotency returns one event; optimistic version conflict; lookup by idempotency after commit.
