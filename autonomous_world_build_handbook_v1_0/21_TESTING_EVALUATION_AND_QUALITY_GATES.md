# Testing, Evaluation, Fault Injection, and Quality Gates

**Version:** 1.0  
**Status:** Normative verification specification  
**Primary owners:** every implementation workstream; quality/review agents  
**Required reading:** all subsystem documents and current stage document

---

## 1. Purpose

This document defines the test pyramid, deterministic fixtures, fake model strategy, database and API integration tests, state-machine/property tests, prompt/model evaluation, knowledge-leakage tests, scenario and soak tests, fault injection, performance budgets, stage promotion gates, and evidence required before a task or stage is considered complete.

A visually entertaining run is not evidence of correctness.

---

## 2. Quality dimensions

The project measures:

```text
CORRECTNESS
  domain invariants and canonical state.

DURABILITY
  restart, retry, idempotency, and recovery.

KNOWLEDGE_ISOLATION
  no accidental omniscience or memory leakage.

CHARACTER_FIDELITY
  recognizable personality, values, voice, and agency.

CAUSAL_COHERENCE
  events, actions, outcomes, and consequences follow supplied state.

MEMORY_QUALITY
  important recall, provenance, uncertainty, and appropriate forgetting.

NARRATIVE_QUALITY
  engaging, restrained, nonrepetitive, non-cringe presentation.

PERFORMANCE
  phase latency, context size, queue health, database efficiency.

OPERABILITY
  observable state, actionable failures, backups, and safe intervention.

SECURITY_AND_PRIVACY
  tool boundaries, auth, secrets, prompt injection, content policy.

VISUAL_CONTINUITY
  Stage 4 identity, outfit, location, and event correctness.
```

Each stage defines which dimensions are mandatory.

---

## 3. Test layers

```text
Static checks
  ↓
Unit tests
  ↓
Property/state-machine tests
  ↓
Repository/database integration tests
  ↓
Adapter/contract tests
  ↓
API and graph integration tests
  ↓
Deterministic scenario tests
  ↓
Fault-injection tests
  ↓
Model evaluation corpus
  ↓
Soak and performance tests
  ↓
Human narrative review
```

Do not replace lower deterministic layers with model-graded tests.

---

## 4. Test classification and markers

Suggested pytest markers:

```text
unit
property
integration
contract
scenario
fault
model_fake
openrouter_live
local_model_live
image_live
slow
soak
security
migration
api
websocket
```

Default command excludes external and long tests:

```bash
uv run pytest -m "not openrouter_live and not local_model_live and not image_live and not soak"
```

Every test file belongs to a clear layer. Avoid “misc” integration tests that require every service.

---

## 5. Determinism and fakes

### 5.1 Fake clock

Use a controllable operational clock and explicit fictional clock. Tests never sleep for fictional phases.

### 5.2 Seeded randomness

Rule-resolution randomness comes from an injectable random source. Tests can supply deterministic roll sequences.

### 5.3 Fake model gateway

The default fake gateway supports scripted behaviour by role and request ID:

```text
valid structured output
malformed JSON
schema-invalid output
semantic-invalid output
provider timeout
429 with retry-after
unsupported parameter
late response
cancelled response
embedding vector result
embedding dimension mismatch
```

It records calls and can assert context/package IDs and token estimates.

### 5.4 Fake image gateway

Supports:

- successful submission/completion;
- validation failure;
- delayed job;
- missed WebSocket event;
- history recovery;
- duplicate output;
- malformed image;
- worker unavailable.

### 5.5 No network in ordinary tests

Block accidental network access in unit/integration CI except explicitly marked live tests.

---

## 6. Test data builders

Prefer typed builders over large hand-written dictionaries:

```python
world = WorldBuilder().with_stage1_defaults().build()
sein = CharacterBuilder("Sein").at("Willow House").build()
alex = CharacterBuilder("Alex").at("Willow House").build()
scene = SceneBuilder(world).with_participants(sein, alex).build()
```

Builders create valid defaults and explicit overrides. Tests for invalid data construct invalid boundary DTOs deliberately.

Maintain canonical fixture IDs for cross-file scenarios in one registry.

---

## 7. Unit tests

Unit tests cover pure logic:

- value-object validation;
- state transitions;
- salience and priority calculations;
- stat/relationship bounds;
- need/emotion decay;
- rule formulas;
- action/effect validation;
- scene assembly matching;
- context token trimming;
- retrieval scoring;
- idempotency-key generation;
- error classification;
- prompt metadata rendering;
- schema minimization;
- role/perspective policies.

Use table-driven tests for enums and effect variants.

---

## 8. Property and state-machine tests

Use Hypothesis or equivalent for invariants over many generated inputs.

### 8.1 Domain properties

- resources never negative;
- stat/relationship/confidence values remain in range;
- no item has two exclusive owners;
- one character has one current physical location;
- card/state versions increase monotonically;
- completed phase cannot transition to active;
- dead character cannot become active without return event;
- applying the same event by idempotency key twice is equivalent to once;
- event sequence strictly increases per world;
- summary citations belong to owner-visible sources.

### 8.2 State-machine models

Model:

- phase lifecycle;
- scene lifecycle;
- task/lease lifecycle;
- image job lifecycle;
- goal/plan lifecycle;
- memory consolidation lifecycle;
- world runtime pause/resume/end lifecycle.

Generate valid and invalid command sequences and assert rejected transitions do not mutate state.

---

## 9. Database integration tests

Use real PostgreSQL with pgvector and real migrations.

Cover:

- constraints and indexes;
- unique idempotency keys;
- optimistic concurrency;
- transaction rollback;
- event/effect/projection atomicity;
- outbox in same transaction;
- row-lock task claiming;
- lease expiration;
- filtered exact vector query;
- owner/visibility filter;
- migration upgrade/downgrade policy;
- seed idempotency;
- data rebuilding from source observations where implemented.

Do not use SQLite as a substitute for PostgreSQL-specific correctness.

### 9.1 Constraint test policy

For every important database constraint, include one test that proves the database itself rejects the violation, not only application validation.

---

## 10. Migration tests

CI must:

1. create empty PostgreSQL;
2. upgrade to head;
3. verify expected extensions/tables/constraints;
4. load a prior-stage fixture snapshot;
5. upgrade it;
6. run consistency audit;
7. generate schema SQL;
8. ensure one migration head unless documented;
9. optionally exercise downgrade where safe.

A migration that rewrites large tables includes a performance/locking note and recovery plan.

---

## 11. Adapter contract tests

### 11.1 Model gateway

Defined in `12`; test fake HTTP server and provider-neutral results.

### 11.2 LangGraph

Defined in `13`; test all graph paths and no canonical writes.

### 11.3 ComfyUI

Defined in `16`; test API workflow and recovery.

### 11.4 Object store

- put/get/head/delete policy;
- checksum validation;
- idempotent upload;
- signed/local URL policy;
- unavailable storage.

### 11.5 Temporal adapter

Stage 4 conformance against application orchestrator.

---

## 12. API tests

Cover:

- request validation;
- role/auth matrix;
- perspective redaction;
- idempotent commands;
- pagination and cursor stability;
- error mapping;
- OpenAPI generation;
- WebSocket authentication/replay/backpressure;
- command disconnect/requery;
- no ORM/internal/provider types in API schema;
- malicious rendered content sanitized.

Generate a permission matrix fixture and test every protected endpoint against every role.

---

## 13. Knowledge-isolation test suite

This is a release-blocking suite.

### 13.1 Seeded-secret test

1. create private secret known only to character A and Director;
2. create semantically similar public memories for B;
3. run B’s context assembly and vector retrieval;
4. assert A’s memory/secret is absent from source IDs and rendered prompt;
5. invoke B model fake that attempts to request A’s secret;
6. assert tools reject access;
7. verify B cannot state secret as known fact in accepted output.

### 13.2 Claim-versus-fact test

A lies to B. Verify:

- canonical event records utterance;
- claim stores speaker belief/intent privately;
- B receives utterance observation;
- B may form belief;
- claim proposition does not enter objective lore/event facts;
- B does not receive `speaker_believes_false`.

### 13.3 Director leakage test

Director knows a planned betrayal. Proposal lacking causal reveal is rejected. Character contexts remain clean.

### 13.4 Perspective API test

Compare omniscient and character responses. Assert hidden fields are absent, not merely null with revealing labels.

### 13.5 Prompt-injection test

Insert malicious instructions into memory, lore, diary, claim, and NPC dialogue. Assert:

- prompt hierarchy unchanged;
- tool calls scoped;
- output schema unchanged;
- no secret access;
- no arbitrary URL/SQL/shell execution.

---

## 14. Deterministic scenario harness

A scenario is a versioned fixture plus expected semantic assertions.

```yaml
scenario_id: stage1-first-day-v1
seed: emberreach-v1
model_script: first_day_script_v1
random_script: first_day_random_v1
steps:
  - advance_phase
  - wait_for_terminal
  - advance_phase
  - wait_for_terminal
assertions:
  - path: world.clock.absolute_phase
    equals: 3
  - invariant: no_duplicate_events
  - invariant: perspectives_isolated
```

The harness produces:

- event timeline;
- task trace;
- model calls;
- state hashes;
- invariant report;
- performance metrics;
- failure bundle.

Scenarios use fake models by default, enabling exact semantic expectations.

---

## 15. Core scenario catalog

### Foundation

- seed and deterministic world tick;
- wait/observe/move/rest effects;
- event commit and restart;
- duplicate command.

### Interaction

- two simultaneous intents merge into one conversation;
- conflicting item actions;
- one attack and one prepared reaction;
- conversation reaches beat cap and continues;
- absent target invalidates/fallbacks.

### Knowledge

- covert action with partial observers;
- lie/rumour chain;
- secret reveal through a letter;
- false belief corrected by later evidence;
- malicious memory.

### Memory

- daily compaction;
- promise recall;
- routine deduplication;
- long-term retrieval;
- summary rebuild;
- embedding unavailable fallback.

### Rules

- stamina exhaustion;
- injury and healing;
- failed magic due to mana;
- improvised magic partial success;
- combat continuation;
- death and return rule.

### Director/world

- quiet phase no proposal;
- stagnation low-disruption event;
- NPC deduplication;
- route encounter;
- arc refusal and adaptation;
- faction consequence.

### Generations

- time compression stop condition;
- succession;
- private-memory noninheritance;
- world peace;
- eradication;
- max-day ending.

---

## 16. Model evaluation corpus

Model outputs are nondeterministic, so evaluate semantic properties over a fixed corpus.

### 16.1 Character-decision metrics

- schema-valid rate;
- domain-valid rate after one repair;
- knowledge violation rate;
- authored-other-reaction rate;
- personality alignment;
- goal relevance;
- proportionate waiting/rest rate;
- action diversity;
- unsupported entity rate.

### 16.2 Resolver metrics

- schema-valid rate;
- effect-envelope violation rate;
- unsupported effect rate;
- protagonist bias tests;
- resource correctness;
- partial/failure outcome calibration;
- citation of supplied factors.

### 16.3 Narrative metrics

- unsupported fact rate;
- voice distinctiveness;
- repetition/catchphrase rate;
- cliché density;
- exposition density;
- emotional overstatement;
- sudden romance/coercion violations;
- content-rating compliance;
- human preference/review.

### 16.4 Memory metrics

- important-event recall;
- promise recall;
- unobserved-fact hallucination;
- source citation validity;
- duplicate-memory rate;
- retrieval precision/recall on seeded queries;
- context token use.

### 16.5 Run policy

- fake deterministic corpus in every relevant PR;
- live candidate model benchmark before profile activation;
- compare old and new prompt/model profiles;
- retain result artefacts and hashes;
- do not promote based on one anecdotal run.

---

## 17. Evaluator use

A model evaluator is diagnostic, not sole judge.

Use deterministic checks first. When an evaluator scores prose/personality:

- supply explicit rubric;
- randomize output order in comparative tests;
- blind model/profile identity where practical;
- test evaluator consistency;
- include human review samples;
- never let evaluator directly change canon;
- store cited spans and confidence.

---

## 18. Longitudinal and soak tests

### 18.1 Seven-day soak

Stage 2 minimum:

- all ten phases/day or configured skips;
- four focus characters;
- fake model varied outputs;
- restart at random task boundaries;
- memory compaction;
- Director triggers;
- no manual database repair.

### 18.2 Thirty-day soak

Stage 3 release blocker:

- long-term memory/RAG;
- at least one active arc;
- relationships and commitments;
- injuries/magic where configured;
- provider-independent fake model for volume;
- periodic live-model sampling separately;
- fault injection;
- memory/context growth metrics;
- narrative repetition review;
- consistency audit every day.

### 18.3 Multi-generation soak

Stage 5:

- detailed and compressed intervals;
- succession;
- lineage records;
- faction/economy updates;
- stop-on-salience;
- ending conditions;
- bounded database/context growth.

---

## 19. Fault injection

Inject failure at every boundary:

```text
before model call
after provider accepts request
before result persistence
after result persistence
before scene transaction
during effect validation
after database commit before acknowledgement
before outbox dispatch
after external image submission
before asset metadata commit
during daily compaction
during migration/restore test
```

Expected result is defined in subsystem docs. Any ambiguous state requires reconciliation, not duplicate execution.

### 19.1 Process-kill testing

Use a harness to terminate worker processes at named checkpoints, restart, run reconciliation, and assert terminal state.

### 19.2 Dependency outage

- PostgreSQL unavailable;
- OpenRouter 429/timeout;
- object store unavailable;
- ComfyUI offline;
- one Halo worker offline;
- Temporal worker deployment change.

---

## 20. Performance budgets

Initial targets are measured and adjusted through ADR, but tests should collect:

```text
phase end-to-end latency
character model latency
resolver latency
context token estimate/actual
SQL query count and slow queries
scene commit latency
memory retrieval latency
queue wait
retry rate
WebSocket lag
image queue latency
RAM/GPU usage later
```

Suggested deterministic/local service budgets:

- API read p95 under 300 ms for ordinary local projections;
- scene commit p95 under 500 ms excluding model calls;
- exact memory retrieval p95 under 250 ms at Stage 3 fixture scale;
- context assembly p95 under 500 ms excluding embeddings;
- no unbounded N+1 queries;
- task reconciliation completes within configured interval.

Model and image latency are environment-dependent; stage docs set user-experience targets after benchmarking.

---

## 21. Database growth and context budgets

Track per simulated day:

- events;
- observations;
- memories;
- embeddings;
- model-call bytes;
- task/outbox rows;
- image assets;
- active context tokens.

Tests assert:

- recent context remains bounded;
- completed operational rows follow retention policy;
- no full lifetime transcript enters prompts;
- routine observations compact appropriately;
- vector rows correspond to active version/model.

---

## 22. Stage quality gates

### Stage 0

- schema, migration, seed, deterministic rules, task idempotency;
- no live model required for acceptance;
- clean restart and duplicate command test.

### Stage 1

- one complete three-phase day;
- two simultaneous character decisions;
- bounded reactions and scenes;
- isolated observations/recent memory;
- restart at every phase boundary;
- OpenRouter smoke separate from deterministic acceptance.

### Stage 2

- coherent seven-day run with ten phases;
- four focus characters;
- Director triggers, temporary NPC, claims/beliefs, daily compaction, travel;
- leakage suite passes;
- no manual repair.

### Stage 3

- thirty-day soak;
- long-term RAG;
- active arc, factions, injuries/magic;
- memory and narrative quality thresholds;
- context/database growth bounded;
- all hard acceptance criteria from project charter.

### Stage 4

- distributed worker failover;
- Temporal/application orchestrator conformance;
- ComfyUI backlog/restart recovery;
- visual continuity corpus;
- images never block phase.

### Stage 5

- compressed-time correctness;
- three-generation cap;
- succession and inheritance boundaries;
- peace/eradication/max-day ending;
- final export and restore.

Detailed gates are repeated in stage documents and traceability matrix.

---

## 23. Test evidence bundle

For a stage promotion, instantiate `38_STAGE_GATE_REPORT_TEMPLATE.md` and produce:

```text
stage-gate-report.md
pytest-junit.xml
coverage.xml
static-analysis reports
migration verification
scenario artefacts
audit/consistency report
performance summary
model evaluation summary
leakage suite results
fault-injection results
known issues and waived gates
version/hash manifest
```

Waivers require product-owner approval and must be explicit. Hard knowledge/canon/idempotency violations are not waivable for promotion.

---

## 24. Coverage policy

Line coverage is a signal, not the goal. Suggested minimums:

- domain/application pure logic: 90% branch coverage target;
- infrastructure adapters: meaningful error-path coverage;
- API routes: role/perspective/validation matrix;
- graph workflows: every path;
- migrations: upgrade validation;
- frontend critical flows: component + E2E coverage.

Never add meaningless tests solely to increase a number.

---

## 25. Flaky-test policy

A flaky test is a bug.

- quarantine only with issue/task ID and owner;
- preserve failure artefacts;
- no blind retries in ordinary CI except known infrastructure startup stabilization;
- model live tests may use statistical thresholds, not exact text;
- generated image tests use metadata/semantic checks, not pixel equality;
- remove quarantine before stage promotion unless explicitly waived as non-gating external dependency.

---

## 26. Definition of done for a task

A coding task is done when:

- acceptance criteria have tests;
- relevant static and architecture checks pass;
- failure and retry paths are covered;
- migration/generated artefacts are current;
- no existing stage scenario regresses;
- documentation and handoff are updated;
- test commands and evidence are recorded in the task packet.

---

## 27. Definition of done for testing subsystem

The project has adequate verification when:

- default tests are deterministic and offline;
- every canonical boundary has idempotency and fault tests;
- strict leakage tests block release;
- model quality is evaluated over corpora, not anecdotes;
- long-running stages have soak tests;
- migration, restore, and distributed failures are exercised;
- every requirement maps to one or more tests in `32`;
- stage promotion produces an auditable evidence bundle.
