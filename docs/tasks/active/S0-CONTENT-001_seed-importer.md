# `S0-CONTENT-001` — Seed source and importer

**Stage:** 0 | **Workstream:** CONTENT | **Status:** IN_PROGRESS | **Priority:** P0  
**Owner:** parent agent | **Branch:** `cursor/s0-content001-seed-importer-09ce`  
**Upstream:** `81c8dcf` | **Depends:** S0-DB-002, S0-DOM-001 (uses S0-DB-003 + S0-SIM-002)  
**AGENTS conceptual branch:** `task/S0-CONTENT-001-seed`

## Objective

Author `caldris-embervale-v1` Stage 0 subset, validate, import atomically with deterministic UUIDv5 IDs, emit `WORLD_SEEDED`, support repeat-import idempotency and secret separation.

## Assumptions

1. Event type is **`WORLD_SEEDED`** (handbook `23`/`25`; not `06`'s `WORLD_INITIALIZED`).
2. Stage 0 default fixture: Cinder Lantern Inn + Mira only; Dain optional via fixture list.
3. `seed_key` stored in `world_config.macro_simulation_policy.seed_keys` and `WORLD_SEEDED.structured_facts` (no schema migration).
4. Initial `phase_snapshot` deferred to S0-ORCH-002.
5. Relationships/items/factions/routes not imported (no Stage 0 tables).

## Writable

- `seed/worlds/caldris-embervale-v1/**`, `seed/schemas/**`
- `scripts/seed_world.py`, `Makefile` seed target
- `backend/src/fictional_world/application/seed/**`
- `backend/src/fictional_world/domain/seed/**` (ids/helpers)
- ports/repos/mappings as needed for location/config/card
- `pyproject.toml` / lock (PyYAML)
- `backend/tests/**/test_seed*`
- task/status/handoff docs

## Non-goals

- Full four-character/region default activation
- Route/faction/item tables
- Phase runner (ORCH-002)
- Live model calls

## Tests

Import empty; repeat import; broken reference rollback; secret separation; stable UUIDv5.
