# Orchestration, Jobs, Concurrency, Recovery, and Distribution

**Version:** 1.0  
**Status:** Normative runtime specification  
**Primary owners:** `application.orchestration`, `infrastructure.tasks`, `infrastructure.outbox`, later `infrastructure.temporal`  
**Required reading:** `04`–`07`, `12`, `13`, `20`–`22`, and the active stage document

---

## 1. Purpose

This document defines the outer orchestration layer that advances phases, creates durable tasks, coordinates bounded LangGraph workflows, prevents duplicate work, recovers from crashes, publishes asynchronous jobs, manages concurrency, and later distributes work across local machines.

The Stage 0–3 implementation is application-owned and PostgreSQL-backed. Temporal is introduced only after the single-host semantics are stable. Temporal’s direct LangGraph integration is currently public preview; the stable architecture must not depend on that plugin. The later migration should wrap bounded LangGraph executions in ordinary Temporal Activities unless the plugin has become stable and passes a separate ADR review.

---

## 2. Ownership boundaries

```text
Outer Orchestrator
  owns phase lifecycle, task dependencies, pause/resume, retries,
  worker routing, and completion barriers.

LangGraph
  owns bounded reasoning inside one task.

Domain Services
  own validation and state-transition logic.

PostgreSQL
  owns canonical state, durable task state, locks, and outbox.

Workers
  execute leased tasks and return typed results.

ComfyUI
  owns image workflow execution only.
```

No layer may assume that another layer’s in-memory state is durable.

---

## 3. Orchestrator interface

```python
class WorldOrchestrator(Protocol):
    async def start_world(self, world_id: UUID) -> None: ...
    async def request_phase_advance(self, world_id: UUID) -> UUID: ...
    async def pause_world(self, world_id: UUID, mode: PauseMode) -> None: ...
    async def resume_world(self, world_id: UUID) -> None: ...
    async def submit_user_command(self, command: UserCommand) -> UUID: ...
    async def reconcile(self, world_id: UUID) -> ReconciliationReport: ...
```

The initial implementation may run in the API process for development, but the interface must not depend on HTTP request lifetime.

---

## 4. Durable task model

### 4.1 Task record

```text
TaskRun
├── task_id
├── world_id
├── phase_id?
├── scene_id?
├── character_id?
├── task_type
├── capability_queue
├── status
├── priority
├── idempotency_key
├── dependency_policy
├── input_reference
├── output_reference?
├── attempt
├── max_attempts
├── lease_owner?
├── lease_expires_at?
├── heartbeat_at?
├── next_attempt_at?
├── cancellation_requested_at?
├── error_class?
├── error_details_sanitized?
├── created_at
├── started_at?
└── completed_at?
```

Statuses:

```text
PENDING
READY
LEASED
RUNNING
WAITING_RETRY
WAITING_INPUT
SUCCEEDED
FALLBACK_SUCCEEDED
FAILED
CANCELLED
SUPERSEDED
DEAD_LETTER
```

### 4.2 Dependencies

Use an association table:

```text
TaskDependency
├── task_id
├── depends_on_task_id
├── required_status_set
└── failure_policy
```

Failure policies:

```text
BLOCK
USE_FALLBACK
SKIP
PAUSE_PHASE
```

A task becomes `READY` only after every mandatory dependency reaches an accepted status.

### 4.3 Idempotency key

Use deterministic keys such as:

```text
world:{world_id}:phase:{phase_id}:character:{character_id}:CHARACTER_DECISION:generation:{generation}

world:{world_id}:phase:{phase_id}:scene:{scene_id}:SCENE_RESOLUTION:generation:{generation}

world:{world_id}:event:{event_id}:IMAGE_JOB:workflow:{workflow_version}
```

A unique constraint prevents duplicate active or terminal work for the same logical operation. A deliberate regeneration increments `generation` and records which task it supersedes.

---

## 5. Phase orchestration workflow

The exact domain phases are defined in `07`; this section maps them to durable tasks.

```text
PHASE_CREATED
  → APPLY_USER_COMMANDS
  → ADVANCE_CLOCK
  → WORLD_TICK
  → DIRECTOR_TRIGGER_EVALUATION
  → optional DIRECTOR_PROPOSAL / WORLD_EVENT_RESOLUTION
  → BUILD_PHASE_SNAPSHOT
  → BUILD_CHARACTER_CONTEXT × N
  → CHARACTER_DECISION × N (parallel)
  → ASSEMBLE_SCENES
  → PRIORITIZE_SCENES
  → PROCESS_SCENE × M (ordered/constrained parallelism)
      ├── REACTION × K
      ├── RESOLUTION
      ├── COMMIT_SCENE
      ├── OBSERVATIONS
      └── OUTBOX RECORDS
  → PHASE_MEMORY_BARRIER
  → FINALIZE_PHASE
```

### 5.1 Phase parent record

`PhaseRun` is the durable parent state machine. It stores expected task counts and barrier status. It does not infer completion solely from an in-memory future list.

### 5.2 Creation transaction

Creating a phase should atomically:

- allocate calendar position;
- create `PhaseRun` with unique world/calendar constraint;
- create initial task rows;
- reserve model budget where required;
- record the orchestrator command.

If the transaction fails, no partial phase exists.

---

## 6. Task claiming and leases

Workers claim tasks with a transaction using PostgreSQL row locks:

```sql
SELECT task_id
FROM task_run
WHERE status = 'READY'
  AND capability_queue = :queue
  AND next_attempt_at <= now()
ORDER BY priority DESC, created_at ASC
FOR UPDATE SKIP LOCKED
LIMIT :batch_size;
```

Then update selected rows to `LEASED` with owner and expiry.

### 6.1 Lease rules

- lease duration exceeds normal heartbeat interval;
- long calls heartbeat outside the model HTTP connection when possible;
- a worker never holds a database transaction during model inference;
- expired leases are reconciled to `READY` or `WAITING_RETRY`;
- terminal tasks are never reclaimed;
- completion uses a compare-and-set on lease owner and status.

### 6.2 Heartbeats

Suggested:

```yaml
heartbeat_interval_seconds: 15
ordinary_lease_seconds: 90
model_call_lease_seconds: 300
image_lease_seconds: 900
```

Configuration should be longer than expected clock jitter and shorter than unacceptable recovery latency.

### 6.3 Worker death

If a worker dies:

1. lease expires;
2. reconciler inspects task and external-call provenance;
3. if a provider call completed and result was stored, resume validation;
4. otherwise retry with the same logical idempotency key;
5. canonical commit services check whether the operation already committed;
6. no effects are applied twice.

---

## 7. Canonical commit idempotency

A scene transaction accepts a `resolution_idempotency_key`.

Before applying effects:

```text
if committed_event exists for key:
    return existing commit result
else:
    validate current aggregate versions
    apply effects
    insert event/effects/observations/outbox
    commit
```

If a process dies after commit but before acknowledging the task, the retry finds the existing event and marks the task succeeded without reapplying effects.

---

## 8. Concurrency model

### 8.1 Safe parallelism

Parallel by default:

- character primary intent generation from the same sealed snapshot;
- context assembly for different characters;
- independent observation wording after allowed facts exist;
- embeddings for different memories;
- noncanonical narration;
- image jobs.

### 8.2 Constrained parallelism

Scenes may run in parallel only when their write sets are disjoint.

Calculate a conservative write-set declaration from:

- participant IDs;
- target entities;
- location resources;
- shared activities;
- items;
- faction/settlement aggregates.

If uncertainty exists, serialize.

### 8.3 Forbidden parallelism

- two scene commits modifying the same character state version;
- two item transfers for the same unique item;
- clock advancement while a phase remains active;
- phase snapshot creation during world-tick mutation;
- memory compaction that deletes active recent rows before phase barrier;
- hard retcon while ordinary phase writes continue.

### 8.4 Optimistic concurrency

Every aggregate projection has a version. Effect commands declare expected versions. A mismatch causes `ConcurrencyConflict`, not a model regeneration. The orchestrator reassembles or serializes affected scenes.

---

## 9. Scene ordering and processing

The scheduler produces a stable scene order after simultaneous intents.

### 9.1 Priority versus canonical causality

Priority determines which scene transaction runs first. Later scenes see effects committed by earlier scenes only when they share relevant state and were intentionally ordered. Independent scenes may use the same phase snapshot and run concurrently.

### 9.2 Scene processing record

`SceneRun` tracks:

- state-machine status;
- snapshot/event sequence baseline;
- participants;
- declared read/write sets;
- beat budget;
- attempt/reaction tasks;
- resolution task;
- commit result;
- continuation state.

### 9.3 Failure

If one independent scene fails:

- completed independent scenes remain committed;
- the phase remains incomplete;
- retry or fallback the failed scene;
- do not replay all scenes;
- pause before next phase if the failed scene cannot resolve safely.

---

## 10. Retry policy

Retries exist at different layers:

```text
HTTP/provider retry
  transient delivery failure, no workflow semantics.

Model-workflow regeneration
  malformed or semantically invalid output, at most one.

Task retry
  worker/process failure or transient infrastructure failure.

Domain conflict retry
  re-read/reassemble after optimistic concurrency conflict.
```

Do not multiply each layer’s maximum blindly. Define a total attempt budget.

### 10.1 Retry table

| Failure | Action |
|---|---|
| worker crash | reclaim lease, same task attempt or increment infrastructure attempt |
| provider timeout | bounded gateway retry |
| malformed model output | graph repair/regeneration |
| invalid action | action fallback |
| database unavailable before commit | retry task |
| database connection lost after commit uncertainty | query idempotency key before retry |
| optimistic conflict | reassemble/serialize scene |
| image failure | independent retry/dead-letter |
| missing user input | `WAITING_INPUT` |
| permanent schema bug | dead-letter and pause |

### 10.2 Dead-letter

A task becomes `DEAD_LETTER` after terminal or exhausted failure. Store:

- sanitized error;
- all attempts;
- last input reference;
- operator actions available;
- whether phase can degrade or must pause.

The operations UI allows retry as a new generation, skip where policy permits, or manual repair through a typed command.

---

## 11. Pause, resume, and cancellation

### 11.1 Pause modes

```text
AFTER_CURRENT_SCENE
AFTER_CURRENT_PHASE
IMMEDIATE_BEFORE_COMMIT
EMERGENCY_STOP_NEW_TASKS
```

An “immediate” pause cannot interrupt an atomic database commit already executing. It stops leasing new tasks and marks cancellation requests.

### 11.2 Safe points

- before phase creation;
- after deterministic world tick;
- after snapshot seal;
- after each scene commit;
- before finalizing phase;
- after day compaction.

### 11.3 Resume

The reconciler reads durable state and creates only missing tasks. It does not rely on an in-memory program counter.

### 11.4 Cancellation

Model HTTP requests may be cancelled when safe, but cancellation uncertainty is handled like a worker crash. Canonical tasks check idempotency before any retry.

---

## 12. Transactional outbox

### 12.1 Purpose

The scene commit transaction inserts outbox rows for asynchronous follow-up:

- image generation;
- embedding;
- timeline projection;
- WebSocket notification;
- diary generation;
- analytics;
- quality evaluation.

### 12.2 Outbox record

Defined in `06`. Required semantics:

- unique idempotency key;
- payload contains references, not enormous binaries;
- status/lease fields similar to tasks;
- created in the same transaction as the canonical event;
- dispatcher marks completion only after target acknowledgement or durable job creation.

### 12.3 At-least-once delivery

The outbox is at-least-once. Every consumer must be idempotent.

Examples:

- image job table has unique `(event_id, workflow_version, generation)`;
- WebSocket stream event has a stable sequence ID;
- embedding row has unique memory/version key;
- timeline projection upserts by event ID.

---

## 13. Reconciliation loop

A periodic reconciler checks:

- expired task/outbox leases;
- phases stuck without ready tasks;
- succeeded dependencies whose child remains pending;
- terminal task whose phase counter was not updated;
- duplicate logical tasks;
- scene resolution committed but task not acknowledged;
- orphaned model-call records;
- incomplete daily memory barriers;
- world marked running without an active or scheduled phase;
- request-budget reservations that expired;
- image jobs with stale worker heartbeat.

Reconciliation emits audit events and metrics. It does not guess canonical outcomes.

---

## 14. Leader and scheduler ownership

On one process, one orchestrator loop is sufficient. When multiple API/worker processes exist, use one of:

- PostgreSQL advisory lock per world;
- lease record on `world_runtime`;
- later Temporal workflow ownership.

Only the owner may create the next phase. Workers can execute tasks independently.

A world-level lock is held briefly during phase creation, not throughout inference.

---

## 15. Capability queues and workers

Logical queues:

```text
orchestration
large_text
small_text
embedding
narration
image
vision_quality
maintenance
```

Stage 0–3 may map all text queues to one OpenRouter worker. Queue names still belong in task records to preserve later migration.

Worker registration:

```text
WorkerRegistration
├── worker_id
├── host_id
├── capabilities[]
├── model_profiles[]
├── max_concurrency
├── current_load
├── status
├── heartbeat_at
└── metadata
```

Never assign a character permanently to a worker.

---

## 16. Request concurrency and rate limiting

Use separate controls:

- global OpenRouter RPM token bucket;
- per-model/profile concurrency semaphore;
- per-worker concurrency;
- per-world phase limits;
- database pool limits;
- later local model queue depth.

Character decisions can be enqueued together but should respect a provider RPM bucket. The scheduler’s canonical simultaneous semantics do not require HTTP requests to begin at the same millisecond; they require all inputs to reference the same sealed snapshot.

---

## 17. Day and month barriers

### 17.1 Phase barrier

Complete when:

- all required scene commits are terminal success/fallback;
- all required observations and immediate memories exist;
- image jobs are durably enqueued where applicable;
- no mandatory task remains active.

### 17.2 Day barrier

Complete when:

- every phase is complete;
- daily summaries/compaction reach required stage status;
- scheduled next-day state is valid;
- recovery snapshot is created;
- provider reservations are reconciled.

### 17.3 Month barrier

Complete when:

- daily records are complete;
- monthly summaries and reflection run or use an approved fallback;
- arc/faction monthly updates are applied;
- personality changes are validated;
- month snapshot exists.

---

## 18. Temporal migration in Stage 4

### 18.1 Why later

Temporal adds durable workflow history, signals, retries, timers, task queues, and operational visibility. It also adds another distributed system and determinism rules. Introduce it only after the PostgreSQL-backed semantics and idempotency tests pass.

### 18.2 Mapping

```text
One world runtime
  → one long-lived WorldWorkflow or bounded PhaseWorkflow hierarchy.

Phase execution
  → child workflow or bounded workflow invocation.

Model/LangGraph call
  → Activity.

Database command
  → Activity with idempotency key.

User intervention
  → Signal or Update.

Pause/resume
  → Workflow state plus signals.

Scheduled fictional event
  → domain schedule, not necessarily wall-clock Temporal timer.
```

### 18.3 Determinism

Temporal Workflow code must be deterministic. Network calls, database access, model calls, and LangGraph nodes run in Activities. Do not run an LLM inside Workflow code.

### 18.4 LangGraph plugin

The official Temporal LangGraph integration is public preview as of this handbook version. Default Stage 4 design:

- invoke compiled bounded LangGraph workflows from standard Activities;
- persist project task/canonical IDs;
- do not make the plugin mandatory;
- review plugin stability through an ADR before adopting it.

### 18.5 Migration strategy

1. keep domain and task interfaces unchanged;
2. implement Temporal adapter behind `WorldOrchestrator`;
3. run both orchestrators against the same conformance suite;
4. avoid dual ownership of one live world;
5. migrate a cloned test database first;
6. promote only after crash, signal, and deployment-version tests.

---

## 19. Multi-machine local distribution

### 19.1 Network assumptions

- stable private LAN addresses or DNS names;
- authenticated control endpoints;
- firewall allows only required ports;
- TLS or trusted private network with explicit risk acceptance;
- synchronized clocks through NTP;
- no shared filesystem assumption.

### 19.2 Model routing

The gateway maintains compatible endpoints and health. It chooses by:

- role compatibility;
- model loaded;
- structured-output support;
- queue depth;
- recent latency/error rate;
- available memory;
- affinity for batching, not character identity.

### 19.3 Worker disappearance

- active lease expires;
- compatible worker may retry;
- same task/snapshot/idempotency key is used;
- if no compatible worker exists, pause or use configured external fallback;
- world state remains in PostgreSQL.

### 19.4 Database ownership

One PostgreSQL primary is canonical. Workers never maintain private canonical copies. Read caches must be versioned and disposable.

---

## 20. Required tests

### Task tests

- two workers cannot complete the same lease;
- expired lease is reclaimed;
- terminal task is never re-leased;
- dependency transitions are correct;
- retry schedules persist across restart;
- dead-letter retains diagnostic context.

### Commit tests

- process dies after database commit but before task acknowledgement;
- duplicate resolution request returns existing event;
- optimistic conflict serializes/reassembles;
- outbox row is present whenever event commit succeeds;
- rolled-back event creates no outbox row.

### Phase tests

- restart at every state-machine boundary;
- pause after current scene;
- player input wait/resume;
- one scene fails while another remains committed;
- no next phase starts before barrier;
- quota shortfall stops phase creation rather than halfway corruption.

### Distribution tests

- kill one text worker mid-call;
- route next task to another compatible worker;
- lose image worker for a full fictional day;
- database temporarily unavailable;
- duplicate WebSocket/outbox delivery is idempotent;
- worker clock skew does not create premature lease takeover within tolerance.

### Temporal conformance tests

The PostgreSQL and Temporal orchestrator adapters must produce the same domain/task terminal states for the same deterministic fake-model scenario.

---

## 21. Stage introduction map

| Capability | First required stage |
|---|---:|
| PostgreSQL task rows, idempotency, reconciliation | 0 |
| Complete phase dependencies and restart safety | 1 |
| Day barriers and background compaction jobs | 2 |
| Month barriers, soak recovery, broader queues | 3 |
| Temporal adapter, multi-machine workers, image queues | 4 |
| Macro-simulation and generation workflow hierarchy | 5 |

---

## 22. Definition of done

The orchestration subsystem is complete for a stage when:

- every long-running operation has durable task state;
- tasks can be retried without duplicate effects;
- worker leases and reconciliation recover from process death;
- simultaneous character semantics are preserved independent of HTTP scheduling;
- phase/day/month barriers are explicit and tested;
- outbox consumers are idempotent;
- pausing and user input survive restart;
- characters are not tied to workers;
- future Temporal migration does not require domain rewrites;
- fault-injection tests pass at every canonical boundary.

---

## 23. Official references

- Temporal Python error handling and retries: <https://docs.temporal.io/develop/python/failure-detection>
- Temporal message passing/signals/updates: <https://docs.temporal.io/develop/python/message-passing>
- Temporal child workflows: <https://docs.temporal.io/develop/python/child-workflows>
- Temporal LangGraph integration, public preview at handbook date: <https://docs.temporal.io/develop/python/integrations/langgraph>
