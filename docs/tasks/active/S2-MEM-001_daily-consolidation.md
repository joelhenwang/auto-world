# `S2-MEM-001` — Daily consolidation and diary pipeline

**Stage:** 2  
**Workstream:** MEM  
**Status:** COMPLETE  
**Priority:** P0  
**Owner:** parent coding agent  
**Branch/worktree:** `cursor/s2-mem-001-diaries-085f`  
**Depends:** S2-KNOW-001  
**AGENTS conceptual branch:** `task/S2-MEM-001-daily-consolidation`

## Objective

```text
At day completion, consolidate each character's observations into perspective
summaries and diaries with source provenance, without deleting raw observations
or leaking secrets.
```

## In scope

- Collect observations/recent memories per character for the day
- Group by event/scene while preserving source IDs
- Salience update; daily perspective summary (fake-model or extractive fallback)
- Extract stable belief/relationship/goal evidence hooks (call CHAR/KNOW services if available)
- Compact routine duplicates without deleting raw records
- Write diary_entry + summary + summary_source + daily_audit rows
- Idempotent retry (no duplicate summaries for same day/version)

## Out of scope

- Vector embeddings; monthly reflection; live model required for gate

## Acceptance

- Source completeness; perspective filtering; diary has no absent secrets
- Failed model → extractive fallback; retry safe
- Tests green; handoff written
