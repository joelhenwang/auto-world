# Architecture Decision and Change Request Templates

**Version:** 1.0  
**Status:** Normative decision-record templates  
**Primary owners:** architecture/contract owner and parent agent  
**Required reading:** `02`, `03`, `31`, `33`, affected subsystem documents, and active stage document

---

## 1. Purpose

Use an Architecture Decision Record for a durable, cross-subsystem, security-sensitive, expensive-to-reverse, or externally benchmarked decision. Use a Change Request to propose and impact-assess a change before implementation. A change request may be resolved by an existing rule, a patch, or a new/superseding ADR.

Do not create an ADR merely to restate an accepted handbook rule. Do create one when deliberately departing from, refining, or selecting an implementation behind a deferred handbook decision.

Repository paths:

```text
docs/adr/ADR-NNNN_<slug>.md
docs/changes/CR-YYYY-NNN_<slug>.md
```

---

## 2. ADR lifecycle

```text
PROPOSED
  ├── ACCEPTED
  │     └── SUPERSEDED by another ADR
  ├── REJECTED
  └── WITHDRAWN
```

Rules:

- ADR numbers are never reused;
- accepted ADR content is not rewritten to hide history;
- corrections may be appended with a dated note;
- a changed decision creates a superseding ADR and links both directions;
- accepted ADRs list concrete follow-up changes and evidence;
- implementation must not be merged before required decision approval unless the task is explicitly an experiment;
- secrets and raw confidential benchmarks do not belong in the ADR.

---

## 3. Full ADR template

~~~markdown
# ADR-NNNN — Decision title

**Status:** PROPOSED | ACCEPTED | REJECTED | WITHDRAWN | SUPERSEDED
**Date:** YYYY-MM-DD
**Decision owners:**
**Reviewers:**
**Decision deadline/checkpoint:**
**Supersedes:** ADR or NONE
**Superseded by:** ADR or NONE
**Related change request:** CR or NONE
**Related requirements:** exact IDs
**Related tasks/stages:** exact IDs

## Context

Describe the concrete problem, current architecture, trigger, and why the decision is needed now. Separate observed facts from hypotheses.

## Decision drivers

Rank the relevant drivers:

1. correctness/canon safety;
2. knowledge isolation/security/privacy;
3. restart/idempotency reliability;
4. maintainability and contract stability;
5. measured quality/performance/cost;
6. operational complexity;
7. reversibility and migration cost.

## Constraints

- accepted requirements/ADRs that cannot be violated;
- hardware/provider/runtime constraints;
- data migration and compatibility constraints;
- stage deadline/gate constraints.

## Options considered

### Option A — Name

**Description:**

**Advantages:**

**Disadvantages/risks:**

**Evidence:** benchmark/test/reference paths and exact conditions.

**Migration/rollback:**

### Option B — Name

Repeat the same structure.

## Decision

State one unambiguous choice, including scope and configuration defaults. Avoid “use A or B depending on context” unless the routing rule is fully specified.

## Detailed consequences

### Positive

### Negative/trade-offs

### New risks and mitigations

### Operational consequences

### Security, privacy, and content consequences

### Data/schema/API/prompt consequences

## Implementation plan

| Task | Owner | Dependency | Deliverable/test |
|---|---|---|---|
| | | | |

## Migration and rollback

State how existing data/configuration/workers are migrated and the exact rollback boundary. Say `not applicable` with justification when appropriate.

## Validation evidence

```text
commands
benchmark fixture and seed
hardware/software versions
results and confidence
failure cases
artefact paths
```

## Acceptance criteria

- [ ] measurable condition;
- [ ] contract/schema changes reviewed;
- [ ] tests and evidence pass;
- [ ] affected docs/status/registry updated.

## Revisit triggers

Specific evidence that justifies reopening the decision.

## Affected files and registries

- code paths;
- migrations;
- generated schemas/OpenAPI;
- prompt/model/workflow registry;
- deployment/configuration;
- handbook/project docs.

## Decision log

| Date | Event | Author |
|---|---|---|
| | Proposed/accepted/corrected | |
~~~

---

## 4. Change request template

~~~markdown
# CR-YYYY-NNN — Change title

**Status:** DRAFT | IMPACT_REVIEW | APPROVED | REJECTED | IMPLEMENTING | VERIFIED | ROLLED_BACK
**Requested:**
**Requester:**
**Owner:**
**Priority:** CRITICAL | HIGH | MEDIUM | LOW
**Target stage/release:**
**Related incident/failure:**
**ADR required:** YES | NO | UNKNOWN

## Problem and evidence

What is wrong or newly required? Include reproduction, metrics, user impact, or official capability change. Do not propose the solution before the problem is explicit.

## Proposed behavior

Describe observable/domain behavior, not only code edits.

## Non-goals

## Requirements impact

| Requirement ID | Unchanged/clarified/changed/new/removed | Explanation |
|---|---|---|
| | | |

## Contract and subsystem impact

| Area | Impact | Owner/reviewer |
|---|---|---|
| Domain/Pydantic | | |
| Event/effect semantics | | |
| Database/migration | | |
| Context/access policy | | |
| Model/prompts/graphs | | |
| Orchestration/jobs | | |
| API/WebSocket | | |
| UI/perspective | | |
| Images/assets | | |
| Security/privacy/content | | |
| Observability/operations | | |
| Seed/fixtures/evaluation | | |

## Data migration and compatibility

- existing rows/worlds affected;
- backfill/rebuild/re-embedding required;
- forward/rollback procedure;
- downtime/locking;
- versioning and retention.

## Options

Include no-change/workaround where meaningful.

## Risk analysis

| Risk | Likelihood | Impact | Mitigation/test |
|---|---:|---:|---|
| | | | |

## Implementation plan

Dependency-ordered task IDs, file ownership, contract freeze amendment, generated artefacts, and merge order.

## Verification plan

Unit, contract, migration, scenario, leakage/security, fault, performance, and human/model evaluation as applicable.

## Rollout

Feature flag/profile, staged enablement, observability, abort thresholds.

## Rollback

Exact safe rollback and irreversible boundaries.

## Approval

| Role | Decision | Date | Notes |
|---|---|---|---|
| Product owner | | | |
| Contract/architecture owner | | | |
| Security/data reviewer | | | |
| QA/stage owner | | | |

## Completion

- implementation commits;
- migration revisions;
- evidence path;
- docs/status/registry updates;
- residual known failures.
~~~

---

## 5. Emergency change addendum

An emergency may bypass normal scheduling, not correctness controls.

Add:

~~~markdown
## Emergency justification

**Active impact:** corruption | leakage | unavailable service | exploitable vulnerability
**Containment already applied:**
**Why normal timing is unsafe:**
**Temporary scope limit:**
**Required retrospective deadline:**
~~~

Minimum emergency rules:

- stop or isolate the unsafe path first;
- preserve evidence and canonical data;
- do not make an unreviewed destructive migration;
- add a regression test with the fix;
- create a retrospective ADR/CR when the emergency patch changes architecture;
- update `KNOWN_FAILURES.md`, status, and incident report.

---

## 6. Decision-quality checklist

Before acceptance:

- [ ] The question is narrow and answerable.
- [ ] Options obey higher-order requirements.
- [ ] Facts, assumptions, and inferences are labelled.
- [ ] Current external facts use official references and dates/versions.
- [ ] Benchmark conditions are reproducible.
- [ ] Security, privacy, data, and perspective effects are covered.
- [ ] Migration and rollback are credible.
- [ ] Consumer tasks and generated contracts are identified.
- [ ] Revisit triggers are measurable.
- [ ] The decision has one clear owner and acceptance record.
