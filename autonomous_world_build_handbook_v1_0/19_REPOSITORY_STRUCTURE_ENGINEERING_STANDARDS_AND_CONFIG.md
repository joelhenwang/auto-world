# Repository Structure, Engineering Standards, and Configuration

**Version:** 1.0  
**Status:** Normative engineering specification  
**Primary owners:** repository maintainers and every coding agent  
**Required reading:** `01`, `03`–`06`, `20`, `21`, current stage document

---

## 1. Purpose

This document defines the monorepo layout, backend module boundaries, frontend structure, dependency direction, Python and TypeScript standards, configuration model, generated artefacts, exception and logging conventions, database session rules, dependency policy, and documentation requirements.

A coding agent must follow this structure unless an approved ADR changes it.

---

## 2. Monorepo layout

```text
autonomous-fictional-world/
├── AGENTS.md
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── package.json                       # optional root scripts only
├── compose.yaml
├── compose.override.yaml.example
├── .env.example
├── .gitignore
├── .editorconfig
├── .pre-commit-config.yaml
├── Makefile                           # thin aliases; commands remain documented
├── backend/
│   ├── README.md
│   ├── alembic.ini
│   ├── migrations/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   ├── src/
│   │   └── fictional_world/
│   │       ├── __init__.py
│   │       ├── bootstrap/
│   │       ├── config/
│   │       ├── domain/
│   │       ├── application/
│   │       ├── agents/
│   │       ├── prompts/
│   │       ├── infrastructure/
│   │       ├── interfaces/
│   │       └── observability/
│   └── tests/
│       ├── unit/
│       ├── integration/
│       ├── contract/
│       ├── scenario/
│       ├── property/
│       ├── fault/
│       ├── live/
│       ├── fixtures/
│       └── conftest.py
├── frontend/
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── playwright.config.ts
│   ├── src/
│   └── tests/
├── prompts/
│   ├── README.md
│   └── <role directories>/
├── seed/
│   ├── worlds/
│   ├── schemas/
│   └── assets/
├── workflows/
│   └── comfyui/                       # Stage 4
├── deploy/
│   ├── docker/
│   ├── temporal/                      # Stage 4
│   ├── systemd/                       # optional local services
│   └── monitoring/
├── scripts/
│   ├── bootstrap.py
│   ├── generate_openapi.py
│   ├── generate_json_schemas.py
│   ├── verify_docs.py
│   ├── verify_migrations.py
│   ├── seed_world.py
│   ├── run_scenario.py
│   └── export_world.py
├── docs/
│   ├── handbook/                      # copy of this handbook
│   ├── adr/
│   ├── status/
│   ├── generated/
│   ├── runbooks/
│   └── diagrams/
├── tools/
│   ├── model_fake_server/
│   ├── scenario_harness/
│   └── test_data/
└── .github/
    ├── workflows/
    ├── pull_request_template.md
    └── ISSUE_TEMPLATE/
```

The root `prompts/` directory is the canonical prompt source. Backend code loads it through package/resource configuration; do not maintain duplicate prompt copies.

---

## 3. Backend package structure

```text
fictional_world/
├── bootstrap/
│   ├── app.py
│   ├── container.py
│   ├── lifespan.py
│   └── worker.py
├── config/
│   ├── settings.py
│   ├── profiles.py
│   └── validation.py
├── domain/
│   ├── common/
│   │   ├── ids.py
│   │   ├── enums.py
│   │   ├── errors.py
│   │   ├── events.py
│   │   └── result.py
│   ├── world/
│   ├── time/
│   ├── entities/
│   ├── characters/
│   ├── psychology/
│   ├── relationships/
│   ├── actions/
│   ├── scenes/
│   ├── rules/
│   ├── magic/
│   ├── health/
│   ├── knowledge/
│   ├── memory/
│   ├── lore/
│   ├── map/
│   ├── factions/
│   ├── visuals/
│   └── endings/
├── application/
│   ├── commands/
│   ├── queries/
│   ├── dto/
│   ├── ports/
│   ├── services/
│   ├── orchestration/
│   ├── context/
│   ├── perception/
│   ├── memory/
│   ├── models/
│   ├── images/
│   └── transactions/
├── agents/
│   ├── common/
│   ├── character_decision/
│   ├── character_reaction/
│   ├── director/
│   ├── npc/
│   ├── validator/
│   ├── resolver/
│   ├── narrator/
│   ├── observation/
│   ├── consolidation/
│   └── reflection/
├── prompts/
│   ├── registry.py
│   ├── renderer.py
│   ├── schema_normalizer.py
│   └── metadata.py
├── infrastructure/
│   ├── database/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── mappings/
│   │   ├── session.py
│   │   ├── unit_of_work.py
│   │   ├── outbox.py
│   │   └── task_queue.py
│   ├── model_gateway/
│   │   ├── openrouter.py
│   │   ├── local_openai.py
│   │   ├── fake.py
│   │   ├── errors.py
│   │   └── capabilities.py
│   ├── langgraph/
│   ├── temporal/                      # Stage 4
│   ├── comfyui/                       # Stage 4
│   ├── object_store/                  # Stage 4
│   ├── auth/
│   └── serialization/
├── interfaces/
│   ├── http/
│   │   ├── app.py
│   │   ├── dependencies.py
│   │   ├── errors.py
│   │   ├── middleware.py
│   │   └── routes/
│   ├── websocket/
│   ├── cli/
│   └── workers/
└── observability/
    ├── logging.py
    ├── tracing.py
    ├── metrics.py
    └── audit.py
```

A stage may omit empty packages. Do not create dozens of placeholder modules in the first commit; add modules when the stage task introduces them while preserving intended boundaries.

---

## 4. Dependency direction

```text
interfaces ─────┐
bootstrap ──────┼──→ application ───→ domain
agents ─────────┘          │
                           ↓ ports
infrastructure ─────────── implements ports
```

Rules:

- `domain` imports only Python standard library and narrowly approved validation utilities where necessary;
- `application` imports domain and application ports, not concrete infrastructure;
- `agents` imports application/domain contracts and model ports, not ORM models;
- `infrastructure` may import application ports and domain value objects;
- `interfaces` invoke application commands/queries;
- domain never imports FastAPI, SQLAlchemy ORM, LangGraph, HTTP clients, OpenRouter SDK, ComfyUI, or Temporal;
- agents never import write repositories;
- frontend never imports backend source; it uses generated API contracts.

Enforce key rules with import-linter or custom architecture tests.

---

## 5. Domain model style

Prefer immutable value objects and explicit state-transition methods/functions.

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Stamina:
    value: int

    def __post_init__(self) -> None:
        if not 0 <= self.value <= 100:
            raise ValueError("stamina must be between 0 and 100")

    def spend(self, amount: int) -> "Stamina":
        if amount < 0:
            raise ValueError("amount cannot be negative")
        if amount > self.value:
            raise InsufficientStamina(required=amount, available=self.value)
        return Stamina(self.value - amount)
```

Use Pydantic primarily at boundaries and for persisted/model-facing contracts. Do not turn every internal arithmetic value into a mutable Pydantic model.

---

## 6. Pydantic conventions

- Pydantic v2;
- `ConfigDict(extra="forbid", strict=True)` for model output and command DTOs;
- discriminated unions for actions/effects/commands;
- constrained lengths/ranges;
- UTC-aware datetimes;
- no `Any` in canonical public contracts unless explicitly justified;
- JSON Schema IDs/version metadata;
- validators may check local shape, not perform database I/O;
- database/domain validation happens in services after parsing.

Example base:

```python
from pydantic import BaseModel, ConfigDict


class StrictContract(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        validate_default=True,
    )
```

Do not use `dict[str, Any]` as a shortcut for typed effect payloads.

---

## 7. Python version and dependency management

- Python 3.12 baseline;
- `uv` owns environments, dependency resolution, lockfile, and script execution;
- one root `pyproject.toml` may configure backend package and development tools;
- dependency groups: `dev`, `test`, `live`, `stage4`, `docs` where useful;
- lockfile committed;
- no unpinned direct dependency in CI/release;
- minimize optional dependencies in domain layer.

Example commands:

```bash
uv sync --all-groups
uv run pytest
uv run ruff check .
uv run basedpyright
```

Do not install project packages globally with `pip`.

---

## 8. Static quality

### 8.1 Ruff

Use Ruff for:

- linting;
- import sorting;
- formatting.

Recommended categories include `E`, `F`, `I`, `B`, `UP`, `SIM`, `ASYNC`, `RUF`, `C4`, `DTZ`, `T20`, `S` with deliberate per-file exceptions for tests and migrations.

Avoid disabling entire rule families without an ADR.

### 8.2 basedpyright

Use strict or near-strict configuration:

```json
{
  "typeCheckingMode": "strict",
  "pythonVersion": "3.12",
  "reportUnknownMemberType": true,
  "reportUnknownArgumentType": true,
  "reportMissingTypeStubs": "warning"
}
```

Type-only compromises must be local, commented, and tracked.

### 8.3 Complexity

Prefer functions under approximately 50 lines and modules with one coherent responsibility. These are review heuristics, not mechanical gates. State-machine code may be longer when explicitness improves correctness.

---

## 9. Async rules

- async at I/O boundaries;
- domain calculations remain synchronous;
- use `asyncio.TaskGroup` for bounded structured concurrency where appropriate;
- never call blocking SDK/file/database operations on the event loop;
- do not create background tasks without lifecycle ownership;
- never use `asyncio.sleep` as durable retry scheduling;
- cancellation must propagate and release resources;
- external calls occur outside database transactions.

---

## 10. SQLAlchemy conventions

- SQLAlchemy 2 typed declarative mapping;
- Psycopg 3 async driver;
- explicit `Mapped[...]` annotations;
- snake_case table/column names;
- naming convention for constraints/indexes;
- avoid implicit lazy loading in async code;
- repositories issue explicit selects and loading plans;
- ORM models are persistence details, not Pydantic DTOs;
- one `AsyncSession` per application unit of work;
- no session stored on domain entity;
- no cross-request session reuse;
- `expire_on_commit=False` only with explicit awareness of stale state.

### 10.1 Transaction rule

Route/worker starts an application command. The unit of work owns the transaction. Repositories do not call `commit()` independently.

### 10.2 Query rule

Queries may use dedicated read repositories/projections. Do not load an entire world object graph.

### 10.3 JSONB rule

JSONB is appropriate for:

- immutable model provenance;
- flexible but validated narrative metadata;
- before/after effect audit payloads;
- configuration snapshots.

JSONB is not appropriate as the only representation of characters, relationships, inventory, memories, or tasks.

---

## 11. Alembic conventions

- every schema change is a reviewed migration;
- migration filenames include revision and short purpose;
- use stable naming convention for constraints;
- autogenerate is a draft, not final truth;
- inspect upgrade and downgrade;
- data migrations are explicit and bounded;
- production-like backup before destructive migration;
- migration test upgrades an empty database and a fixture database;
- current schema is generated into `docs/generated/database-schema.sql`;
- no application auto-creates missing tables in runtime.

Do not edit an already shared/applied migration; add a new one.

---

## 12. Repository and unit-of-work patterns

Application ports expose domain-focused operations:

```python
class CharacterRepository(Protocol):
    async def get_state_for_update(
        self, character_id: CharacterId
    ) -> CharacterState: ...

    async def save_state(
        self,
        state: CharacterState,
        *,
        expected_version: int,
    ) -> None: ...
```

Avoid generic repositories like `Repository[T].save(anything)` when they obscure aggregate rules.

Unit of work:

```python
class UnitOfWork(Protocol):
    characters: CharacterRepository
    events: EventRepository
    outbox: OutboxRepository

    async def __aenter__(self) -> "UnitOfWork": ...
    async def __aexit__(self, exc_type, exc, tb) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
```

Commit service logic is tested against real PostgreSQL integration fixtures.

---

## 13. IDs, enums, and time

### 13.1 IDs

Use distinct NewType/value classes where practical:

```text
WorldId
CharacterId
SceneId
EventId
PhaseId
TaskId
```

At persistence/API boundaries, encode UUIDv7-compatible UUID values. Application generates IDs before inserts to support idempotency and references.

### 13.2 Enums

Use Python `StrEnum` in contracts and database `VARCHAR/TEXT` plus `CHECK` constraints where evolution is expected. Do not use PostgreSQL native enums by default.

Unknown external enum variants should fail strict backend parsing. Frontend generated clients should include safe display fallback for additive event types.

### 13.3 Operational time

Always timezone-aware UTC. Reject naive datetimes.

### 13.4 Fictional time

Use structured fields:

```text
generation
calendar_year
month
month_day
phase_name
phase_index
absolute_phase_number
```

Do not map fictional time to system UTC.

---

## 14. Exceptions and results

Domain exceptions are expected rule failures, for example:

```text
InvalidAction
InsufficientMana
UnknownTarget
ConcurrencyConflict
InvalidStateTransition
SecretAccessDenied
```

Infrastructure exceptions are normalized at ports.

Do not use exceptions for every negative model verdict; typed validation results are appropriate where multiple issues are expected.

Every exception crossing a boundary is mapped to:

- task failure class;
- API error code;
- sanitized log fields;
- retry policy.

Never catch broad exceptions without logging and re-raising or mapping intentionally.

---

## 15. Configuration

Use `pydantic-settings` with layered sources:

```text
code defaults
  < profile YAML/TOML
  < .env / environment variables
  < command-line overrides for local tools
```

Secrets come only from environment/secret store, not committed profile files.

### 15.1 Settings groups

```text
AppSettings
├── environment
├── api
├── database
├── auth
├── orchestration
├── model_gateway
├── openrouter
├── memory
├── simulation
├── rules
├── observability
├── image
├── object_storage
└── temporal
```

### 15.2 Profiles

```text
config/profiles/
├── test.toml
├── stage0.toml
├── stage1.toml
├── stage2.toml
├── stage3.toml
├── stage4-local.toml
└── stage5.toml
```

Profiles state feature flags and limits, never secrets.

### 15.3 Validation

Startup fails for:

- missing mandatory secret in enabled provider mode;
- incompatible feature flags;
- invalid context/output sizes;
- embedding dimension mismatch with database schema;
- enabled Stage 4 image pipeline without workflow profile;
- database migration behind expected version in write mode;
- unsafe public bind without auth unless explicit development override.

---

## 16. Feature flags

Feature flags enable staged implementation, for example:

```yaml
features:
  director: false
  long_term_memory: false
  magic: false
  combat: false
  images: false
  temporal: false
  macro_simulation: false
```

Rules:

- flags are explicit configuration;
- disabled code paths have deterministic behaviour;
- flags cannot remove mandatory validation/security;
- tests cover both relevant states;
- once a feature is foundational, remove obsolete flag rather than accumulating permanent branches.

---

## 17. Logging conventions

Use structured logs through the central observability module. Application code logs fields, not formatted JSON strings.

Required correlation fields where available:

```text
request_id
command_id
world_id
phase_id
scene_id
character_id
task_id
workflow_id
model_call_id
worker_id
```

No API keys, raw auth headers, database URLs, or private prompts in ordinary logs.

Use parameterized logging, not f-strings for expensive/sensitive values.

---

## 18. Frontend standards

- TypeScript strict;
- Composition API and `<script setup>`;
- generated API types are source of server contract truth;
- no `any` except isolated third-party adapters;
- domain IDs use branded types where generated/client layer permits;
- components receive typed props/emits;
- server state separated from client UI state;
- route-level feature boundaries;
- no direct HTML injection from model content;
- ESLint/formatter configuration pinned;
- `pnpm` as package manager;
- no npm/yarn lockfile alongside `pnpm-lock.yaml`.

---

## 19. Generated artefacts

Generate and commit when useful:

```text
docs/generated/openapi.json
docs/generated/domain-schemas/*.json
docs/generated/database-schema.sql
docs/generated/model-capabilities.example.json
frontend/src/api/generated/*
```

CI verifies freshness. Generated files contain a header or manifest indicating source command and version.

Do not hand-edit generated files.

---

## 20. Documentation standards

Every implemented subsystem has:

- code-level README when operational setup is non-obvious;
- ADR for changed architecture;
- current-stage status update;
- public API/schema generated docs;
- runbook for recurring operational failure;
- tests serving as executable examples.

Code comments explain why, invariants, and non-obvious constraints—not restate syntax.

Every coding session updates `docs/status/SESSION_LOG.md` and the handoff template when work remains incomplete.

---

## 21. Git and branch standards

- one focused branch per task packet;
- descriptive names such as `stage1/character-decision-graph`;
- commits separated by coherent purpose;
- no generated/binary secrets;
- migrations and corresponding model/tests in the same change;
- prompt versions and evaluation updates in the same change;
- rebase/merge according to parent-agent integration plan;
- subagents do not rewrite unrelated files;
- draft PR until stage task tests pass.

Commit messages use imperative subject and optional task ID:

```text
S1-ACT-003 add character action fallback validation
```

---

## 22. Dependency policy

Before adding a dependency, record:

- purpose;
- why standard library/current dependency is insufficient;
- maintenance and release health;
- license;
- security implications;
- transitive weight;
- whether it enters runtime or dev only;
- removal/migration plan if experimental.

Avoid agent-framework overlap. LangGraph is the bounded graph framework; do not add another orchestration/agent framework without ADR.

Temporal plugin integrations in preview remain optional and isolated.

---

## 23. Required architecture tests

- domain does not import infrastructure/framework modules;
- agent graphs do not import write repositories or ORM models;
- route modules do not directly use SQLAlchemy sessions;
- model gateway SDK types do not escape infrastructure adapter;
- prompt renderer has no database imports;
- canonical effect union has no untyped catch-all payload;
- migrations have unique revision graph and single head unless deliberate;
- generated OpenAPI/schema files are current;
- configuration profiles validate.

---

## 24. Definition of done

Repository engineering foundations are complete when:

- module boundaries and imports are enforceable;
- environment builds from lockfiles;
- strict static analysis passes;
- database transactions have one owner;
- config validation prevents unsafe/incompatible startup;
- generated API/schema artefacts are reproducible;
- coding agents can locate responsibility from the tree;
- a new provider, graph, or UI feature can be added without leaking framework types into the domain;
- documentation and session status stay synchronized with code.
