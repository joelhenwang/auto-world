# Contract Freeze — Stages 0–1

**Status:** FROZEN (Stage 0 + Stage 1)  
**Freeze date:** 2026-07-29  
**Freeze owner:** parent coding agent  
**Integration commit:** `7727c7f69d935bba58dd6608c9504efe86aa9ec5` (main after PR #19)  
**Stage documents:** `25_STAGE_0_FOUNDATION.md`, `26_STAGE_1_FIRST_COMPLETE_DAY.md`  
**Gate reports:**  
- Stage 0: `docs/status/evidence/stage-0/stage-gate-report.md`  
- Stage 1: `docs/status/evidence/stage-1/stage-gate-report.md`

## Frozen contracts — Stage 0

| Contract | Source | Generated artefact | Version/hash | Allowed change during freeze |
|---|---|---|---|---|
| Domain IDs/enums | S0-DOM-001 | `docs/generated/domain-schemas/` | generated tree | additive only via ADR |
| Pydantic schemas | S0-DOM-001 | `docs/generated/domain-schemas/` | generated tree | additive |
| Effect-command union | S0-DOM-001 / S0-SIM-001 | domain package | Stage 0 surface | additive kinds need ADR |
| Repository/UoW ports | S0-DB-003 | application ports | Stage 0 | additive methods OK |
| Database migration head (S0) | S0-DB-002 | `docs/generated/database-schema.sql` | through `0002` | superseded by Stage 1 head |
| Event/outbox semantics | S0-SIM-002 / S0-ORCH-001 | — | Stage 0 | no silent reinterpretation |
| Model gateway protocols | S0-MODEL-001 | — | Stage 0 | additive |
| API DTO/event envelope (S0) | S0-API-001 | `docs/generated/openapi.json` | Stage 0 baseline | superseded by Stage 1 OpenAPI |
| Seed manifest | S0-CONTENT-001 | `seed/worlds/caldris-embervale-v1/` | `caldris-embervale-v1` | content_version bump |
| Task/idempotency keys | S0-ORCH-001/002 | — | Stage 0 | preserve key grammar |
| Monorepo layout | S0-ENG-001 / `19` §2 | — | handbook v1.0 | additive packages |

## Frozen contracts — Stage 1

| Contract | Source | Generated artefact / evidence | Version/hash | Allowed change in Stage 2 |
|---|---|---|---|---|
| Migration head | S1-DB-001 | `docs/generated/database-schema.sql` | `d5affce1…7fae` / `0003_stage1_action_scene_tables` | **new revisions only** |
| `ActionProposal` / `ReactionProposal` / `SceneResolution` | S1-MODEL/GRAPH | domain schemas | `1.0` | additive fields via ADR |
| `SealedContextPackage` | S1-KNOW-001 | application context | `1.0` | additive sections + leakage tests |
| Scene tables/repos | S1-DB-001 | `worldsim.action_*` / `scene_*` / `stream_event` / … | `0003` | additive columns/tables |
| Scene atomic commit | S1-SIM-002 | `SceneCommitService` | Stage 1 | no alternate canon path |
| Phase/day orchestration | S1-ORCH-001 | `DeterministicPhaseRunner` Stage 1 profile | `stage1-first-day-v1` | preserve simultaneous intents + barriers |
| REST/WebSocket v1 core | S1-API-001 | `docs/generated/openapi.json` | `7ca48ab0…f63a` | additive endpoints/events |
| Prompt/corpus v1 | S1-MODEL-001 | `backend/prompts/**`, fixtures | character/reaction/resolver v1 | new prompt IDs for changes |
| First-day fake corpus | S1-QA-001 | `backend/tests/fixtures/model_corpus/stage1/` | `fake/stage1-first-day-v1` | additive scripts |

## Consumers (Stage 2)

| Contract | Consumer tasks |
|---|---|
| Stage 1 proposals/context/commit | S2-GRAPH-*, S2-SIM-*, S2-ORCH-* |
| Stage 1 API/WS | S2-API-001, S2-UI-001 |
| Migration `0003` | S2-DB-001 (revises forward only) |

## Freeze tests

```bash
uv sync
sudo chmod 666 /var/run/docker.sock
uv run python scripts/run_stage1_gate.py
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
| 2026-07-29 | S1-DB-001 additive migration `0003_stage1_action_scene_tables` | `0002_core_stage0_tables` | `0003_stage1_action_scene_tables` | S1-* | parent (merged PR #19) |
| 2026-07-29 | Stage 1 gate merge → freeze Stage 1 contracts | candidate | FROZEN @ `7727c7f` | S2-* | parent |
