# `S2-DB-001` — Stage 2 persistence extensions

**Stage:** 2  
**Workstream:** DB  
**Status:** READY  
**Priority:** P0  
**Owner:** parent coding agent  
**Branch/worktree:** TBD `cursor/s2-db-001-5704`  
**Upstream commit:** `7727c7f` (main after Stage 1)  
**Target merge order:** first Stage 2 implementation packet  
**AGENTS conceptual branch:** `task/S2-DB-001-persistence-extensions`

---

## 1. Objective

```text
Add Stage 2 tables for goals/plans/commitments, relationships, claims/beliefs,
activities/travel, Director hooks, NPC lifecycle, and summaries so later packets
can persist seven-day continuity without altering frozen Stage 1 tables.
```

## 2. Why this task exists

- Requirements: Stage 2 continuity / FR-CHAR / FR-KNOW / FR-WORLD
- Stage gate: `27` § hard exit (beliefs, relationships, travel, NPCs, diaries)
- Upstream: Stage 1 freeze (`0003_stage1_action_scene_tables`)
- Downstream: S2-CHAR-001, S2-KNOW-001, S2-MEM-001, S2-WORLD-*, S2-SIM-*

## 3. Required reading

1. `AGENTS.md`
2. `27_STAGE_2_SEVEN_DAY_WORLD.md` §5–§7, S2-DB-001
3. `05`, `06` (relevant table sections)
4. `docs/status/CONTRACT_FREEZE.md` (Stage 1 FROZEN)
5. Existing `0003_stage1_action_scene_tables.py` and Stage 1 scene repos

## 4. Frozen contracts

| Contract | Version | Allowed change |
|---|---|---|
| Stage 1 tables / `0003` | FROZEN | none — new revision only |
| EffectCommand / SceneCommit | Stage 1 | additive kinds via ADR later |
| UoW ports | Stage 1 | additive repos/methods OK |

## 5. Scope

### In scope

Tables/extensions (handbook `27` S2-DB-001):

```text
goal, plan, plan_step, commitment,
relationship_edge, relationship_evidence,
claim, belief, belief_evidence, secret_access,
activity, activity_participant, travel_progress, route,
hook, narrative_metric, npc_profile, npc_lifecycle,
summary (+ summary_source if required by 06)
```

Also: Alembic `0004_*`, ORM models, domain persistence records, additive repos/UoW, migration + constraint tests, regenerate `docs/generated/database-schema.sql`.

### Explicitly out of scope

- Vector/embedding tables
- Domain services for beliefs/relationships (S2-CHAR / S2-KNOW)
- Director/NPC graphs, travel logic, API/UI
- Reinterpreting Stage 1 scene/action semantics

## 6. File/path ownership

### Writable

```text
backend/migrations/versions/0004_*.py
backend/src/fictional_world/domain/**/persistence.py (additive)
backend/src/fictional_world/infrastructure/database/models/**
backend/src/fictional_world/infrastructure/database/repositories/**
backend/src/fictional_world/infrastructure/database/mappings/**
backend/src/fictional_world/infrastructure/database/unit_of_work.py
backend/src/fictional_world/application/ports/repositories.py
backend/tests/integration/test_stage2_schema*
docs/generated/database-schema.sql
docs/tasks/active/S2-DB-001_*
docs/status/** (integration notes only)
docs/handoffs/**
```

## 7. Assumptions

- ASSUMP-S2-001: Column layouts follow handbook `06` where present; otherwise Stage 1 naming/CHECK conventions.
- ASSUMP-S2-002: `claim` / `belief` land here even if Stage 1 deferred them; no silent rewrite of `observation` / `recent_memory`.

## 8. Required tests

- Migration upgrade/downgrade/upgrade; single head `0004`
- Unique constraints for relationship edge, belief owner+key, NPC id
- Duplicate rejection for commitment/plan_step where specified

## 9. Acceptance criteria

- [ ] Sole Alembic head after `0003`
- [ ] Named constraints/indexes
- [ ] Repos + UoW wired for new aggregates needed by CHAR/KNOW stubs
- [ ] Integration tests green with Docker
- [ ] Schema snapshot regenerated
- [ ] Handoff written

## 10. Handoff recipient

Parent → S2-CHAR-001 / S2-KNOW-001 / S2-CONTENT-001
