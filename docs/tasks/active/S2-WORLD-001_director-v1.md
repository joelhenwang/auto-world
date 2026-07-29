# `S2-WORLD-001` — Narrative Director v1

**Stage:** 2  
**Workstream:** WORLD  
**Status:** COMPLETE  
**Priority:** P0  
**Owner:** parent coding agent  
**Branch/worktree:** `cursor/s2-world-001-director-085f`  
**Depends:** S2-DB-001  
**AGENTS conceptual branch:** `task/S2-WORLD-001-director-v1`

## Objective

```text
Implement deterministic Director trigger metrics and a validated proposal path
that commits only through the normal resolver — never choosing scene outcomes.
```

## In scope

- Trigger metrics: phases since meaningful choice, repeated patterns, goal stagnation, unresolved hooks, intensity trend, disruption cooldown
- DirectorProposal schema + validation (no secret reveal without path; no mandatory romance; cooldown)
- Safe no-event fallback
- Persist hook / narrative_metric updates
- Unit tests with stagnation fixture and healthy progression (no call)

## Out of scope

- NPC registry (S2-WORLD-002); Temporal; generation arcs

## Acceptance

- No call during healthy progression; trigger on stagnation
- Proposal cannot reveal secret without disclosure path
- Tests green; handoff written
