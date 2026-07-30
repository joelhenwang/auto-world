# `S3-DB-001` — Stage 3 long-term persistence

**Stage:** 3  
**Workstream:** DB  
**Status:** IN_PROGRESS  
**Priority:** P0  
**Owner:** parent coding agent  
**Branch/worktree:** `cursor/s3-db-001-persistence-03fc`  
**Upstream commit:** `9294a5a` (main after Stage 2 integration)  
**Target merge order:** first Stage 3 implementation packet  
**AGENTS conceptual branch:** `task/S3-DB-001-long-term-persistence`

---

## 1. Objective

```text
Add Stage 3 tables for long-term memory/embeddings, stats/skills/magic/injuries,
items, factions/arcs, trope/novelty, evaluator/export so later packets can persist
a thirty-day month without altering frozen Stage 0–2 tables.
```

## 2. Why this task exists

- Requirements: Stage 3 long-horizon memory/rules/world (FR-MEM / FR-RULES / FR-WORLD)
- Stage gate: `28` §9 exit criteria depend on these entities
- Upstream: Stage 2 freeze (`0004_stage2_continuity_tables`)
- Downstream: S3-MEM-*, S3-RULES-*, S3-WORLD-*, S3-ORCH-001, S3-QA-001

## 3. Required reading

1. `AGENTS.md`
2. `28_STAGE_3_AUTONOMOUS_MONTH.md` §5–§7 S3-DB-001
3. `05`, `06` (memory §12, stats/skills/magic §14, arcs/factions §15)
4. `docs/status/CONTRACT_FREEZE.md` (Stages 0–2 FROZEN)
5. Existing `0004_stage2_continuity_tables.py` and Stage 2 schema tests

## 4. Frozen contracts

| Contract | Version | Allowed change |
|---|---|---|
| Stage 0–2 tables / through `0004` | FROZEN | none — new revision only |
| EffectCommand union | Stage 2 | additive kinds via ADR later (not this packet) |
| UoW ports | Stage 2 | additive repos/methods OK |
| Seed content_version | `2` | bump deferred to content packet |

## 5. Scope

### In scope

Tables (handbook `28` S3-DB-001; extend existing `hook`/`summary`/`scheduled_effect` only if additive columns required — prefer new tables):

```text
memory, memory_source, memory_embedding,
embedding_model_version, embedding_job, retrieval_trace,
monthly_chapter, reflection_run, character_trait_version,
stat_state, stat_potential,
skill_definition, skill_state, skill_progress_evidence,
spell_definition, known_spell, magic_affinity,
item, inventory_entry, equipment_state,
condition, injury, recovery_plan,
faction, faction_membership, faction_relation, faction_state,
settlement_indicator,
arc,
trope_usage, novelty_signature,
evaluator_run, quality_finding,
export_run, month_run
```

Also: Alembic `0005_*`, ORM models, domain persistence records, additive repos/UoW
stubs needed by later packets, migration + constraint tests, regenerate
`docs/generated/database-schema.sql`.

### Explicitly out of scope

- Embedding pipeline / retrieval logic (S3-MEM-*)
- Combat/magic domain formulas (S3-RULES-*)
- Arc/faction simulation services (S3-WORLD-*)
- Effect-command union expansions (freeze owner later)
- API/UI, thirty-day orchestration, Stage 4+

## 6. File/path ownership

### Writable

```text
backend/migrations/versions/0005_*.py
backend/src/fictional_world/domain/memory/**
backend/src/fictional_world/domain/rules/** (persistence records only if needed)
backend/src/fictional_world/domain/world/** (persistence records additive)
backend/src/fictional_world/infrastructure/database/models/**
backend/src/fictional_world/infrastructure/database/repositories/**
backend/src/fictional_world/infrastructure/database/mappings/**
backend/src/fictional_world/infrastructure/database/unit_of_work.py
backend/src/fictional_world/application/ports/repositories.py
backend/tests/integration/test_stage3_schema*
backend/tests/integration/test_migrations_baseline.py (head assertion)
scripts/export_database_schema.py (header revision comment)
docs/generated/database-schema.sql
docs/tasks/active/S3-DB-001_*
docs/status/**
docs/handoffs/**
backend/src/fictional_world/domain/continuity/__init__.py  # gate unblocker fix
```

## 7. Assumptions

- ASSUMP-S3-001: Column layouts follow handbook `06` where present; otherwise Stage 2 naming/CHECK conventions.
- ASSUMP-S3-002: `memory` is a new table alongside existing `recent_memory` (no silent reinterpretation of Stage 0 recent_memory).
- ASSUMP-S3-003: Embedding dimension baseline is 2048; column is `vector(2048)`; HNSW deferred.
- ASSUMP-S3-004: Existing Stage 2 `hook` / `summary` / `scheduled_effect` remain; Stage 3 adds `arc` and related metrics tables rather than replacing hooks.
- ASSUMP-S3-005: Table name `skill_definition` / `spell_definition` match handbook `06` §14 (packet list used shorthand `skill` / `spell`).

## 8. Required tests

- Migration upgrade/downgrade/upgrade; single head `0005`
- Stage 3 tables exist; named constraints/indexes
- Unique constraints for memory (owner+hash+version), memory_embedding identity, stat_state PK, skill_state, known_spell
- Owner/visibility columns present on memory for query-layer filtering
- pgvector column accepts `vector(2048)` writes

## 9. Acceptance criteria

- [x] Sole Alembic head after `0004`
- [x] Named constraints/indexes; no opaque “character state” JSON substitute for rule entities
- [x] Repos + UoW wired for core Stage 3 aggregates (insert/get stubs OK)
- [x] Integration tests green with Docker
- [x] Schema snapshot regenerated through `0005`
- [x] Handoff written
- [x] Stage 1/2 static checks remain green after continuity `__init__` fix

## 10. Handoff recipient

Parent → S3-MEM-001 / S3-RULES-001 / S3-WORLD-001

**Status:** COMPLETE (implementation) — awaiting parent review/merge
