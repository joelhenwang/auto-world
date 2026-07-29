# Stage 3 — Autonomous Month and Long-Term Coherence

**Version:** 1.0  
**Stage outcome:** The world runs for thirty autonomous days with long-term perspective memory, vector retrieval, coherent arcs/factions, bounded magic and conflict, injuries and recovery, monthly reflection, anti-repetition controls, quality evaluation, and no manual repair.  
**Primary proof:** `stage3-autonomous-month-v1` thirty-day soak, fault/leakage suite, and human quality review.

---

## 1. Purpose

Stage 3 is the project’s first product-level proof. It must satisfy the user’s initial success criterion:

> A complete autonomous month with convincing personalities, coherent memory, long-running stability, and engaging story-making that does not collapse into melodrama, repetition, or accidental omniscience.

The stage expands depth rather than hardware breadth. It should run on the provider-backed architecture or one local development machine; distributed local serving and image generation are Stage 4.

---

## 2. Required capabilities

- long-term episodic memory and pgvector retrieval;
- embedding versioning, batching, re-embedding, and exact-search baseline;
- optional reranking with deterministic fallback;
- retrieval access controls and source provenance;
- monthly autobiographical chapter and character reflection;
- bounded personality/value evolution supported by accumulated evidence;
- active/dormant arc and hook lifecycle;
- faction and aggregate settlement simulation;
- trope/repetition metrics and cooldowns;
- skill evidence/progression;
- structured Resonance magic;
- nonlethal and lethal-capable combat resolution;
- injuries, conditions, recovery, death rules, and rare-return constraints;
- delayed consequences;
- adaptive quiet-phase skipping within a detailed month, without macro year skips;
- evaluator/critic workflows that diagnose but cannot silently rewrite canon;
- thirty-day consistency, continuity, leakage, and quality reporting;
- exportable month timeline, diaries, encyclopedia, map, model/provenance manifest.

---

## 3. Explicit exclusions

- multiple physical inference hosts as a hard requirement;
- Temporal as a hard dependency;
- ComfyUI/image assets as a completion condition;
- multi-year/month macro time compression;
- births, ageing through decades, genealogy, succession;
- public deployment or untrusted multi-user tenancy;
- arbitrary world-rule mutation by an autonomous Director;
- unbounded combat/dialogue loops;
- perfect deterministic replay across live model calls.

---

## 4. New action/effect capability

### 4.1 Additional action families

```text
ATTACK
DEFEND
CAST_MAGIC
USE_ITEM
TRANSFER
CREATE
CRAFT
RITUAL
PERFORM
```

### 4.2 Additional effects

```text
APPLY_INJURY
UPDATE_INJURY
APPLY_CONDITION
REMOVE_CONDITION
TRANSFER_ITEM
CREATE_ITEM
DESTROY_ITEM
UPDATE_SKILL_EVIDENCE
AWARD_SKILL_PROGRESS
REVEAL_SECRET
UPDATE_FACTION_STATE
UPDATE_FACTION_RELATION
UPDATE_SETTLEMENT_INDICATOR
CREATE_ARC
UPDATE_ARC
CLOSE_ARC
CREATE_HOOK
UPDATE_HOOK
CLOSE_HOOK
MARK_DEATH
RETURN_FROM_DEATH       # privileged, lore-constrained
ALTER_CHARACTER_CARD    # bounded/versioned, evidence-gated
ALTER_WORLD_LORE        # permission-gated proposal/commit
```

`MARK_DEATH`, `RETURN_FROM_DEATH`, foundational card changes, and world-lore changes require high-impact resolution mode, explicit prerequisite validation, and a consistency checkpoint before commit.

---

## 5. Stage work packages

```text
S3-DB-001       Long-term memory/rules/world schema
S3-MEM-001      Embedding pipeline and version registry
S3-MEM-002      Retrieval/reranking/context integration
S3-MEM-003      Monthly chapter/reflection/forgetting
S3-RULES-001    Stats, potential, skills, progression
S3-RULES-002    Magic and mana resolution
S3-RULES-003    Combat, injuries, recovery, death
S3-WORLD-001    Arcs, hooks, factions, aggregate background simulation
S3-WORLD-002    Pacing, novelty, trope and repetition controls
S3-GRAPH-001    Resolver/narrator/evaluator graph expansion
S3-ORCH-001     Thirty-day workflow, delayed effects, monthly barrier
S3-API-001      Long-term history/rules/faction/export API
S3-UI-001       Month explorer, memories, arcs, faction/rule views
S3-QA-001       Thirty-day soak and quality gate
```

---

## 6. Safe parallel lanes

- **Memory lane:** schemas, embedding jobs, retrieval, compaction, leakage tests.
- **Rules lane:** stats/skills/magic/injury pure domain functions and fixtures.
- **World lane:** arcs/factions/background simulation/pacing metrics.
- **Graph lane:** resolver/narrator/evaluator schemas only after rule/effect contracts freeze.
- **Operations lane:** delayed effects, monthly barrier, exports, audit jobs.
- **API/UI lane:** after query projections freeze.
- **QA lane:** month scenario generator, oracle, quality/repetition analysis.

Unsafe parallel work includes separate changes to the effect union, memory access policy, combat formulas, or active-arc state machine. One owner must freeze each contract before dependent agents begin.

---

## 7. Task packets

### S3-DB-001 — Stage 3 persistence

Add or extend:

```text
memory
memory_embedding
embedding_model_version
embedding_job
retrieval_trace
monthly_chapter
reflection_run
character_trait_version
stat_state
stat_potential
skill
skill_state
skill_progress_evidence
spell
known_spell
magic_affinity
item
inventory_entry
condition
injury
recovery_plan
faction
faction_relation
faction_state
settlement_indicator
arc
hook
trope_usage
novelty_signature
evaluator_run
quality_finding
export_run
```

Constraints and source provenance are normative. Do not store opaque “character state” JSON as a substitute for relational rule entities.

### S3-MEM-001 — Embedding pipeline

**Initial provider profile**

```text
model: nvidia/nemotron-3-embed-1b:free
provider: OpenRouter
native vector dimension: capability-probed and migration-configured
application baseline expected by current design: 2048
input prefixes:
  query: "query: "
  passage: "passage: "
```

The application must not assume that the external endpoint remains free, available, or unchanged. On startup/deployment:

1. verify configured model identifier;
2. verify an embedding request and response dimension in a capability probe;
3. reject a dimension mismatch against the active database embedding version;
4. store provider/model/dimension/prefix/truncation version;
5. batch only within provider limits;
6. retry idempotently;
7. leave memories usable through relational retrieval when embeddings are unavailable.

Implement exact pgvector search first. Add HNSW only after a benchmark proves meaningful need and verifies filtered recall.

**Tests**

- dimension mismatch;
- partial batch failure;
- duplicate embedding job;
- provider outage;
- new embedding version and background migration;
- owner/visibility filters applied before results reach caller.

### S3-MEM-002 — Retrieval and context integration

Implement:

```text
request construction
→ mandatory world/owner/time/visibility filters
→ semantic candidate search
→ relational feature enrichment
→ composite score
→ diversity deduplication
→ optional reranker
→ token-budget selection
→ source/provenance trace
```

Default score:

```text
0.35 semantic_similarity
0.20 salience
0.15 goal_relevance
0.10 recency
0.10 entity_overlap
0.05 emotional_resonance
0.05 unresolved_commitment
```

Return approximately eight to twelve memories under a three-to-four-thousand-token budget. A second retrieval pass is allowed only for a referenced entity/event lookup.

Never query across character owners and then filter in prompt code. Mandatory access predicates belong in the repository/query layer.

**Tests**

- seeded secret cannot enter another owner’s candidate set;
- event duplicate diversity;
- old high-salience promise beats recent irrelevant routine;
- no-embedding fallback;
- reranker failure fallback;
- retrieval trace recreates selected source IDs.

### S3-MEM-003 — Monthly chapter, reflection, and forgetting

At month end:

- create a perspective-specific monthly life chapter;
- summarize important relationships, goals, injuries, skills, beliefs, unresolved questions;
- propose bounded trait/value changes;
- validate every change against accumulated evidence and configured maximum movement;
- update autobiographical summary;
- archive resolved commitments;
- decay ordinary retrieval weights without deleting raw memory;
- preserve identity-changing and commitment memories;
- identify trigger links for recoverable older memories.

Personality evolution should normally be subtle. A trait cannot move only because a reflection model says it learned a lesson.

**Tests**

- unsupported trait change rejected;
- multiple source events required;
- reflection contains no unperceived facts;
- raw observations unchanged;
- old trigger memory can be recalled;
- retry/version history.

### S3-RULES-001 — Stats, potential, skills, progression

Implement the `0–100` world scale, dynamic potential, growth rate, derived capability functions, skill evidence, and bounded progression.

Rules:

- attributes do not substitute for skills;
- actions create evidence, not automatic level increases;
- progression considers difficulty, practice quality, teacher, repetition, recovery, personality, and potential;
- temporary conditions/modifiers do not overwrite base values;
- every increase cites evidence events;
- no sudden shounen leap without explicit extraordinary event and high-impact validation.

Property tests must cover bounds, monotonic evidence accumulation, age/species modifiers, and deterministic seeded calculations.

### S3-RULES-002 — Resonance magic

Implement structured spell/technique contracts:

```text
school/elements
prerequisites
mana cost range
cast time
range
target rules
possible effects
failure modes
counters
proficiency
visibility
```

Support only seed-defined and explicitly registered techniques at first. Improvisation becomes a high-uncertainty experiment inside a feasible effect envelope.

The resolver cannot invent arbitrary permanent powers, infinite mana, unknown spells, or world-rule exceptions.

Tests cover mana, prerequisites, interruption, counterplay, partial failure, environmental interaction, and provider-independent resolution.

### S3-RULES-003 — Combat, injuries, recovery, and death

Implement:

- initiative envelope separate from global scene priority;
- attempts and bounded reactions;
- capability, skill, equipment, preparation, terrain, teamwork, morale, injury, and seeded randomness;
- feasible outcome envelope;
- typed injury/condition effects;
- consciousness/life status;
- treatment and recovery progression;
- permanent consequence possibility;
- death prerequisites and high-impact audit;
- lore-constrained return-from-death path.

No HP is introduced.

Hard tests:

- weaker prepared character may win within a causal envelope;
- impossible outcome rejected;
- reactor cannot retroactively prepare;
- severe injury affects later action;
- recovery is not instant;
- duplicate resolution cannot apply injury twice;
- zero mana/stamina constraints;
- death/return cannot occur through ordinary conversation schema.

### S3-WORLD-001 — Arcs, factions, and background simulation

Implement:

- one active major arc slot;
- up to two active secondary hooks;
- dormant hooks;
- arc prerequisites, milestones, deadlines, participants, closure conditions;
- faction goals, resources, leadership, territory, plans, relations;
- aggregate settlement indicators;
- daily/weekly low-resolution background updates;
- causal event promotion when background changes affect focus characters;
- explicit plot-armour configuration (default outcome bias `0`).

The Director proposes opportunities and arc changes. Deterministic/background services and resolver apply valid state changes.

### S3-WORLD-002 — Pacing and anti-repetition

Track rolling metrics for:

- event/scene embeddings or normalized signatures;
- trope tags;
- location repetition;
- participant combinations;
- action families;
- emotional curve;
- antagonist and hook reuse;
- phases since meaningful choice;
- romance progression evidence;
- quiet/dramatic balance.

Implement configurable cooldowns for common anime/fantasy clichés. A cooldown reduces proposal score; it is not a hard ban when causality genuinely requires recurrence.

The Director should prefer invitations, information, discoveries, social obligations, consequences, and quiet character choices before arbitrary attacks.

### S3-GRAPH-001 — Graph expansion

Add or extend:

- high-impact semantic validator;
- hybrid SceneResolutionGraph with deterministic envelope;
- NarrationGraph that cannot alter effects;
- memory retrieval step in CharacterDecisionGraph;
- MonthlyReflectionGraph;
- quality/evaluator graph;
- arc/faction proposal schemas;
- combat/magic task-specific effect unions.

Evaluator findings are diagnostics. A critic may request at most one narration regeneration before publication; it cannot rewrite the canonical event or loop indefinitely.

### S3-ORCH-001 — Thirty-day workflow

Implement:

- scheduled/delayed effects across days;
- daily/weekly faction and background tasks;
- embedding/retrieval maintenance;
- monthly barrier and reflection;
- thirty-day run/stop condition;
- optional quiet-phase deterministic skipping;
- persistent progress/cost/request metrics;
- audit and recovery snapshots;
- quarantine for repeatedly failing optional derived tasks;
- export after successful gate.

Canonical phase completion still depends on effects/observations/immediate memories and durable outbox, not image or embedding completion.

### S3-API-001 — Stage 3 API

Add:

- long-term memories and retrieval trace (authorized/debug);
- monthly chapter/reflection;
- stats, skills, magic, injuries, conditions, inventory;
- factions, arcs, hooks, pacing metrics;
- delayed/scheduled effects;
- quality findings;
- month run/progress;
- export creation/status/download metadata;
- deity/high-impact commands with explicit warnings and audit.

### S3-UI-001 — Month experience

Add:

- month calendar and phase/day navigation;
- memory timeline with source/provenance;
- character skill/magic/injury/condition panels;
- arc/hook tracker;
- faction map overlays and settlement indicators;
- trope/quality diagnostic dashboard in debug/director mode;
- monthly chapter and reflection diff;
- high-impact deity command confirmation;
- export controls.

### S3-QA-001 — Thirty-day gate

Build:

- deterministic fake-model month with seeded event variants;
- live-provider representative run or selected days under quota constraints;
- invariant oracle over every event/effect/projection;
- memory recall and secret leakage benchmark;
- relationship/personality drift analysis;
- repetition/trope report;
- combat/magic/injury scenario matrix;
- provider outage and embedding backlog test;
- process/database/outbox fault matrix;
- human story-quality review;
- export verification.

---

## 8. Thirty-day quality targets

### Hard integrity targets

- zero hard invariant violations;
- zero unauthorized secret leakage in deterministic adversarial suite;
- zero duplicate canonical effects;
- zero source-less projection changes;
- zero unresolved phase/day/month runs;
- zero image/embedding dependency blocking canon;
- all deaths/injuries/high-impact changes have valid prerequisites and provenance.

### Model and memory targets

- at least 95% valid structured output after one repair/regeneration path in measured sample;
- at least 90% recall of seeded important promises, discoveries, and relationships in benchmark prompts;
- no more than one unsupported claimed recollection per one hundred evaluated factual memory questions;
- retrieval access control passes 100% of adversarial fixtures;
- monthly trait changes all have sufficient source evidence.

### Story targets

Human review should find:

- distinct focus-character voices;
- believable quiet periods;
- no automatic romance;
- no repeated arbitrary disaster loop;
- at least one coherent minor/secondary arc with closure or clear progression;
- consequences that persist;
- NPCs that contribute without replacing protagonists;
- dialogue that avoids exposition dumps and constant one-liners.

---

## 9. Hard exit gate

- thirty days complete without manual database editing;
- all Stage 0–2 gates remain green;
- long-term retrieval is perspective-safe, versioned, traceable, and optional during provider outage;
- at least one old important memory meaningfully influences a later decision;
- at least one false/uncertain belief changes through evidence without rewriting history;
- one arc progresses causally and one hook closes or expires;
- faction/background changes occur without full NPC simulation;
- magic and conflict obey deterministic feasibility envelopes;
- injury/recovery affects subsequent behavior;
- monthly reflection produces only evidence-supported bounded changes;
- repetition metrics and cooldowns prevent obvious recurring templates in deterministic corpus;
- evaluator cannot mutate canon or create regeneration loops;
- thirty-day fault/soak suite passes;
- month export can reconstruct timeline, character perspectives, diaries, map/encyclopedia, and provenance;
- architecture, migration, security, privacy, type, lint, and test gates pass.

---

## 10. Handoff to Stage 4

Freeze and archive:

- thirty-day fixture database, event stream, export, and quality report;
- memory/embedding/retrieval contract v1;
- rule/effect union v1 for magic/combat/injuries;
- arc/faction/background state machines;
- monthly reflection constraints;
- provider-neutral model and orchestration interfaces;
- measured request/token/latency workload per role;
- representative text prompts/outputs for local model benchmarking.

Stage 4 may change where inference and orchestration run, but it must not change canonical semantics merely to accommodate hardware.
