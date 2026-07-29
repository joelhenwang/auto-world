# `S0-API-001` + `S0-OPS-001` — Minimal API/CLI and observability baseline

**Stage:** 0 | **Workstream:** API + OPS | **Status:** IN_PROGRESS | **Priority:** P0  
**Owner:** parent agent | **Branch:** `cursor/s0-api001-ops001-09ce`  
**Upstream:** `7350ce5` | **Depends:** S0-ORCH-002, S0-ENG-002  
**AGENTS conceptual branch:** `task/S0-API-001-ops-001`

## Objective

FastAPI app with health + world/clock/phase/event reads and phase-advance command; CLI for seed/advance/reconcile; structured logging with correlation IDs and secret redaction; OpenAPI export.

## Assumptions

1. Loopback bind default; public bind rejected without auth/override (existing `validate_settings`).
2. Phase advance reuses `DeterministicPhaseRunner` idempotency keys.
3. No WebSocket, auth product, or frontend client generation beyond OpenAPI JSON.

## Writable

- `backend/src/fictional_world/interfaces/**`
- `backend/src/fictional_world/observability/**`
- `backend/src/fictional_world/application/queries/**` (thin DTOs if needed)
- `pyproject.toml` / `uv.lock` (fastapi/uvicorn)
- `scripts/export_openapi.py`, CLI script, Makefile aliases
- `docs/generated/openapi.json`
- tests under `backend/tests/unit/test_api*`, `test_logging*`, `backend/tests/integration/test_api*`
- task/status/handoff docs

## Non-goals

- S0-QA-002 full stage gate / evidence bundle
- WebSocket, Temporal, image APIs
- Production auth

## Tests

Health live/ready; read projections; advance phase via API; correlation header; API key redaction; unsafe bind already covered by settings tests.
