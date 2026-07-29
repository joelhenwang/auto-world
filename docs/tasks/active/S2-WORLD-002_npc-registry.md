# `S2-WORLD-002` — NPC registry and actor v1

**Stage:** 2  
**Workstream:** WORLD  
**Status:** COMPLETE  
**Priority:** P0  
**Owner:** coding subagent (S2-WORLD-002)  
**Branch/worktree:** `cursor/s2-world-002-npc-085f`  
**Depends:** S2-WORLD-001 (proposal path), S2-KNOW-001 (NPC knowledge package)  
**AGENTS conceptual branch:** `task/S2-WORLD-002-npc-registry`

## Objective

```text
Director-only NPC proposal with dedup, compact cards, TTL/archive, and
knowledge packages that never include omniscient Director data.
```

## In scope

- Dedup search (name/location/role/traits/hook)
- Active budgets (scene ≤6 detailed NPCs; region ≤24; ≤3 new/day)
- Compact card + knowledge package
- TTL extension / archive with legacy summary
- Archived NPCs not scheduled for ordinary actor tasks

## Out of scope

- Promoting NPCs into focus slots; full off-screen inference

## Acceptance

- Duplicate blacksmith → existing NPC
- NPC context excludes Director-only knowledge
- Tests green; handoff written
