# Glossary and Architecture Decisions

**Version:** 1.0  
**Status:** Normative  
**Purpose:** Eliminate ambiguous language and record the decisions that implementation agents must not silently revisit.

---

## 1. Ubiquitous language

| Term | Exact meaning |
|---|---|
| **World** | The single canonical fictional setting, its rules, entities, history, map, clock, and configuration. |
| **Canon** | Facts and state represented by committed world events plus validated current projections. |
| **World Engine** | Deterministic application code that advances fictional time and applies world rules. It is not an LLM. |
| **Narrative Director** | Omniscient model role that proposes events, hooks, arcs, NPCs, pacing adjustments, and worldbuilding additions. It does not commit state. |
| **Resolver** | Hybrid outcome component combining deterministic feasibility/rules with bounded model judgment for ambiguity. |
| **Validator** | Layered schema, permission, prerequisite, knowledge, invariant, and semantic checks applied before commit. Usually code plus an optional model-assisted semantic step. |
| **Focus character** | One of the two main or two sub-main persistent characters receiving detailed decision calls. |
| **Lineage character** | A descendant or heir tracked for a future generation transition. It is not an ordinary temporary NPC. |
| **NPC** | A non-focus entity represented at background, temporary, or recurring-supporting resolution. |
| **Character card** | Versioned identity, backstory, appearance, personality, values, voice, and foundational capability specification. It is not a mutable transcript. |
| **Character state** | Current body, location, resources, emotions, needs, life status, active card version, and optimistic version. |
| **Phase** | One detailed fictional day interval: dawn, sunrise, morning, noon, afternoon, sunset, dusk, evening, night, or midnight. |
| **Absolute phase index** | Monotonically increasing integer that totally orders detailed and macro-derived time positions. |
| **Phase run** | Operational execution record for advancing and completing one phase. |
| **Phase snapshot** | Immutable, sealed projection of committed state used to generate all same-phase primary intents. |
| **Perception package** | Access-controlled context for one character at one decision point. |
| **Intent** | A character’s one proposed meaningful action from a sealed snapshot. |
| **Attempt** | Validated externally observable execution of an intent before the outcome is determined. |
| **Reaction** | Bounded response by an eligible participant to an observable attempt. |
| **Beat** | One short meaningful action and/or utterance by one scene participant. |
| **Scene** | A causally interacting set of intents, attempts, reactions, entities, and one atomic outcome commit. |
| **Action family** | Stable broad category such as move, communicate, attack, cast magic, train, rest, or observe. |
| **Desired effect** | Non-authoritative structured description of what an actor hopes to accomplish. |
| **Effect command** | Typed candidate mutation such as move entity, spend mana, transfer item, apply injury, or create claim. It is not authoritative until validated and committed. |
| **World event** | Immutable historical record of one committed canonical occurrence. |
| **Projection** | Current-state table derived and updated from accepted effects for efficient queries. |
| **Observation** | Perspective-specific record of what one observer could perceive from an event. |
| **Claim** | Proposition communicated by an entity. It may be true, false, misleading, or uncertain. |
| **Belief** | Confidence-weighted proposition held by one character. |
| **Rumour** | A claim propagated through one or more intermediaries with provenance and distortion risk. |
| **Memory** | Perspective-owned retained representation derived from observations, interpretations, beliefs, or reflection. |
| **Recent memory** | Relational, non-vector working/episodic memory available directly to context assembly. |
| **Long-term memory** | Compacted, provenance-linked memory eligible for embedding retrieval. |
| **Summary** | Derived compression of multiple source observations or memories; versioned and never a replacement for raw sources. |
| **Context assembler** | Central service that builds role- and perspective-safe model input from approved sources. |
| **Model role** | Logical use such as character action, director proposal, semantic validator, resolver, narrator, or memory consolidator. It is independent of physical model deployment. |
| **Model profile** | Versioned configuration mapping a logical role to provider, slug, prompts, sampling, context budget, and capability requirements. |
| **Task run** | Durable record for one asynchronous or retryable unit of work. |
| **Outbox message** | Transactionally written notification that asynchronous work must occur after commit. |
| **Idempotency key** | Stable identifier ensuring repeated delivery produces one logical result. |
| **Optimistic version** | Monotonic aggregate version checked before state mutation to detect stale writes. |
| **Arc** | Bounded long-running narrative direction with goals, phases, hooks, progress, and completion conditions. |
| **Hook** | Potential future event or unresolved opportunity that may remain dormant. |
| **Macro simulation** | Lower-resolution advancement over days, weeks, months, or years while preserving important state transitions. |
| **Visual asset** | Non-canonical portrait, expression, background, reference sheet, item image, or event illustration. |

---

## 2. Architectural decision record format

Each fixed decision is recorded as:

```text
ADR-ID
Status
Decision
Reason
Consequences
Revisit trigger
```

The implementation repository may split these into individual ADR files later. Until then, this document is the accepted ADR index.

---

## ADR-001 — Canon lives in PostgreSQL

**Status:** Accepted

**Decision:** Canonical world state is represented by immutable committed events plus current PostgreSQL projections. Model histories, LangGraph checkpoints, generated prose, and images are not canonical.

**Reason:** The world requires transactions, constraints, filtering, provenance, restart safety, and inspectable mutations.

**Consequences:** Every state change needs an effect command and source event. A model cannot directly save ORM entities. Reconstructing context always starts from domain data, not chat history.

**Revisit trigger:** None expected. A future storage technology may replace PostgreSQL only if it preserves the same semantics.

---

## ADR-002 — Hybrid event log plus projections, not pure event sourcing

**Status:** Accepted

**Decision:** Keep an append-only canonical event/effect history and update normalized current-state projections in the same transaction. Do not require every normal query to replay all events.

**Reason:** Pure event sourcing adds operational complexity that does not improve the creative system at its initial scale. An event log is still necessary for explanation, audits, retcons, and rebuilds.

**Consequences:** Projection rebuild tools and consistency audits are required. Projection rows retain source-event/version metadata.

**Revisit trigger:** Event volume or branching requirements make current projection strategy inadequate.

---

## ADR-003 — Models propose; application code commits

**Status:** Accepted

**Decision:** Models may propose intents, reactions, events, interpretations, and typed effects. Deterministic application services validate and commit.

**Reason:** LLM output is probabilistic, can be malformed, and cannot enforce concurrent state or database invariants.

**Consequences:** All state-affecting calls use structured output. The resolver output is still untrusted. Narration is generated after commit.

**Revisit trigger:** None.

---

## ADR-004 — World Engine and Narrative Director are separate

**Status:** Accepted

**Decision:** The “world character” is split into deterministic World Engine code and an LLM-driven Narrative Director.

**Reason:** Time, travel, resources, recovery, scheduled effects, and end conditions require deterministic authority. Pacing and creative opportunities benefit from a model.

**Consequences:** The Director cannot silently alter rules or outcomes. World-first behaviour means the deterministic tick always occurs; the Director call is optional.

**Revisit trigger:** None.

---

## ADR-005 — Simulation decides facts; narrative decides opportunities and presentation

**Status:** Accepted

**Decision:** When realism/causality conflicts with desired drama, simulation rules determine facts. The Director may create opportunities and spotlight bias but not hidden outcome bias.

**Reason:** Otherwise characters become puppets and consequences lose meaning.

**Consequences:** Plot armour is an explicit configurable setting. Narration cannot override structured results.

**Revisit trigger:** Product owner explicitly requests a story-first mode as a separately named configuration.

---

## ADR-006 — Simultaneous primary intents from one snapshot

**Status:** Accepted

**Decision:** All eligible focus characters generate their primary intent from the same sealed phase snapshot. Same-phase results are not fed into another unrelated character’s primary intent.

**Reason:** Sequential generation gives later actors unfair information and makes outcome depend on compute order.

**Consequences:** Intents are assembled into scenes after generation. Causal reactions inside a scene are sequential and bounded.

**Revisit trigger:** A future real-time mode intentionally models continuous initiative rather than phase turns.

---

## ADR-007 — Scene-centric resolution

**Status:** Accepted

**Decision:** Scheduler and resolver operate on scenes, not isolated character turns. Interacting or conflicting intents share one resolution boundary.

**Reason:** “A visits B” and “B waits for A,” or two actors targeting one item, cannot be resolved correctly as independent commits.

**Consequences:** Scene assembly and shared-entity conflict detection are first-class systems.

**Revisit trigger:** None.

---

## ADR-008 — Characters cannot author other characters’ private reactions

**Status:** Accepted

**Decision:** An actor describes its own attempt and observable expectations only. The target or a deterministic fallback owns the target’s reaction.

**Reason:** Letting one character write another’s preparation or hidden intention destroys agency and leaks information.

**Consequences:** Scene interaction uses attempt → eligible reaction → resolver. Beat budgets limit calls.

**Revisit trigger:** None.

---

## ADR-009 — Broad action ontology with free-form intent

**Status:** Accepted

**Decision:** Actions use stable broad families plus freely written intent, targets, resources, duration, and desired effects. New prose actions normally map to an existing family.

**Reason:** Fully closed verbs restrict creativity; fully arbitrary effects make validation impossible.

**Consequences:** `OTHER` exists but is stricter. Effect-command vocabulary evolves through reviewed code and migrations.

**Revisit trigger:** Evaluation shows the family set blocks common valid behaviour.

---

## ADR-010 — No HP

**Status:** Accepted

**Decision:** Health is represented through injuries, conditions, consciousness, life status, treatment, and recovery. No universal HP pool is used.

**Reason:** The intended world needs persistent, body-specific consequences rather than an arcade abstraction.

**Consequences:** Combat resolution is more structured. Injury models and death rules are required before complex combat.

**Revisit trigger:** A separate game-like mode is introduced.

---

## ADR-011 — Directional relationships

**Status:** Accepted

**Decision:** Relationship state is stored per source character and target character across multiple dimensions. The two directions are independent.

**Reason:** People perceive and value relationships differently.

**Consequences:** Each character sees its own attitude and inferred reciprocity, not the other side’s true numbers.

**Revisit trigger:** None.

---

## ADR-012 — Claims and beliefs are not facts

**Status:** Accepted

**Decision:** Spoken assertions create claims; listeners update beliefs. Canonical facts change only through world events/effects.

**Reason:** Lies, rumours, uncertainty, investigation, and limited perspective require this distinction.

**Consequences:** Dialogue cannot directly create objective facts. Belief confidence and provenance are stored.

**Revisit trigger:** None.

---

## ADR-013 — PostgreSQL plus pgvector for early memory

**Status:** Accepted

**Decision:** Use PostgreSQL and pgvector rather than a separate vector service through at least Stage 3.

**Reason:** The expected memory volume is modest, strict metadata filtering is essential, and transactions/operational simplicity are more valuable than a second datastore.

**Consequences:** Exact search is the starting mode. Approximate HNSW is added only after profiling and isolation tests.

**Revisit trigger:** Memory volume, latency, or deployment topology exceeds measured PostgreSQL capability.

---

## ADR-014 — Recent memory stays outside the system prompt

**Status:** Accepted

**Decision:** Stable identity and behavioural rules live in the system/character identity sections. Dynamic state, recent events, and retrieved memories are assembled per call.

**Reason:** Rewriting an ever-growing system prompt causes drift, weak provenance, and context blow-up.

**Consequences:** The context assembler becomes a critical service. Character cards are versioned independently of memories.

**Revisit trigger:** None.

---

## ADR-015 — Character identity is independent of hardware and model process

**Status:** Accepted

**Decision:** Character identity comes from canonical data and context assembly. Any compatible model server may serve any character request.

**Reason:** Binding a character to one machine prevents failover, balancing, and model migration.

**Consequences:** Workers are stateless with respect to fictional identity. KV cache reuse is an optimization, never an authority source.

**Revisit trigger:** None.

---

## ADR-016 — LangGraph is bounded reasoning orchestration

**Status:** Accepted

**Decision:** Use LangGraph for bounded role workflows such as character decision, director proposal, validation, narration, or memory consolidation. The global world scheduler remains application-owned.

**Reason:** A long-lived world needs explicit database and task semantics beyond a monolithic graph thread.

**Consequences:** Checkpoints represent resumable graph execution only. Domain repositories remain external ports.

**Revisit trigger:** A future stable framework proves it can preserve the same domain boundaries with less complexity.

---

## ADR-017 — Initial orchestrator is application-owned; Temporal is a later adapter

**Status:** Accepted

**Decision:** Stages 0–3 use a deterministic application orchestrator plus database task/outbox records. Stage 4 may introduce Temporal. LangGraph’s Temporal plugin is optional because it is currently preview-level; standard Temporal activities are the safe integration path.

**Reason:** Distributed durable workflow infrastructure should not obscure basic simulation bugs during the first vertical slices.

**Consequences:** Orchestrator ports and task contracts must be designed for later Temporal mapping. No business rule may depend on an in-process scheduler detail.

**Revisit trigger:** Stage 3 reliability requirements cannot be met with the database-backed orchestrator, or the Temporal adapter becomes the active Stage 4 task.

---

## ADR-018 — OpenRouter free models are initial adapters

**Status:** Accepted

**Decision:** Initial text and embedding adapters use:

```text
nvidia/nemotron-3-super-120b-a12b:free
nvidia/nemotron-3-embed-1b:free
```

Capabilities and quotas are probed at runtime. The architecture does not assume permanent free availability.

**Reason:** They enable fast development before local serving is stabilized.

**Consequences:** A request budget ledger, deterministic degradation, synthetic-only prompt data, and provider-independent gateway contracts are required.

**Revisit trigger:** Endpoint removal, quality failure, quota exhaustion, or local-model migration.

---

## ADR-019 — Embedding versioning and exact search first

**Status:** Accepted

**Decision:** Store native 2048-dimensional Nemotron embeddings, prefix queries/documents consistently, record model/prefix/content versions, and use exact similarity search until profiling justifies HNSW.

**Reason:** Correct isolation and retrieval evaluation are more important than premature approximate indexing.

**Consequences:** Re-embedding uses parallel versioned rows. Retrieval filters by world, owner, visibility, and active version before scoring.

**Revisit trigger:** Stage 3 profiling demonstrates unacceptable exact-search latency.

---

## ADR-020 — Images follow committed events

**Status:** Accepted

**Decision:** Generate images only from committed scenes/events and treat them as non-canonical illustrations.

**Reason:** Proposed actions may fail, and image models may add visual mistakes.

**Consequences:** Image jobs are written through the transactional outbox. Image failure never rolls back canon.

**Revisit trigger:** None.

---

## ADR-021 — Reusable visual-novel assets plus salient event CGs

**Status:** Accepted

**Decision:** Use portraits, expressions, outfits, and location backgrounds for routine scenes; generate event illustrations for visually significant moments.

**Reason:** Generating every line is expensive, slow, and inconsistent.

**Consequences:** Asset selection and appearance versions are part of presentation state. Image budgets are configurable.

**Revisit trigger:** Local image throughput becomes high enough and continuity quality remains acceptable.

---

## ADR-022 — One world, one active timeline, explicit hard retcons

**Status:** Accepted

**Decision:** The product initially has one canonical world and one active timeline. Hard retcons preserve audit history and mark downstream data as potentially inconsistent; they do not create a normal branch UI.

**Reason:** Branching multiplies state, memory, and image complexity before core stability is proven.

**Consequences:** Recovery snapshots are operational, not fictional alternate universes.

**Revisit trigger:** A later product requirement explicitly introduces branches.

---

## ADR-023 — Adaptive temporal resolution is mandatory for generations

**Status:** Accepted

**Decision:** Detailed ten-phase simulation is used during active periods. Quiet periods may advance by day, week, month, or year through macro simulation.

**Reason:** Three generations would otherwise require hundreds of thousands of detailed phases and millions of model calls.

**Consequences:** Macro simulation must preserve schedules, ageing, relationships, health, faction state, and high-salience interruption.

**Revisit trigger:** None.

---

## ADR-024 — Focus slots, not permanently fixed entities

**Status:** Accepted

**Decision:** The system has two main and two sub-main focus slots. At generation transitions, lineage characters may occupy them. Ordinary NPCs never auto-promote.

**Reason:** Generational continuity requires changing protagonists without uncontrolled cast growth.

**Consequences:** Focus assignment is versioned and event-sourced.

**Revisit trigger:** Product owner changes focus-cast limits.

---

## ADR-025 — User commands are events, not hidden edits

**Status:** Accepted

**Decision:** Watcher, director, player, and deity commands enter through typed command APIs, permission checks, validation, and audit records.

**Reason:** Hidden database edits destroy explainability and can violate invariants.

**Consequences:** Even authoritative overrides have provenance and consistency effects.

**Revisit trigger:** None.

---

## ADR-026 — Young-adult soft-dark default

**Status:** Accepted

**Decision:** Default content allows meaningful danger, injury, death, grief, betrayal, and non-graphic horror while excluding explicit sexual content, sexualized minors, sexual violence, fetishized abuse, and prolonged graphic torture.

**Reason:** This matches the intended audience and product tone.

**Consequences:** Prompts, UI controls, seed content, and evaluation include these boundaries.

**Revisit trigger:** A separately configured and policy-reviewed content mode is introduced.

---

## ADR-027 — Vue local web application

**Status:** Accepted

**Decision:** The first full interface is a local Vue 3 + TypeScript web application backed by FastAPI and WebSocket updates.

**Reason:** It supports timeline, map, character pages, role controls, and live queue status while matching the owner’s existing experience.

**Consequences:** API schemas generate TypeScript types. CLI/debug tools may exist but are not the primary product.

**Revisit trigger:** A desktop wrapper or alternative client becomes a requirement.

---

## ADR-028 — Strict typing and layered architecture

**Status:** Accepted

**Decision:** Use Pydantic v2 at boundaries, SQLAlchemy 2 typed mappings, `Protocol` ports, Ruff, and strict basedpyright. Domain code has no infrastructure imports.

**Reason:** The project’s complexity makes implicit dictionaries and circular dependencies dangerous.

**Consequences:** More initial schema work; easier multi-agent implementation and refactoring.

**Revisit trigger:** None.

---

## ADR-029 — No production dependence on provider-specific structured-output support

**Status:** Accepted

**Decision:** Prefer strict JSON Schema when the chosen endpoint supports it, but preserve local extraction, validation, one bounded repair/regeneration, and safe fallback.

**Reason:** OpenRouter capability support is endpoint-specific and may change.

**Consequences:** Capability probes and malformed-response tests are mandatory.

**Revisit trigger:** All active local models provide a stronger guaranteed schema protocol.

---

## ADR-030 — Explicit non-cringe quality system

**Status:** Accepted

**Decision:** Narrative quality is evaluated through style constraints, repetition metrics, romance pacing, voice distinctiveness, causality, and human/evaluator scenarios rather than model size alone.

**Reason:** Larger models can still produce melodrama, repetition, forced romance, exposition dumps, and generic voices.

**Consequences:** Quality evaluation and trope cooldown data are product features, not optional polish.

**Revisit trigger:** Metrics prove harmful or misaligned with human preference.

---

## 3. Decisions deliberately deferred

These are not permission for arbitrary implementation. They are deferred until the named stage and require a task/ADR before final selection:

| Decision | Deferred until | Current safe assumption |
|---|---|---|
| Exact local text model | Stage 4 | Internal OpenAI-compatible model gateway; benchmark candidates. |
| Exact local serving runtime | Stage 4 | Model gateway supports vLLM/llama.cpp-compatible adapters. |
| Exact image model/workflow | Stage 4 | ComfyUI workflow is versioned and replaceable. |
| Exact object store | Stage 4 | S3-compatible interface; MinIO is likely local default. |
| Temporal deployment details | Stage 4 | Standard activities wrapping application services. |
| Reranker model | Stage 3 evaluation | Embedding retrieval plus deterministic hybrid scoring/MMR. |
| Fine-grained economy model | Stage 3/5 | Aggregate economy only. |
| Resurrection mechanics | World seed/lore | Rare, costly, explicit world rule. |
| Plot-armour defaults | Content configuration | Disabled for outcomes; spotlight bias enabled. |
| Maximum simulated days | Stage 5 configuration | Required field before generation run. |

---

## 4. Terminology misuse to reject during review

Reject or correct these phrases in code and documentation:

- “the character remembers because it is in the chat history”;
- “the world agent updates the database”;
- “the model decided the event is canonical”;
- “character A’s turn contains character B’s reaction”;
- “the vector database is the source of truth”;
- “the LangGraph thread is the character”;
- “the image shows it, so add it to state”;
- “retry the whole day” when only one idempotent task failed;
- “priority model decides reality”;
- “NPC promotion” for lineage succession;
- “HP” in ordinary health logic;
- “user edit” without specifying director, player, or deity command semantics.

Use the precise terms in this document instead.
