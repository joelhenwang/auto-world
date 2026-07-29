# Autonomous Fictional World

**Version:** 1.0  
**Date:** 2026-07-29  
**Status:** Implementation repository + normative build handbook (Stages 0–5)  
**Audience:** Coding agents, subagents, reviewers, and the human project owner  
**Primary language:** Python 3.12 (`uv`)  
**Initial inference:** OpenRouter free endpoints  
**Long-term inference target:** Local model servers across two Strix Halo systems plus one RTX 4060 Ti image worker

---

## Development quickstart

Stage 0 bootstrap (`S0-ENG-001`) provides the Python package skeleton and a PostgreSQL+pgvector Compose service. Domain logic, migrations, and seed import arrive in later Stage 0 tasks.

```bash
cp .env.example .env
uv sync
uv run python -c "import fictional_world"
docker compose up -d postgres   # optional; validates with: docker compose config
```

Useful aliases (thin wrappers; see `Makefile`):

```bash
make sync
make check          # ruff format --check + ruff check
make compose-config
make compose-up
```

Normative layout and standards: `autonomous_world_build_handbook_v1_0/19_*.md` and `20_*.md`. Agent operating rules: `AGENTS.md`. Current stage status: `docs/status/CURRENT_STAGE.md`.

Never commit `.env`. Default tests must not call external model providers.

---

## 1. What this handbook is

This folder is the complete implementation context for building the autonomous fictional-world project. It is written so that a coding agent can work across many sessions, delegate bounded work to subagents, and resume without reconstructing architectural intent from chat history.

The project is a persistent simulation and narrative system in which:

- a deterministic World Engine advances time and enforces rules;
- an omniscient Narrative Director proposes events, arcs, NPCs, and pacing adjustments;
- persistent characters independently propose actions from isolated perspectives;
- scenes assemble simultaneous intents, allow bounded reactions, and resolve outcomes;
- only validated, typed effect commands committed inside a database transaction alter canon;
- character-specific observations become beliefs and memories without leaking omniscient knowledge;
- images are generated asynchronously from committed scenes and never define canon;
- the user can switch between watcher, director, deity, and player modes;
- the world can eventually progress through at most three family generations.

This is not a collection of suggestions. Unless a document explicitly labels a section as optional, experimental, or deferred, the decisions are normative.

---

## 2. Non-negotiable architectural rule

> **Models may invent intentions, dialogue, interpretations, event proposals, and typed effects. Only deterministic validation plus an atomic database commit may change the world.**

No prompt, narration, image, checkpoint, or model conversation is canonical by itself.

---

## 3. Document precedence

When documents appear to disagree, use this order:

1. `02_PROJECT_CHARTER_AND_REQUIREMENTS.md` — product intent and externally observable behaviour.
2. `03_GLOSSARY_AND_ARCHITECTURE_DECISIONS.md` — fixed architectural decisions and terminology.
3. `05_DOMAIN_CONTRACTS_AND_STATE_MACHINES.md` — domain schemas and lifecycle rules.
4. `06_PERSISTENCE_DATABASE_AND_EVENT_LOG.md` — database constraints and transaction semantics.
5. Stage documents `25`–`30` — temporary scope restrictions for the active milestone.
6. System-specific documents `07`–`23`.
7. `24_MASTER_IMPLEMENTATION_PLAN.md` and backlog documents.
8. Examples and illustrative pseudocode.

A later version number supersedes an earlier version of the same document. An implementation must never silently choose between contradictions. Record the conflict in the session handoff and either resolve it through an ADR or stop the affected task.

---

## 4. Reading order for a new coding-agent session

### Mandatory first read

1. `01_AGENTS.md`
2. `02_PROJECT_CHARTER_AND_REQUIREMENTS.md`
3. `03_GLOSSARY_AND_ARCHITECTURE_DECISIONS.md`
4. `04_SYSTEM_ARCHITECTURE.md`
5. `24_MASTER_IMPLEMENTATION_PLAN.md`
6. The current stage document
7. The subsystem document for the assigned task
8. `32_BACKLOG_TRACEABILITY_RISKS_AND_DEFINITION_OF_DONE.md`

### For database work

Read `05`, `06`, `07`, `19`, `21`, and the current stage document.

### For model or prompt work

Read `05`, `08`–`15`, `21`, `22`, and the current stage document.

### For API or UI work

Read `02`, `04`, `17`, `18`, `19`, `22`, and the current stage document.

### For infrastructure or distributed runtime work

Read `12`, `14`, `16`, `20`, `22`, `29`, and `31`.

### For parent-agent, subagent, or multi-session coordination

Read `31`, `34`, `35`, `36`, `37`, `38`, and `39`. Use `39` to start a fresh parent session or construct a bounded subagent context pack.

---

## 5. Handbook map

| File | Purpose |
|---|---|
| `00_README.md` | Index, precedence, reading order, and project-wide conventions. |
| `01_AGENTS.md` | Operating rules for coding agents and subagents. Copy to repository root as `AGENTS.md`. |
| `02_PROJECT_CHARTER_AND_REQUIREMENTS.md` | Product goals, user modes, functional requirements, non-functional requirements, and scope. |
| `03_GLOSSARY_AND_ARCHITECTURE_DECISIONS.md` | Ubiquitous language and accepted architecture decisions. |
| `04_SYSTEM_ARCHITECTURE.md` | Components, boundaries, data flow, trust boundaries, and deployment evolution. |
| `05_DOMAIN_CONTRACTS_AND_STATE_MACHINES.md` | Pydantic contracts, phase lifecycle, scene lifecycle, effect contracts, and invariants. |
| `06_PERSISTENCE_DATABASE_AND_EVENT_LOG.md` | PostgreSQL schema, indexes, constraints, migrations, event log, projections, and outbox. |
| `07_SIMULATION_ENGINE_PHASES_SCENES_AND_TIME.md` | Clock, world tick, activation, scene assembly, initiative, time compression, and end conditions. |
| `08_CHARACTERS_PSYCHOLOGY_RELATIONSHIPS_AND_AGENCY.md` | Character cards, emotions, needs, goals, plans, relationships, lies, and personality evolution. |
| `09_WORLD_DIRECTOR_NPCS_LORE_MAP_AND_GENERATIONS.md` | Director rules, arcs, world generation, NPC lifecycle, factions, map, economy, and succession. |
| `10_STATS_SKILLS_MAGIC_COMBAT_AND_INJURIES.md` | Attribute model, potential, progression, mana, magic, combat, conditions, injuries, and death. |
| `11_PERCEPTION_CONTEXT_MEMORY_AND_RAG.md` | Knowledge isolation, observation, claims, beliefs, memory tiers, compaction, embedding, and retrieval. |
| `12_MODEL_GATEWAY_OPENROUTER_AND_LOCAL_MIGRATION.md` | Model abstraction, OpenRouter payloads, quotas, capability probing, retries, and local-serving migration. |
| `13_LANGGRAPH_AGENT_WORKFLOWS.md` | Bounded LangGraph graphs, graph state, nodes, interrupts, checkpointers, and testing. |
| `14_ORCHESTRATION_JOBS_CONCURRENCY_AND_DISTRIBUTION.md` | Outer orchestrator, task state, leases, retries, idempotency, concurrency, and Temporal migration. |
| `15_PROMPT_CATALOG_AND_OUTPUT_CONTRACTS.md` | Initial system prompts, context envelopes, output schemas, sampling profiles, and repair prompts. |
| `16_IMAGE_PIPELINE_AND_VISUAL_CONTINUITY.md` | Image selection, ComfyUI jobs, reference assets, appearance versioning, retries, and gallery behaviour. |
| `17_BACKEND_API_AND_REALTIME_EVENTS.md` | REST API, WebSocket events, commands, idempotency headers, DTOs, and error model. |
| `18_FRONTEND_UX_AND_USER_MODES.md` | Vue application, views, perspective filtering, role switching, visual-novel presentation, and accessibility. |
| `19_REPOSITORY_STRUCTURE_ENGINEERING_STANDARDS_AND_CONFIG.md` | Repository tree, module boundaries, Python/TypeScript standards, configuration, and dependency policy. |
| `20_LOCAL_DEVELOPMENT_DOCKER_CI_AND_DEPLOYMENT.md` | Bootstrap, Docker Compose, CI, environment profiles, release process, and later multi-machine deployment. |
| `21_TESTING_EVALUATION_AND_QUALITY_GATES.md` | Unit, integration, property, scenario, leakage, model, soak, and acceptance testing. |
| `22_OBSERVABILITY_SECURITY_PRIVACY_AND_OPERATIONS.md` | Logs, traces, metrics, audit, threat model, secrets, content boundaries, incident response, and runbooks. |
| `23_INITIAL_WORLD_SEED_AND_CONTENT_AUTHORING.md` | Minimal seed world, four staged focus-character profiles, fixtures, authoring format, and generated-content review. |
| `24_MASTER_IMPLEMENTATION_PLAN.md` | Stage sequence, dependency graph, workstreams, milestones, and promotion gates. |
| `25_STAGE_0_FOUNDATION.md` | Domain, database, deterministic engine, model-gateway smoke tests, and foundation exit gate. |
| `26_STAGE_1_FIRST_COMPLETE_DAY.md` | Two characters, three active phases, live action generation, simple scenes, and restart-safe one-day loop. |
| `27_STAGE_2_SEVEN_DAY_WORLD.md` | Ten phases, four focus characters, director triggers, claims, relationships, travel, and daily compaction. |
| `28_STAGE_3_AUTONOMOUS_MONTH.md` | Long-term RAG, active arcs, injuries, magic, factions, quality evaluation, and thirty-day soak. |
| `29_STAGE_4_LOCAL_DISTRIBUTION_AND_IMAGES.md` | Halo model replicas, gateway routing, durable orchestration, ComfyUI, image continuity, and failover. |
| `30_STAGE_5_GENERATIONS_AND_MACRO_SIMULATION.md` | Time compression, genealogy, succession, generation arcs, world peace, eradication, and maximum-day endings. |
| `31_PARALLEL_SUBAGENT_AND_SESSION_PLAYBOOK.md` | Task decomposition, file ownership, subagent briefs, merge order, session protocol, and review strategy. |
| `32_BACKLOG_TRACEABILITY_RISKS_AND_DEFINITION_OF_DONE.md` | Task catalog, dependencies, requirement-to-test traceability, risk register, and done criteria. |
| `33_REFERENCE_REGISTRY_AND_CHANGE_CONTROL.md` | Official source registry, version registry, ADR/change process, and documentation maintenance. |
| `34_SESSION_HANDOFF_TEMPLATE.md` | Mandatory end-of-session handoff format. |
| `35_TASK_PACKET_TEMPLATE.md` | Reusable bounded task specification for a coding agent or subagent. |
| `36_PROJECT_STATUS_TEMPLATES.md` | Copy-ready current-stage, integration, open-decision, known-failure, contract-freeze, and session-log templates. |
| `37_ADR_AND_CHANGE_REQUEST_TEMPLATES.md` | Copy-ready architecture-decision, change-request, and emergency-change records. |
| `38_STAGE_GATE_REPORT_TEMPLATE.md` | Promotion evidence template with build, migration, scenario, fault, quality, security, and sign-off sections. |
| `39_FRESH_AGENT_KICKOFF_AND_CONTEXT_PACK_TEMPLATE.md` | Fresh parent-agent kickoff, Stage 0 kickoff, bounded subagent context packs, and specialist review prompts. |
| `40_REVIEW_REPORT.md` | Review performed on this handbook, corrections applied, validation results, and explicitly deferred decisions. |

---

## 6. Stage sequence

```text
Stage 0 — Foundation and deterministic contracts
    ↓
Stage 1 — First complete three-phase day
    ↓
Stage 2 — Coherent seven-day world with all ten phases
    ↓
Stage 3 — Autonomous month with long-term memory
    ↓
Stage 4 — Distributed local inference and asynchronous images
    ↓
Stage 5 — Multi-generation macro simulation
```

A stage cannot be promoted because the UI “looks convincing.” Promotion requires every mandatory quality gate in the stage document and `21_TESTING_EVALUATION_AND_QUALITY_GATES.md`.

---

## 7. Initial technology baseline

| Concern | Initial choice |
|---|---|
| Python | 3.12, managed with `uv` |
| API | FastAPI + Uvicorn |
| Validation | Pydantic v2 + pydantic-settings |
| Database | PostgreSQL + pgvector |
| ORM | SQLAlchemy 2 typed declarative mapping |
| Driver | Psycopg 3 async |
| Migrations | Alembic |
| Agent graphs | LangGraph, bounded per task |
| Stage 0–3 orchestration | Application-owned orchestrator plus PostgreSQL task/outbox tables |
| Later orchestration | Temporal, wrapping LangGraph calls as activities; preview integrations are optional |
| Initial text model | `nvidia/nemotron-3-super-120b-a12b:free` through OpenRouter |
| Initial embedding model | `nvidia/nemotron-3-embed-1b:free` through OpenRouter |
| Frontend | Vue 3 + TypeScript + Vite |
| Realtime | WebSocket event stream |
| Image execution | ComfyUI, introduced in Stage 4 |
| Object storage | Local S3-compatible storage, introduced with image assets |
| Tests | pytest, pytest-asyncio, Hypothesis, testcontainers, mocked model contracts, scenario harness |
| Static quality | Ruff + basedpyright strict |
| Observability | Structured JSON logs + OpenTelemetry-compatible traces and metrics |

The exact dependency pins belong in `uv.lock`, the frontend lockfile, and the version registry. Documentation describes compatibility policy; lockfiles define an executable build.

---

## 8. Working rules

- Never code directly from this index; open the relevant subsystem document.
- Do not allow an LLM response to write SQL or mutate ORM entities directly.
- Do not persist a character’s whole lifetime as chat messages.
- Do not use LangGraph checkpoint state as canonical world state.
- Do not associate character identity with one physical model worker.
- Do not begin a phase unless the scheduler can finish it or use defined deterministic fallbacks.
- Do not block phase completion on image generation.
- Do not expose omniscient information in player mode.
- Do not accept autogenerated Alembic migrations without manual review.
- Do not merge parallel subagent work without running the integration gate for the affected stage.
- Names such as `Alex` and `Sein` in adversarial or explanatory examples are noncanonical test fixtures inherited from the design discussion. The canonical seed characters are defined only in `23_INITIAL_WORLD_SEED_AND_CONTENT_AUTHORING.md`.

---

## 9. Expected repository documents after implementation begins

The handbook is design input. The working repository must additionally maintain:

```text
AGENTS.md
README.md
docs/status/CURRENT_STAGE.md
docs/status/SESSION_LOG.md
docs/adr/ADR-XXXX-*.md
docs/generated/openapi.json
docs/generated/domain-schemas/*.json
docs/generated/database-schema.sql
docs/generated/model-capabilities.json
```

Generated files must be reproducible from code or migrations. They are not manually edited.

---

## 10. Completion definition for the handbook

A coding agent has enough context to begin when it can answer, without consulting prior chat history:

- what is canonical;
- what every model role may and may not do;
- how one phase proceeds;
- how simultaneous intents and reactions work;
- how state is committed and retried safely;
- how character knowledge remains isolated;
- how memories are compacted and retrieved;
- how OpenRouter limits affect early simulation;
- which modules and tables own each responsibility;
- how work is split between parallel agents;
- what test proves each milestone is complete;
- what is deliberately deferred.

That information is contained in the documents listed above.

---

## 11. Release-package integrity files

The distributed handbook archive also contains two non-normative integrity files:

```text
manifest.json
  Machine-readable document inventory, titles, sizes, hashes, and validation summary.

CHECKSUMS.sha256
  SHA-256 entries for every Markdown document and manifest.json.
```

Use `00_README.md` as the entry point and `40_REVIEW_REPORT.md` as the release-review record. Integrity files help verify the package; they do not override the normative precedence in Section 2.
