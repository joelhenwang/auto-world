# Reference Registry, Version Policy, and Change Control

**Version:** 1.0  
**Status:** Normative external-reference and architecture-change procedure  
**Last handbook verification date:** 2026-07-29

---

## 1. Purpose

External services and libraries will change during this project. This document records the current intended dependencies, what must be reverified at implementation time, and how architectural or contract changes are proposed and propagated.

Never treat a model name, free quota, framework integration, GPU support statement, or API behavior in this handbook as permanently guaranteed.

---

## 2. External reference policy

Use primary sources for technical decisions:

- official provider/API documentation;
- official model cards/repositories;
- official framework/library documentation;
- official hardware compatibility matrices;
- source repository release notes/issues when documentation is insufficient.

Community reports may identify a risk, but they do not replace capability probes and local benchmarks.

For each adopted dependency record:

```text
name
purpose
source URL
license
version/commit/image digest
verified date
runtime capability probe
configuration
known constraints
upgrade owner
rollback version
```

Raw links are included in this internal artifact so a coding agent can verify current behavior directly.

---

## 3. Current model/provider registry

## 3.1 OpenRouter text development model

```text
Configured model slug:
  nvidia/nemotron-3-super-120b-a12b:free

Purpose:
  Early development character, Director, resolver, narrator,
  summarizer, and evaluator calls through role-specific prompts.

Current reference:
  https://openrouter.ai/nvidia/nemotron-3-super-120b-a12b:free
```

Current design assumptions, subject to runtime probe:

- OpenAI-compatible chat endpoint through OpenRouter;
- large served context advertised by the model page at handbook verification time;
- free endpoint availability and provider routing may change;
- structured-output enforcement is endpoint/provider-specific;
- free endpoint privacy/data handling must be reviewed before every use profile;
- fictional/synthetic development data only in early stages.

The application-level context limits in `12` are intentionally much smaller than the advertised maximum.

## 3.2 OpenRouter embedding development model

```text
Configured model slug:
  nvidia/nemotron-3-embed-1b:free

Purpose:
  Stage 3 long-term memory embeddings and retrieval experiments.

Current reference:
  https://openrouter.ai/nvidia/nemotron-3-embed-1b:free

Official model reference:
  https://huggingface.co/nvidia/Nemotron-3-Embed-1B-BF16
```

The current handbook baseline expects:

- 2,048-dimensional native embeddings;
- `query: ` and `passage: ` input prefixes where recommended by the official model card;
- versioned database columns/tables;
- a startup/deployment capability probe that verifies returned dimension;
- no vector retrieval dependency when endpoint is unavailable.

Do not create a production migration solely from this text. Verify the current official model card and endpoint response, then record the result in the embedding model registry.

## 3.3 OpenRouter API references

```text
Quickstart / OpenAI-compatible API:
  https://openrouter.ai/docs/quickstart

Embeddings:
  https://openrouter.ai/docs/api-reference/embeddings

Structured outputs:
  https://openrouter.ai/docs/features/structured-outputs

Limits and rate-limit information:
  https://openrouter.ai/docs/api-reference/limits

Provider routing:
  https://openrouter.ai/docs/features/provider-routing
```

Free-model request limits are not hard-coded as durable truth. The scheduler should query provider/key state where possible and make current limits configurable. At handbook verification, OpenRouter documentation described a 20 requests/minute free-model limit and daily limits dependent on account credit history; implementation must verify the current values.

---

## 4. Core framework registry

## 4.1 Python

Use a currently supported Python version compatible with all selected packages. The repository configuration should pin a minimum/target version after dependency resolution. Do not use unreleased Python features in domain contracts.

## 4.2 Pydantic

Purpose:

- immutable/validated domain DTOs;
- model output schemas;
- settings;
- JSON Schema generation.

Reference:

```text
https://docs.pydantic.dev/latest/
```

Pin a compatible major/minor range and run schema snapshots in CI.

## 4.3 SQLAlchemy 2 and Psycopg 3

Purpose:

- typed ORM/mappings;
- async application persistence;
- explicit transaction/unit-of-work behavior.

References:

```text
https://docs.sqlalchemy.org/en/20/
https://www.psycopg.org/psycopg3/docs/
```

Do not mix legacy SQLAlchemy patterns into the new project.

## 4.4 Alembic

Reference:

```text
https://alembic.sqlalchemy.org/
```

Every persistent schema change must be reviewed as generated and final SQL, tested against clean and upgrade fixtures, and recorded in the evidence bundle.

## 4.5 PostgreSQL and pgvector

References:

```text
https://www.postgresql.org/docs/
https://github.com/pgvector/pgvector
```

Current policy:

- PostgreSQL is canonical;
- exact vector search first;
- mandatory owner/visibility filters cannot be delegated to prompts;
- approximate index adoption requires benchmark/ADR;
- record PostgreSQL/pgvector versions in deployment manifests.

## 4.6 LangGraph

Reference:

```text
https://docs.langchain.com/oss/python/langgraph/
```

Use bounded, reusable graphs and persistence/checkpoints for execution recovery only. Canonical world state stays in the domain database.

Pin LangGraph and associated LangChain packages together through tested lock files. Review release notes before upgrades because checkpoint/state semantics can affect recovery.

## 4.7 FastAPI

Reference:

```text
https://fastapi.tiangolo.com/
```

Use server-side authorization, generated OpenAPI, tested WebSocket replay/resync, and no domain logic in route handlers.

## 4.8 Vue 3

References:

```text
https://vuejs.org/guide/typescript/overview
https://vuejs.org/guide/extras/composition-api-faq
```

Use TypeScript and the Composition API. Generate API types/clients from the frozen OpenAPI rather than duplicating server DTOs by hand.

## 4.9 Temporal

References:

```text
https://docs.temporal.io/develop/python
https://docs.temporal.io/develop/python/integrations/langgraph
```

Policy:

- Stage 0–3 code targets a project-owned `WorldOrchestrator` interface;
- Stage 4 performs an ADR/evaluation;
- the documented LangGraph integration was public preview at handbook verification time;
- canonical state remains PostgreSQL even if Temporal is adopted;
- use ordinary activities around bounded LangGraph work unless current evidence supports tighter integration.

## 4.10 ComfyUI

References:

```text
https://docs.comfy.org/development/comfyui-server/comms_routes
https://docs.comfy.org/development/comfyui-server/api-examples
```

Use exported API-format workflows, version them, submit only for committed events, and isolate image failure from simulation.

## 4.11 MinIO or S3-compatible storage

Reference:

```text
https://min.io/docs/
```

The specific object store can change behind an S3-compatible asset interface. Record server/client versions and backup strategy.

---

## 5. Local model-serving registry

No serving stack is final before Stage 4 benchmark.

Candidate references:

```text
vLLM:
  https://docs.vllm.ai/

llama.cpp:
  https://github.com/ggml-org/llama.cpp

SGLang:
  https://docs.sglang.ai/

PyTorch ROCm:
  https://rocm.docs.amd.com/projects/install-on-linux/

AMD Ryzen/ROCm compatibility:
  https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityryz.html
```

Record for every benchmark:

- host hardware/BIOS;
- OS/kernel;
- ROCm/CUDA/driver;
- container/base image digest;
- PyTorch/framework/server version;
- model repository commit and file hashes;
- quantization;
- memory settings;
- command/configuration;
- success/failure evidence.

Do not generalize one model’s success to all architectures/quantizations.

---

## 6. Version pinning policy

### Development

- maintain a lock file;
- prefer exact container image digests for infrastructure;
- pin model revisions/hashes when reproducibility matters;
- allow controlled dependency update branches;
- never allow CI to install an unbounded “latest” critical runtime dependency.

### Stage completion

The evidence bundle records:

```text
application commit
schema/migration head
Python and package lock hash
PostgreSQL/pgvector
provider/model slugs and capability probe
prompt/schema versions
local model/checkpoint/quantization if applicable
ComfyUI workflow/model versions if applicable
OS/driver/runtime versions
```

### Upgrade

A dependency upgrade requires:

1. changelog/security review;
2. compatibility test branch;
3. contract/schema diff;
4. migration impact;
5. previous-stage regression;
6. fault/leakage checks for affected subsystem;
7. benchmark/quality comparison where model/runtime changes;
8. rollback plan;
9. registry update.

---

## 7. Model and asset license registry

Before a model, checkpoint, embedding model, reranker, LoRA, vision model, image model, or asset pack enters a persistent world/deployment, record:

```text
asset_id
name/repository
revision/hash
license text/URL
commercial-use status
redistribution status
derivative/output conditions
attribution requirements
acceptable-use restrictions
source and download date
approved deployment profiles
reviewer
```

Do not assume “available on Hugging Face/OpenRouter” means unrestricted commercial use.

The initial seed world and characters in `23` are original project content and should remain separate from recognizable copyrighted anime franchises.

---

## 8. Architecture Decision Records

Use ADRs for decisions that are:

- difficult to reverse;
- cross-subsystem;
- security/privacy relevant;
- likely to be questioned later;
- based on external capability/benchmark;
- a deviation from this handbook.

ADR format is instantiated from `37_ADR_AND_CHANGE_REQUEST_TEMPLATES.md`. The minimum shape is:

```markdown
# ADR-XXXX — Title

Status: Proposed | Accepted | Superseded | Rejected
Date:
Owners:
Related requirements/tasks:

## Context
## Decision
## Alternatives considered
## Consequences
## Security/privacy/data implications
## Migration/rollback
## Evidence
## Affected contracts/docs/code
```

Important initial ADR candidates:

- PostgreSQL + pgvector versus separate vector database;
- hybrid event log + projections;
- Python/application UUIDv7 strategy;
- JSONB policy;
- OpenRouter structured-output mode;
- embedding version/dimension;
- exact search versus HNSW;
- local model/server selection;
- database orchestrator versus Temporal;
- object store selection;
- image model/workflow strategy;
- authentication/network profile;
- macro simulation formulas/end thresholds.

---

## 9. Change request procedure

Instantiate change requests from `37_ADR_AND_CHANGE_REQUEST_TEMPLATES.md`. A change request contains:

```text
CR ID/title
requester/date
problem/evidence
proposed behavior
requirements affected
contracts affected
schema/data migration
API/UI impact
prompt/model impact
security/privacy/content impact
backward compatibility
implementation stages/tasks
alternatives
rollback
approval
```

### 9.1 Classify change

- **Patch:** compatible correction, no contract/schema behavior change;
- **Minor:** additive backward-compatible behavior/schema/API;
- **Major:** breaking contract, semantics, migration, perspective, or user role change;
- **Emergency:** critical security/corruption fix.

### 9.2 Impact analysis

Search at least:

- requirement IDs in `02` and `32`;
- ADRs;
- domain contracts/JSON Schemas;
- migration/schema;
- phase/scene state machine;
- effect union;
- context/access policy;
- prompts/fake corpus;
- orchestration/idempotency;
- OpenAPI/generated client/UI;
- tests/evidence;
- seed/export/migration fixtures;
- operations/security policy.

### 9.3 Approval

- patch: subsystem owner + tests;
- minor: parent/integration owner + affected contract owners;
- major: project owner + architecture review + ADR;
- emergency: security/parent may implement immediately, then retrospective ADR/traceability.

### 9.4 Propagation

After acceptance:

1. version contract;
2. update handbook/ADR/reference registry;
3. write migration/backfill if needed;
4. update generated schemas/OpenAPI/client;
5. update fake-model corpus/prompts;
6. update task packets/traceability;
7. run affected current and previous-stage gates;
8. record release/evidence.

---

## 10. Schema and contract compatibility

### Pydantic/model output schemas

- additive optional fields may be minor;
- required fields, enum changes, or semantic changes require a new schema version;
- stored model outputs retain original schema version;
- normalization adapters may upgrade old payloads;
- do not mutate old records in place without migration/provenance.

### Database

- use expand/migrate/contract for disruptive changes;
- prefer additive columns/tables, backfill, dual-read/write only when necessary, then remove later;
- never reinterpret existing JSON payload silently;
- verify projection rebuild;
- retain source event compatibility or an explicit migration event.

### API

- avoid returning watcher-only fields in shared DTOs with frontend hiding;
- perspective/role filtering is server-side;
- additive fields are not automatically safe if they reveal data;
- breaking route/DTO changes require OpenAPI/client version coordination.

### Prompts/models

- prompt change receives a new version;
- model change receives a new profile/version and quality comparison;
- do not mix results from different embedding spaces;
- store sampling/provider endpoint provenance where available.

---

## 11. Runtime capability probes

Implement probes for:

### OpenRouter text

- model discoverability/availability;
- minimal chat completion;
- supported structured-output behavior for the selected endpoint/routing policy;
- context/application limit assumptions;
- rate-limit/key state when exposed;
- response metadata/model/provider identity;
- privacy/profile policy.

### Embedding

- model availability;
- output dimension;
- batch behavior;
- prefix behavior recorded in configuration;
- maximum safe input under application policy.

### Local model server

- health;
- model identity/hash;
- context;
- structured output/tool support;
- concurrency;
- cancellation;
- loaded/ready state.

### ComfyUI

- health;
- required nodes/models/workflow version;
- queue submission;
- output path/access.

A failed optional probe marks a capability unavailable; it should not corrupt or partially advance the world.

---

## 12. Scheduled revalidation

Revalidate:

- before beginning a new implementation stage;
- whenever dependency lock/model profile changes;
- after provider/API documentation changes;
- after driver/ROCm/CUDA/kernel updates;
- before using a free endpoint with a new data profile;
- monthly during active development for externally hosted free models;
- before any public/commercial deployment.

Record verification date and evidence rather than editing a number in prose without provenance.

---

## 13. Handbook maintenance

The stable handbook version changes when:

- product requirement changes;
- architecture decision changes;
- stage scope/gate changes;
- external assumption materially changes;
- a review discovers inconsistency.

Use semantic handbook versions:

- `1.x.y` compatible clarification/addition;
- `2.0.0` major product/architecture break.

Every published handbook bundle includes:

- all separate Markdown files;
- manifest with sizes/hashes;
- checksum file;
- review report;
- ZIP checksum;
- generation/review date.
