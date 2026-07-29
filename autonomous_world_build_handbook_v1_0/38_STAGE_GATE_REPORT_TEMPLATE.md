# Stage Gate Report Template

**Version:** 1.0  
**Status:** Normative promotion-evidence template  
**Primary owners:** stage owner, QA owner, parent/integration agent  
**Required reading:** `21`, `24`, `32`, active stage document, and affected subsystem documents

---

## 1. Purpose

A stage is not complete because its code merged or its demo looks convincing. This report records the exact build, contracts, data, commands, results, failures, and reviewer decisions used to promote or reject a stage.

Create:

```text
docs/status/evidence/stage-N/stage-gate-report.md
```

All evidence paths are repository-relative or immutable artefact references. Never write “tests pass” without the command, result, and artefact.

---

## 2. Report template

~~~markdown
# Stage N Gate Report — Stage title

**Decision:** PASS | FAIL | CONDITIONAL_FAIL
**Report date:**
**Stage owner:**
**QA owner:**
**Integration commit:**
**Release/tag candidate:**
**Previous verified stage/tag:**
**Environment/profile:**
**Handbook/stage version:**

## 1. Intended outcome

Copy the stage outcome, then describe the concrete demonstrated vertical slice.

## 2. Scope delivered

| Task ID | Status | Commit/PR | Deliverable | Evidence |
|---|---|---|---|---|
| | VERIFIED | | | |

## 3. Explicit exclusions

Confirm every exclusion from the stage document remains excluded or is safely additive. Flag accidental premature dependencies.

## 4. Build and version manifest

| Component | Version/hash |
|---|---|
| Git commit | |
| Python/uv lock | |
| Frontend lock | |
| PostgreSQL/pgvector | |
| Alembic head | |
| Domain schema hash | |
| OpenAPI hash | |
| Prompt catalog version | |
| Model capability snapshot | |
| Seed manifest | |
| Orchestrator adapter | |
| Image workflow registry, if applicable | |

## 5. Environment and data

- host/container/OS architecture;
- relevant hardware;
- provider/model profiles;
- feature flags;
- fixture/seed and random seeds;
- database starting condition;
- network/external-service assumptions;
- privacy classification.

## 6. Static and build quality

| Check | Command | Result | Artefact |
|---|---|---|---|
| Ruff | | | |
| basedpyright | | | |
| Python tests/build | | | |
| Frontend lint/type/build | | | |
| Architecture/import tests | | | |
| Secret/dependency scans | | | |

## 7. Migration and persistence evidence

- [ ] clean upgrade;
- [ ] previous-stage fixture upgrade;
- [ ] downgrade/rollback where supported;
- [ ] generated/final SQL reviewed;
- [ ] constraints/indexes verified;
- [ ] event/projection audit passes;
- [ ] backup/restore or export/restore requirement passes.

| Scenario | Command | Result | Evidence |
|---|---|---|---|
| | | | |

## 8. Functional scenarios

| Scenario ID | Requirement/task | Seed/model mode | Expected | Actual | Result | Artefact |
|---|---|---|---|---|---|---|
| | | fake/scripted/live/local | | | | |

## 9. Hard invariants and consistency

| Invariant/test | Result | Evidence |
|---|---|---|
| No model-direct state mutation | | |
| Atomic scene/event commit | | |
| Duplicate delivery is safe | | |
| No partially canonical next phase | | |
| Projection provenance/audit | | |
| No illegal HP field | | |
| Image work nonblocking, when present | | |

List every consistency-audit finding, even repaired findings.

## 10. Knowledge, privacy, and security

| Test | Result | Evidence |
|---|---|---|
| Cross-character secret leakage | | |
| Player perspective filtering | | |
| Director disclosure path | | |
| Memory/lore prompt injection | | |
| Least-privilege tools | | |
| Role permission enforcement | | |
| Secret/log redaction | | |
| Provider data-classification policy | | |

## 11. Restart, idempotency, and fault injection

| Failure point | Injection method | Expected recovery | Result | Evidence |
|---|---|---|---|---|
| before model call | | | | |
| after model response/before save | | | | |
| before event transaction commit | | | | |
| after commit/before task ack | | | | |
| duplicate task delivery | | | | |
| provider timeout/429 | | | | |
| worker termination | | | | |
| image/embedding outage, when applicable | | | | |

## 12. Performance and growth

| Metric | Fixture/load | Target | Result | Notes |
|---|---|---:|---:|---|
| API read p95 | | | | |
| commit p95 excluding model | | | | |
| context assembly p95 | | | | |
| memory retrieval p95 | | | | |
| queue wait/model latency | | measured | | |
| DB rows/bytes per simulated day | | bounded | | |
| context tokens over horizon | | bounded | | |

## 13. Model and narrative quality

Separate deterministic correctness from sampled model quality.

| Corpus/run | Provider/model | Prompt/schema | Samples | Metric/rubric | Result | Evidence |
|---|---|---|---:|---|---:|---|
| | | | | | | |

Include:

- structured-output success and repair/fallback rate;
- personality/voice distinction;
- unsupported memory claims;
- agency/refusal behavior;
- relationship/romance evidence;
- repetition/exposition/melodrama review;
- resolver plausibility;
- image identity/scene quality in Stage 4.

## 14. Human review

**Reviewers:**
**Blind/randomized sampling method:**
**Rubric version:**

| Dimension | Score/threshold | Findings |
|---|---:|---|
| Coherence | | |
| Character continuity | | |
| Agency | | |
| Non-cringe narrative quality | | |
| Quiet-scene quality | | |
| Perspective correctness | | |
| Visual continuity, when applicable | | |

## 15. Open failures, risks, and technical debt

| ID | Severity | Impact | Workaround | Blocks promotion? | Follow-up task |
|---|---|---|---|---|---|
| | | | | | |

## 16. Waivers

Hard canon, isolation, idempotency, migration-safety, and security gates are not waivable. For other items:

| Gate | Reason | Risk | Expiry/follow-up | Approved by |
|---|---|---|---|---|
| | | | | |

## 17. Gate checklist

Paste the exact hard exit gate from the active stage document and mark every item with evidence.

## 18. Decision

### PASS

State why every hard gate is satisfied and name the promoted tag/stage.

### FAIL / CONDITIONAL_FAIL

State exact blockers and the minimum rerun scope. Do not promote.

## 19. Promotion/rollback actions

- tag/branch/status updates;
- fixture/export snapshot;
- next stage contract-draft tasks;
- deployment changes;
- rollback point and retention.

## 20. Sign-off

| Role | Name | Decision | Date | Notes |
|---|---|---|---|---|
| Stage owner | | | | |
| QA owner | | | | |
| Contract/architecture reviewer | | | | |
| Knowledge/security reviewer | | | | |
| Project owner | | | | |
~~~

---

## 3. Stage-specific mandatory sections

### Stage 0

- clean and fixture migration;
- deterministic effect/event transaction;
- task/outbox idempotency;
- seed import determinism;
- fake-model acceptance;
- OpenRouter capability smoke kept separate;
- process restart and duplicate-command proof.

### Stage 1

- one complete three-phase day;
- two intents from one sealed snapshot;
- bounded reactions;
- isolated observations/recent memories;
- player action remains an attempt;
- restart at each phase boundary;
- minimal UI/WebSocket projection.

### Stage 2

- seven days and all ten phases;
- four focus characters;
- goals/plans/relationships;
- claims/beliefs/secrets;
- travel and interruption;
- Director trigger/no-event behavior;
- temporary NPC limits and actor knowledge;
- daily compaction/diaries;
- no manual repair.

### Stage 3

- thirty-day soak;
- versioned embedding/RAG isolation;
- memory recall and unsupported-claim metrics;
- arcs/factions/pacing;
- magic/injury/combat plausibility;
- monthly reflection;
- database/context growth bounds;
- narrative quality threshold.

### Stage 4

- hardware/model benchmark manifest;
- local worker routing/failover;
- provider fallback semantics;
- orchestrator conformance;
- object-store recovery;
- ComfyUI queue/restart behavior;
- visual identity/appearance-version corpus;
- image outage never blocks canon.

### Stage 5

- macro eligibility and expansion triggers;
- deterministic and model-assisted macro audit;
- genealogy/private-memory inheritance boundary;
- focus succession;
- three-generation cap;
- peace/eradication/max-day endings;
- final export and restore.

---

## 4. Report quality checklist

- [ ] Results are tied to one immutable commit and version manifest.
- [ ] Live model tests are not substituted for deterministic acceptance.
- [ ] Failures are shown, not summarized away.
- [ ] Every hard gate has an evidence path.
- [ ] Human-review sampling method is recorded.
- [ ] External-provider conditions and dates are recorded.
- [ ] Waivers do not cover hard integrity/security gates.
- [ ] A fresh agent can reproduce the gate from the report.
