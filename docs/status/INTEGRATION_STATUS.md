# Integration Status

**Updated:** 2026-07-30T03:00:00Z  
**Integration owner:** Stage 4 parent coding agent  
**Integration branch/worktree:** `cursor/s4-integration-8b4a`  
**Target stage:** 4 (ACTIVE)  
**Main tip at Stage 4 kickoff:** `05db78a`

## Contract baseline

| Contract | Status | Notes |
|---|---|---|
| Stage 0–3 | FROZEN | see `CONTRACT_FREEZE.md` |
| Migration head | `0005_stage3_long_term_tables` | Stage 4 adds `0006+` only |
| Stage 4 | ACTIVE | S4-BENCH-001 first |

## Task matrix

| Task | Status | Notes |
|---|---|---|
| S4-BENCH-001 | COMPLETE | corpus + harness + ADR-0002 |
| S4-MODEL-001 | IN_PROGRESS | local adapters + registry |
| S4-MODEL-002 | READY | packet authored |
| S4-ORCH-001 | READY | packet authored; owns `0006` if needed |
| S4-ORCH-002 | COMPLETE | ADR-0003 DEFER; DB orchestrator = Stage 4 prod path; noop port |
| S4-STORAGE-001 | COMPLETE | migration 0007_stage4_img; FakeObjectStore/MinIO; prefix policy |
| S4-IMG-001 | COMPLETE | ComfyUI adapter + fake + workflow registry |
| S4-IMG-002 | COMPLETE | visual_profile table + prompt compiler |
| S4-IMG-003 | COMPLETE | QC + gallery lifecycle; phase isolation guaranteed |
| S4-OPS-001 | PENDING | |
| S4-API-001 | PENDING | |
| S4-UI-001 | PENDING | |
| S4-QA-001 | PENDING | |

## Gate commands (regression)

```bash
sudo service docker start
sudo chmod 666 /var/run/docker.sock
uv run pytest -q
uv run python scripts/run_stage3_gate.py
# Stage 4 gate (when S4-QA-001 lands):
# uv run python scripts/run_stage4_gate.py
```

## Current failures

None at kickoff. Offline baseline green on main `05db78a`.
