# Contract Freeze — Stage 0

**Status:** DRAFT
**Freeze date:** pending (after S0-DOM-001 + S0-DB-002)
**Freeze owner:** parent coding agent
**Integration commit:** pending
**Stage document:** `25_STAGE_0_FOUNDATION.md`

## Frozen contracts

| Contract | Source | Generated artefact | Version/hash | Allowed change during freeze |
|---|---|---|---|---|
| Domain IDs/enums | S0-DOM-001 | docs/generated/domain-schemas | — | none/additive |
| Pydantic schemas | S0-DOM-001 | docs/generated/domain-schemas | — | — |
| Effect-command union | S0-DOM-001 / S0-SIM-001 | — | — | — |
| Repository/UoW ports | S0-DB-003 | — | — | — |
| Database migration head | S0-DB-002 | docs/generated/database-schema.sql | — | — |
| Event/outbox semantics | S0-SIM-002 / S0-ORCH-001 | — | — | — |
| Model gateway protocols | S0-MODEL-001 | — | — | — |
| Graph input/output | Stage 1+ | — | — | — |
| API DTO/event envelope | S0-API-001 | docs/generated/openapi.json | — | — |
| Seed manifest | S0-CONTENT-001 | seed/ | — | — |
| Monorepo layout | S0-ENG-001 / `19` §2 | — | handbook v1.0 | additive packages |

## Consumers

| Contract | Consumer tasks/modules |
|---|---|
| Monorepo layout | all Stage 0 tasks |

## Freeze tests

```bash
# After S0-DOM-001 / S0-DB-*: schema snapshots, import boundaries, generated artefact diff
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
