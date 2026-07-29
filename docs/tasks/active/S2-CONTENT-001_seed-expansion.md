# `S2-CONTENT-001` — Stage 2 seed cast and geography

**Stage:** 2  
**Workstream:** CONTENT  
**Status:** COMPLETE  
**Priority:** P0  
**Owner:** parent coding agent  
**Branch/worktree:** `cursor/s2-content-001-seed-085f`  
**Upstream:** S2-DB-001 tip (`5de09a3`, Alembic `0004`)  
**Depends:** Stage 1 freeze (can parallel S2-DB-001)  
**AGENTS conceptual branch:** `task/S2-CONTENT-001-seed-expansion`

## Objective

```text
Extend caldris-embervale-v1 so Iri Voss and Torren Kest plus Stage 2 locations
import cleanly under a stage2 fixture, without breaking stage0/stage1 fixtures.
```

## In scope

- Character YAMLs: `iri-voss`, `torren-kest` (from handbook `23`)
- Locations: Archive Annex, Lantern Ward, North Road, Ash Orchard (+ existing inn/market/bridge)
- `fixtures/stage2.yaml` activating four characters + Stage 2 geography
- Goals/relationships seed extensions for four-character cast
- Importer/tests: stage2 fixture import; stage1 fixture still works
- `content_version` bump if required by freeze rules

## Out of scope

- Belief engine, NPC generation, Director hooks runtime
- Map UI / travel graph logic (SIM/API)

## Acceptance

- [x] Deterministic `seed_uuid` keys for new entities
- [x] `import_caldris_stage2` (or fixture flag) loads four characters
- [x] Stage 1 fixture regression still green
- [x] Handoff written
