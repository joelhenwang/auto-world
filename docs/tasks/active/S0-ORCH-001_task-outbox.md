# `S0-ORCH-001` — Task/outbox queue primitives

**Stage:** 0 | **Workstream:** ORCH | **Status:** IN_PROGRESS | **Priority:** P0  
**Owner:** parent agent | **Branch:** `cursor/s0-orch001-task-outbox-leases-09ce`  
**Upstream:** `81c8dcf` | **Depends:** S0-DB-002 (schema), S0-DB-003 (UoW)  
**AGENTS conceptual branch:** `task/S0-ORCH-001-task-outbox`

## Objective

Task creation/dependency/claim/lease/heartbeat/retry/dead-letter; outbox claim/dispatch; budget reservation data operations. Claim uses `FOR UPDATE SKIP LOCKED`.

## Assumptions

1. Stage 0 `TaskState`: handbook READY→`pending`, LEASED→`claimed`; retry delay via `available_at`.
2. Dependencies: child claimable only when all parents are `succeeded`.
3. Budget ops are data-layer only (no provider RPM enforcement).
4. Outbox states: `pending` / `claimed` / `completed`.

## Writable

- `backend/src/fictional_world/application/orchestration/**`
- `backend/src/fictional_world/application/ports/**`
- `backend/src/fictional_world/domain/tasks/**`
- `backend/src/fictional_world/domain/common/enums.py` (OutboxState, BudgetStatus)
- `backend/src/fictional_world/infrastructure/database/repositories/**`
- `backend/src/fictional_world/infrastructure/database/unit_of_work.py`
- `backend/src/fictional_world/infrastructure/database/mappings/**`
- `backend/tests/unit/test_task_transitions*`
- `backend/tests/integration/test_task_queue*`
- `backend/tests/integration/test_outbox_dispatch*`
- `backend/tests/integration/test_budget_ledger*`
- task/status/handoff docs

## Non-goals

- WorldOrchestrator / phase runner (S0-ORCH-002)
- Fencing tokens (Stage 4)
- Seed importer (S0-CONTENT-001)
- Claim indexes (handbook defers to Stage 2–3)

## Tests

Two-worker claim exclusivity; lease expiry reclaim; terminal never re-leased; dependency gate; retry→dead-letter; outbox at-least-once complete idempotency; budget reserve/consume/release/expire.
