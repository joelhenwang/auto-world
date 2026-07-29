# `S0-MODEL-002` — Fake + OpenRouter adapters

**Stage:** 0 | **Workstream:** MODEL | **Status:** IN_PROGRESS | **Priority:** P0  
**Owner:** parent agent | **Branch:** `cursor/s0-db002-model002-09ce`  
**Upstream:** `538372a` | **Depends:** S0-MODEL-001, S0-QA-001  
**AGENTS conceptual branch:** `task/S0-MODEL-002-fake-openrouter`

## Objective

Provider adapters implementing `TextModelGateway` / `EmbeddingGateway`: scripted fake, OpenRouter httpx skeleton, error mapping, capability-probe stub, opt-in live marker.

## Writable

- `backend/src/fictional_world/infrastructure/model_gateway/**`
- `backend/src/fictional_world/testing/fake_model.py` (bridge only)
- `backend/tests/contract/test_model_gateway*`
- `backend/tests/unit/test_openrouter*`
- `pyproject.toml` / `uv.lock` (`httpx`)
- task/status/handoff docs

## Non-goals

- LangGraph wiring
- Live OpenRouter as stage gate
- Request budget ledger application logic (ORCH)

## Tests

Fake contract: valid/malformed/schema/429/embedding dimension; OpenRouter error mapping unit tests; live tests `@pytest.mark.openrouter_live` skipped by default.
