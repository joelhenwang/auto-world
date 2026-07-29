# Local Development, Docker, CI, Release, and Deployment

**Version:** 1.0  
**Status:** Normative development and delivery specification  
**Primary owners:** repository maintainers, infrastructure agents  
**Required reading:** `01`, `12`, `14`, `19`, `21`, `22`, active stage document

---

## 1. Purpose

This document defines how a fresh coding agent or developer boots the project, runs PostgreSQL/pgvector, applies migrations, seeds the world, runs tests and services, uses OpenRouter safely, executes CI, and later deploys the control plane and model/image workers across local machines.

All commands are designed to be reproducible. Do not rely on undocumented workstation state.

---

## 2. Host prerequisites

Stage 0–3:

- Linux development host;
- Git;
- Docker Engine with Compose plugin or compatible container runtime;
- Python 3.12 support through `uv`;
- `uv` installed;
- Node.js LTS and `pnpm` for frontend stages;
- OpenRouter API key only for opt-in live model tests and runtime;
- at least 8 GB free RAM recommended for application/database development;
- adequate disk for PostgreSQL volumes and logs.

Stage 4 additionally requires:

- two Strix Halo hosts with pinned compatible OS/ROCm/model-serving stack;
- RTX 4060 Ti host with pinned NVIDIA driver/CUDA/image stack;
- stable private network;
- ComfyUI and approved workflow/model assets;
- object storage;
- optionally Temporal development/server deployment.

Exact validated host versions belong in `33_REFERENCE_REGISTRY_AND_CHANGE_CONTROL.md` and generated environment manifests.

---

## 3. First clone bootstrap

```bash
git clone <repository-url>
cd autonomous-fictional-world

cp .env.example .env
uv sync --all-groups
pnpm --dir frontend install --frozen-lockfile   # once frontend exists

docker compose up -d postgres
uv run alembic -c backend/alembic.ini upgrade head
uv run python scripts/seed_world.py --seed seed/worlds/emberreach-v1
uv run pytest -m "not live and not soak"
```

The root README must keep a shorter verified version of these commands.

Never commit `.env`.

---

## 4. Environment file

`.env.example` contains names, safe defaults, and comments but no secrets.

Illustrative variables:

```dotenv
APP_ENV=development
APP_PROFILE=stage1
APP_BIND_HOST=127.0.0.1
APP_BIND_PORT=8000

DATABASE_HOST=127.0.0.1
DATABASE_PORT=5432
DATABASE_NAME=fictional_world
DATABASE_USER=fictional_world
DATABASE_PASSWORD=change-me-local

OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_TEXT_MODEL=nvidia/nemotron-3-super-120b-a12b:free
OPENROUTER_EMBEDDING_MODEL=nvidia/nemotron-3-embed-1b:free
OPENROUTER_LIVE_TEST_MAX_REQUESTS=3

AUTH_ENABLED=false
AUTH_LOCAL_ADMIN_PASSWORD=

LOG_LEVEL=INFO
OTEL_ENABLED=false

COMFYUI_BASE_URL=http://127.0.0.1:8188
OBJECT_STORE_ENDPOINT=http://127.0.0.1:9000
OBJECT_STORE_ACCESS_KEY=
OBJECT_STORE_SECRET_KEY=

TEMPORAL_ENABLED=false
TEMPORAL_ADDRESS=127.0.0.1:7233
```

Settings use documented prefixes and fail startup for missing enabled secrets.

---

## 5. Docker Compose services

### 5.1 Stage 0–3 base profile

```text
postgres
  PostgreSQL with pgvector extension

optional pgadmin/adminer
  disabled by default; never public

backend
  optional containerized API/worker development

frontend
  optional containerized frontend development
```

Use bind-mounted source only in development profiles. Production-like containers use built images.

### 5.2 Stage 4 services

```text
minio or another local S3-compatible object store
temporal + UI + supported persistence, if enabled
otel collector
prometheus/grafana or chosen local monitoring stack
```

Model servers and ComfyUI may run natively or in separately validated containers on their GPU hosts. Do not force one Compose file to manage incompatible GPU stacks across three machines.

### 5.3 Health checks

Compose service dependencies use health checks, not only startup order.

PostgreSQL health:

```text
pg_isready plus application migration readiness checked separately
```

Object storage and Temporal use their official health endpoints/tools where available.

---

## 6. PostgreSQL initialization

Use a pgvector-enabled image pinned by digest or a custom Dockerfile based on supported PostgreSQL.

Initialization responsibilities:

- database/user creation through environment/bootstrap;
- `CREATE EXTENSION IF NOT EXISTS vector` in a reviewed migration or bootstrap migration;
- separate schemas if desired: `world`, `langgraph`, `temporal` owned appropriately;
- UTC server time;
- durable named volume;
- local password not reused outside development.

The application never assumes initialization SQL reruns after a volume already exists. Use migrations for schema evolution.

---

## 7. Developer commands

Recommended root aliases:

```bash
make bootstrap       # install deps, start db, migrate, seed
make dev             # backend + frontend dev processes
make api
make worker
make frontend
make test
make test-unit
make test-integration
make lint
make typecheck
make check
make migrate
make seed
make reset-db        # destructive, explicit confirmation/local only
make export-schemas
make openrouter-smoke
make scenario NAME=first-day
```

Makefile targets are thin aliases. CI calls underlying commands directly when clarity matters.

### 7.1 Backend development

```bash
uv run fastapi dev backend/src/fictional_world/interfaces/http/app.py
```

or the project’s explicit entrypoint. Start the durable worker/reconciler separately if architecture requires it:

```bash
uv run fictional-world-worker
```

### 7.2 Frontend development

```bash
pnpm --dir frontend dev
```

Configure Vite proxy to local API/WebSocket without disabling origin/security checks in production.

---

## 8. Database migration workflow

1. update SQLAlchemy models/domain persistence plan;
2. generate draft migration;
3. inspect every operation;
4. name constraints/indexes explicitly;
5. add manual data transformations if needed;
6. test upgrade from empty database;
7. test upgrade from latest fixture snapshot;
8. test downgrade where supported;
9. regenerate schema SQL;
10. run integration and migration verification;
11. commit model, migration, tests, and generated schema together.

Example:

```bash
uv run alembic -c backend/alembic.ini revision --autogenerate -m "add phase snapshot"
uv run alembic -c backend/alembic.ini upgrade head
uv run python scripts/verify_migrations.py
```

Never automatically run destructive downgrade on user data.

---

## 9. Seed workflow

```bash
uv run python scripts/seed_world.py \
  --seed seed/worlds/emberreach-v1 \
  --world-id auto \
  --strict
```

Requirements:

- schema validation before database write;
- idempotent seed version key;
- transaction for all canonical initial records;
- deterministic IDs derived from seed namespace or stored manifest;
- no model/provider call required for baseline seed;
- output seed report with IDs and hashes;
- reject reseeding a nonempty world unless explicit reset/import mode.

---

## 10. OpenRouter local development

### 10.1 Default tests are offline

Use a fake model server/adapter with recorded synthetic fixtures. Ordinary CI never consumes external quota.

### 10.2 Live smoke

Run manually:

```bash
OPENROUTER_LIVE_TESTS=1 \
uv run pytest -m openrouter_live -q
```

The suite enforces a maximum request count and synthetic content only.

### 10.3 Runtime guard

Before running an autonomous simulation against free endpoints:

- verify API key metadata;
- run capability probe;
- display estimated mandatory requests;
- verify daily/RPM ledger;
- choose manual or automatic pause policy;
- do not run high-volume soak tests on free endpoints by default.

Soak tests use fake deterministic models unless deliberately budgeted.

---

## 11. Test database strategy

### 11.1 Unit tests

No database.

### 11.2 Integration tests

Use testcontainers or a dedicated ephemeral PostgreSQL/pgvector container. Apply real migrations.

### 11.3 Parallel tests

Each worker receives a separate database/schema. Do not run write-heavy tests against one shared schema unless transactions/isolation are proven.

### 11.4 Fixture snapshots

Maintain small versioned SQL/seed fixtures for migration tests, not giant production dumps.

---

## 12. CI pipeline

Suggested jobs:

```text
metadata
  validate lockfiles, docs links, generated manifests

backend-lint
  ruff format --check, ruff check

backend-type
  basedpyright

backend-unit
  pytest unit/property fast suite

backend-integration
  PostgreSQL + pgvector; migrations; repository/API tests

architecture
  import rules, schema consistency, prompt metadata checks

frontend-lint-type
  eslint/formatter/vue-tsc

frontend-unit
  vitest

frontend-e2e-smoke
  Playwright with fake backend/model

security
  dependency/license/secret scans

build
  backend and frontend container images

scenario
  deterministic Stage-current acceptance scenario
```

Live provider tests and long soak tests are scheduled/manual, not on every pull request.

### 12.1 CI ordering

Fast static/unit checks first. Build/integration/scenario after. Use dependency caching keyed by lockfile. Do not cache virtual environments across incompatible runner images blindly.

### 12.2 Required branch gate

At minimum:

- formatting/lint;
- type check;
- unit/property tests;
- migration verification;
- integration tests for touched persistence/API;
- prompt/schema checks for touched agent code;
- current-stage scenario;
- generated artefacts current.

---

## 13. Container images

### 13.1 Backend

Multi-stage build:

- pinned Python base;
- install from `uv.lock`;
- non-root runtime user;
- no compiler/dev dependencies at runtime;
- read-only root filesystem where practical;
- explicit writable temp/log paths;
- health endpoint;
- image labels with Git SHA/version.

### 13.2 Frontend

Build static assets with pinned Node/pnpm, then serve through a minimal web server or backend integration. Apply security headers and correct WebSocket proxy settings.

### 13.3 No secrets in images

Secrets are runtime environment/secret mounts only. Build args and layers must not contain API keys.

---

## 14. Release process

1. all stage gates pass;
2. clean migration head;
3. version registry updated;
4. changelog/release notes;
5. prompt/model/schema versions recorded;
6. container images built and scanned;
7. database backup/export tested;
8. deploy to a cloned/staging world;
9. smoke and restart tests;
10. promote local production profile;
11. retain rollback application image and database recovery plan.

The project does not promise old worlds remain runnable across every incompatible development version, per product decision. Still, migrations and exports must be explicit and data loss must never be silent.

---

## 15. Single-host deployment, Stages 1–3

Recommended:

```text
Host
├── PostgreSQL/pgvector
├── FastAPI API
├── task/orchestration worker
├── Vue static app/dev server
└── external OpenRouter calls
```

Run API and worker as separate processes even if same codebase when background work becomes significant.

For private LAN access:

- enable auth;
- bind to LAN explicitly;
- firewall database from LAN clients;
- expose only API/frontend;
- use TLS via reverse proxy if traffic crosses untrusted networks;
- do not expose debug/OpenAPI operations endpoints without protection.

---

## 16. Stage 4 multi-host topology

```text
Control-plane host
├── PostgreSQL + pgvector
├── FastAPI/frontend
├── orchestrator/Temporal worker
├── object storage
└── monitoring

Halo A
└── text-model endpoint + worker registration

Halo B
└── text-model endpoint + worker registration

RTX host
├── ComfyUI
└── image worker/adapter
```

The control plane may live on the RTX host only if image load does not compromise database/API reliability. Prefer always-on stable host ownership.

### 16.1 Network ports

Document exact ports in deployment inventory. Firewall default-deny between hosts except:

- API/UI ingress;
- PostgreSQL only from approved control/worker hosts;
- model endpoints only from gateway workers;
- ComfyUI only from image adapter;
- object storage from application/image services;
- Temporal ports from approved workers;
- monitoring scrape endpoints.

### 16.2 Host identity

Use stable DNS or configured hostnames. Worker registration includes host ID. Character IDs never appear in host routing configuration.

---

## 17. GPU stack validation

For each GPU host, record:

```text
host hardware
OS and version
kernel
GPU driver
ROCm or CUDA version
PyTorch/runtime version
model server version
container/image digest
model/quantization hashes
startup command
context/KV settings
known limitations
benchmark date/results
```

Do not auto-update GPU drivers, ROCm, CUDA, ComfyUI, model server, or custom nodes on the stable profile.

A candidate upgrade runs:

- model startup;
- structured-output corpus;
- long-context test;
- concurrency/queue test;
- 24-hour soak if material;
- image workflow regression for RTX stack.

---

## 18. Temporal deployment

Only Stage 4 after ADR.

Development may use local Temporal server. Stable local deployment requires:

- pinned Temporal version;
- persistent supported database or explicit dev-only mode;
- namespace/configuration;
- task queues;
- UI protected on LAN;
- workflow build/version strategy;
- backup and operational runbooks.

Do not use the preview LangGraph plugin as the only path to executing graphs.

---

## 19. Backup, restore, and export

### 19.1 Backup scope

- PostgreSQL canonical/event/task data;
- object-store images/references/workflows;
- seed and configuration profiles;
- prompt files and hashes;
- model/workflow registry;
- deployed code/version manifests.

Model checkpoints may be backed up separately or referenced by immutable hashes and source.

### 19.2 Schedule

Development recommendation:

- end-of-day logical dump or snapshot;
- before migration;
- before hard retcon/import;
- generation boundary export.

### 19.3 Restore test

A backup is not trusted until a clean environment can restore it and:

- migrations/version are recognized;
- event/projection consistency audit passes;
- images resolve;
- one phase can resume or read-only export succeeds.

### 19.4 World export

Provide a self-describing manifest with:

- schema version;
- world ID/config;
- event data;
- projections where included;
- memories;
- image object inventory/checksums;
- prompt/model/workflow provenance;
- omissions and privacy class.

---

## 20. Common runbooks

Detailed runbooks belong in `docs/runbooks/`, including:

```text
postgres-unavailable.md
migration-failed.md
phase-stuck.md
openrouter-rate-limited.md
model-output-invalid-loop.md
worker-lease-stuck.md
outbox-backlog.md
memory-embedding-backlog.md
comfyui-offline.md
image-job-stuck.md
temporal-worker-deployment.md
restore-world-backup.md
hard-retcon-consistency-audit.md
```

`22` defines operational content expectations.

---

## 21. CI/release security

- secret scanning;
- dependency vulnerability scan;
- license inventory;
- pinned GitHub Actions by commit or trusted version policy;
- minimal job permissions;
- no OpenRouter key on untrusted pull requests;
- no production database credentials in CI;
- signed or checksummed release artefacts where practical;
- SBOM for containers in later stages.

---

## 22. Definition of done

Development/deployment foundations are complete when:

- a fresh clone reaches a seeded deterministic scenario through documented commands;
- migrations and generated schemas are reproducible;
- default tests make no external model calls;
- live calls are explicit and budget-capped;
- CI enforces static, test, migration, architecture, and generated-contract gates;
- containers contain no secrets and run non-root;
- restart/restore procedures are tested;
- Stage 4 host stacks are pinned and benchmarked;
- no GPU/service upgrade is introduced without regression evidence.
