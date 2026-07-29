# `S0-DB-002` — Core schema

**Stage:** 0 | **Workstream:** DB | **Status:** IN_PROGRESS | **Priority:** P0  
**Owner:** parent agent | **Branch:** `cursor/s0-db002-model002-09ce`  
**Upstream:** `538372a` | **Depends:** S0-DB-001  
**AGENTS conceptual branch:** `task/S0-DB-002-core-schema`

## Objective

Stage 0 core tables, ORM models, named constraints/indexes, Alembic revision `0002_core_stage0_tables`, and generated schema snapshot.

## Writable

- `backend/src/fictional_world/infrastructure/database/models/**`
- `backend/migrations/versions/0002_*.py`
- `backend/migrations/env.py` (model imports only)
- `scripts/export_database_schema.py` (or equivalent)
- `docs/generated/database-schema.sql`
- `backend/tests/integration/test_core_schema*`
- `docs/tasks/active/S0-DB-002_*`, status/handoff docs

## Non-goals

- Repositories / UoW (S0-DB-003)
- Seed importer (S0-CONTENT-001)
- Scene/action/claim/belief/embedding tables
- Append-only triggers beyond Stage 0 constraint tests

## Tables

world, world_config, world_clock, entity, location, character, character_card_version, character_state, phase_run, phase_snapshot, phase_snapshot_character, world_event, event_effect, observation, recent_memory, model_profile, model_call, task_run, task_dependency, request_budget_ledger, outbox_message, aggregate_version, user_command

## Tests

Database rejects duplicate phase/event/effect/idempotency keys and invalid numeric ranges; upgrade/downgrade/upgrade; single head.
