# `S1-INTEGRATION-001` — Remaining Stage 1 vertical slice

**Stage:** 1  
**Workstream:** GRAPH/SIM/ORCH/API/UI/QA  
**Status:** COMPLETE_PENDING_PARENT_REVIEW
**Priority:** P0  
**Owner:** integration subagent  
**Reviewer(s):** parent integration agent  
**Branch/worktree:** `cursor/s1-integration-5704` / `/workspace`  
**Upstream commit:** `0e60c89`  
**Target merge order:** after S1-DB-001, S1-KNOW-001, S1-MODEL-001, S1-SIM-001

## 1. Objective

Complete the remaining Stage 1 vertical slice so the deterministic fake-model
`stage1-first-day-v1` scenario advances dawn → morning → evening for Mira and
Dain with one sealed snapshot per phase, isolated contexts, idempotent atomic
scene commits, restart-safe orchestration, perspective-safe API/WebSocket
basics, and a minimal Vue client.

## 2. Why this task exists

- Requirements: FR-SCENE-001–014, FR-MEM-002/004/006, FR-UI-001/006/008,
  NFR-COR-002/003, NFR-REL-001/003, NFR-SEC-005, NFR-PERF-003.
- Stage gate: handbook `26` §8 and `21` §22.
- Risks: R-001–004, R-020–022, R-037, R-048–050.
- Upstream: S1-DB-001, S1-KNOW-001, S1-MODEL-001, S1-SIM-001.
- Delivers: S1-GRAPH-001/002, S1-SIM-002, S1-ORCH-001, S1-API-001,
  S1-UI-001, and S1-QA-001 integration.

## 3. Required reading

1. `README.md`, `AGENTS.md`, and `docs/status/CURRENT_STAGE.md`;
2. handbook `02`–`07`, `11`–`15`, `17`–`19`, `21`, `23`, `26`, and `32`;
3. `docs/status/CONTRACT_FREEZE.md` and existing ADRs;
4. active Stage 1 task packets and handoffs;
5. existing agent/model/context/simulation/orchestration/API/seed/test code.

## 4. Frozen contracts

| Contract | Version | Owner | Allowed change |
|---|---|---|---|
| Stage 0 canon/effects/event commit | Stage 0 freeze | domain/simulation | additive only |
| Stage 1 action/scene schema | migration `0003` | DB | no reinterpretation |
| ActionProposal/ReactionProposal/SceneResolution | `1.0` | domain | none |
| SealedContextPackage | S1-KNOW-001 | context | additive only |
| Prompt/gateway protocols | S1-MODEL-001 | model | additive only |
| SceneDraft assembly | S1-SIM-001 | simulation | none |

## 5. Scope

### In scope

- Plain async bounded character-decision, reaction, resolver, and narrator
  pipelines with repair → one regeneration → deterministic fallback.
- Atomic scene execution persistence through `EventCommitService`, including
  observations, recent memories, narration and stream/outbox records.
- Stage 1 dawn/morning/evening orchestrator profile, same-snapshot parallel
  decisions, barriers, budget reservation, pause/resume, and retry boundaries.
- Stage 1 seed fixture for Mira, Dain, the inn, Market Square, and East Bridge.
- Additive REST/WebSocket routes and generated OpenAPI.
- Minimal Vue 3/TypeScript client and focused component/client tests.
- Deterministic scenario, fault/leakage coverage, Stage 1 gate script/evidence,
  current status, contract freeze, session log, task status, and handoff.

### Explicitly out of scope

- LangGraph dependency, autonomous Director, Stage 2 beliefs/claims engine,
  combat, injury, inventory transfer, full magic, NPC creation, vector RAG,
  images, distributed workers, and production authentication.
- Live OpenRouter as a deterministic/default test dependency.
- Breaking changes to Stage 0 or merged Stage 1 contracts.

## 6. File/path ownership

Writable paths are `backend/src/fictional_world/agents/**`,
`backend/src/fictional_world/application/**`,
`backend/src/fictional_world/infrastructure/database/**`,
`backend/src/fictional_world/interfaces/**`, `backend/tests/**`, `seed/**`,
`frontend/**`, `scripts/**`, `tools/scenario_harness/**`, generated API
artifacts, and Stage 1 task/status/evidence/handoff documents. Existing
migrations are read-only; no schema change is planned.

## 7. Data and migration ownership

No new migration. S1-SIM-002 targets migration `0003` repositories and Stage 0
event/observation/memory/outbox tables. Stage 1 fixture content is additive.

## 8. Interface inputs and outputs

- Inputs: sealed context packages, model gateway results, Stage 1 domain
  proposals, scene drafts, typed effects, phase/task records, API commands.
- Outputs: persisted proposals/scenes/reactions/resolutions, one idempotent
  committed event per scene, owner-scoped observations/memories, durable stream
  records, phase/day terminal state, perspective-safe DTOs.
- Errors: malformed/invalid model output uses bounded repair/regeneration and
  safe fallback; identity/snapshot corruption surfaces; high-impact ambiguity
  fails closed.
- Idempotency: deterministic graph request, task, resolution, commit, outbox,
  stream, observation, memory, and user-command keys.
- Concurrency: model calls occur without an open UoW; primary decisions may run
  concurrently only from the same sealed snapshot.

## 9. Security, privacy, perspective, and content constraints

- Character contexts and read DTOs are observer-scoped; hidden fields are absent.
- Model/memory/user text remains untrusted and models receive no write tools.
- All canonical mutations use typed Stage 1 effects and `EventCommitService`.
- Loopback development access is permitted; player-control ownership is still
  enforced server-side.
- Default tests use synthetic fixtures and no external calls.

## 10. Implementation sequence

1. Establish merged baseline and inspect current contracts.
2. Add graph pipelines and graph-path tests.
3. Add atomic scene execution and PostgreSQL retry/isolation tests.
4. Extend orchestration/fixture and prove complete first-day scenario.
5. Add API/WebSocket routes, tests, and generated OpenAPI.
6. Add minimal Vue client with TypeScript/component tests.
7. Add gate/evidence/status/handoff and run all acceptance checks.

## 11. Test matrix

| Layer | Required proof |
|---|---|
| Graph | valid, malformed, semantic invalid, unknown target, outage, fallback, resume |
| Simulation integration | atomic commit, duplicate retry, rollback, observation isolation |
| Orchestration/scenario | three enabled phases, same snapshots, budget gate, pause/resume/restart |
| API/WebSocket | idempotent commands, perspective reads, player validation, cursor replay |
| UI | strict build, component/client tests, provider/image-degraded text-first state |
| Gate | migration cycle, full offline suite, leakage/fault/consistency evidence |

## 12. Required commands

```bash
uv run pytest <targeted paths>
pnpm --dir frontend test
pnpm --dir frontend build
uv run alembic -c backend/alembic.ini upgrade head
uv run alembic -c backend/alembic.ini downgrade -1
uv run alembic -c backend/alembic.ini upgrade head
uv run alembic -c backend/alembic.ini check
uv run ruff format --check backend scripts tools
uv run ruff check backend scripts tools
uv run basedpyright
uv run pytest
uv run python scripts/run_stage1_gate.py
```

## 13. Acceptance criteria

- All handbook `26` §8 deterministic hard-gate items pass except the explicitly
  separate live-provider sample when no configured credential/quota is available.
- No duplicate event/effect/observation/memory/stream record on retry.
- Both characters use one sealed snapshot per phase and receive isolated context.
- Every accepted state change is a typed effect committed through the existing
  canonical transaction service.
- API/OpenAPI/WebSocket and frontend build/tests pass.
- Stage 0 remains green; static, migration, full test, and Stage 1 gate pass.
- Evidence and handoff identify commands, versions, assumptions, and any gap.

## 14. Deliverables

Code and tests in the writable paths above; no migration; generated OpenAPI and
frontend lockfile; Stage 1 evidence under `docs/status/evidence/stage-1/`;
handoff `docs/handoffs/2026-07-29_S1-INTEGRATION-001.md`.

## 15. Known risks and likely pitfalls

- The merged persistence schema may not expose every convenience repository
  operation; preserve one UoW/transaction rather than adding a second canon path.
- The existing Stage 0 runner models only scripted Mira actions; extend its
  boundaries without reapplying clock/tick events.
- API/UI scope is intentionally minimal but perspective filtering remains
  server-side and release-blocking.

## 16. Blocker/escalation rule

Stop for a normative contradiction, unsafe canonical reinterpretation,
knowledge leak, or required migration rewrite. Continue independent work for
ordinary implementation friction.

## 17. Handoff requirements

Return changed files, coherent commits, exact commands/results, gate status,
assumptions, contract deviations, unresolved risks, and next action.

## 18. Parent verification

Automated gate PASS at `8b64197`; evidence:
`docs/status/evidence/stage-1/stage-gate-report.md`.

Parent actions: review the commit series, run or accept
`uv run python scripts/run_stage1_gate.py`, merge the branch, and set the final
Stage 1 contract freeze/sign-off.
