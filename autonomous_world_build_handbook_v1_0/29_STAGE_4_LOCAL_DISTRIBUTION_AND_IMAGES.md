# Stage 4 — Local Distribution, Durable Orchestration, and Images

**Version:** 1.0  
**Stage outcome:** The proven thirty-day world runs across the two Strix Halo systems and the RTX 4060 Ti system through provider-neutral model routing, durable distributed jobs, health-aware failover, object storage, ComfyUI image generation, and versioned visual continuity—without changing canonical simulation semantics.  
**Primary proof:** `stage4-distributed-local-v1` multi-host failure/soak suite and visual-continuity review.

---

## 1. Purpose

Stage 4 changes deployment topology, not the fictional rules.

The main engineering question is:

> Can the existing world continue safely when inference, orchestration, storage, and image workers are distributed across three local machines that can fail independently?

Do not begin Stage 4 until Stage 3 has a reproducible workload profile and a green thirty-day gate. Otherwise hardware and framework failures will be confused with domain/model-quality failures.

---

## 2. Target hardware topology

### 2.1 Strix Halo A — 128 GB unified memory

Preferred roles:

- primary large text-generation server replica;
- any focus character;
- Director/narrator overflow;
- optional local embedding/reranker service if benchmarked;
- worker heartbeat and model inventory.

### 2.2 Strix Halo B — 128 GB unified memory

Preferred roles:

- second compatible large text-generation server replica;
- any focus character;
- small-model services;
- summarization/evaluation/overflow;
- failover for Halo A.

### 2.3 RTX 4060 Ti — 16 GB VRAM, 32 GB RAM

Preferred roles:

- ComfyUI image worker;
- optional image-quality vision worker;
- control-plane services if it is the most continuously available host:
  - FastAPI;
  - PostgreSQL/pgvector;
  - orchestration service;
  - model gateway/router;
  - MinIO;
  - frontend.

Text inference must not depend on character-to-machine affinity. A character is a context package and canonical identity, not a process or loaded model instance.

---

## 3. Required capabilities

- measured local-model benchmark and selected serving stack;
- provider-neutral routing between OpenRouter and local endpoints;
- model capability registry and health-aware placement;
- two compatible text replicas or explicitly documented role partition;
- task leases, heartbeats, retries, idempotency, and failover across hosts;
- durable outer orchestration, with Temporal as a target option after evaluation;
- no canonical state in model-server memory/KV cache;
- separate image queue and canonical event critical path;
- MinIO/S3-compatible object storage;
- ComfyUI workflow versioning and API integration;
- character/location/style reference assets and visual-state versions;
- image prompt compilation from committed structured state;
- image quality/retry/manual-review policy;
- local network authentication, TLS or trusted-segment controls, and secret handling;
- distributed tracing and per-host metrics;
- multi-host deployment/runbooks/backups;
- failure tests for every host and service.

---

## 4. Explicit exclusions

- cloud autoscaling;
- public internet exposure without a separate security review;
- Kubernetes;
- character-specific text-model LoRAs unless benchmark evidence proves they are needed;
- image output becoming canonical automatically;
- video generation;
- multi-world or multi-tenant orchestration;
- generation-scale macro simulation.

---

## 5. Stage work packages

```text
S4-BENCH-001    Workload corpus and local serving benchmark
S4-MODEL-001    Local model adapters and capability registry
S4-MODEL-002    Health-aware model gateway/routing/failover
S4-ORCH-001     Distributed workers, leases, heartbeats, reconciliation
S4-ORCH-002     Temporal evaluation/adapter and durable workflows
S4-STORAGE-001  MinIO/object assets, backup, integrity
S4-IMG-001      ComfyUI adapter and workflow registry
S4-IMG-002      Visual profiles, prompt compiler, continuity
S4-IMG-003      Quality control, retries, gallery lifecycle
S4-OPS-001      Multi-host deployment, network, secrets, observability
S4-API-001      Model/worker/image administration API
S4-UI-001       Queue, gallery, worker, visual management UI
S4-QA-001       Distributed failure/soak/visual gate
```

---

## 6. Benchmark before selection

Do not hard-code vLLM, llama.cpp, SGLang, Transformers, or a particular quantization before benchmarking the exact hardware/software combination.

### 6.1 Benchmark corpus

Use the frozen Stage 3 representative requests:

- character action — short output, 12K–20K context;
- reaction — short output, 4K–10K context;
- Director proposal — structured medium output;
- resolver — strict structured output;
- narrator — prose output;
- daily/monthly summarization;
- evaluation;
- embedding query/passages;
- concurrent phase fan-out of four character requests.

Include valid, malformed, long-context, Unicode, and cancellation cases.

### 6.2 Candidate stacks

Evaluate at least:

- vLLM where the selected build/model/quantization supports `gfx1151` reliably;
- llama.cpp using a compatible quantized model;
- one conservative Transformers/PyTorch baseline if needed;
- optional SGLang only if it is stable on the pinned ROCm environment.

Use official compatibility matrices and project documentation at implementation time. The handbook intentionally does not promise that one stack/model combination will remain supported.

### 6.3 Metrics

- clean startup success across ten restarts;
- model load time;
- idle/loaded memory;
- maximum safe context;
- prompt and decode throughput;
- p50/p95 latency by role;
- four-request concurrency;
- structured-output validity;
- cancellation behavior;
- OOM recovery;
- twenty-four-hour soak stability;
- exact model/quantization quality against the Stage 3 rubric;
- power/thermal behavior if operationally important.

### 6.4 Selection gate

Select a stack only when:

- repeated startup is reliable;
- the full required context works;
- no silent output corruption occurs;
- one worker failure does not wedge the server;
- structured output and story quality remain acceptable;
- throughput supports the chosen world pacing;
- deployment is reproducible from pinned images/configuration.

Keep an OpenRouter adapter as a development/emergency provider, but never silently send private local-only worlds to it without policy approval.

---

## 7. Task packets

### S4-BENCH-001 — Local workload benchmark

**Deliverables**

- frozen JSONL request corpus with expected schemas and quality labels;
- benchmark runner that records environment/model/server versions;
- hardware inventory and memory settings;
- repeatable scripts for each candidate stack;
- results in machine-readable and human-readable forms;
- selection ADR with rejected alternatives and rollback option.

Do not edit domain prompts merely to make one server look better without rerunning Stage 3 quality comparisons.

### S4-MODEL-001 — Local adapters and capability registry

Implement provider adapters behind the interfaces in `12_MODEL_GATEWAY_OPENROUTER_AND_LOCAL_MIGRATION.md`.

Each endpoint advertises:

```text
endpoint_id
host_id
provider_kind
base_url
model_id/model_hash
roles
context_limit
structured_output_mode
quantization
max_concurrency
health
loaded_state
software versions
privacy policy
cost class
```

Capability discovery must be explicit. A local server does not automatically receive every role merely because it can answer a chat request.

### S4-MODEL-002 — Routing and failover

Implement a gateway that:

1. receives role, privacy, context, schema, quality, and deadline requirements;
2. filters endpoints by capability and policy;
3. scores healthy candidates;
4. reserves concurrency;
5. executes with stable request/idempotency ID;
6. records model provenance;
7. retries only safe failures;
8. fails over to a compatible endpoint;
9. preserves character identity through reconstructed context;
10. never reuses another request’s hidden KV/session state.

Default routing should spread simultaneous character intents across healthy replicas while preserving the same phase snapshot.

Tests include endpoint death, stale health, OOM, incompatible context, structured-output mismatch, privacy policy, and double completion.

### S4-ORCH-001 — Distributed workers

Extend the durable task system with:

- host/worker registry;
- capability labels;
- leases with fencing tokens;
- heartbeats;
- graceful drain;
- task cancellation;
- delayed retry and dead-letter state;
- reconciliation of abandoned leases;
- idempotent output acceptance;
- per-capability concurrency limits;
- phase fan-out/fan-in across workers.

A stale worker must not commit after its lease/fencing token is superseded.

### S4-ORCH-002 — Temporal evaluation and adapter

Temporal is a target durable workflow option, not a mandatory rewrite.

First create an ADR comparing:

- current database-backed orchestrator;
- Temporal Python SDK;
- operational complexity;
- deterministic workflow restrictions;
- deployment footprint;
- visibility/retry benefits;
- migration strategy;
- LangGraph integration maturity.

The official LangGraph integration should be treated as optional/public-preview at the time of this handbook. Prefer calling bounded LangGraph work inside ordinary activities through the project’s interfaces unless a current evaluation proves the plugin mature enough.

If adopted:

- workflow code coordinates only;
- activities perform database/model/graph I/O;
- canonical state remains PostgreSQL;
- activity idempotency keys remain domain-defined;
- signals control pause/player/deity commands;
- workflow versioning/change strategy is documented;
- a migration/rollback path exists.

The Stage 4 gate may pass with the proven database orchestrator if Temporal creates more risk than value. The interface and evaluation are mandatory; adoption is evidence-based.

### S4-STORAGE-001 — Object storage

Deploy S3-compatible object storage and implement:

- bucket/prefix policy;
- immutable content-addressed or versioned asset keys;
- checksums;
- image metadata in PostgreSQL;
- thumbnails/previews;
- orphan reconciliation;
- retention policy;
- export inclusion;
- backup and restore verification;
- signed/internal access URLs;
- no database BLOB storage for full assets.

Suggested prefixes:

```text
worlds/{world_id}/references/characters/...
worlds/{world_id}/references/locations/...
worlds/{world_id}/events/{event_id}/images/...
worlds/{world_id}/exports/...
workflows/comfyui/{workflow_version}/...
```

### S4-IMG-001 — ComfyUI adapter and workflow registry

Implement:

- ComfyUI health/capability probe;
- versioned API-format workflow registry;
- `/prompt` submission;
- returned prompt/job ID persistence;
- queue/history/status polling or event integration;
- output asset discovery/download/import;
- cancellation where supported;
- deterministic application idempotency around submissions;
- retry without duplicate canonical image records;
- timeout and worker-unavailable behavior.

Never block phase completion on ComfyUI.

### S4-IMG-002 — Visual state and prompt compiler

Implement versioned:

- world style profile;
- character visual profile;
- appearance version;
- outfit/equipment state;
- expression/pose inventory;
- location visual profile;
- item/faction references;
- image scene plan.

Compile prompts from committed structured scene state plus allowed narration constraints. Include event/scene IDs, appearance versions, location, time, weather, participants, relative positions, action outcome, camera, tone, and negative constraints.

Do not ask a character agent to generate its own authoritative visual prompt.

### S4-IMG-003 — Quality, retries, and gallery

Implement:

- deterministic technical checks: dimensions, corruption, output existence;
- optional vision checks: participant identity, count, major outfit/location/action mismatch, severe artifacts;
- confidence/quality report;
- bounded retry policy with changed seed/conditioning;
- manual approve/reject/regenerate;
- canonical metadata versus noncanonical asset status;
- late placement in historical timeline;
- gallery and provenance.

Images remain illustrative. Unexpected visual details never mutate world state automatically.

### S4-OPS-001 — Multi-host deployment and operations

Deliver:

- per-host deployment manifests/Compose or systemd units;
- pinned OS/kernel/driver/ROCm/CUDA/container versions;
- static LAN addressing or reliable names;
- firewall rules;
- internal authentication/service tokens;
- TLS or documented trusted-network exception;
- secret distribution and rotation;
- time synchronization;
- shared observability;
- backup locations;
- service startup order;
- drain/maintenance/reboot procedures;
- disaster recovery if the control-plane host is lost.

The database should live on the most reliable host with tested backups. Do not distribute PostgreSQL casually across machines.

### S4-API-001 — Administration API

Add authorized endpoints for:

- model endpoints/capabilities/health;
- task queues/leases/dead letters;
- host drain/re-enable;
- route/model override;
- image jobs/status/retry/cancel/approve/reject;
- visual profiles and references;
- ComfyUI workflow versions;
- storage integrity/reconciliation;
- distributed trace lookup.

### S4-UI-001 — Distributed operations and image UI

Add:

- host/model health dashboard;
- role routing and active loads;
- task queue/dead-letter view;
- image queue and historical placement;
- gallery filters;
- character/location visual reference management;
- image review/retry;
- workflow/model/seed/provenance display;
- clear indication that images are noncanonical illustrations.

### S4-QA-001 — Stage gate

Build tests and evidence for:

- one Halo loss during character fan-out;
- both Halos unavailable with safe pause/provider policy;
- model server OOM and restart;
- stale worker attempting late commit;
- orchestrator restart;
- control-plane restart;
- PostgreSQL restart before/after commit;
- MinIO outage;
- ComfyUI outage/backlog;
- duplicate image submission response;
- network partition and recovery;
- full Stage 3 month semantics under distributed execution;
- visual identity/location/outfit review across a representative image set.

---

## 8. Image relevance and budget

Default event-CG score:

```text
0.25 narrative significance
0.20 visual novelty
0.20 emotional intensity
0.15 focus-character importance
0.10 action intensity
0.10 user preference
```

Defaults:

- target four event CGs per detailed day;
- hard default cap eight per detailed day;
- one new CG per scene;
- unlimited reuse of approved portraits/backgrounds;
- image queue priority follows importance, not necessarily chronology;
- historical UI placement always follows source event time.

These values are configuration, not canonical world rules.

---

## 9. Hard exit gate

### Distributed correctness

- Stage 3 thirty-day deterministic scenario produces equivalent canonical semantics under distributed scheduling;
- any character can be served by either compatible Halo endpoint;
- host/process/network failures do not duplicate or lose canonical effects;
- fencing prevents stale workers from committing;
- all model calls retain endpoint/model/version provenance;
- no canonical state depends on process-local session/KV state;
- safe pause occurs when no compatible endpoint exists.

### Operational reliability

- all services restart from documented procedures;
- backups and restore are tested;
- secrets do not appear in logs/assets/export;
- queue/backlog/dead-letter state is observable;
- metrics/traces correlate phase → task → model → event → image;
- local network access is authenticated or explicitly constrained and documented.

### Image integrity

- images are submitted only after source event commit;
- image failure never blocks or rolls back simulation;
- image records include event/scene/workflow/model/seed/visual-version provenance;
- character/location reference versions are stable and update through explicit events;
- wrong or low-quality assets can be rejected/regenerated;
- visual surprises do not become canon;
- representative human review finds acceptable identity/style continuity.

### Regression

- all Stage 0–3 gates remain green;
- repository, migration, type, test, security, architecture, and deployment checks pass.

---

## 10. Handoff to Stage 5

Freeze:

- selected/pinned local serving environments and benchmark ADR;
- provider/local model routing policy;
- durable orchestration implementation and rollback path;
- worker/fencing/task contracts;
- object-storage and image metadata contracts;
- visual profile/workflow versions;
- multi-host deployment/runbook;
- representative distributed trace and failure evidence.

Stage 5 expands fictional time and generations; it does not require changing the local host topology.
