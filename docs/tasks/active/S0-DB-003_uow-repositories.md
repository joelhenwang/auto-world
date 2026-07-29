# `S0-DB-003` — Unit of work and repositories

**Stage:** 0 | **Workstream:** DB | **Status:** IN_PROGRESS | **Priority:** P0  
**Owner:** parent agent | **Branch:** `cursor/s0-db003-uow-repositories-09ce`  
**Upstream:** `462a6fa` | **Depends:** S0-DB-002  
**AGENTS conceptual branch:** `task/S0-DB-003-uow-repositories`

## Objective

Explicit repository ports and SQLAlchemy implementations for core Stage 0 aggregates; SqlAlchemy unit of work as transaction owner; optimistic version operations.

## Writable

- `backend/src/fictional_world/application/ports/**`
- `backend/src/fictional_world/domain/world/**`, `domain/characters/**` (persistence records)
- `backend/src/fictional_world/infrastructure/database/repositories/**`
- `backend/src/fictional_world/infrastructure/database/unit_of_work.py`
- `backend/src/fictional_world/infrastructure/database/mappings/**`
- `backend/tests/integration/test_repositories*`
- task/status/handoff docs

## Non-goals

- Event commit service (S0-SIM-002)
- Task claim/lease/heartbeat (S0-ORCH-001)
- Seed importer (S0-CONTENT-001)
- Scene/action tables

## Ports (minimum)

World, WorldClock, CharacterState, PhaseRun, WorldEvent(+effects), Observation, RecentMemory, AggregateVersion, Outbox (insert/get by idempotency), UnitOfWork

## Tests

Real PostgreSQL CRUD, query, rollback, optimistic concurrency conflict.
