# `S1-DB-001` — Action/scene persistence

**Stage:** 1  
**Workstream:** DB  
**Status:** IN_PROGRESS  
**Priority:** P0  
**Owner:** parent coding agent  
**Reviewer(s):** parent integration  
**Branch/worktree:** `cursor/s1-db-001-5704`  
**Upstream commit:** `0c58f6d` (main after S0-QA-002)  
**Target merge order:** first Stage 1 packet (before SIM-002 / ORCH)  
**AGENTS conceptual branch:** `task/S1-DB-001-action-scene-persistence`

---

## 1. Objective

```text
Add Stage 1 action/scene/reaction/resolution/narration/stream/player_control
tables, ORM models, domain persistence records, and repository ports so later
packets can persist simultaneous intents and atomic scene commits without
altering frozen Stage 0 tables.
```

## 2. Why this task exists

- Requirements: FR-SCENE-*, FR-CHAR-*, restart/idempotency NFRs
- Stage gate: `26` §8 (snapshot-linked actions, typed effects, restart safety)
- Risks mitigated: missing durable scene state, duplicate primary actions
- Upstream: Stage 0 freeze (`0002_core_stage0_tables`)
- Downstream: S1-SIM-002, S1-ORCH-001, S1-API-001

## 3. Required reading

1. `AGENTS.md`
2. `26_STAGE_1_FIRST_COMPLETE_DAY.md` §3, §6 S1-DB-001
3. `05_DOMAIN_CONTRACTS_AND_STATE_MACHINES.md` (ActionProposal/SceneResolution)
4. `06_PERSISTENCE_DATABASE_AND_EVENT_LOG.md` §9
5. `17_BACKEND_API_AND_REALTIME_EVENTS.md` §19 (stream envelope)
6. `docs/status/CONTRACT_FREEZE.md`
7. Existing `0002_core_stage0_tables.py`, UoW/repos, domain `scenes/`

## 4. Frozen contracts

| Contract | Version/hash/commit | Owner | Allowed change |
|---|---|---|---|
| Stage 0 tables / `0002` | FROZEN | Stage 0 | none — new revision only |
| EffectCommand union | Stage 0 surface | DOM | additive kinds via ADR later |
| Repository/UoW ports | Stage 0 | DB | additive methods/repos OK |
| ActionProposal Pydantic | Stage 0 domain | DOM | already present; persist only |

## 5. Scope

### In scope

- Alembic `0003_stage1_action_scene_tables`
- Tables: `action_proposal`, `action_target`, `scene`, `scene_action`, `scene_participant`, `reaction_proposal`, `scene_resolution`, `scene_run`, `narration`, `stream_event`, `player_control_session`
- Optional FK: `world_event.scene_id` → `scene.id`
- Domain persistence records + ORM + mappers
- Additive repository ports + SQLAlchemy impl + UoW wiring
- Integration tests: migration round-trip; duplicate action/participant rejection
- Update `docs/generated/database-schema.sql` when exportable

### Explicitly out of scope

- Context assembler (S1-KNOW-001)
- Graphs / scene assembly logic (GRAPH/SIM packets)
- Enabling new effect validators beyond Stage 0
- API/WebSocket handlers (S1-API-001)
- Frontend
- Claim/belief/embedding tables (Stage 2 / later unless needed by commit)

## 6. File/path ownership

### Writable

```text
backend/migrations/versions/0003_*.py
backend/src/fictional_world/domain/scenes/**
backend/src/fictional_world/infrastructure/database/models/**
backend/src/fictional_world/infrastructure/database/repositories/**
backend/src/fictional_world/infrastructure/database/mappings/**
backend/src/fictional_world/infrastructure/database/unit_of_work.py
backend/src/fictional_world/application/ports/repositories.py
backend/tests/integration/test_stage1_schema*
docs/generated/database-schema.sql
docs/tasks/active/S1-DB-001_*
docs/status/**
docs/handoffs/**
```

### Read-only dependencies

```text
backend/migrations/versions/0001_*.py
backend/migrations/versions/0002_*.py
docs/status/CONTRACT_FREEZE.md
```

## 7. Assumptions

- ASSUMP-S1-001: `scene_run`, `narration`, `stream_event`, `player_control_session` are Stage 1 operational tables not fully column-specified in `06`; columns follow `05` SceneRun, `17` stream envelope, and player-control needs.
- ASSUMP-S1-002: One primary action uniqueness is `(phase_run_id, actor_id)` for `proposal_kind='primary'`.
- ASSUMP-S1-003: `world_event.scene_id` gains an FK only after `scene` exists; nullable remains for Stage 0 events.

## 8. Non-goals

- Combat/injury/inventory/NPC/Director tables
- Vector/RAG memory
- Breaking Stage 0 idempotency or event semantics

## 9. Dependencies

- Stage 0 gate on main
- Docker for migration/integration tests

## 10. Required tests

- Migration upgrade head / downgrade -1 / upgrade head
- Duplicate primary action rejected
- Duplicate scene participant rejected
- Resolution idempotency unique key
- Alembic single head

## 11. Acceptance criteria

- [ ] New revision is sole Alembic head after `0002`
- [ ] Named constraints/indexes follow Stage 0 convention
- [ ] Repos insert/get by id and idempotency key
- [ ] UoW exposes new repos
- [ ] Integration tests green with Docker
- [ ] Status/handoff updated

## 12. Handoff recipient

Parent agent → next packets S1-KNOW-001 / S1-SIM-001 / S1-MODEL-001
