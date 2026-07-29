# `S1-MODEL-001` — Prompts, schemas, and fake corpus

**Stage:** 1  
**Workstream:** MODEL  
**Status:** IN_REVIEW  
**Priority:** P0  
**Owner:** model subagent  
**Reviewer(s):** parent/integration agent  
**Branch/worktree:** `cursor/s1-model-001-5704` / `/tmp/s1-model`  
**Upstream commit:** `0c58f6daa111850a1c2a3d814df0b797d311e6fb`  
**Target merge order:** before `S1-GRAPH-001` and `S1-GRAPH-002`

---

## 1. Objective

Implement versioned Stage 1 decision, reaction, resolver, and narrator prompts with
strict rendering/provenance, plus an offline fake-output corpus that exercises valid,
malformed, schema-invalid, and character-agency cases.

## 2. Why this task exists

- Requirements: handbook `05` §§7.1–7.2, `13` §§7–13, `15` §§2–12 and 20.
- Stage gate items: `26` §§2, 3, 8 — typed model output, bounded repair, and no
  authored-other reaction.
- Risks mitigated: cross-character knowledge leakage, schema drift, prompt injection,
  and tests accidentally depending on live OpenRouter.
- Upstream/downstream tasks: Stage 0 model gateway/contracts; consumed by
  `S1-GRAPH-001`, `S1-GRAPH-002`, and `S1-QA-001`.

## 3. Required reading

1. `AGENTS.md`;
2. `26_STAGE_1_FIRST_COMPLETE_DAY.md`;
3. handbook `05`, `08`–`15`, `21`, and `22`;
4. `docs/status/CONTRACT_FREEZE.md`;
5. model roles, gateway fake, scene proposal contracts, and neighboring tests;
6. `docs/handoffs/2026-07-29_S0-DB002-MODEL002.md`.

## 4. Frozen contracts

| Contract | Version/hash/commit | Owner | Allowed change |
|---|---|---|---|
| `ActionProposal` / `ReactionProposal` / `SceneResolution` | Stage 0 freeze | domain | none |
| Model gateway request/result protocols | Stage 0 freeze | model | additive only |
| Stage 1 action families | handbook `26` §3 | simulation | none |

## 5. Scope

### In scope

- Versioned Jinja prompt assets and validated metadata.
- Strict prompt registry/renderer with sealed variables and SHA-256 provenance.
- Stage 1 fake model JSON corpus and corpus routing in the fake adapter.
- Contract/leakage tests for rendering, schema parsing, and authored-other reaction.

### Explicitly out of scope

- LangGraph workflow implementation and regeneration control flow.
- Domain-schema or effect-union changes.
- Live OpenRouter calls, provider benchmarking, persistence, and migrations.

## 6. File/path ownership

### Writable

```text
backend/prompts/**
backend/src/fictional_world/prompts/**
backend/src/fictional_world/infrastructure/model_gateway/fake.py
backend/tests/contract/prompts/**
backend/tests/contract/test_model_gateway_fake.py
backend/tests/fixtures/model_corpus/stage1/**
pyproject.toml
uv.lock
docs/tasks/active/S1-MODEL-001_prompts-schemas-corpus.md
docs/handoffs/*S1-MODEL-001*
```

### Read-only dependencies

```text
backend/src/fictional_world/application/models/**
backend/src/fictional_world/domain/**
autonomous_world_build_handbook_v1_0/**
docs/status/**
```

### Shared/generated files

`pyproject.toml` and `uv.lock` receive only the Jinja2 dependency update.

## 7. Data and migration ownership

```text
New tables/columns/indexes: none
Migration revision reservation: none
Backfill/rebuild: none
Fixture updates: Stage 1 model corpus only
No database change: yes
```

## 8. Interface inputs and outputs

### Inputs

```text
prompt_id, sealed render-variable mapping, TextGenerationRequest request_id/role
```

### Outputs

```text
PromptMeta, PromptAsset, RenderedPrompt, scripted fake TextGenerationResult
```

### Errors/fallbacks

Unknown/duplicate prompt IDs, invalid metadata, missing/extra render variables, or
missing corpus files fail closed. Existing fake gateway error kinds remain unchanged.

### Idempotency/concurrency

Registry loads immutable files. Rendering is deterministic for identical prompt content
and variables. Fake routing remains request-ID first, then role, then default.

## 9. Security, privacy, perspective, and content constraints

- [x] No cross-character access beyond frozen policy.
- [ ] Server-side role authorization (not applicable: no API surface).
- [x] Model/memory/user text treated as untrusted.
- [x] No secret/key/raw sensitive prompt logging.
- [x] Remote-provider data profile is allowed (synthetic corpus only).
- [x] No model direct state mutation.
- [x] High-impact effect privilege enforced by restricted resolver instructions/schema.
- [x] Young-adult/soft-dark content policy maintained.

## 10. Implementation sequence

1. Run existing fake-gateway contract baseline.
2. Add prompt metadata/runtime and strict rendering.
3. Add versioned prompt assets and repair templates.
4. Add corpus fixtures and fake-adapter corpus selection.
5. Add contract and leakage tests.
6. Run targeted tests, all offline tests, formatting, lint, and strict type checking.
7. Record results and commit/push.

## 11. Test matrix

| Test type | Scenario | Expected result | File/command |
|---|---|---|---|
| Contract | Complete and incomplete render mappings | exact sections render; missing/extra variables fail | `test_render_variables.py` |
| Contract | Valid and invalid corpus payloads | valid actions parse; malformed/schema invalid reject | `test_action_proposal_schema.py` |
| Security/leakage | Actor authors another character's reaction | semantic convention check rejects payload | `test_no_authored_other_reaction.py` |
| Adapter | request-ID and role corpus routing | selected corpus text is returned and parsed | `test_model_gateway_fake.py` |
| Static | all changed Python | Ruff and basedpyright pass | required commands |

Database, migration, property, API/UI/E2E, and fault/idempotency rows are not applicable:
the task adds immutable prompt files and an offline fake adapter extension only.

## 12. Required commands

```bash
uv run pytest backend/tests/contract/prompts backend/tests/contract/test_model_gateway_fake.py
uv run pytest
uv run ruff format --check backend/src backend/tests
uv run ruff check backend/src backend/tests
uv run basedpyright
```

## 13. Acceptance criteria

- [x] All requested prompt assets exist with validated metadata.
- [x] System prompts enforce proposal-only authority, knowledge isolation, Stage 1
  action families, and JSON-only schema output.
- [x] Registry loads by ID and lists active prompts.
- [x] Renderer rejects undeclared variables and hashes prompt content plus variables.
- [x] Fake corpus includes all requested valid and invalid cases.
- [x] Fake gateway selects corpus by request ID or role without network access.
- [x] Contract/leakage tests and static checks pass.
- [ ] No Critical/High reviewer finding remains.

## 14. Deliverables

- code: `backend/src/fictional_world/prompts/**`,
  `backend/src/fictional_world/infrastructure/model_gateway/fake.py`;
- migrations: none;
- tests: `backend/tests/contract/prompts/**`, fake gateway contract extension;
- fixtures: `backend/tests/fixtures/model_corpus/stage1/**`;
- generated artefacts: none;
- docs/ADR: this task packet; no ADR needed;
- evidence: command results in handoff;
- handoff: `docs/handoffs/2026-07-29_S1-MODEL-001.md`.

## 15. Known risks and likely pitfalls

- Prompt metadata variables can drift from templates; registry/renderer fail closed.
- Pydantic shape validation cannot detect another character's authored reaction; an
  explicit conservative semantic convention check covers the corpus case.
- Fake corpus routing must preserve Stage 0 scripted error behavior.

## 16. Blocker/escalation rule

Stop for any frozen-contract contradiction, knowledge leak, or required domain-schema
change. Continue independent prompt/corpus work for unrelated integration uncertainty.

## 17. Handoff requirements

Return changed files, exact commands/results, assumptions, contract deviations, and
integration risks to the parent agent.

## 18. Parent verification

```text
Reviewed by:
Merged commit:
Acceptance commands rerun:
Findings:
Traceability updated:
Status: VERIFIED / RETURNED
```
