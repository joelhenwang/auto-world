# Contract Freeze — Stages 0–2

**Status:** FROZEN (Stage 0 + Stage 1 + Stage 2)  
**Freeze date:** 2026-07-29  
**Freeze owner:** parent coding agent  
**Stage 1 integration commit:** `7727c7f69d935bba58dd6608c9504efe86aa9ec5` (main after PR #19)  
**Stage 2 freeze branch:** `cursor/s2-qa-001-gate-085f` (see `docs/status/evidence/stage-2/version-manifest.json`)  
**Stage documents:** `25_STAGE_0_FOUNDATION.md`, `26_STAGE_1_FIRST_COMPLETE_DAY.md`, `27_STAGE_2_SEVEN_DAY_WORLD.md`  
**Gate reports:**  
- Stage 0: `docs/status/evidence/stage-0/stage-gate-report.md`  
- Stage 1: `docs/status/evidence/stage-1/stage-gate-report.md`  
- Stage 2: `docs/status/evidence/stage-2/stage-gate-report.md`

## Frozen contracts — Stage 0

| Contract | Source | Generated artefact | Version/hash | Allowed change during freeze |
|---|---|---|---|---|
| Domain IDs/enums | S0-DOM-001 | `docs/generated/domain-schemas/` | generated tree | additive only via ADR |
| Pydantic schemas | S0-DOM-001 | `docs/generated/domain-schemas/` | generated tree | additive |
| Effect-command union | S0-DOM-001 / S0-SIM-001 | domain package | Stage 0 surface | additive kinds need ADR |
| Repository/UoW ports | S0-DB-003 | application ports | Stage 0 | additive methods OK |
| Database migration head (S0) | S0-DB-002 | `docs/generated/database-schema.sql` | through `0002` | superseded by Stage 1/2 heads |
| Event/outbox semantics | S0-SIM-002 / S0-ORCH-001 | — | Stage 0 | no silent reinterpretation |
| Model gateway protocols | S0-MODEL-001 | — | Stage 0 | additive |
| API DTO/event envelope (S0) | S0-API-001 | `docs/generated/openapi.json` | Stage 0 baseline | superseded by Stage 1/2 OpenAPI |
| Seed manifest | S0-CONTENT-001 | `seed/worlds/caldris-embervale-v1/` | `caldris-embervale-v1` | content_version bump |
| Task/idempotency keys | S0-ORCH-001/002 | — | Stage 0 | preserve key grammar |
| Monorepo layout | S0-ENG-001 / `19` §2 | — | handbook v1.0 | additive packages |

## Frozen contracts — Stage 1

| Contract | Source | Generated artefact / evidence | Version/hash | Allowed change in Stage 2+ |
|---|---|---|---|---|
| Migration head (S1) | S1-DB-001 | `docs/generated/database-schema.sql` | `0003_stage1_action_scene_tables` | **new revisions only** |
| `ActionProposal` / `ReactionProposal` / `SceneResolution` | S1-MODEL/GRAPH | domain schemas | `1.0` | additive fields via ADR |
| `SealedContextPackage` | S1-KNOW-001 | application context | `1.0` | additive sections + leakage tests |
| Scene tables/repos | S1-DB-001 | `worldsim.action_*` / `scene_*` / `stream_event` / … | `0003` | additive columns/tables |
| Scene atomic commit | S1-SIM-002 | `SceneCommitService` | Stage 1 | no alternate canon path |
| Phase/day orchestration | S1-ORCH-001 | `DeterministicPhaseRunner` Stage 1 profile | `stage1-first-day-v1` | preserve simultaneous intents + barriers |
| REST/WebSocket v1 core | S1-API-001 | `docs/generated/openapi.json` | Stage 1 baseline | additive endpoints/events |
| Prompt/corpus v1 | S1-MODEL-001 | `backend/prompts/**`, fixtures | character/reaction/resolver v1 | new prompt IDs for changes |
| First-day fake corpus | S1-QA-001 | `backend/tests/fixtures/model_corpus/stage1/` | `fake/stage1-first-day-v1` | additive scripts |

## Frozen contracts — Stage 2

| Contract | Source | Generated artefact / evidence | Version/hash | Allowed change in Stage 3 |
|---|---|---|---|---|
| Migration head | S2-DB-001 | `docs/generated/database-schema.sql` | `08236d04096262d07026aecb9e79bfeaf8aa9a6733d0c80d80a76f5cc77ccab2` / `0004_stage2_continuity_tables` | **new revisions only** |
| Continuity tables | S2-DB-001 | goals/plans/claims/beliefs/day_run/diary/… | `0004` | additive columns/tables |
| Seed content_version | S2-CONTENT-001 | `seed/worlds/caldris-embervale-v1/manifest.yaml` | `content_version: 2` | bump + fixture for Stage 3 |
| Goals/plans/commitments/relationships | S2-CHAR-001 | domain + repos | Stage 2 | additive fields via ADR |
| Observation→claim→belief + secret access | S2-KNOW-001 | application knowledge | Stage 2 | additive; keep isolation tests |
| Daily consolidation / diary / audit | S2-MEM-001 | `day-consolidation:{world}:{day}` | Stage 2 | no silent reinterpretation of sources |
| Director trigger/proposal v1 | S2-WORLD-001 | director application | v1 | additive trigger kinds |
| NPC registry/lifecycle v1 | S2-WORLD-002 | npc application | v1 | additive lifecycle states |
| Ten-phase calendar / travel / activation | S2-SIM-001 | simulation services | Stage 2 | preserve sleep/activation semantics |
| Multiparty scene assembly | S2-SIM-002 | scene assembly | Stage 2 | additive participant rules |
| Stage 2 graphs | S2-GRAPH-001 | agents package | Stage 2 | additive graphs |
| Seven-day orchestration | S2-ORCH-001 | `DeterministicPhaseRunner` stage2 profile | `stage2-seven-day-world-v1` | preserve day barrier + restart safety |
| REST/WebSocket Stage 2 queries | S2-API-001 | `docs/generated/openapi.json` | `ec9569b32e9308d771c90f357a3562829d28f218f099b22bc0b3599149b60bf2` | additive endpoints/events |
| Observer UI Stage 2 panels | S2-UI-001 | `frontend/**` | Stage 2 | additive views |
| Seven-day fake corpus | S2-QA-001 / ORCH | `backend/tests/fixtures/model_corpus/stage2/` | `fake/stage2-seven-day-v1` | additive scripts |

Key freeze hashes (recomputed by `scripts/run_stage2_gate.py`):

| Artefact | sha256 |
|---|---|
| `uv.lock` | `c43c220b80302e42f452d72c65a02e97ebd101ff73845fe866c1eb3010e5454e` |
| `frontend/pnpm-lock.yaml` | `22002950d79c21ad580902db44355d4e0f817b76e7a4ed2d4b8c3ed0520c32ac` |
| `docs/generated/openapi.json` | `ec9569b32e9308d771c90f357a3562829d28f218f099b22bc0b3599149b60bf2` |
| `docs/generated/database-schema.sql` | `08236d04096262d07026aecb9e79bfeaf8aa9a6733d0c80d80a76f5cc77ccab2` |

## Consumers (Stage 3)

| Contract | Consumer tasks |
|---|---|
| Stage 2 continuity/knowledge/memory | S3 memory retrieval, arcs, reflection |
| Stage 2 Director/NPC | stronger evaluation, factions |
| Migration `0004` | S3 schema revisions forward only |
| Stage 2 API/UI | additive long-horizon observer surfaces |

## Freeze tests

```bash
uv sync
sudo chmod 666 /var/run/docker.sock
uv run python scripts/run_stage1_gate.py
uv run python scripts/run_stage2_gate.py
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
| 2026-07-29 | S2-DB-001 additive migration `0004_stage2_continuity_tables` | `0003_stage1_action_scene_tables` | `0004_stage2_continuity_tables` | S2-* | parent |
| 2026-07-29 | Stage 2 gate → freeze Stage 2 contracts | candidate | FROZEN @ S2-QA-001 tip | S3-* | QA automated PASS; parent merge pending |
