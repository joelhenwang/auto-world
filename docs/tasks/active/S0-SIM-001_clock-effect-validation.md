# `S0-SIM-001` — Deterministic clock and effect validation

**Stage:** 0 | **Workstream:** SIM | **Status:** IN_PROGRESS | **Priority:** P0  
**Owner:** parent agent | **Branch:** `cursor/s0-db001-sim001-model001-09ce`  
**Depends:** S0-DOM-001

## Objective
Ten-phase calendar VOs, phase/status transition rules, validators/projectors for wait/observe/rest/move/spend/memory, invariant registry.

## Writable
`backend/src/fictional_world/domain/time/**`, `domain/rules/**`, `backend/tests/unit/test_calendar*`, `test_effect_*`, `test_invariants*`, `backend/tests/property/**`

## Non-goals
S0-SIM-002 commit service; DB writes; scene assembly.

## Tests
Calendar order/rollover; effect validation/projection; property monotonic absolute_phase_index.
