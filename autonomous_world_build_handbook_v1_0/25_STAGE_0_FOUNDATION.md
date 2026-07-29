# Stage 0 — Foundation and Deterministic Contracts

**Version:** 1.0  
**Stage outcome:** A seeded world can execute and persist deterministic phase primitives, tasks, events, observations, and recent memories with no external model dependency and full restart/idempotency safety.  
**Primary proof:** `stage0-foundation-v1` deterministic scenario and fault suite.

---

## 1. Scope

Stage 0 establishes the repository, core contracts, PostgreSQL/pgvector schema, event/effect transaction, task/outbox machinery, minimal deterministic World Engine, seed import, provider-neutral model gateway with fake and OpenRouter smoke support, health API, observability, and testing infrastructure.

Stage 0 does not implement autonomous character decisions, complex scenes, long-term RAG, Director events, combat, images, or production frontend.

---

## 2. Required capabilities

- reproducible development environment;
- strict domain contracts and enums;
- PostgreSQL + pgvector migrations;
- one seeded world and initial character/location records;
- fictional clock and phase lifecycle primitives;
- typed effects for `WAIT`, `OBSERVE`, `REST`, simple `MOVE`, resource update, and recent-memory creation;
- immutable event/effect log plus projections;
- perspective observation record;
- durable task, lease, retry, idempotency, and outbox records;
- deterministic orchestration interface and reconciler;
- model gateway protocols, fake adapter, OpenRouter capability smoke;
- structured logs/request IDs;
- minimal health/read API or CLI;
- unit/property/integration/migration/fault tests.

---

## 3. Explicit exclusions

- live model calls as a gate;
- LangGraph character graph;
- two-character simultaneous scene;
- Director and NPC actors;
- claims/beliefs/relationships beyond seed storage needed later;
- embeddings used for retrieval;
- full Vue UI;
- magic/combat/injury runtime;
- Temporal;
- ComfyUI/object storage;
- generations.

---

## 4. Task dependency graph

```text
S0-ENG-001 repository/bootstrap
   ├── S0-ENG-002 configuration/static quality
   ├── S0-DOM-001 domain primitives/contracts
   └── S0-QA-001 test harness/fakes

S0-DOM-001
   ├── S0-DB-001 PostgreSQL/Alembic baseline
   ├── S0-SIM-001 clock/effect validation
   └── S0-MODEL-001 gateway protocols

S0-DB-001
   ├── S0-DB-002 core migrations/models
   ├── S0-DB-003 UoW/repositories
   └── S0-CONTENT-001 seed importer

S0-DB-003 + S0-SIM-001
   └── S0-SIM-002 event/effect commit service

S0-DB-002
   └── S0-ORCH-001 task/outbox/leases

S0-MODEL-001 + S0-QA-001
   └── S0-MODEL-002 fake + OpenRouter adapter/probe

S0-SIM-002 + S0-ORCH-001 + S0-CONTENT-001
   └── S0-ORCH-002 deterministic phase runner/reconciler

all
   ├── S0-API-001 health/read endpoints
   ├── S0-OPS-001 logging/security baseline
   └── S0-QA-002 stage scenario/gate
```

---

## 5. Parallel lanes

After `S0-ENG-001` and `S0-DOM-001` contracts are merged:

- Lane A: database/migrations/UoW;
- Lane B: model protocols/fake/OpenRouter adapter;
- Lane C: seed source/import validation;
- Lane D: pure deterministic rule/effect logic;
- Lane E: test tooling/architecture checks.

Integration order is DB → event commit/task → seed → phase runner → API/gate.

Do not let two agents generate overlapping core migrations.

---

## 6. Task packets

### S0-ENG-001 — Repository bootstrap

**Owns:** root files, `pyproject.toml`, baseline backend package, test folders, docs/status.  
**Deliver:** Python 3.12/uv project, package import, root commands, `.env.example`, Docker Compose PostgreSQL service skeleton.  
**Tests:** clean `uv sync`, package import, `docker compose config`.  
**Do not:** add framework-heavy domain code.

### S0-ENG-002 — Configuration and static quality

**Depends on:** S0-ENG-001.  
**Deliver:** pydantic-settings groups, stage0 profile, Ruff, basedpyright strict, pre-commit, generated-artefact commands.  
**Tests:** valid profile; invalid embedding dimensions/public bind configurations fail; lint/type pass.

### S0-DOM-001 — Domain primitives and contracts

**Deliver:** IDs, StrEnums, strict base contracts, fictional time, phase/scene/task/event/effect/observation/recent-memory contracts required by Stage 0; state-transition errors.  
**Source:** `05`, `06`, `07`.  
**Tests:** JSON Schema generation, enum/length/range validation, forbidden extra fields.  
**Do not:** create ORM classes in domain.

### S0-QA-001 — Test harness and fakes

**Deliver:** fake operational clock, seeded random source, fake model gateway, PostgreSQL testcontainer fixture, scenario harness skeleton, network-block fixture.  
**Tests:** fixtures self-test and clean teardown.

### S0-DB-001 — Database/Alembic baseline

**Depends on:** S0-DOM-001.  
**Deliver:** async engine/session, naming convention, Alembic environment, vector extension migration, migration verification script.  
**Tests:** empty upgrade, extension available, single head.

### S0-DB-002 — Core schema

**Depends on:** S0-DB-001.  
**Tables:** world, world_config, world_clock, entity, location, character, character_card_version, character_state, phase_run, phase_snapshot, phase_snapshot_character, world_event, event_effect, observation, recent_memory, model_profile, model_call, task_run, task_dependency, request_budget_ledger, outbox_message, aggregate_version, user_command/idempotency record.  
**Deliver:** models, migration, constraints/indexes, generated schema.  
**Tests:** database rejects duplicate phase/event/effect/idempotency and invalid ranges.

### S0-DB-003 — Unit of work and repositories

**Depends on:** S0-DB-002.  
**Deliver:** explicit repository ports and SQLAlchemy implementations for core aggregates; transaction owner; optimistic version operations.  
**Tests:** real database CRUD/query/rollback/concurrency.

### S0-SIM-001 — Deterministic clock and effect validation

**Depends on:** S0-DOM-001.  
**Deliver:** ten-phase calendar value objects, transition rules, minimal effect validators/projectors for wait/observe/rest/move/resource/memory; invariant registry.  
**Tests:** property/state-machine tests.

### S0-SIM-002 — Atomic event commit service

**Depends on:** S0-DB-003, S0-SIM-001.  
**Deliver:** scene/operation commit transaction that checks idempotency, expected versions, inserts event/effects/projections/observations/recent-memory/outbox, and returns existing result on retry.  
**Tests:** rollback, duplicate, process-uncertain lookup, optimistic conflict.

### S0-ORCH-001 — Task/outbox queue primitives

**Depends on:** S0-DB-002.  
**Deliver:** task creation/dependency/claim/lease/heartbeat/retry/dead-letter; outbox claim/dispatch interface; budget reservation data operations.  
**Tests:** two-worker claim, expiry, terminal protection, at-least-once consumer idempotency.

### S0-MODEL-001 — Gateway protocols and profiles

**Depends on:** S0-DOM-001, S0-ENG-002.  
**Deliver:** provider-neutral interfaces/results/errors/model profile registry and sampling config.  
**Tests:** profile selection, configuration validation, no provider SDK escape.

### S0-MODEL-002 — Fake/OpenRouter adapters and capability probe

**Depends on:** S0-MODEL-001, S0-QA-001.  
**Deliver:** fake scripted adapter, OpenRouter text/embed adapter skeleton, error mapping, JSON schema modes, key/quota probe, opt-in live smoke.  
**Tests:** fake HTTP contract, malformed/schema/429/embedding dimension; live tests marked and capped.

### S0-CONTENT-001 — Seed source and importer

**Depends on:** S0-DB-002, S0-DOM-001.  
**Deliver:** `caldris-embervale-v1` Stage 0 subset, deterministic seed IDs, validation report, atomic import, `WORLD_SEEDED` event.  
**Tests:** import empty, repeat import, broken reference rollback, secret separation fixture.

### S0-ORCH-002 — Deterministic phase runner and reconciliation

**Depends on:** S0-SIM-002, S0-ORCH-001, S0-CONTENT-001.  
**Deliver:** `WorldOrchestrator` initial adapter; create phase, advance clock/world tick, seal snapshot, execute scripted deterministic actions/effects, finalize phase; resume from durable state.  
**Tests:** restart at each boundary, no duplicate phase/event, pause/resume.

### S0-API-001 — Minimal API/CLI

**Depends on:** core services.  
**Deliver:** FastAPI app/lifespan; `/health/live`, `/health/ready`, world/clock/phase/event read endpoints; command to advance deterministic phase; OpenAPI generation. A CLI may invoke seed/scenario/reconcile.  
**Tests:** route validation/idempotency/read projections.

### S0-OPS-001 — Observability and security baseline

**Deliver:** structured logging, correlation IDs, redaction, audit skeleton, loopback bind default, config safety checks, dependency health.  
**Tests:** no API key in logs; unsafe public bind rejected without override/auth.

### S0-QA-002 — Stage gate and review

**Depends on:** all.  
**Deliver:** deterministic foundation scenario, fault injection, migration/architecture/security report, stage evidence bundle, documentation/status update.  
**Gate:** Section 8.

---

## 7. Required implementation sequence

1. repository/config/test harness;
2. domain contracts;
3. database baseline/core migration;
4. repositories/UoW;
5. deterministic effects and event transaction;
6. task/outbox machinery;
7. seed import;
8. model adapters/probe;
9. deterministic phase runner;
10. minimal API/CLI;
11. fault/consistency review.

Do not begin Stage 1 character prompting before the atomic commit and restart gate pass.

---

## 8. Hard exit gate

All must pass:

- clean clone/bootstrap succeeds;
- empty and prior-fixture migrations succeed;
- seed imports atomically and idempotently;
- one deterministic phase advances and commits source-linked event/effects/observations/recent memory;
- same command/task repeated produces no duplicate effect/event;
- process termination after commit before acknowledgement recovers correctly;
- two workers cannot own same task lease;
- phase snapshot seals and cannot be modified;
- strict contracts generate schemas;
- fake provider paths and opt-in OpenRouter smoke work;
- default tests make no external requests;
- consistency audit reports zero hard violations;
- lint/type/architecture tests pass;
- no secret appears in logs/generated docs.

---

## 9. Demonstration

A CLI/API command seeds Caldris, advances one or more scripted phases, displays the fictional clock, event timeline, character-specific observations, recent memories, and task trace, then stops/restarts and resumes without duplication.

The demonstration is intentionally boring. Durability is the product at this stage.

---

## 10. Handoff to Stage 1

Freeze:

- core contract/schema version;
- initial migration head;
- seed version;
- task/idempotency semantics;
- model gateway interface;
- event commit interface;
- stage gate artefacts.

Stage 1 may extend contracts through new versions/migrations but must not bypass these foundations.
