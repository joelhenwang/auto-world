# `S2-KNOW-001` — Claims, beliefs, secrets, observation engine v2

**Stage:** 2  
**Workstream:** KNOW  
**Status:** READY  
**Priority:** P0  
**Owner:** parent coding agent  
**Branch/worktree:** TBD `cursor/s2-know-001-*-085f`  
**Upstream:** after S2-DB-001  
**Depends:** S2-DB-001  
**AGENTS conceptual branch:** `task/S2-KNOW-001-claims-beliefs-observation`

## 1. Objective

```text
Implement observation→claim→belief pipeline v2 with secret access policy and
leakage tests so four-character weeks never expose unauthorized knowledge.
```

## 2. Required reading

1. `AGENTS.md`, `27` S2-KNOW-001, `11` perception/knowledge
2. Existing `application/context/` assembler + Stage 1 leakage tests
3. S2-DB-001 claim/belief/secret_access tables

## 3. Scope

### In scope

- Observable fact keys + observer eligibility
- Direct / hearing-only / partial / absent observation paths
- Lies as claims (not facts); rumour as sourced claim
- Belief evidence + confidence updates
- Secret access policy; knowledge lookup restricted by observer
- Leakage tests (≥ Stage 2 seed secrets + NPC/player projections)

### Out of scope

- Daily consolidation/diaries (S2-MEM-001)
- Vector memory
- Director omniscient disclosure bypass

## 4. Acceptance

- [ ] Seeded Mira secret not in Dain/Iri/Torren contexts
- [ ] Lie → claim not objective fact
- [ ] Two witnesses may diverge
- [ ] Prompt injection in observation cannot escalate authority
- [ ] Tests green; handoff written
