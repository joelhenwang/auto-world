# Integration Status

**Updated:** 2026-07-29T20:14:53Z
**Integration owner:** parent coding agent  
**Integration branch/worktree:** `cursor/s1-integration-5704` / `/workspace`
**Integration HEAD:** `8b64197` plus evidence/status handoff
**Target stage:** 1

## Contract baseline

| Contract | Frozen version/hash | Producer task | Consumers | Change allowed? |
|---|---|---|---|---|
| Stage 0 foundation | FROZEN (S0-QA-002) | Stage 0 | Stage 1 | additive only |
| Stage 1 action/scene schema | `0003_stage1_action_scene_tables` | S1-DB-001 | SIM-002/ORCH/API | candidate freeze |
| Stage 1 context/proposals | contract `1.0` | KNOW/MODEL/GRAPH | ORCH/SIM | candidate freeze |
| Stage 1 API/WebSocket | OpenAPI `7ca48ab0…f63a` | API | UI | additive v1 only |

## Task integration matrix

| Task ID | Branch | Owner | Status | Required predecessors | Files/contracts touched | Tests/evidence | Merge order |
|---|---|---|---|---|---|---|---:|
| S1-DB/KNOW/MODEL/SIM-001 | merged into integration branch | parent/subagents | VERIFIED | Stage 0 | migration/context/prompts/assembly | full gate | 1–4 |
| S1-GRAPH/SIM-002/ORCH | `cursor/s1-integration-5704` | integration subagent | VERIFIED | upstream Stage 1 | graphs/commit/runner | scenario/fault tests | 5 |
| S1-API/UI | `cursor/s1-integration-5704` | integration subagent | VERIFIED | projections stable | API/OpenAPI/frontend | API + frontend tests | 6 |
| S1-QA-001 | `cursor/s1-integration-5704` | integration subagent | GATE_PASS | all prior | gate/evidence | 154 offline + 2 live | 7 |

## Exact integration commands

```bash
uv sync
sudo chmod 666 /var/run/docker.sock
uv run python scripts/run_stage1_gate.py
```

## Current failures

No hard failures. Two Starlette/httpx deprecation warnings are non-blocking and
recorded in `docs/status/evidence/stage-1/pytest.txt`.
