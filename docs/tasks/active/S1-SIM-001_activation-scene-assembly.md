# `S1-SIM-001` — Activation, scene assembly, priority, and beat budgets

**Stage:** 1 | **Workstream:** SIM | **Status:** IN_REVIEW | **Priority:** P0
**Owner:** simulation subagent | **Reviewer:** parent/integration agent
**Branch/worktree:** `cursor/s1-sim-001-5704` / `/tmp/s1-sim`
**Upstream commit:** `0c58f6daa111850a1c2a3d814df0b797d311e6fb`
**Target merge order:** after Stage 0 contract freeze; before `S1-GRAPH-002` and `S1-SIM-002`

## 1. Objective

Implement deterministic Stage 1 activation, proposal conflict sets, weighted priority,
beat-budget selection, and stable scene assembly so simultaneous proposals from one snapshot
produce reproducible, correctly merged `SceneDraft` values without database or model access.

## 2. Why this task exists

- Stage proof: handbook `26` §§2, 4, 6–8.
- Subsystem behavior: handbook `07` §§7–12.
- Upstream: frozen Stage 0 scene proposal contracts.
- Downstream: `S1-GRAPH-002`, `S1-SIM-002`, and `S1-ORCH-001`.

## 3. Required reading

1. repository `README.md` and `AGENTS.md`;
2. `docs/status/CURRENT_STAGE.md`;
3. handbook `26_STAGE_1_FIRST_COMPLETE_DAY.md`;
4. handbook `05_DOMAIN_CONTRACTS_AND_STATE_MACHINES.md` and
   `07_SIMULATION_ENGINE_PHASES_SCENES_AND_TIME.md`;
5. handbook `19_REPOSITORY_STRUCTURE_ENGINEERING_STANDARDS_AND_CONFIG.md` and
   `21_TESTING_EVALUATION_AND_QUALITY_GATES.md`;
6. `backend/src/fictional_world/domain/scenes/proposals.py` and neighboring application code;
7. existing ADRs and `docs/status/SESSION_LOG.md`.

## 4. Frozen contracts

| Contract | Version | Owner | Allowed change |
|---|---|---|---|
| `ActionProposal` | `1.0` | domain | none |
| `PriorityBreakdown` | Stage 0 freeze | domain | none |
| `SceneDraft` | Stage 0 freeze | domain | none |
| `EffectCommand` | Stage 0 freeze | domain | none |

## 5. Scope

### In scope

- Pure synchronous activation eligibility for alive, dead, and unconscious character states.
- Proposal read/write conflict sets.
- Weighted deterministic scene priority with Stage 1 narrative salience fixed to zero.
- Stage 1 beat budgets clamped to the domain range.
- Deterministic grouping, ordering, and UUIDv5 scene identities.
- Focused unit tests for activation, scoring, and grouping.

### Explicitly out of scope

- Database access, schema changes, or migrations.
- Model calls or model-derived priority.
- Reaction, resolution, commit, orchestration, API, or UI behavior.
- Changes to frozen domain scene/effect contracts.
- Post-Stage 1 grouping keys such as routes, items, factions, and director encounters.

## 6. File/path ownership

### Writable

```text
backend/src/fictional_world/application/simulation/activation.py
backend/src/fictional_world/application/simulation/conflict_sets.py
backend/src/fictional_world/application/simulation/priority.py
backend/src/fictional_world/application/simulation/beat_budget.py
backend/src/fictional_world/application/simulation/scene_assembly.py
backend/tests/unit/application/simulation/**
docs/tasks/active/S1-SIM-001_activation-scene-assembly.md
```

### Read-only dependencies

```text
backend/src/fictional_world/domain/**
backend/src/fictional_world/application/simulation/commit.py
backend/migrations/**
```

No shared generated files are changed.

## 7. Data and migration ownership

```text
New tables/columns/indexes: none
Migration revision reservation: none
Backfill/rebuild: none
Fixture updates: none
No database change: yes
```

## 8. Interface inputs and outputs

- Inputs: `CharacterStateRecord`, `ActionProposal`, UUID phase/snapshot/location mappings,
  normalized priority factors, and scene type/participant count.
- Outputs: `EligibilityStatus` plus reason, frozen UUID sets, `PriorityBreakdown`, integer beat
  budget, and ordered `tuple[SceneDraft, ...]`.
- Errors: strict input contracts reject malformed values; missing actor locations remain `None`.
- Idempotency/concurrency: pure functions and UUIDv5 identity make identical inputs reproducible.

## 9. Security, privacy, perspective, and content constraints

No model, persistence, authorization, or perspective data is accessed. Proposals remain attempts;
scene assembly does not mutate canon or infer hidden character state.

## 10. Implementation sequence

1. Run baseline contract/static checks.
2. Add focused unit tests for required behavior and deterministic edge cases.
3. Implement pure activation, conflict-set, priority, budget, and assembly functions.
4. Run targeted Ruff, formatting, basedpyright, and pytest checks.
5. Review the final diff for frozen-contract and scope compliance.

## 11. Test matrix

| Test type | Scenario | Expected result |
|---|---|---|
| Unit | Alive/dead/unconscious activation | eligible or explicit deterministic skip |
| Unit | Priority factors and bounds | exact documented weighted score |
| Unit | Visit/wait social overlap | one social scene |
| Unit | Different locations without overlap | independent scenes |
| Unit | Shared target entity | one conflict scene |
| Unit | Reordered inputs | stable ordering and scene UUIDs |
| Static | New source/tests | Ruff and strict basedpyright pass |

Integration, migration, fault, API/UI, and live-model tests are not applicable to pure logic.

## 12. Required commands

```bash
uv run ruff check backend/src/fictional_world/application/simulation \
  backend/tests/unit/application/simulation
uv run ruff format --check backend/src/fictional_world/application/simulation \
  backend/tests/unit/application/simulation
uv run basedpyright backend/src/fictional_world/application/simulation
uv run pytest backend/tests/unit/application/simulation -q
```

## 13. Acceptance criteria

- [x] Alive characters are eligible; dead and unconscious characters have distinct skip statuses.
- [x] Conflict sets are immutable and include the Stage 1 actor/target/location/activity aggregates.
- [x] Priority uses weights `0.25/0.20/0.15/0.15/0.10/0.10/0.05`, with narrative zero.
- [x] Beat budgets include solo `1`, two-person social `4`, and clamp to `1..12`.
- [x] Assembly follows target entity, target location, colocated social, then solo precedence.
- [x] Scenes sort by descending priority then actor UUID and have deterministic UUIDv5 IDs.
- [x] Required unit and static checks pass.
- [x] Frozen domain contracts and migrations remain unchanged.

## 14. Deliverables and handoff

- Code: five application simulation modules listed in §6.
- Tests: three focused test modules under `backend/tests/unit/application/simulation/`.
- Documentation: this task packet.
- Migrations, fixtures, generated artifacts, and ADRs: none.
- Handoff: parent-agent response containing changed files, commands/results, assumptions, risks,
  and commit SHA.

## 15. Known risks and blocker rule

- Grouping can be order-dependent; use deterministic connected components and UUID sorting.
- Actor locations are read context, not automatically mutable writes.
- Stop and report any conflict with frozen scene contracts; do not alter them as a workaround.

## 16. Parent verification

```text
Reviewed by:
Merged commit:
Acceptance commands rerun:
Findings:
Traceability updated:
Status: VERIFIED / RETURNED
```
