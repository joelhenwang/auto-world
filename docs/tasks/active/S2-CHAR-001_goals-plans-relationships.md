# `S2-CHAR-001` — Goals, plans, commitments, and relationships

**Stage:** 2  
**Workstream:** CHAR  
**Status:** COMPLETE  
**Priority:** P0  
**Owner:** parent coding agent  
**Branch/worktree:** `cursor/s2-char-001-goals-085f`  
**Upstream:** after S2-DB-001 (`0004`)  
**Depends:** S2-DB-001  
**AGENTS conceptual branch:** `task/S2-CHAR-001-goals-plans-relationships`

## 1. Objective

```text
Implement pure services for goals/plans/commitments and directional relationship
evidence aggregation so Stage 2 characters retain commitments and bounded
relationship movement without models writing aggregates directly.
```

## 2. Required reading

1. `AGENTS.md`, `27` S2-CHAR-001
2. `05` relationship/goal rules; `08` character continuity
3. `docs/status/CONTRACT_FREEZE.md`
4. Persistence from S2-DB-001 (`domain/continuity/persistence.py`, continuity repos)

## 3. Scope

### In scope

- Goal create/activate/complete/abandon + priority
- Plan create/revise + plan_step status; one active primary plan per goal
- Commitments with debtor/beneficiary/due/status
- Directional relationship evidence → bounded aggregate updates
- Relevance helpers for context assembly
- Unit tests: asymmetric relationships, diminishing repeats, betrayal, promise recall, plan invalidation

### Out of scope

- Observation/claim/belief engine (S2-KNOW-001)
- Director/NPC (S2-WORLD-*)
- API/UI

## 4. Acceptance

- [x] Model proposes evidence only; resolver applies bounded deltas
- [x] Trust cannot jump beyond configured normal-scene delta
- [x] Attraction not inferred from generic kindness
- [x] Personality/values unchanged in Stage 2
- [x] Tests green; handoff written
