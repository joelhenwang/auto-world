# Parallel Subagent and Multi-Session Playbook

**Version:** 1.0  
**Status:** Normative coding-agent operating procedure  
**Audience:** parent coding agent, implementation subagents, reviewers, future sessions

---

## 1. Purpose

This project is too large to hold safely in one conversational session or to let several agents modify without coordination. This document defines how work is divided, handed off, reviewed, merged, and resumed without losing architectural context or creating conflicting implementations.

The central rule is:

> Parallelize implementation after contracts are frozen; never parallelize disagreement about the same contract.

Subagents are temporary specialists. The parent agent remains accountable for architecture, dependency order, integration, and stage gates.

---

## 2. Roles

## 2.1 Project owner

The human owner decides:

- product direction;
- user-facing behavior;
- explicit world/content policy;
- acceptable tradeoffs;
- model/hardware spending;
- deity/director privileges;
- stage promotion when a non-hard quality preference remains subjective.

The coding agent should not repeatedly ask about choices already resolved in the handbook. Record new decisions through ADR/change control.

## 2.2 Parent/integration agent

Exactly one parent agent owns a stage integration cycle.

Responsibilities:

- read and obey the handbook;
- inspect actual repository state before planning;
- freeze contracts and task dependencies;
- create bounded task packets;
- assign nonoverlapping ownership;
- answer/resolve cross-agent contract questions;
- merge in dependency order;
- run integration and stage tests;
- update traceability/status/ADRs;
- reject unscoped changes;
- produce session handoffs;
- never claim a stage is complete without evidence.

The parent may implement small integration changes, but should not become a hidden second owner of every subagent’s files.

## 2.3 Implementation subagent

A subagent owns one bounded task packet. It must:

- read the exact required documents and relevant code;
- preserve defined interfaces;
- modify only assigned paths except explicitly approved generated files;
- add tests and migrations required by its task;
- run declared checks;
- document deviations/blockers;
- hand back coherent, reviewable work;
- avoid opportunistic refactors unrelated to the task.

A subagent must not:

- redesign the architecture in isolation;
- create a competing domain schema;
- bypass failing tests;
- edit another task’s migration;
- silently change a public interface;
- directly merge/promote the stage unless assigned as integration agent;
- store secrets or live provider responses in fixtures.

## 2.4 Contract owner

For each stage, one person/agent owns each cross-cutting contract:

- domain Pydantic models and enums;
- effect command union;
- database schema/migration sequence;
- phase/scene states;
- model gateway protocols;
- context-access policy;
- API/OpenAPI contract;
- task/orchestration states.

Contract owners may be implementation subagents, but their contract must be frozen before dependent work begins.

## 2.5 Review agents

Use separate review passes where possible:

- domain/architecture reviewer;
- database/migration reviewer;
- concurrency/idempotency reviewer;
- knowledge-isolation/security reviewer;
- model/prompt/output reviewer;
- API/frontend reviewer;
- test/quality reviewer;
- final integration reviewer.

A reviewer reports findings with severity and evidence. It should not silently rewrite broad areas unless assigned a follow-up task packet.

---

## 3. Sources of truth and precedence

Every session begins from this order:

1. explicit current user instruction;
2. repository `AGENTS.md` and local scoped agent instructions;
3. current-stage document (`25`–`30`);
4. normative architecture/domain documents (`02`–`23`);
5. accepted ADRs and change records;
6. current status/handoff/task packet;
7. generated schemas/OpenAPI/migrations/code;
8. old chat history or memory.

When code and handbook conflict:

- do not guess which is correct;
- identify whether the discrepancy is an intentional accepted change;
- update the contract/ADR and all dependents if architecture changed;
- otherwise fix the implementation;
- record the decision in the handoff.

The database is canonical for fictional state. The handbook is canonical for intended architecture until superseded by an accepted ADR.

---

## 4. Recommended repository coordination files

The project repository should maintain:

```text
docs/status/
├── CURRENT_STAGE.md
├── INTEGRATION_STATUS.md
├── OPEN_DECISIONS.md
├── KNOWN_FAILURES.md
├── CONTRACT_FREEZE.md
└── evidence/
    └── stage-<n>/

docs/tasks/
├── active/
├── completed/
└── blocked/

docs/handoffs/
└── YYYY-MM-DD_<session-or-task>.md

docs/adr/
└── ADR-XXXX_<slug>.md
```

These are project runtime documents. They should not replace the stable handbook. Instantiate them from `36_PROJECT_STATUS_TEMPLATES.md`.

---

## 5. Stage kickoff procedure

The parent agent performs this sequence:

1. verify previous stage tag/gate/evidence;
2. read the new stage document and dependent subsystem docs;
3. inspect current code, migrations, tests, and deployment state;
4. list contract changes required by the stage;
5. name a contract owner for each;
6. create `CONTRACT_FREEZE.md` with status `DRAFT`;
7. resolve contract changes in a short architecture pass;
8. run schema/code generation and contract tests;
9. mark frozen interfaces with version/hash/date;
10. create dependency-ordered task packets;
11. assign file/path ownership and branch/worktree;
12. establish merge order and required reviewers;
13. begin safe parallel work.

Do not fan out implementation while the effect schema, migration ownership, or access policy is still being independently invented.

---

## 6. Task packet design

Use `35_TASK_PACKET_TEMPLATE.md`; use `39_FRESH_AGENT_KICKOFF_AND_CONTEXT_PACK_TEMPLATE.md` when delegating it.

A good task packet is independently implementable and normally fits one focused agent/session.

Every packet uses `35_TASK_PACKET_TEMPLATE.md` and includes:

- task ID and stage;
- objective and user-visible/system outcome;
- exact scope and explicit exclusions;
- required reading;
- upstream contracts/commit SHA;
- owned file paths;
- read-only dependent paths;
- interfaces that may not change;
- data/migration ownership;
- implementation steps;
- test matrix;
- commands to run;
- acceptance criteria;
- handoff requirements;
- known risks/questions;
- merge dependencies.

Avoid packets such as:

> “Implement memory.”

Prefer:

> “Implement owner-filtered exact pgvector candidate retrieval for `MemoryRepository`, using frozen `MemoryQueryV1`, without context assembly or reranking; add migration/index, unit/integration/leakage tests, and benchmark query plan.”

---

## 7. Sizing work

A task is too large when it combines several of these:

- new domain contract;
- migration;
- repository;
- orchestration;
- model prompt/graph;
- API;
- UI;
- full QA gate.

A vertical feature may span these layers, but assign it as an ordered task chain unless one agent can complete and verify it coherently without a long session.

Suggested packet sizes:

- **Small:** one pure service, schema adapter, view, or test fixture;
- **Medium:** one migration + repository + tests; one bounded graph + corpus + tests; one API slice + generated client + UI view;
- **Large:** one tightly coupled subsystem integration, reserved for parent or experienced subagent with explicit checkpoints.

If an agent discovers the packet is larger than expected, it should stop at a coherent boundary, record completed work, and propose split packets rather than improvising an incomplete mega-change.

---

## 8. Branches and worktrees

Recommended setup:

```text
main
stage/<n>-integration
task/<task-id>-<slug>
```

Each parallel subagent receives a separate Git worktree or isolated clone. Do not run several agents in the same working directory.

Example:

```bash
git worktree add ../worktrees/S2-KNOW-001 -b task/S2-KNOW-001-beliefs stage/2-integration
git worktree add ../worktrees/S2-SIM-001 -b task/S2-SIM-001-travel stage/2-integration
```

Rules:

- never commit secrets, `.env`, model caches, DB volumes, or generated images;
- do not rewrite shared branch history after another task depends on it;
- one task branch should contain coherent commits;
- generated artefacts are committed only according to repository policy;
- migrations have globally reserved revision IDs or sequence slots;
- parent rebases/merges and resolves integration conflicts.

---

## 9. File ownership matrix

Before starting parallel agents, publish a matrix such as:

| Task | Writable paths | Shared generated path | Contract dependency |
|---|---|---|---|
| S2-DB-001 | `src/.../db/**`, `migrations/**`, DB tests | generated schema only through owner | Domain v2 |
| S2-KNOW-001 | `src/.../knowledge/**`, leakage tests | none | DB repository interfaces |
| S2-SIM-001 | `src/.../simulation/time.py`, `activity.py`, route tests | none | Activity/Route contracts |
| S2-GRAPH-001 | `src/.../agents/**`, prompt assets | JSON schemas generated by contract owner | Model/domain contracts |
| S2-UI-001 | `web/src/**` | API client generated after OpenAPI freeze | API v2 |

If two agents need the same file, choose one:

1. sequence tasks;
2. split the file/interface first;
3. assign one owner and have the other provide a patch/spec;
4. create an integration packet.

“Both edit it and parent resolves later” is not a normal strategy.

---

## 10. Contract freeze

A freeze record contains:

```text
contract name
version
owner
date/commit
files/schemas
hash or generated artefact
allowed compatible changes
breaking-change procedure
dependent task IDs
```

Examples:

- `ActionProposalV1`;
- `EffectCommandV2`;
- `PhaseStatusV1`;
- `MemoryQueryV1`;
- `ModelGatewayProtocolV1`;
- OpenAPI `stage2-v1`;
- migration head revision.

After freeze, a subagent may make only backward-compatible changes explicitly allowed by the packet. A breaking change requires:

1. stop affected tasks;
2. change proposal/ADR;
3. impact list;
4. parent approval;
5. new contract version;
6. regeneration/migration updates;
7. dependent task packet revisions.

---

## 11. Subagent startup checklist

A subagent should begin by reporting internally or in its task log:

```text
Task ID:
Current branch/worktree:
Upstream commit:
Required docs read:
Owned paths:
Explicit exclusions:
Frozen interfaces:
Tests expected:
Uncertainties/blockers:
```

Then it must inspect:

- actual code and tests;
- current migration head;
- neighboring patterns;
- current static/type settings;
- relevant generated artefacts;
- active known failures.

Do not implement from the task text alone without checking repository reality.

---

## 12. Implementation loop

Use this loop:

```text
1. Write/confirm failing test or contract example.
2. Implement smallest coherent behavior.
3. Run targeted unit tests.
4. Run static/type checks for changed package.
5. Add integration/migration/fault tests as required.
6. Inspect logs/provenance/security behavior.
7. Update docs generated from the code if required.
8. Review own diff against packet exclusions.
9. Run packet acceptance commands.
10. Produce handoff and commits.
```

For database work:

- inspect generated SQL;
- migrate a clean database;
- migrate an upgraded previous-stage fixture;
- test downgrade only where project policy requires it;
- verify constraints directly;
- test transaction rollback and duplicate delivery.

For model/graph work:

- fake adapter tests are authoritative;
- use fixed response corpus;
- test malformed/semantic-invalid/provider-outage paths;
- do not make live provider calls in unit tests;
- store no sensitive prompts/responses;
- verify schema capability fallbacks.

For concurrency work:

- test leases/fencing/idempotency;
- deliberately kill workers/processes;
- verify a late result cannot overwrite a newer task generation;
- inspect transaction boundaries.

---

## 13. Communication between subagents

Subagents should not depend on conversational memory shared through the parent alone. Communicate through versioned artefacts:

- contract schema;
- task packet update;
- ADR;
- generated OpenAPI/JSON Schema;
- code interface;
- test fixture;
- handoff document.

A subagent with a cross-task discovery writes a concise issue into its handoff:

```text
Cross-task finding ID: XTF-...
Affected contract/task:
Evidence:
Why current interface is insufficient:
Minimal proposed change:
Breaking or compatible:
Workaround used/not used:
```

The parent decides and broadcasts the resolution.

---

## 14. Blocker protocol

A subagent should not silently invent a workaround for a hard contract blocker.

Classify blockers:

- **B0 — Local:** solvable inside owned scope;
- **B1 — Upstream bug:** dependent implementation differs from frozen contract;
- **B2 — Contract ambiguity:** handbook/schema lacks a required decision;
- **B3 — Breaking change required:** current contract cannot support task;
- **B4 — Environment/external:** tool/provider/hardware unavailable;
- **B5 — Safety/security:** requested behavior violates isolation/content/security invariant.

Response:

- B0: solve and document;
- B1: create evidence/reproducer and notify parent/upstream owner;
- B2: propose a precise default and stop only the affected part;
- B3: do not implement incompatible API; request change control;
- B4: provide fake/local fallback and evidence of limitation;
- B5: stop unsafe path and escalate immediately.

Agents should continue independent portions when possible rather than abandoning an entire packet.

---

## 15. Handoff protocol

Every completed or interrupted task uses `34_SESSION_HANDOFF_TEMPLATE.md`.

Minimum handoff:

- task/status;
- upstream and final commit(s);
- exact files changed;
- behavior implemented;
- migrations/generated artefacts;
- commands/tests run with results;
- tests not run and why;
- known issues/risks;
- contract deviations;
- integration/merge order;
- next exact action;
- cleanup/worktree state.

A handoff must make it possible for a new agent with no chat context to continue.

Do not write:

> “Mostly done; continue implementing the rest.”

Write:

> “`MemoryRepository.search_exact()` and owner/time/visibility SQL are complete at commit X. Reranking is excluded. Integration test `test_no_cross_owner_candidate` passes. Migration `2026...` is head. Next task should wire `RetrievalService` to the context assembler using frozen `MemoryQueryV1`; do not alter the repository signature.”

---

## 16. Parent integration procedure

Record promotion evidence using `38_STAGE_GATE_REPORT_TEMPLATE.md`.

For each task branch:

1. read packet and handoff;
2. verify upstream commit assumptions;
3. inspect diff, especially files outside ownership;
4. run task acceptance commands;
5. run relevant contract tests;
6. invoke specialist review if high-risk;
7. merge/rebase in dependency order;
8. resolve conflicts by contract, not by whichever code is newest;
9. regenerate schemas/clients if required;
10. run subsystem integration tests;
11. update status/traceability;
12. archive task packet as completed or return findings.

Recommended merge order:

```text
contracts/enums
→ migrations/repositories
→ pure domain services
→ model gateway/prompts/graphs
→ orchestration
→ API/OpenAPI
→ generated client/UI
→ operations/docs
→ stage QA/evidence
```

---

## 17. Review severity

Use:

- **Critical:** data loss, secret leakage, canonical corruption, duplicate irreversible effect, security bypass, unsafe content boundary;
- **High:** incorrect state transition, missing idempotency, migration failure, cross-character knowledge leak, unbounded model loop, impossible outcome accepted;
- **Medium:** incomplete failure path, weak validation, performance risk, confusing API, insufficient test, documentation drift;
- **Low:** naming, maintainability, optional optimization, nonblocking UX polish.

Critical/High findings block merge/stage promotion. Medium findings require resolution or an explicit tracked risk with owner/date. Low findings may enter backlog.

Review findings include:

```text
ID
severity
file/line or scenario
violated requirement/invariant
reproducer/evidence
recommended correction
blocking status
```

---

## 18. Specialist review checklists

## 18.1 Domain reviewer

- contract matches handbook;
- no model output is canonical before validation;
- typed effects only;
- perspective versus objective facts separated;
- no hidden cross-entity mutation;
- version/provenance fields present;
- high-impact operations privileged.

## 18.2 Database reviewer

- migration ordering and upgrade fixture;
- FK/unique/check constraints;
- transaction boundary;
- immutable event behavior;
- projection/source links;
- idempotency keys;
- indexes/query plans;
- no uncontrolled JSONB/EAV;
- rollback/rebuild path.

## 18.3 Concurrency reviewer

- leases/fencing;
- task generation;
- duplicate delivery;
- stale result;
- read/write conflict handling;
- phase/day barriers;
- cancellation and shutdown;
- outbox atomicity.

## 18.4 Knowledge/security reviewer

- mandatory owner/world/time/visibility predicates;
- no prompt-only filtering;
- logs/traces/API projections;
- user-mode authorization;
- memories treated as untrusted data;
- NPC/Director context separation;
- secrets/provider policy.

## 18.5 Model/graph reviewer

- bounded nodes/calls/beats;
- strict capability schema;
- repair/regenerate/fallback;
- no direct state commit;
- no actor-authored other reaction;
- fake-model deterministic corpus;
- provider capability probing;
- prompt/provenance versioning.

## 18.6 QA reviewer

- happy and failure paths;
- deterministic fixtures;
- property/invariant tests;
- process/database/provider failure;
- leakage/adversarial cases;
- previous-stage regression;
- evidence reproducible from documented commands.

---

## 19. Session startup protocol

At the start of every new coding session—even with the same model—do this:

1. read repository `AGENTS.md`;
2. read `docs/status/CURRENT_STAGE.md`;
3. read current task packet and latest relevant handoff;
4. inspect Git status/branch/log;
5. inspect migration head and service health if relevant;
6. run or inspect the smallest baseline test;
7. state the intended change and boundaries;
8. proceed.

Do not rely on prior chat context as the only source of current code state.

---

## 20. Session end protocol

Before ending:

1. stop at a coherent state;
2. format/lint/type/test changed scope;
3. run integration checks required by packet;
4. inspect `git diff` and untracked files;
5. remove temporary secrets/logs/assets;
6. commit coherent work or state why not;
7. update task checklist/status;
8. write handoff;
9. identify the next exact command or file;
10. report blocking findings separately.

Never leave a half-applied migration or undocumented schema generation.

---

## 21. Context packs for subagents

The parent should provide a compact context pack rather than the entire handbook when possible. It contains:

```text
Task packet
Relevant stage section
Relevant subsystem docs
Frozen contract files/schemas
Repository paths and neighboring examples
Known failures/status
Test commands
Upstream commit
```

Examples:

### Database subagent context pack

- `01`, `03`, `05`, `06`, current stage, `19`, `20`, `21`;
- Pydantic/enum contract files;
- current migrations and fixture;
- database test conventions.

### Memory subagent context pack

- `05`, `06`, `08`, `11`, `12`, `13`, current stage, `21`, `22`;
- observer-access contract;
- memory/retrieval schemas;
- seeded leakage fixtures.

### Frontend subagent context pack

- `02`, `17`, `18`, current stage, `19`, `21`;
- frozen OpenAPI;
- generated client command;
- design tokens/components;
- user-mode visibility matrix.

The subagent can read more documents, but the parent should identify the load-bearing ones.

---

## 22. Example parallel plan: Stage 2

### Freeze pass

Parent + contract owners freeze:

- claim/belief/relationship/goal/plan contracts;
- activity/route states;
- Director/NPC proposal schemas;
- Stage 2 migration table plan;
- API query DTO outline.

### Wave 1

- Agent A: `S2-DB-001` migrations/repositories;
- Agent B: `S2-CHAR-001` pure relationship/goal services against repository protocols/fakes;
- Agent C: `S2-KNOW-001` pure observation/belief policy and leakage fixtures;
- Agent D: `S2-SIM-001` pure activation/travel/activity services;
- Agent E: prompt/fake corpus draft against generated schemas;
- Agent F: QA scenario specification and oracle extensions.

### Integration checkpoint 1

Parent merges DB, adapts B/C/D repository implementations, runs contract/integration tests.

### Wave 2

- Agent G: Director/NPC;
- Agent H: daily memory/diary;
- Agent I: graph integrations;
- Agent J: multi-party scene assembly;
- Agent K: API OpenAPI v2;

### Integration checkpoint 2

Parent merges domain/graph/orchestration, freezes API.

### Wave 3

- Agent L: Vue Stage 2 views;
- Agent M: orchestration/fault tests;
- Agent N: security/leakage review;
- Agent O: stage evidence automation.

### Final review

Parent runs full seven-day gate, invokes reviewers, resolves blockers, updates traceability and tag.

---

## 23. Example parallel plan: Stage 4

Do not assign “make local inference work” as one task.

Parallelize:

- benchmark corpus/runner;
- ROCm server candidate A;
- ROCm server candidate B;
- model gateway capability registry;
- distributed lease/fencing tests;
- MinIO/object store;
- ComfyUI adapter;
- visual profile/content authoring;
- multi-host observability/deployment;
- QA fault matrix.

Only after benchmark ADR selects the server/model does the parent assign production adapter/deployment tasks.

---

## 24. Avoiding documentation drift

Every contract-changing task identifies affected docs. The parent runs a documentation link/term check before stage promotion.

Update stable docs only when behavior is accepted—not for speculative implementation notes. Temporary discoveries belong in status/task/handoff files until resolved.

At minimum update:

- ADR/change record;
- relevant subsystem doc;
- current stage task/gate;
- traceability matrix;
- generated JSON Schema/OpenAPI/database diagram if applicable;
- reference registry/version pin if external dependency changed.

---

## 25. Completion criteria for an agent-assisted stage

A stage is coordinated successfully when:

- no critical contract was implemented in competing forms;
- every merged task has a packet and handoff;
- file ownership violations are reviewed;
- migrations form one valid chain;
- generated contracts match source contracts;
- integration commits are understandable;
- status/known failures are accurate;
- stage evidence can be reproduced by a fresh session;
- a new parent agent can continue from repository documents without old chat history.

That final point is the real test of multi-session readiness.
