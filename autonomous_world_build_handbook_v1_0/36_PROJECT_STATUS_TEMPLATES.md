# Project Status and Contract-Freeze Templates

**Version:** 1.0  
**Status:** Normative repository-coordination templates  
**Primary owners:** parent/integration agent and current stage lead  
**Required reading:** `00`, `01`, `24`, `31`, `32`, and the active stage document

---

## 1. Purpose

A new coding session must be able to discover the repository’s exact state without relying on chat history. These templates define the persistent coordination files maintained in the implementation repository.

Create these files at Stage 0 kickoff:

```text
docs/status/
├── CURRENT_STAGE.md
├── INTEGRATION_STATUS.md
├── OPEN_DECISIONS.md
├── KNOWN_FAILURES.md
├── CONTRACT_FREEZE.md
└── SESSION_LOG.md
```

Rules:

- repository state, Git, migrations, tests, and generated artefacts outrank stale status prose;
- status files are updated in the same task/commit that changes the reported state;
- do not place API keys, prompt payloads containing private data, or raw secrets here;
- use exact task IDs, branch names, commit hashes, migration revisions, paths, and commands;
- replace stale entries rather than accumulating contradictory summaries, except `SESSION_LOG.md`, which is append-only;
- unresolved architecture choices belong in `OPEN_DECISIONS.md` and, when accepted, an ADR;
- failed tests or incidents are not hidden to make a stage look complete.

---

## 2. `CURRENT_STAGE.md`

This is the first project-status file every fresh session reads.

~~~markdown
# Current Stage

**Updated:** YYYY-MM-DDTHH:MM:SSZ
**Updated by:** agent/person
**Repository:** repository name or path
**Current branch:** branch
**HEAD:** full commit SHA
**Working tree:** clean | dirty — explanation

## Stage

**Stage:** 0 | 1 | 2 | 3 | 4 | 5
**Stage name:** exact handbook stage title
**Stage status:** NOT_STARTED | CONTRACT_DRAFT | READY | IN_PROGRESS | BLOCKED | IN_REVIEW | VERIFIED
**Stage document:** handbook filename
**Stage owner:** name/agent
**Target integration branch:** branch
**Last verified stage tag:** tag or NONE

## Current objective

One paragraph describing the exact vertical result currently being pursued.

## Frozen contract versions

| Contract | Version/hash | Source path | Status | Owner |
|---|---|---|---|---|
| Domain schemas | | | DRAFT/FROZEN/CHANGING | |
| Database schema/Alembic head | | | | |
| Effect-command union | | | | |
| API/OpenAPI | | | | |
| Prompt catalog | | | | |
| Model capability snapshot | | | | |
| Seed manifest | | | | |

## Runtime profile

| Item | Current value |
|---|---|
| Python/uv lock hash | |
| Node/package lock hash | |
| PostgreSQL version | |
| pgvector version | |
| Orchestrator adapter | |
| Text provider/model | |
| Embedding provider/model | |
| Feature flags | |
| Migration head | |
| Seed version | |

## Active tasks

| Task ID | Owner | Branch/worktree | Status | Dependencies | Next integration point |
|---|---|---|---|---|---|
| | | | | | |

## Blocked tasks

| Task ID | Blocker ID | Evidence | Owner | Required decision/action |
|---|---|---|---|---|
| | | | | |

## Latest verified baseline

```bash
# Exact commands last run successfully
uv run ruff check .
uv run basedpyright
uv run pytest <scope>
# frontend commands when applicable
```

**Result timestamp:**
**Evidence path:**
**Known excluded tests:**

## Current integration risks

- concrete risk and affected task;
- no generic “might conflict” wording.

## Next exact actions

1. exact task/command/file;
2. exact merge/review dependency;
3. exact gate evidence to produce.

## Latest handoffs

- `docs/handoffs/...`

## Notes that a fresh session must know

Only current, actionable facts. Historical narrative belongs in the session log or Git history.
~~~

### Update triggers

Update `CURRENT_STAGE.md` whenever:

- the active stage/status changes;
- a task starts, blocks, merges, or verifies;
- the contract freeze changes;
- migration head changes;
- the default model/runtime profile changes;
- a baseline command starts failing;
- the next integration action changes.

---

## 3. `INTEGRATION_STATUS.md`

Use this to coordinate parallel branches and merge order.

~~~markdown
# Integration Status

**Updated:**
**Integration owner:**
**Integration branch/worktree:**
**Integration HEAD:**
**Target stage:**

## Contract baseline

| Contract | Frozen version/hash | Producer task | Consumers | Change allowed? |
|---|---|---|---|---|
| | | | | no / ADR required / additive only |

## Task integration matrix

| Task ID | Branch | Owner | Status | Required predecessors | Files/contracts touched | Tests/evidence | Merge order |
|---|---|---|---|---|---|---|---:|
| | | | | | | | |

## Pending generated artefacts

| Artefact | Producer | Expected path | Regeneration command | Required before task(s) |
|---|---|---|---|---|
| JSON Schemas | | | | |
| OpenAPI/client | | | | |
| Migration SQL | | | | |
| Seed manifest | | | | |

## Known overlap/conflict plan

| Paths/contracts | Tasks | Designated final owner | Merge strategy |
|---|---|---|---|
| | | | |

## Integration checkpoints

### Checkpoint 1 — contracts

- [ ] schema hashes match freeze;
- [ ] generated artefacts committed/reproducible;
- [ ] consumer compile tests pass.

### Checkpoint 2 — subsystem

- [ ] task tests pass on integration branch;
- [ ] migrations upgrade clean and fixture databases;
- [ ] no duplicate provider/domain abstractions.

### Checkpoint 3 — vertical slice

- [ ] stage scenario runs end to end;
- [ ] restart/idempotency/failure paths pass;
- [ ] evidence bundle updated.

## Exact integration commands

```bash
# Include repository-specific commands; do not write “run tests”.
```

## Current failures

Link IDs from `KNOWN_FAILURES.md`.
~~~

---

## 4. `OPEN_DECISIONS.md`

Use this for decisions that are unresolved but do not yet justify a full ADR. A task must not independently choose a cross-subsystem answer while an entry is open.

~~~markdown
# Open Decisions

## DEC-YYYY-NNN — Concise title

**Status:** OPEN | EVIDENCE_GATHERING | READY_FOR_DECISION | ACCEPTED | REJECTED | SUPERSEDED
**Opened:**
**Owner:**
**Decision deadline/integration checkpoint:**
**Affected requirements:**
**Affected tasks/contracts:**
**Blocking:** yes/no — exact work blocked

### Question

One answerable decision, not a broad research topic.

### Constraints

- accepted handbook/ADR constraints;
- performance/security/data constraints;
- options that are already forbidden.

### Options

| Option | Benefits | Costs/risks | Evidence needed |
|---|---|---|---|
| A | | | |
| B | | | |

### Current evidence

Commands, benchmark artefacts, official references, code findings.

### Default safe fallback

The behavior used if the deadline arrives without enough evidence.

### Decision

Filled when accepted/rejected. Link ADR if cross-subsystem or hard to reverse.

### Follow-up changes

Tasks, docs, schemas, migrations, configuration, and tests to update.
~~~

---

## 5. `KNOWN_FAILURES.md`

A known failure is reproducible evidence, not a vague concern.

~~~markdown
# Known Failures

## FAIL-YYYY-NNN — Concise symptom

**Status:** OPEN | MITIGATED | FIX_IN_REVIEW | VERIFIED_FIXED | ACCEPTED_LIMITATION
**Severity:** CRITICAL | HIGH | MEDIUM | LOW
**First observed:**
**Last reproduced:**
**Owner:**
**Affected stage/tasks:**
**Suspected first-bad commit:**

### User/system impact

What becomes incorrect, unavailable, leaked, duplicated, or slow.

### Reproduction

```bash
# Complete deterministic command sequence where possible
```

### Expected

### Actual

### Evidence

Logs/traces/event IDs/screenshot/test artefact paths. Redact secrets.

### Scope

Known affected/unaffected components and configurations.

### Workaround

Safe temporary workaround, or `NONE`.

### Candidate root cause

Clearly labelled hypothesis until proven.

### Fix task/branch

### Verification

Exact regression test and evidence needed before `VERIFIED_FIXED`.
~~~

Critical canon, isolation, idempotency, or security failures block stage promotion even when a workaround exists.

---

## 6. `CONTRACT_FREEZE.md`

Freeze contracts before parallel implementation fans out.

~~~markdown
# Contract Freeze — Stage N

**Status:** DRAFT | FROZEN | AMENDING | RELEASED
**Freeze date:**
**Freeze owner:**
**Integration commit:**
**Stage document:**

## Frozen contracts

| Contract | Source | Generated artefact | Version/hash | Allowed change during freeze |
|---|---|---|---|---|
| Domain IDs/enums | | | | none/additive |
| Pydantic schemas | | | | |
| Effect-command union | | | | |
| Repository/UoW ports | | | | |
| Database migration head | | | | |
| Event/outbox semantics | | | | |
| Model gateway protocols | | | | |
| Graph input/output | | | | |
| API DTO/event envelope | | | | |
| Seed manifest | | | | |

## Consumers

| Contract | Consumer tasks/modules |
|---|---|
| | |

## Freeze tests

```bash
# schema snapshots, import boundaries, generated artefact diff, API compatibility
```

## Amendment procedure

1. open decision/change request;
2. name contract owner;
3. list consumers and migration impact;
4. update producer and generated artefacts;
5. run contract and consumer tests;
6. rebase/notify affected tasks;
7. record old/new hash and approval here.

## Amendments

| Date | Change/CR | Old hash | New hash | Affected tasks | Approved by |
|---|---|---|---|---|---|
~~~

A freeze does not mean no bugs can be fixed. It means contract changes are coordinated rather than silently invented in consumer branches.

---

## 7. `SESSION_LOG.md`

This is an append-only high-level journal. Detailed per-task context belongs in handoff files.

~~~markdown
# Session Log

## YYYY-MM-DDTHH:MM:SSZ — session title

**Agent/person:**
**Branch/worktree:**
**Task IDs:**
**Starting HEAD:**
**Ending HEAD:**

### Intended outcome

### Completed

- exact code/docs/migrations/tests;

### Decisions/findings

- decision ID/ADR/failure ID and evidence;

### Verification

```bash
# exact commands and results
```

### State left behind

Clean/dirty tree, running services, migration state, generated artefacts.

### Handoff

`docs/handoffs/YYYY-MM-DD_....md`
~~~

Do not paste entire model conversations or duplicate Git diffs into the session log.

---

## 8. Stage 0 initialization sequence

The parent agent creates the files in this order:

1. instantiate `CURRENT_STAGE.md` with Stage 0 status `CONTRACT_DRAFT`;
2. instantiate `OPEN_DECISIONS.md` with the explicit Stage 0 decisions from `25`;
3. instantiate `CONTRACT_FREEZE.md` as `DRAFT`;
4. instantiate `INTEGRATION_STATUS.md` after task packets are assigned;
5. create empty `KNOWN_FAILURES.md` with its heading and policy;
6. create `SESSION_LOG.md` and append the kickoff entry;
7. commit these with repository bootstrap or the first dedicated planning commit;
8. update them before delegating implementation tasks.

---

## 9. Review checklist

- [ ] Every active task appears in current/integration status.
- [ ] No merged task remains marked `IN_PROGRESS`.
- [ ] Migration head and lock hashes match the repository.
- [ ] Contract hashes are generated from current files.
- [ ] Open decisions have owners and deadlines/checkpoints.
- [ ] Known failures contain reproducible evidence.
- [ ] Session log references the latest handoff.
- [ ] No secrets or external-provider payloads containing disallowed data are present.
- [ ] A fresh agent can identify the next exact action in under five minutes.
