# `S2-GRAPH-001` — Stage 2 graph integrations

**Stage:** 2  
**Workstream:** GRAPH  
**Status:** COMPLETE  
**Priority:** P0  
**Depends:** S2-CHAR-001, S2-KNOW-001, S2-WORLD-001, S2-MEM-001  
**AGENTS conceptual branch:** `task/S2-GRAPH-001-stage2-graphs`  
**Branch/worktree:** `cursor/s2-graph-001-graphs-085f`

## Objective

Extend decision/reaction/resolver pipelines and add Director/NPC/MemoryConsolidation graph wrappers — bounded, fake-adapter deterministic, never direct-commit.

## In scope

- CharacterDecisionGraph with goals/plans/claims context
- Reaction for multi-party; NPCSceneGraph stub; DirectorProposalGraph; MemoryConsolidationGraph
- Restricted effect schemas; malformed repair path

## Out of scope

- LangGraph requirement; live provider gate dependency
