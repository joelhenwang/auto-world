# Integration Status

**Updated:** 2026-07-29T23:30:00Z  
**Integration owner:** Stage 2 parent coding agent  
**Integration branch/worktree:** `cursor/s2-qa-001-gate-085f`  
**Target stage:** 2 (GATE_PASS / FROZEN)  
**Main tip at Stage 2 kickoff:** `5c9299e`

## Contract baseline

| Contract | Status | Notes |
|---|---|---|
| Stage 0 | FROZEN | additive only |
| Stage 1 | FROZEN @ `7727c7f` | see `CONTRACT_FREEZE.md` |
| Stage 2 | FROZEN (QA PASS) | `0004` + content_version 2; see evidence |
| Stage 3 | READY | not started |

## Task matrix

| Task ID | Status | Branch / notes |
|---|---|---|
| S1-* | VERIFIED on main | PR #19 |
| S2 kickoff/freeze docs | MERGED | PR #20 |
| S2-DB-001 | COMPLETE | continuity migration `0004` |
| S2-CONTENT-001 | COMPLETE | seed content_version 2 |
| S2-CHAR-001 | COMPLETE | goals/plans/relationships |
| S2-KNOW-001 | COMPLETE | claims/beliefs/secrets |
| S2-MEM-001 | COMPLETE | daily consolidation/diaries |
| S2-WORLD-001 | COMPLETE | Director trigger/proposal v1 |
| S2-WORLD-002 | COMPLETE | NPC registry/lifecycle v1 |
| S2-SIM-001 | COMPLETE | calendar/activation/travel |
| S2-SIM-002 | COMPLETE | multiparty scenes |
| S2-GRAPH-001 | COMPLETE | Stage 2 graphs |
| S2-ORCH-001 | COMPLETE | seven-day workflow |
| S2-API-001 | COMPLETE | Stage 2 queries/commands |
| S2-UI-001 | COMPLETE | observer panels |
| S2-QA-001 | COMPLETE | gate script + evidence PASS |

## Merge order

```text
S2-DB-001 → S2-CONTENT-001 → (CHAR ‖ KNOW) → MEM ‖ WORLD* → SIM → GRAPH → ORCH → API → UI → QA
```

## Gate commands

```bash
sudo chmod 666 /var/run/docker.sock
uv run python scripts/run_stage1_gate.py   # must remain green
uv run python scripts/run_stage2_gate.py   # Stage 2 hard exit
```

## Current failures

None. Stage 2 automated gate PASS; human rubric worksheet blank (non-blocking).
