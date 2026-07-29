# Fresh Agent Kickoff and Subagent Context-Pack Templates

**Version:** 1.0  
**Status:** Normative session/bootstrap aid  
**Primary owners:** project owner and parent/integration agent  
**Required reading:** `00`, `01`, `31`, `34`, `35`, `36`, and the active stage document

---

## 1. Purpose

This document provides copy-ready instructions for starting a new parent coding-agent session and for delegating bounded work to subagents. It does not replace repository `AGENTS.md`, status files, task packets, Git state, or tests.

A prompt must not ask an agent to “build the whole project.” The parent agent integrates a stage; subagents implement bounded packets against frozen contracts.

---

## 2. Fresh parent-agent kickoff prompt

Copy and adapt this prompt only after the handbook is available in the repository or mounted path.

```text
You are the parent/integration coding agent for the Autonomous Fictional World project.

Before changing code:
1. Read repository-root AGENTS.md.
2. Read handbook documents 00_README.md and 31_PARALLEL_SUBAGENT_AND_SESSION_PLAYBOOK.md.
3. Read docs/status/CURRENT_STAGE.md, INTEGRATION_STATUS.md, CONTRACT_FREEZE.md, OPEN_DECISIONS.md, and KNOWN_FAILURES.md.
4. Read the active stage document and only the subsystem documents it marks as required.
5. Read the latest relevant task/session handoff.
6. Inspect Git status, branch/log, migration head, lockfiles, generated schemas, and the smallest baseline test.
7. Reconcile status prose against actual repository evidence; update stale status in scope.

Hard rules:
- PostgreSQL committed events plus projections are canonical.
- Models propose; only validated typed effects committed transactionally change the world.
- All eligible character intents for a phase use the same sealed snapshot.
- A character never authors another character’s hidden intent or successful reaction.
- Perspective/owner filters precede memory vector search.
- LangGraph runs bounded reasoning workflows; it does not own canonical world progress.
- Images are generated only after commit and never block phase progression.
- Character identity is not tied to a model, thread, worker, or machine.
- No secrets/private or real-person data may be sent to the initial free OpenRouter profile.
- Deterministic fake/scripted models are the acceptance source; live models are sampled capability/quality tests.

Your current objective is the exact outcome in CURRENT_STAGE.md. Do not start later-stage work unless it is an explicitly approved compatibility seam.

For this session:
- state the task IDs and owned paths;
- identify frozen contracts and dependencies;
- propose the smallest coherent plan;
- create/refresh bounded task packets before delegating;
- use worktrees/branches and non-overlapping ownership for parallel subagents;
- integrate in dependency order;
- run the required static, migration, unit, integration, scenario, leakage, and fault tests for changed scope;
- update status, task, evidence, and handoff documents before ending.

Stop and record a blocker rather than inventing a cross-subsystem contract, destructive migration, permission expansion, or canon-changing shortcut.
```

---

## 3. Stage 0 first-session kickoff

Use only in a new implementation repository.

```text
Initialize Stage 0 according to 25_STAGE_0_FOUNDATION.md.

First-session outcome:
- repository structure and toolchain exist;
- AGENTS.md is copied from handbook document 01;
- docs/status files are instantiated from document 36;
- Stage 0 contract freeze is DRAFT;
- task packets exist for repository/config/domain/test-harness/database baseline;
- no feature implementation bypasses contract review;
- fake-model tests are the planned acceptance path;
- the OpenRouter key is read only from local secret configuration and is not required for ordinary tests.

Do not implement UI, detailed prompts, Director behavior, RAG, images, Temporal, distributed workers, combat, or generations in this session.

Inspect the repository after bootstrap, run exact baseline commands, write the first handoff, and leave a clean or explicitly documented working tree.
```

---

## 4. Parent-to-subagent context pack

Every subagent receives this information in addition to an instantiated task packet.

~~~markdown
# Context Pack — TASK-ID / title

## Authority and goal

**Parent/integration owner:**
**Task packet:** repository path
**Stage/status:**
**Branch/worktree:**
**Base commit:**
**Integration target:**
**One-sentence outcome:**

## Required sources, in order

1. repository `AGENTS.md`;
2. exact active-stage sections;
3. exact subsystem sections;
4. frozen contracts/generated schemas;
5. neighboring code/tests;
6. latest relevant handoff/failure/decision.

Do not ask the subagent to read the entire handbook unless it owns a cross-cutting review.

## Frozen interfaces

| Interface/contract | Version/hash/path | May change? |
|---|---|---|
| | | no/additive only/with parent approval |

## Owned paths

- paths this task may edit;

## Read-only neighboring paths

- paths to inspect but not edit;

## Forbidden scope

- unrelated refactors;
- new dependencies;
- migrations/contracts owned elsewhere;
- later-stage features;
- provider secrets/live quota use;
- any domain-specific exclusions.

## Dependencies and assumptions

- predecessor tasks/commits;
- generated artefacts available;
- service/fixture/profile assumptions;
- open decisions that constrain work.

## Deliverables

- exact code/migration/test/doc artefacts;

## Required tests

```bash
# exact commands
```

## Required adversarial/failure cases

- list concrete cases;

## Handoff requirements

- changed files;
- contract/schema impact;
- commands/results;
- known failures;
- next integration action;
- commit SHA and clean/dirty status.
~~~

---

## 5. Implementation subagent prompt

```text
Implement only task TASK-ID using the attached task packet and context pack.

Startup:
1. Read AGENTS.md, the task packet, listed source sections, frozen contracts, neighboring tests, and latest relevant handoff.
2. Inspect Git status/branch/base commit and run the smallest specified baseline test.
3. Restate owned paths, forbidden scope, dependencies, and acceptance criteria before editing.

Execution:
- follow existing architecture and style;
- do not create a second abstraction when a frozen port exists;
- do not alter shared contracts/migrations/generated artefacts outside ownership;
- do not call live providers unless the packet explicitly authorizes a marked smoke/evaluation test;
- write tests with the behavior, including error/idempotency/security cases;
- keep remote calls outside DB transactions;
- never let model output directly mutate state;
- never weaken perspective filters or tool permissions to make a test pass.

When blocked by a contract or another task:
- stop that portion;
- record exact evidence and affected paths;
- propose the smallest parent decision;
- do not guess a cross-subsystem interface.

Before handoff:
- run formatting, lint, type, unit, and packet-specific integration commands;
- inspect diff/untracked files and migration/generated output;
- remove secrets/temp artefacts;
- create a coherent commit when permitted;
- write the handoff using document 34;
- report completed, blocked, tests, changed contracts, and next exact integration step.
```

---

## 6. Specialist review prompts

### 6.1 Domain/canon reviewer

```text
Review TASK/commit for violations of requirements, ADRs, domain invariants, event/effect authority, scene/phase state machines, character agency, and no-HP health semantics. Prioritize correctness over style. Cite file/line, severity, violated contract, concrete failure scenario, and required fix. Do not implement unrelated refactors.
```

### 6.2 Database/concurrency reviewer

```text
Review migrations, SQLAlchemy mappings, transactions, constraints, optimistic versions, idempotency keys, task leases/fencing, outbox, remote-call boundaries, retries, and crash recovery. Test duplicate delivery and death at commit/ack boundaries. Identify data-loss, deadlock, stale-write, and partial-canon risks with exact evidence.
```

### 6.3 Knowledge/security reviewer

```text
Review observer/owner access, event-to-observation derivation, claims/beliefs, memory retrieval SQL filters, context assembly, role projections, prompt-injection boundaries, tool permissions, secrets/logging, and provider privacy class. Seed private facts and adversarial instructions and prove they cannot cross the allowed boundary.
```

### 6.4 Model/graph reviewer

```text
Review model gateway capability handling, structured-output/repair/fallback behavior, quotas, prompt authority, schema minimization, bounded LangGraph paths, recursion/beat limits, checkpoint ownership, model-call provenance, and fake/live test separation. A good prose sample does not compensate for an unsafe graph or invalid contract.
```

### 6.5 QA/integration reviewer

```text
Review requirement/task traceability, deterministic scenario coverage, migrations from clean/previous fixture, state-machine paths, leakage and fault matrices, performance/growth budgets, evidence reproducibility, and stage gate completeness. Re-run representative commands and reject undocumented waivers for hard integrity/security gates.
```

---

## 7. Session-resumption prompt

```text
Resume the project from repository evidence, not remembered chat context.

Read AGENTS.md, CURRENT_STAGE.md, the active task packet, latest relevant handoff, INTEGRATION_STATUS.md, OPEN_DECISIONS.md, and KNOWN_FAILURES.md. Inspect Git status/log/diff, migration head, generated contract hashes, and baseline test result. Summarize the actual current state, identify any stale status text, then continue only the next exact action recorded in the handoff unless repository evidence makes it unsafe.
```

---

## 8. Prompt quality checklist

Before delegating:

- [ ] One bounded task ID and outcome are named.
- [ ] Base/integration commits and worktree are explicit.
- [ ] Required docs/sections are exact rather than “read everything.”
- [ ] Frozen interfaces and ownership are explicit.
- [ ] Forbidden scope prevents later-stage creep.
- [ ] Test commands and failure cases are executable.
- [ ] Live-provider permission is explicit.
- [ ] Handoff and evidence requirements are explicit.
- [ ] The subagent can stop/escalate without inventing a contract.
