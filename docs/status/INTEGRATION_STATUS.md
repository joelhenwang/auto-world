# Integration Status

**Updated:** 2026-07-29T23:50:00Z  
**Integration owner:** Stage 3 parent coding agent  
**Integration branch/worktree:** `cursor/s3-db-001-persistence-03fc`  
**Target stage:** 3 (IN_PROGRESS)  
**Main tip at Stage 3 kickoff:** `9294a5a`

## Contract baseline

| Contract | Status | Notes |
|---|---|---|
| Stage 0 | FROZEN | additive only |
| Stage 1 | FROZEN @ `7727c7f` / main includes | see `CONTRACT_FREEZE.md` |
| Stage 2 | FROZEN @ `9294a5a` | `0004` + content_version 2 |
| Stage 3 | IN_PROGRESS | new revisions after `0004` only |

## Task matrix

| Task ID | Status | Branch / notes |
|---|---|---|
| S2-* | VERIFIED on main | PR #34 integration |
| S3 kickoff/status | COMPLETE | this branch |
| S3-DB-001 | COMPLETE | `cursor/s3-db-001-persistence-03fc` / `0005` |
| S3-MEM-* / RULES-* / WORLD-* | READY | after DB merge |
| S3-GRAPH / ORCH / API / UI / QA | READY | dependency order |

## Merge order

```text
S3-DB-001
  → (S3-MEM-001 ‖ S3-RULES-001 ‖ S3-WORLD-001)
  → S3-MEM-002 → S3-MEM-003
  → S3-RULES-002 ‖ S3-RULES-003
  → S3-WORLD-002
  → S3-GRAPH-001 → S3-ORCH-001 → S3-API-001 → S3-UI-001 → S3-QA-001
```

One owner freezes before dependents: effect-command union expansions, memory access
policy, combat formulas, active-arc state machine.

## Gate commands

```bash
sudo chmod 666 /var/run/docker.sock
uv run python scripts/run_stage1_gate.py   # must remain green
uv run python scripts/run_stage2_gate.py   # must remain green
uv run python scripts/run_stage3_gate.py   # Stage 3 hard exit (S3-QA-001)
```

## Current failures

Preflight found merge-regression basedpyright/ruff issues in
`domain/continuity/__init__.py` (duplicate imports / incomplete `__all__`) on main tip
`9294a5a`. Fixed on this Stage 3 branch before S3-DB-001 schema work. Stage 2 evidence
artefacts left restored to frozen PASS (do not overwrite with failed re-runs casually).
