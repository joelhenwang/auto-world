# `S0-MODEL-001` — Gateway protocols and profiles

**Stage:** 0 | **Workstream:** MODEL | **Status:** IN_PROGRESS | **Priority:** P0  
**Owner:** parent agent | **Branch:** `cursor/s0-db001-sim001-model001-09ce`  
**Depends:** S0-DOM-001, S0-ENG-002

## Objective
Provider-neutral Text/Embedding protocols, results/errors, ModelProfile registry, sampling defaults. No provider SDK escape.

## Writable
`backend/src/fictional_world/application/models/**`, `config/model_profiles/**`, related unit/contract tests

## Non-goals
OpenRouter HTTP (S0-MODEL-002); live probes; budget ledger.

## Tests
Profile selection/validation; import boundary (no openai/httpx/openrouter in application.models).
