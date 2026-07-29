# AGENTS.md — Coding-Agent Operating Contract

**Version:** 1.0  
**Intended location:** Repository root  
**Applies to:** Parent coding agents, delegated subagents, reviewers, and automation agents

---

## 1. Mission

Build the autonomous fictional-world system described by the handbook without silently replacing its simulation architecture with a collection of chatbots.

The project succeeds when it can run a persistent world for the required stage duration while preserving:

- canonical consistency;
- character agency;
- perspective and secret isolation;
- restart and retry safety;
- explainable state changes;
- bounded model usage;
- engaging but causally grounded narration.

The project fails if it produces attractive prose while state, memory, or causality are unreliable.

---

## 2. Mandatory source-reading protocol

Before changing code:

1. Read `00_README.md` and this file.
2. Read `docs/status/CURRENT_STAGE.md` if the working repository already exists.
3. Read the active stage specification.
4. Read every subsystem document named in the task packet.
5. Read existing ADRs that touch the module.
6. Inspect the current code and tests; do not assume the repository still matches the initial handbook.
7. Run the narrowest existing verification command before editing, so pre-existing failures are known.

Do not ask the user to repeat information already available in the handbook or repository.

---

## 3. Source-of-truth hierarchy

Use this order when deciding implementation behaviour:

1. Accepted product requirements.
2. Accepted ADRs and glossary definitions.
3. Domain contracts and invariants.
4. Database constraints and state-machine rules.
5. Current-stage scope and exit criteria.
6. Subsystem specifications.
7. Existing tests that accurately reflect the above.
8. Existing implementation.
9. Examples and pseudocode.

If code or a test contradicts a higher source, do not preserve the contradiction merely for backward compatibility. Record it, fix it in the task scope if safe, and update tests and documentation together.

---

## 4. Hard architecture rules

### 4.1 Canon

- PostgreSQL canonical state and committed `world_event` history are authoritative.
- Models produce proposals only.
- LangGraph state is execution state, not fictional truth.
- Narration and images are projections, never authoritative inputs.
- Every canonical mutation must be represented by a typed effect command, validated, and committed atomically.

### 4.2 Knowledge isolation

- A character receives only its perspective package.
- No arbitrary repository or SQL method may return omniscient state to a character graph.
- Claims, rumours, beliefs, observations, and facts remain distinct.
- A character never writes another character’s private intention or memory.
- The director may be omniscient, but disclosure still passes through perception rules.

### 4.3 Concurrency and retries

- Every externally retried operation has an idempotency key.
- A retry may not duplicate events, injuries, NPCs, memories, item transfers, or image jobs.
- Primary character intents for one phase reference the same sealed phase snapshot.
- Conflicting scenes are merged or rejected before commit; they are not resolved concurrently against stale state.
- Do not hold database transactions open during remote model inference.

### 4.4 Model boundaries

- Models never receive raw database credentials, unrestricted filesystem access, shell access, or arbitrary HTTP tools.
- State-affecting responses use structured output and local validation.
- Do not request or store hidden chain-of-thought. Ask only for concise, externally useful rationale fields where the contract requires them.
- Free OpenRouter endpoints are development dependencies, not assumed production infrastructure.
- All model slugs, capabilities, limits, prompts, and sampling settings are versioned.

### 4.5 Time and scenes

- The World Engine acts first at every detailed phase.
- Director intervention is optional and trigger-based.
- Primary intents are simultaneous from one snapshot.
- Reactions are bounded and causal within assembled scenes.
- Images are enqueued only after canonical event commit and never block the next phase.

---

## 5. Work only from a task packet

Every implementation task must have, at minimum:

- task ID;
- objective;
- stage;
- documents to read;
- files or modules allowed to change;
- explicit non-goals;
- dependencies;
- required tests;
- acceptance criteria;
- handoff recipient or integration owner.

Use `35_TASK_PACKET_TEMPLATE.md` when creating a task. A parent agent may create the packet immediately before delegation, but it must exist in the session record.

Do not accept vague work such as “build the memory system.” Split it into bounded outputs such as schema, repository operations, ranking function, context assembler, contract tests, and scenario tests.

---

## 6. Parent-agent responsibilities

The parent agent owns integration and cannot delegate away accountability.

Before delegation:

1. Identify task dependencies and shared files.
2. Assign non-overlapping write ownership wherever possible.
3. Give every subagent a self-contained packet.
4. State whether the subagent may modify tests, migrations, public interfaces, or documentation.
5. Define the expected return format.

After delegation:

1. Review diffs rather than relying on summaries.
2. Run affected unit, integration, static, and migration checks.
3. Resolve conflicting assumptions centrally.
4. Update the session log and task states.
5. Never merge multiple subagent changes merely because each passed isolated tests.

---

## 7. Subagent responsibilities

A subagent must:

- stay inside assigned scope;
- avoid editing files owned by another active task;
- state any necessary assumption before implementing it;
- stop and report a handbook contradiction rather than inventing a new architecture;
- add or update tests for every behavioural change;
- document migrations and public interface changes;
- return changed files, commands run, test results, risks, and unresolved concerns;
- not reformat unrelated files;
- not replace working typed contracts with untyped dictionaries for convenience;
- not introduce a dependency without explaining why existing dependencies are insufficient.

A subagent may inspect any file but may write only its assigned set unless the parent explicitly expands scope.

---

## 8. File ownership and parallel work

Prefer parallel work across these seams:

```text
Domain contracts          → src/worldsim/domain/**
Persistence               → src/worldsim/infrastructure/db/** + migrations/**
Simulation application    → src/worldsim/application/simulation/**
Model gateway             → src/worldsim/infrastructure/models/**
Agent graphs              → src/worldsim/agents/**
Memory/context            → src/worldsim/application/memory/**
API                        → src/worldsim/interfaces/api/**
Frontend                   → apps/web/**
Tests/fixtures             → tests/** and fixtures/**
Infrastructure            → compose.yaml, docker/**, scripts/**
Documentation             → docs/**
```

Do not parallelize tasks that both alter:

- the same Alembic revision chain;
- the same Pydantic discriminated union;
- the same public API DTO;
- the same phase transition table;
- generated OpenAPI or JSON Schema outputs;
- repository-wide dependency files.

For these, appoint one integration owner and have other agents propose patches or notes rather than commit competing edits.

---

## 9. Branch and commit discipline

When Git is available:

- one branch per task packet;
- branch name: `task/<task-id>-<short-name>`;
- small, intentional commits;
- migration and matching model changes in the same task branch;
- no generated secrets, local databases, model outputs, or images committed;
- do not squash away meaningful migration history before review;
- parent agent performs integration merge order according to dependencies.

Suggested commit prefixes:

```text
feat(domain):
feat(db):
feat(simulation):
feat(agent):
feat(memory):
feat(api):
feat(ui):
fix(...):
test(...):
docs(...):
refactor(...):
chore(...):
```

A commit message must state the behaviour, not merely the file changed.

---

## 10. Coding standards summary

Detailed rules live in `19_REPOSITORY_STRUCTURE_ENGINEERING_STANDARDS_AND_CONFIG.md`.

Minimum requirements:

- Python 3.12 syntax and type annotations.
- Pydantic v2 models for boundary contracts.
- SQLAlchemy 2 typed mappings.
- `async` only for I/O paths; domain logic remains synchronous and deterministic where possible.
- `ruff check`, `ruff format --check`, and strict `basedpyright` must pass.
- No broad `Any` in domain or application layers without a documented boundary reason.
- Use `Protocol` for ports and adapters.
- No infrastructure imports from the domain package.
- No hidden singleton database sessions or global mutable simulation state.
- All timestamps timezone-aware UTC; fictional time uses explicit domain fields.
- Public functions have docstrings when behaviour or invariants are not obvious from types.
- Exceptions are typed by layer and translated at boundaries.
- Every log event is structured and includes relevant world/phase/scene/task IDs.

---

## 11. Database and migration rules

- All schema changes use Alembic.
- Every constraint and index has an explicit deterministic name.
- Autogenerate is a starting point; inspect and edit every revision.
- A migration includes an upgrade path, rollback policy, data backfill plan, and expected lock impact.
- Never alter already-applied migration files in shared history.
- Store flexible provenance in JSONB, but normalize fields used for constraints, joins, filtering, or state resolution.
- Do not use PostgreSQL-native enums for fast-changing domain vocabularies; use strings plus named check constraints unless an ADR says otherwise.
- No direct delete of committed events or observations through ordinary application services.
- Use optimistic versions on mutable aggregates.
- Do not call remote services while a transaction is open.

Before completing a database task, run:

```bash
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
uv run alembic check
```

Use a disposable test database, never a developer’s canonical world.

---

## 12. Testing rules

Every behavioural change must have the narrowest appropriate test:

- pure rule → unit or property test;
- repository → PostgreSQL integration test;
- model payload or parser → contract test with recorded synthetic responses;
- graph lifecycle → graph test with fake ports;
- full phase → scenario test;
- retry or crash safety → fault-injection integration test;
- character secrecy → leakage test;
- long-duration behaviour → soak test.

Do not use live free-model calls in ordinary CI. Live provider tests are explicitly marked and manually or periodically run.

A mocked test that merely returns the desired Pydantic object is insufficient for parser robustness. Include malformed JSON, missing fields, unsupported effect types, timeouts, 429s, and duplicate deliveries.

---

## 13. Documentation obligations

Update documentation in the same task when changing:

- a public API;
- a domain schema;
- an invariant;
- a database table or migration policy;
- a prompt contract;
- a model role or sampling profile;
- a stage gate;
- a deployment procedure;
- an operational runbook.

Create an ADR when changing a previously fixed architecture decision. Do not rewrite the history of why a decision was made.

Generated documentation is regenerated, not hand-edited.

---

## 14. Session protocol

Use repository status files instantiated from `36_PROJECT_STATUS_TEMPLATES.md` and context packs from `39_FRESH_AGENT_KICKOFF_AND_CONTEXT_PACK_TEMPLATE.md`.

### At session start

1. Read the previous handoff.
2. Check branch, working tree, and current stage.
3. Run the stated baseline checks.
4. Confirm the task packet remains valid against current code.
5. Reserve or mark the task as active.

### During the session

- maintain a concise work log;
- surface discovered defects early;
- avoid opportunistic refactors outside scope;
- make partial progress testable;
- keep the repository runnable.

### At session end

Complete `34_SESSION_HANDOFF_TEMPLATE.md`, including:

- exact task status;
- files changed;
- migrations created;
- commands and tests run;
- known failures;
- assumptions;
- next concrete step;
- any task that is now unblocked or blocked.

Never end with only “implemented most of it.” State what remains at file/function/test level.

---

## 15. Model-assisted coding cautions

When using a coding model or subagent:

- provide exact source documents and file boundaries;
- do not paste secrets or real personal information into free endpoints;
- require the agent to inspect current code before proposing replacement code;
- require tests and explicit assumptions;
- never allow it to create migrations and application models independently without cross-review;
- verify framework APIs against current official documentation when there is meaningful version risk;
- treat generated code as untrusted until static checks and tests pass.

---

## 16. Stop conditions

Stop the affected task and escalate to the parent agent when:

- two normative documents conflict;
- a task requires breaking a stage’s non-goal;
- a migration would destroy or silently reinterpret canonical data;
- a model-facing change could leak private character knowledge;
- an idempotency guarantee cannot be preserved;
- a dependency’s current behaviour is materially uncertain and unverified;
- a required test fixture exposes real personal or proprietary data to OpenRouter;
- the task requires changing more than one major subsystem without an integration plan.

Do not stop the entire project for an unrelated uncertainty. Isolate it, document it, and continue safe independent work.

---

## 17. Definition of a good implementation

A good implementation is:

- boring at the state boundary;
- creative only behind validated contracts;
- explicit about ownership and perspective;
- restart-safe;
- inspectable;
- typed;
- testable without live models;
- replaceable at provider boundaries;
- incrementally extensible through the stage plan.

A clever shortcut that obscures causality, state ownership, or retries is not an improvement.
