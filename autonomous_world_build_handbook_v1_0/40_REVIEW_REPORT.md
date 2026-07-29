# Handbook Review Report

**Handbook:** Autonomous Fictional World Build Handbook  
**Version reviewed:** 1.0  
**Review date:** 2026-07-29  
**Status:** Approved as implementation input, subject to the explicit runtime decisions and stage gates documented below  
**Review scope:** Documents `00` through `40`, including requirements, architecture, domain contracts, persistence, simulation, agents, prompts, operations, stages, task packets, coordination templates, and review evidence

---

## 1. Executive conclusion

The handbook is internally coherent enough for a coding agent to start Stage 0 without relying on the design conversation that produced it.

It gives a fresh parent agent and bounded implementation subagents the information required to determine:

- what data is canonical;
- which component owns each decision;
- which model outputs are proposals rather than facts;
- how one phase and one scene progress;
- how simultaneous character intent and bounded causal reactions coexist;
- how a scene commits atomically and idempotently;
- how character knowledge, claims, beliefs, and memories remain isolated;
- which tables, services, graphs, API endpoints, UI views, jobs, and tests are introduced in each stage;
- how early OpenRouter use is constrained and how local inference is introduced later;
- how multiple coding sessions and subagents divide work without silently changing contracts;
- what evidence is required before each stage may be promoted.

The handbook is not a substitute for executable source code, lockfiles, generated schemas, migrations, tests, or stage evidence. It is the normative build specification from which those artefacts are created.

No known unresolved contradiction blocks Stage 0. Decisions intentionally deferred to later benchmarks or ADRs are listed in Section 9.

---

## 2. Review methodology

The review used several complementary passes.

### 2.1 Product-decision reconciliation

The accepted product answers and follow-up architecture decisions were reconciled against:

- `02_PROJECT_CHARTER_AND_REQUIREMENTS.md`;
- `03_GLOSSARY_AND_ARCHITECTURE_DECISIONS.md`;
- `04_SYSTEM_ARCHITECTURE.md`;
- subsystem documents `05` through `23`;
- stage documents `25` through `30`.

The pass checked that later implementation documents did not silently weaken or reverse an accepted product requirement.

### 2.2 Normative-precedence review

The handbook precedence rules were checked so that an implementation agent knows what to do when prose appears to differ:

1. accepted requirements and ADRs;
2. domain contracts and invariants;
3. persistence and subsystem specifications;
4. current stage specification;
5. task packet;
6. illustrative examples.

Examples, prompts, UI copy, generated narration, and model output never override a domain invariant.

### 2.3 Cross-document architecture review

The following boundaries were reviewed across all relevant documents:

- PostgreSQL event history and projections versus LangGraph checkpoints;
- deterministic World Engine versus Narrative Director;
- validator, resolver, narrator, and commit responsibilities;
- phase snapshot versus character context;
- objective event versus observation, claim, belief, and memory;
- application orchestrator versus bounded LangGraph workflows;
- canonical scene commit versus asynchronous image generation;
- character identity versus model worker or physical machine;
- focus characters versus temporary, recurring, and lineage characters;
- detailed phases versus macro-time simulation.

### 2.4 Stage and dependency review

The master plan, six stage documents, backlog, and subagent playbook were checked for:

- one consistent Stage 0–5 feature map;
- no premature hard dependency on vector retrieval, images, distributed inference, or Temporal;
- task identifiers and dependency order;
- parallel work lanes and contract-freeze points;
- explicit stage exclusions;
- promotion gates and evidence bundles;
- handoff from each stage to the next.

### 2.5 Contract and example validation

Machine-assisted checks were run against fenced examples and references:

- balanced Markdown fences;
- Python syntax parsing;
- JSON parsing;
- YAML parsing;
- local document-reference existence;
- unique charter requirement identifiers;
- complete requirement presence in the traceability matrix;
- unique ADR identifiers;
- unique stage task-packet identifiers;
- presence of all ten canonical phase names;
- absence of an executable `hp` or `hit_points` field in code blocks;
- presence of both initial OpenRouter model slugs and core architecture guard phrases.

SQL examples were reviewed as design DDL, but were not executed against PostgreSQL because the handbook is not yet an implementation repository with Alembic context, database fixtures, or pinned dependencies.

### 2.6 Failure-path review

The design was checked against representative failure cases:

- model malformed output;
- quota exhaustion;
- duplicate delivery;
- worker death after commit;
- stale aggregate version;
- database failure before commit;
- image-worker outage;
- missing embedding;
- character knowledge leakage;
- prompt-injection text inside memory;
- hard retcon producing downstream inconsistency;
- phase restart after process termination.

### 2.7 External-reference verification

Current official sources were used to verify the initial provider/model assumptions and to avoid turning changeable service facts into permanent architecture:

- OpenRouter model pages and API documentation;
- NVIDIA’s official Nemotron embedding model card;
- LangGraph persistence/subgraph documentation;
- Temporal Python and LangGraph-integration documentation;
- ComfyUI server/API documentation;
- pgvector documentation.

The implementation is still required to probe current capabilities and account limits at runtime. Documentation verification is not a service-level guarantee.

---

## 3. Corrections applied during review

### 3.1 Stage map normalized

The earlier domain-contract draft used a smaller stage vocabulary. It was aligned to the final six-stage handbook:

```text
Stage 0  foundation and deterministic contracts
Stage 1  first complete three-phase day
Stage 2  coherent seven-day world with ten phases
Stage 3  autonomous month and long-term memory
Stage 4  local distribution, durable orchestration, and images
Stage 5  generations and macro simulation
```

All stage documents, master-plan references, and quality gates now follow this map.

### 3.2 Early embedding dependency removed

Active long-term embedding retrieval is a Stage 3 capability. Stage 2 may run optional shadow embedding jobs, but decision correctness does not depend on them. Recent relational memory and daily summaries remain sufficient for the seven-day gate.

### 3.3 Free-provider use made quota-aware

The handbook no longer assumes that a free endpoint can power deterministic CI or a complete live soak. It now requires:

- fake/scripted model adapters for acceptance and regression tests;
- runtime capability and limit probes;
- request-budget reservation before a phase;
- bounded retries and safe fallbacks;
- sampled live quality runs rather than quota-consuming CI;
- no secret, personal, proprietary, or real-person material in the selected free endpoint profile.

### 3.4 Provider capabilities made runtime facts

Context size, structured-output support, embedding dimension, routing availability, privacy profile, and quota are recorded through a capability registry. The current Nemotron embedding profile expects a native 2,048-dimensional vector, but the adapter must fail closed if the endpoint returns a different shape.

### 3.5 Temporal dependency deferred and isolated

Stages 0–3 use the application-owned PostgreSQL-backed orchestrator. Stage 4 evaluates a Temporal adapter behind the same interface. The direct Temporal/LangGraph integration is treated as optional while it remains preview-level; ordinary Temporal activities wrapping bounded LangGraph work are the default migration design.

### 3.6 Python examples repaired

Two illustrative Python blocks were corrected so that every labelled Python block parses:

- event insert construction in the persistence document;
- the context-assembler function signature in the memory/RAG document.

### 3.7 Official reference targets corrected

The external registry was updated to point to:

- the exact NVIDIA `Nemotron-3-Embed-1B-BF16` model card;
- the current Temporal Python LangGraph-integration path.

### 3.8 Canonical-prose wording clarified

The scene requirement now says that narration is a **presentation of canon**. Narration itself remains noncanonical and cannot mutate or override structured state.

### 3.9 Example-name ambiguity removed

The README now explicitly distinguishes `Alex` and `Sein`, which appear in adversarial/explanatory fixtures, from the canonical seed characters defined in document `23`.

### 3.10 Seed scope clarified

The initial seed document contains four staged focus-character profiles. Stage 1 activates only the two-character slice required by its gate; later characters are enabled in Stage 2 rather than being silently generated during the first day.

### 3.11 Narrative requirements added to central traceability

The final traceability pass found that the ten `NAR-*` quality requirements were present in the charter and subsystem documents but absent from the central matrix. A dedicated narrative-quality section was added to document `32`, with primary design documents and concrete prompt/evaluator/human-review evidence for every requirement.

### 3.12 Copy-ready coordination and gate templates added

The multi-session playbook referred to status, ADR, change, contract-freeze, and stage-gate artefacts, but the first release did not provide a copy-ready form for every one. Documents `36`–`39` now define repository status files, ADR/change requests, stage promotion reports, fresh parent-agent kickoff instructions, bounded subagent context packs, and specialist review prompts.

---

## 4. Architecture decisions verified consistently

The review confirmed the following decisions across requirements, contracts, stages, tests, and operations.

### 4.1 Canon and mutation

- PostgreSQL is canonical.
- Immutable committed events plus current projections represent history and current state.
- A model never writes SQL or ORM state directly.
- Typed effect commands are validated before an atomic commit.
- Every state mutation has provenance and a source event.
- Narration, images, prompts, model histories, and LangGraph checkpoints are noncanonical.

### 4.2 Phase and scene semantics

- The World Engine ticks before character decisions.
- The Director is trigger-driven rather than mandatory every phase.
- All eligible primary character intents use one sealed phase snapshot.
- Eligibility may skip a deterministic sleeper, unconscious character, or uninterrupted activity without an LLM call.
- Scene assembly is entity/location/resource/route/conflict aware.
- Acting characters do not author another character’s hidden intent or successful reaction.
- Reactions and dialogue are bounded by beat budgets.
- Scene order, compute order, and intra-scene initiative are distinct concepts.
- Phase completion waits for canonical actions, observations, immediate memories, and durable async enqueue—not completed images.

### 4.3 Character agency and psychology

- Two main and two sub-main slots use the same personhood rules.
- Character identity is domain data, not a model, thread, adapter, or machine.
- Character cards are versioned; recent memory is not appended to the permanent system prompt.
- Goals, plans, needs, emotions, beliefs, commitments, and directional relationships influence action.
- Characters may reject intended romances, quests, and Director hooks.
- The Director adapts consequences rather than forcing compliance.
- Personality change requires accumulated evidence and bounded review.

### 4.4 Rules and health

- Stats use a 0–100 world scale with dynamic potential and growth evidence.
- Skills are distinct from base stats.
- No HP field exists.
- Harm uses injury, condition, impairment, consciousness, life status, treatment, and recovery.
- Magic has structured costs, prerequisites, affinities, possible effects, and failure modes.
- Hybrid combat uses deterministic feasibility, capability, preparation, environment, seeded uncertainty, and bounded model judgement.

### 4.5 Knowledge and memory

- Objective event, observation, claim, belief, episodic memory, summary, and semantic knowledge are distinct.
- Character context is assembled by observer identity and phase/scene scope.
- Ownership and visibility filters are applied before vector similarity.
- Characters do not receive omniscient state, another character’s private memory, or the Director’s hidden plan.
- Recent memory, daily summaries, long-term memories, and structured obligations have separate lifecycles.
- Memory source IDs and embedding/model versions remain auditable.
- Prompt-like text in memory is untrusted data.

### 4.6 World, NPCs, and generations

- The deterministic engine and creative Director have separate authority.
- The Director may propose NPCs; the registry validates uniqueness and budgets; the resolver approves/rejects.
- NPC actor mode receives only the NPC’s allowed perspective, not omniscient Director context.
- Ordinary NPCs never auto-promote to focus slots.
- Lineage succession is an explicit Stage 5 workflow.
- Adaptive temporal resolution is mandatory for a three-generation horizon.
- Stable peace, world eradication, and maximum-day termination are explicit evaluators rather than prose guesses.

### 4.7 Infrastructure

- LangGraph is used for bounded reasoning workflows, not global canonical scheduling.
- The outer orchestrator owns phase/task lifecycle and restart safety.
- Character identity is portable across provider/model workers.
- Image jobs are created only from committed scenes/events and remain asynchronous.
- Stage 4 benchmarks local text stacks and image workflows before selection.
- Deployment, model, prompt, workflow, and embedding versions are recorded.

---

## 5. Requirements and task traceability

The charter defines uniquely identified product principles, functional requirements, and non-functional requirements. Every identifier is represented in the traceability matrix in `32_BACKLOG_TRACEABILITY_RISKS_AND_DEFINITION_OF_DONE.md`.

The stage documents define bounded task packets with unique identifiers of the form:

```text
S<stage>-<workstream>-<number>
```

Each task packet includes or references:

- scope;
- dependencies;
- owned paths or subsystem boundaries;
- deliverables;
- tests;
- exclusions;
- merge/integration expectations;
- stage gate contribution.

The parent agent must still instantiate a task from `35_TASK_PACKET_TEMPLATE.md` before delegation. A stage heading is not by itself a sufficiently bounded subagent prompt.

---

## 6. Automated validation summary

<!-- VALIDATION_METRICS_START -->
| Measure | Result |
|---|---:|
| Markdown documents | 41 |
| Total bytes | 832,409 |
| Total lines | 27,146 |
| Approximate words | 99,522 |
| Traced charter identifiers | 152 |
| Accepted ADRs | 30 |
| Stage task packets | 80 |
| Labelled Python blocks parsed | 16 |
| JSON blocks parsed | 9 |
| YAML blocks parsed | 43 |
| Broken local references | 0 |
| Validation errors | 0 |
<!-- VALIDATION_METRICS_END -->

The placeholder-like tokens reported by the auxiliary scan are intentional notation such as `<task-id>` and `<TASK>` in operating instructions or prompt envelopes; they are not unresolved product decisions.

The final release validation is generated after this report is included. The release is accepted only when all of the following are true:

- every expected Markdown document exists;
- every local Markdown/document filename reference resolves;
- every fenced block is balanced;
- all labelled Python, JSON, and YAML examples parse;
- every charter requirement is unique and appears in the traceability document;
- every ADR and stage task definition is unique;
- all ten phase names appear in the normative contract;
- both initial OpenRouter model slugs appear in the handbook;
- no executable HP field exists in example schemas/code;
- the archive manifest and checksums match the released files.

The generated `manifest.json` records exact file counts, sizes, line/word counts, titles, SHA-256 hashes, and validation results for this release. `CHECKSUMS.sha256` provides a standard integrity list.

---

## 7. Stage-readiness findings

### Stage 0 — Ready to start

The handbook provides enough detail for:

- repository bootstrap;
- configuration and strict static quality;
- core domain types and Pydantic contracts;
- PostgreSQL/pgvector/Alembic baseline;
- event/projection/unit-of-work services;
- deterministic clock and effect validation;
- task/outbox primitives;
- fake and OpenRouter gateway adapters;
- capability probe and request ledger;
- seed import;
- restart-safe deterministic phase runner;
- minimal API/CLI and foundation evidence.

### Stage 1 — Specified, gated by Stage 0

The first complete three-phase day is fully described, including two simultaneous intents, simple scenes, bounded reactions, isolated observations/recent memory, player input, live status, and restart tests.

### Stage 2 — Specified, gated by Stage 1

The seven-day scope adds all ten phases, four focus characters, goals/plans/relationships, claims/beliefs, daily compaction, travel, trigger-based Director activity, bounded NPCs, multi-party scenes, and leakage testing without making vector retrieval mandatory.

### Stage 3 — Specified, gated by Stage 2

The autonomous month adds versioned embeddings and RAG, monthly reflection, stats/skills/magic/injuries, active arcs/factions, anti-repetition, quality evaluation, and a thirty-day no-repair soak.

### Stage 4 — Specified, benchmark-dependent

Local model selection, routing, failover, object storage, ComfyUI, visual state, image quality, multi-host deployment, and optional Temporal adoption are specified as measured implementation work rather than assumed facts.

### Stage 5 — Specified, research-heavy

Macro eligibility, compressed progression, genealogy, childhood, succession, generational world evolution, ending evaluators, long-horizon audits, and exports are defined. Stage 5 remains dependent on the detailed simulation surviving the earlier month gate.

---

## 8. Security, privacy, and safety findings

The handbook consistently requires:

- synthetic fictional data for the selected free external endpoints by default;
- credentials only in secret configuration, never prompts/logs/fixtures;
- role- and perspective-aware projections;
- deny-by-default model tools;
- no arbitrary SQL, shell, filesystem, or network tools exposed to agents;
- schema validation and effect authorization after model output;
- prompt-injection treatment for dialogue, memories, lore, and user text;
- explicit audit events for Director, deity, player, retcon, and administrative commands;
- young-adult/soft-dark content boundaries;
- no sexualized minors or explicit sexual content in the default profile;
- private-service network exposure only after authentication and authorization are configured;
- backups, restore drills, consistency audits, and incident runbooks.

The security design is suitable as a local-first baseline. It is not approval for public internet deployment. That requires a separate threat review and deployment ADR.

---

## 9. Intentionally deferred decisions

The following are not omissions. They are explicitly deferred because selecting them before evidence would create false certainty or lock the project prematurely.

### 9.1 Stage 4 local text runtime

To be selected by benchmark:

- exact local text model or role-specific models;
- vLLM, llama.cpp, another server, or a mixed stack;
- quantization formats;
- context/KV-cache limits;
- concurrency and batching;
- Halo failover/routing policy.

The provider-neutral gateway and capability registry are mandatory regardless of the winner.

### 9.2 Temporal adoption

The adapter and conformance evaluation are mandatory in Stage 4; adopting Temporal is evidence-based. The existing database-backed orchestrator may remain the production choice if it meets the reliability gate with less risk.

### 9.3 Image model and workflow

Stage 4 selects:

- image checkpoint/model;
- visual conditioning strategy;
- character LoRA/reference approach;
- ComfyUI workflow versions;
- quality-check model;
- resolution and retry budgets.

Images remain noncanonical whichever stack wins.

### 9.4 Object-storage implementation

The interface is S3-compatible. The exact local product, retention settings, replication, and backup procedure are selected during Stage 4 deployment work.

### 9.5 Current OpenRouter limits and endpoint behaviour

Free quotas, provider availability, privacy terms, structured-output support, and served context can change. The current implementation must probe/configure them and record the observed capability profile; no dated number in documentation is a durable contract.

### 9.6 Authentication and network exposure

The initial app is local and single-user. The exact authentication provider, session model, TLS termination, and multi-user authorization scheme require an ADR before any broader network exposure.

### 9.7 UUIDv7 library

The persistence contract requires sortable UUIDv7-compatible identifiers. The exact Python package or application implementation is selected and pinned in Stage 0 after maintenance and compatibility review.

### 9.8 End-condition thresholds

The categories are fixed, but exact numerical windows for stable peace, eradication confidence, and maximum days are world configuration and Stage 5 evaluation decisions.

### 9.9 Commercial/public product requirements

Licensing, moderation operations, multi-tenancy, billing, public-user content policy, and service-level objectives are out of the initial private local-first scope. They require a new charter revision rather than being inferred from the prototype.

---

## 10. Known limitations of the handbook

- It contains design-level SQL, Pydantic, JSON, YAML, HTTP, and configuration examples, not a compiled application.
- It cannot prove provider uptime, model quality, or current quota at implementation time.
- It cannot choose a local model without measuring the user’s actual three machines.
- It defines target API and database contracts; generated OpenAPI and final migration SQL must come from implementation.
- It provides an original seed world suitable for testing, but narrative quality still requires human evaluation and model-specific tuning.
- It defines three-generation mechanics, but no document can substitute for long-horizon empirical testing.
- It deliberately avoids prescribing character-specific text LoRAs before prompt/context isolation is measured.
- It does not authorize public deployment or use of private/proprietary material with the initial free endpoint profile.

---

## 11. Release checklist

A handbook archive may be released only when:

- [x] all documents `00`–`40` are present;
- [x] README order and precedence are defined;
- [x] requirements and ADRs are explicit;
- [x] domain contracts and state machines are implementation-oriented;
- [x] persistence and transaction boundaries are specified;
- [x] model, graph, orchestration, memory, API, UI, image, operations, and seed systems are covered;
- [x] stages `0`–`5` have dependencies, task packets, exclusions, and gates;
- [x] subagent/session procedures and templates exist;
- [x] traceability, risks, and definitions of done exist;
- [x] current official-reference registry exists;
- [x] cross-document corrections have been applied;
- [x] machine validation passes;
- [x] manifest and checksums are generated;
- [x] individual files and one ZIP archive are made available.

---

## 12. Reviewer recommendation

Start with `25_STAGE_0_FOUNDATION.md`, not with prompts or the UI.

The parent coding agent should:

1. copy `01_AGENTS.md` to repository-root `AGENTS.md`;
2. create the repository status files from `36_PROJECT_STATUS_TEMPLATES.md`;
3. freeze Stage 0 domain/config/repository contracts;
4. instantiate the first bounded tasks from `35_TASK_PACKET_TEMPLATE.md` and use `39_FRESH_AGENT_KICKOFF_AND_CONTEXT_PACK_TEMPLATE.md` for delegation;
5. use fake models for deterministic acceptance;
6. treat the live OpenRouter calls as capability and quality smoke tests;
7. merge only after the Stage 0 integration and restart/idempotency evidence passes.

Do not begin by writing elaborate character prompts, distributing inference across machines, or generating images. Those layers depend on a correct canonical event transaction, sealed snapshots, perspective isolation, and restart-safe orchestration.
