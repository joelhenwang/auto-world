# `S1-KNOW-001` — Perception and context assembler v1

**Stage:** 1 | **Workstream:** KNOW | **Status:** IN_PROGRESS | **Priority:** P0  
**Owner:** parent agent | **Branch:** `cursor/s1-know-001-5704`  
**Upstream:** main `0c58f6d` | **Depends:** Stage 0 freeze (DB contracts sketched)  
**AGENTS conceptual branch:** `task/S1-KNOW-001-context-assembler`

## Objective

```text
Assemble sealed perspective-safe character context packages for Mira and Dain
from the same phase snapshot, with provenance hashing, token trimming, and
leakage tests — no vector/RAG retrieval.
```

## In scope

- `application/context/**` SealedContextPackage + assembler + budget + hashing
- Directional relationship + goal Stage 1 fixtures (seed YAML)
- Leakage / hash / trim unit tests

## Out of scope

- Vector memory, belief engine writes, graphs, scene commit, API

## Acceptance

- Same snapshot ID for both characters
- Private belief of other character absent
- True reverse relationship row absent
- Malicious memory delimiter neutralized
- Deterministic package_hash
