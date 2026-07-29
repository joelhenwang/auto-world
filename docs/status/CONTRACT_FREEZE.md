# Contract Freeze — Stage 0

**Status:** FROZEN  
**Freeze date:** 2026-07-29  
**Freeze owner:** parent coding agent  
**Integration commit:** pending main tip after S0-QA-002 merge (`6b54e47` on gate branch)  
**Stage document:** `25_STAGE_0_FOUNDATION.md`  
**Gate report:** `docs/status/evidence/stage-0/stage-gate-report.md`

## Frozen contracts

| Contract | Source | Generated artefact | Version/hash | Allowed change during freeze |
|---|---|---|---|---|
| Domain IDs/enums | S0-DOM-001 | `docs/generated/domain-schemas/` | generated tree | additive only via ADR |
| Pydantic schemas | S0-DOM-001 | `docs/generated/domain-schemas/` | generated tree | additive |
| Effect-command union | S0-DOM-001 / S0-SIM-001 | domain package | Stage 0 surface | additive kinds need ADR |
| Repository/UoW ports | S0-DB-003 | application ports | Stage 0 | additive methods OK |
| Database migration head | S0-DB-002 | `docs/generated/database-schema.sql` | `5f8b48b8…` / `0002_core_stage0_tables` | new revisions only |
| Event/outbox semantics | S0-SIM-002 / S0-ORCH-001 | — | Stage 0 | no silent reinterpretation |
| Model gateway protocols | S0-MODEL-001 | — | Stage 0 | additive |
| API DTO/event envelope | S0-API-001 | `docs/generated/openapi.json` | `9b2ae479…` | additive endpoints |
| Seed manifest | S0-CONTENT-001 | `seed/worlds/caldris-embervale-v1/` | `caldris-embervale-v1` | content_version bump |
| Task/idempotency keys | S0-ORCH-001/002 | — | Stage 0 | preserve key grammar |
| Monorepo layout | S0-ENG-001 / `19` §2 | — | handbook v1.0 | additive packages |

## Consumers

| Contract | Consumer tasks/modules |
|---|---|
| Domain + DB | Stage 1 graphs/memory/API |
| Event commit | Stage 1 scene resolution |
| Phase runner | Stage 1 orchestrator extension |
| OpenAPI | Stage 1 frontend client |

## Freeze tests

```bash
uv run ruff check backend scripts tools
uv run basedpyright
uv run pytest
uv run python scripts/run_stage0_gate.py
```

## Amendment procedure

1. open decision/change request;
2. name contract owner;
3. list consumers and migration impact;
4. update producer and generated artefacts;
5. run contract and consumer tests;
6. rebase/notify affected tasks;
7. record old/new hash and approval here.

## Amendments

| Date | Change/CR | Old hash | New hash | Affected tasks | Approved by |
|---|---|---|---|---|---|
| — | — | — | — | — | — |
