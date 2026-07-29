# Stage 2 — Coherent Seven-Day World

**Version:** 1.0  
**Stage outcome:** All four focus characters complete seven autonomous days across the full ten-phase calendar with perspective-correct beliefs, relationships, plans, travel, a triggered Narrative Director, one or more bounded temporary NPCs, daily consolidation, diaries, and restart-safe orchestration.  
**Primary proof:** `stage2-seven-day-world-v1` deterministic scenario suite plus one sampled live-provider run.

---

## 1. Purpose

Stage 2 expands the first-day vertical slice into a small but genuinely living world. It is the first stage in which the system must demonstrate continuity across several days rather than merely complete one bounded interaction.

The central engineering question is:

> Can four agents develop distinct, causally consistent lives for a week without leaking knowledge, losing commitments, duplicating events, or requiring manual repair?

Stage 2 should still favor simplicity over spectacle. Combat, deep magic, long-term vector retrieval, generation succession, distributed inference, and generated images remain outside the hard stage scope.

---

## 2. Active content profile

### 2.1 Focus characters

- Mira Talren — main;
- Dain Arcen — main;
- Iri Voss — sub-main;
- Torren Kest — sub-main.

### 2.2 Calendar

All ten phases are enabled:

```text
dawn
sunrise
morning
noon
afternoon
sunset
dusk
evening
night
midnight
```

A character does not require a model call merely because a phase exists. Deterministic activation rules may select `SLEEP`, `CONTINUE_ACTIVITY`, or no full inference when no decision exists.

### 2.3 Initial geography

Use the seed region and locations from `23_INITIAL_WORLD_SEED_AND_CONTENT_AUTHORING.md`, with at least:

- Cinder Lantern Inn;
- Market Square;
- East Bridge;
- Archive Annex;
- Lantern Ward;
- North Road;
- Ash Orchard.

### 2.4 Narrative scope

The Director may introduce:

- one minor seven-day hook;
- up to two dormant hooks;
- one or two temporary named NPCs;
- environmental or social opportunities;
- a low-stakes mystery, obligation, discovery, or journey.

The Director must not introduce a generation-defining arc, apocalyptic threat, major war, irreversible world-rule change, or mandatory romance.

---

## 3. Required capabilities

- all four focus characters active under one reusable CharacterDecisionGraph;
- full ten-phase calendar and sleep/routine activation suppression;
- multi-phase activities and route-based travel;
- scene assembly for two to four focus characters plus bounded NPCs;
- claims, beliefs, secrets, and confidence updates;
- directional relationship state and source evidence;
- goals, plans, commitments, and plan revision;
- Director trigger and proposal workflow;
- NPC registry, deduplication, compact cards, actor context, and TTL;
- perspective-safe perception generation for witnesses and absent characters;
- end-of-day memory consolidation and perspective diaries;
- day-level consistency audit and recovery checkpoint;
- timeline, map, character, beliefs, relationships, and diary UI projections;
- seven-day deterministic soak with provider-independent fake scripts;
- sampled OpenRouter execution without making provider uptime a gate.

---

## 4. Explicit exclusions

- vector memory affecting decisions;
- monthly reflection and personality evolution;
- full faction simulation or economy;
- lethal combat;
- advanced magic resolution;
- permanent severe injuries;
- autonomous pregnancy, births, ageing, or succession;
- Temporal as a required orchestrator;
- multi-host model serving;
- ComfyUI and generated images;
- public multi-user deployment.

A simple nonlethal conflict or harmless Resonance use may be represented if it remains within Stage 2 effect semantics.

---

## 5. Allowed action and effect scope

### 5.1 Action families

```text
WAIT
CONTINUE_ACTIVITY
MOVE
OBSERVE
COMMUNICATE
SOCIALIZE
PERSUADE
DECEIVE
INVESTIGATE
REST
TRAIN
WORK
CARE
INTERACT_ENVIRONMENT
CAST_MAGIC       # low-impact, predeclared techniques only
OTHER            # strict semantic review, no new effect type
```

### 5.2 Typed effects

```text
MOVE_ENTITY
SPEND_STAMINA
RECOVER_STAMINA
SPEND_MANA
RECOVER_MANA
ADVANCE_ACTIVITY
START_ACTIVITY
INTERRUPT_ACTIVITY
CREATE_CLAIM
UPDATE_BELIEF_EVIDENCE
UPDATE_RELATIONSHIP_EVIDENCE
CREATE_COMMITMENT
UPDATE_COMMITMENT
UPDATE_GOAL
UPDATE_PLAN
CREATE_OBSERVATION
CREATE_RECENT_MEMORY
REGISTER_NPC
ARCHIVE_NPC
SCHEDULE_EFFECT
CREATE_LORE_PROPOSAL
CREATE_LOCATION_PROPOSAL
SKILL_PROGRESS_EVIDENCE
```

No effect may directly change a foundational character trait, kill an entity, create a severe injury, transfer unique property, or rewrite world rules.

---

## 6. Task dependency graph

```text
S2-DB-001      Stage 2 persistence extensions
S2-CHAR-001    Goals, plans, commitments, relationship evidence
S2-KNOW-001    Claims, beliefs, secrets, observation engine v2
S2-MEM-001     Daily consolidation and diary pipeline
S2-WORLD-001   Director trigger/proposal/validation
S2-WORLD-002   NPC registry, actor workflow, TTL/archival
S2-SIM-001     Ten phases, activation, sleep, activities, travel
S2-SIM-002     Multi-party scene assembly and bounded dialogue
S2-GRAPH-001   Stage 2 graph integrations and schemas
S2-ORCH-001    Seven-day workflow, day barrier, recovery checkpoint
S2-API-001     Expanded query/command/WebSocket API
S2-UI-001      Map, diary, relationship, belief, task views
S2-QA-001      Seven-day scenario, leakage/fault/continuity gate
```

High-level dependencies:

```text
DB ─┬─> CHAR ─┐
    ├─> KNOW ─┼─> GRAPH/SIM ─> ORCH ─> API/UI ─> QA
    ├─> MEM  ─┤
    └─> WORLD ┘

SIM travel/location contracts must freeze before map API/UI.
KNOW access rules must freeze before NPC actor context.
MEM consolidation depends on observations, claims, beliefs, and source links.
```

---

## 7. Safe parallel lanes

### Lane A — Persistence and migrations

Own only Stage 2 tables, constraints, repositories, DTO mappings, and migration fixtures.

### Lane B — Character state

Own goals, plan steps, commitments, relationship evidence/aggregation, and associated pure domain services.

### Lane C — Knowledge and memory

Own claims, beliefs, observation derivation, access-control tests, daily consolidation, and diaries.

### Lane D — World and NPCs

Own Director trigger/proposal logic, hook state, NPC registry/deduplication, compact cards, NPC actor graph, and lifecycle.

### Lane E — Simulation

Own phase activation, sleep, multi-phase activity, routes/travel, scene grouping, beat budgets, and conflict read/write sets.

### Lane F — Model/graph corpus

Own task schemas, prompts, fake-model scripts, graph nodes, and provider capability tests after contracts freeze.

### Lane G — API/UI

Own OpenAPI projections, generated client, map and character views only after domain query DTOs freeze.

### Lane H — QA

Own seven-day fixtures, invariant oracle, leakage corpus, process-fault harness, and human review worksheet.

The parent agent integrates contracts in this order:

```text
DB schema
→ knowledge/character domain services
→ travel/activation/scene contracts
→ Director/NPC contracts
→ prompts/graphs
→ orchestration
→ API/UI
→ QA evidence
```

---

## 8. Task packets

### S2-DB-001 — Persistence extensions

**Deliverables**

Add and migrate:

```text
goal
plan
plan_step
commitment
relationship_edge
relationship_evidence
claim
belief
belief_evidence
secret_access
activity
activity_participant
travel_progress
route
hook
narrative_metric
npc_profile
npc_lifecycle
summary
summary_source
diary_entry
day_run
daily_audit
```

Extend existing action/scene/event tables for:

- multiple participants;
- observer eligibility metadata;
- Director/NPC provenance;
- delayed/scheduled effects;
- multi-phase continuation IDs;
- source links for belief/relationship changes.

**Constraints**

- one relationship edge per `(source, target)`;
- every relationship aggregate has one or more evidence rows unless seed-created;
- belief confidence is within `[0, 1]`;
- claims never use the objective-fact table as their storage type;
- one active primary plan per goal unless the goal explicitly allows alternatives;
- no active travel activity without a valid route;
- one active NPC registry row per canonical entity;
- every diary/source summary row references only observations available to the owner;
- archived NPCs cannot receive ordinary actor tasks.

**Tests**

- upgrade from Stage 1 database and rollback in disposable environment;
- foreign-key and uniqueness tests;
- belief/relationship source provenance;
- route and activity transition constraints;
- migration fixture checksum.

### S2-CHAR-001 — Goals, plans, commitments, and relationships

**Deliverables**

Implement pure services for:

- goal creation, priority, activation, completion, abandonment;
- plan creation/revision and step status;
- commitments/promises with debtor, beneficiary, due condition, status;
- directional relationship evidence and bounded aggregation;
- goal relevance and commitment relevance for context assembly;
- action-to-progress evidence;
- relationship cooldowns to avoid a single scene causing extreme changes.

**Rules**

- the model proposes evidence; the resolver applies bounded changes;
- relationship dimensions remain directional;
- attraction is not inferred from generic kindness;
- trust cannot jump by more than a configured normal-scene delta;
- plan revision may occur after any relevant event;
- personality/values are not modified in Stage 2.

**Tests**

- asymmetric relationships;
- repeated positive evidence with diminishing effect;
- betrayal evidence and confidence;
- promise reminder/retrieval;
- plan invalidation after location/resource change;
- no unsupported relationship update.

### S2-KNOW-001 — Claims, beliefs, secrets, and observation engine v2

**Deliverables**

Implement:

```text
canonical event
  → allowed observable fact keys
  → observer eligibility
  → observer-specific observation
  → claim exposure
  → belief evidence
  → confidence update
```

Support:

- direct witness;
- hearing-only observation;
- partial/ambiguous observation;
- absent character with no observation;
- one character lying to another;
- rumour transmission as a new sourced claim;
- secret access policy;
- knowledge lookup tool restricted by observer;
- omission of Director omniscient data from actor context.

**Tests**

- seeded secret visible to Mira but not Dain/Iri/Torren;
- lie produces claim, not fact;
- two witnesses get different observations;
- NPC actor receives only NPC knowledge;
- user/player projection follows controlled-character access;
- prompt injection stored in an observation cannot escalate authority.

### S2-MEM-001 — Daily consolidation and diaries

**Deliverables**

At day completion:

1. collect each character’s observations and immediate memories;
2. group by event/scene/entity/time while preserving source IDs;
3. compute/update salience;
4. generate or deterministically assemble a daily perspective summary;
5. extract stable belief/relationship/goal evidence;
6. mark routine duplicate memories as compacted;
7. write a UI retrospective diary;
8. create a daily memory audit record;
9. retain raw observations unchanged.

Use fake-model consolidation in deterministic tests. A live model may improve prose but cannot introduce unsupported fact IDs.

**Tests**

- source completeness;
- perspective filtering;
- diary has no absent secrets;
- failed model summary falls back to extractive summary;
- retry does not duplicate summaries;
- routine observations compact without deleting raw records.

### S2-WORLD-001 — Narrative Director v1

**Deliverables**

Implement deterministic trigger metrics:

- phases since meaningful choice;
- repeated location/participant/action pattern;
- goal progress stagnation;
- unresolved hook count;
- emotional-intensity trend;
- recent disruptive-event cooldown.

When triggered, run DirectorProposalGraph with:

- world snapshot;
- public and private canonical state as omniscient input;
- explicit protected secrets;
- active/dormant hooks;
- pacing and trope metrics;
- permissions profile;
- restricted proposal schema.

Validate proposal prerequisites and effect capability. Commit only through the normal resolver.

**Tests**

- no call during healthy progression;
- trigger during controlled stagnation fixture;
- proposal cannot reveal secret without disclosure path;
- no mandatory romance or guaranteed outcome;
- cooldown blocks repeated disruptions;
- safe no-event fallback.

### S2-WORLD-002 — NPC registry and actor v1

**Deliverables**

Implement:

- Director-only NPC proposal;
- similarity/dedup search over names, location, role, traits, and source hook;
- active NPC budgets;
- compact card and knowledge package;
- batch actor workflow for several NPCs in one scene;
- TTL and relevance extension;
- archive with compact legacy summary;
- archived NPC lookup for continuity;
- no promotion into focus slots.

**Default budgets**

- six individually represented NPCs in one scene;
- twenty-four active detailed NPCs in active region;
- three new named NPCs per ordinary day;
- no full off-screen inference for temporary NPCs.

**Tests**

- duplicate blacksmith proposal resolves to existing NPC;
- NPC cannot use Director-only knowledge;
- TTL extension after meaningful scene;
- archive after irrelevance;
- archived NPC can be recalled without actor scheduling.

### S2-SIM-001 — Calendar, activation, activities, and travel

**Deliverables**

- all ten phase transitions;
- sleep schedule and interruption rules;
- deterministic skip/continue decisions;
- `Activity` state machine;
- route-based travel distance/progress;
- weather/route modifiers using stored random seed;
- interruption and arrival events;
- no real-time catch-up while application is stopped;
- maximum task request estimation before each phase.

**Tests**

- full day phase sequence;
- sleeping actor skipped unless event wakes them;
- travel continues without unnecessary LLM call;
- meeting on intersecting routes;
- route invalidation interrupts safely;
- restart preserves progress exactly.

### S2-SIM-002 — Multi-party scenes and bounded dialogue

**Deliverables**

- scene assembly for up to four focus characters and bounded NPC participants;
- merge compatible intents and conflicting resource/location intents;
- stable global priority and intra-scene initiative distinction;
- dialogue/negotiation/group beat budgets;
- continuation to next phase when budget expires;
- independent-scene conflict detection through read/write sets;
- no actor-authored hidden reaction.

**Default beat budgets**

| Scene type | Budget |
|---|---:|
| Two-person conversation | 2 exchange rounds |
| Group conversation | 6 total character beats |
| Negotiation | 1 proposal + 1 response per participant |
| Nonlethal conflict | 3 attempt/reaction exchanges |
| Background NPC response | 1 compact group beat |

**Tests**

- four-character social scene;
- two independent scenes run concurrently;
- same-item conflict is merged/serialized;
- conversation continues next phase rather than looping;
- NPC group batch respects per-NPC knowledge.

### S2-GRAPH-001 — Graph and output contracts v2

**Deliverables**

Extend or add:

- CharacterDecisionGraph with goals/plans/claims;
- CharacterReactionGraph for multi-party scenes;
- NPCSceneGraph;
- DirectorProposalGraph;
- MemoryConsolidationGraph;
- semantic validation graph/path;
- task-specific restricted effect schema generation.

All graphs remain bounded, provider-neutral, checkpointable, and deterministic under fake adapters.

**Tests**

- every graph node pure or effect-isolated;
- malformed/unsupported output repair path;
- task capability schema excludes unrelated effects;
- provider outage/fallback;
- no graph directly commits domain state.

### S2-ORCH-001 — Seven-day workflow

**Deliverables**

- day workflow over ten phases;
- reservation of provider requests needed for a safely finishable phase;
- Director conditional task;
- four character decision fan-out/fan-in;
- scene/NPC/reaction task graph;
- day-finalization barrier;
- daily summary/diary/audit tasks;
- daily recovery snapshot;
- pause at phase/day boundaries;
- reconciler for abandoned tasks;
- seven-day run command and progress projection.

**Tests**

- restart at every task boundary;
- provider shortfall before phase and mid-request failure;
- failed diary never leaves day ambiguous;
- duplicate day-finalization delivery;
- pause/resume after day three;
- no fictional time advancement while stopped.

### S2-API-001 — API expansion

**Deliverables**

Queries:

- world clock/day progress;
- map and route state;
- character current state, goals, plans, commitments;
- perspective-filtered beliefs and known encyclopedia;
- directional relationships;
- NPC list/detail/lifecycle;
- daily summaries/diaries;
- Director hooks/metrics in watcher/director mode;
- task/failure diagnostics.

Commands:

- advance phase/day;
- run until day/condition;
- pause/resume;
- propose Director event;
- player action;
- archive/retain NPC with privilege check;
- edit goal/plan through explicit user command where allowed.

Stream events include stable sequence and projection versions.

### S2-UI-001 — Seven-day observer UI

**Deliverables**

- ten-phase day strip and run progress;
- timeline filters by character, location, scene, hook;
- character goals/plans/commitments and directional relationship view;
- belief/claim provenance drawer;
- daily diary and summary views;
- map nodes/routes/current travel;
- NPC lifecycle view;
- Director metrics/hooks for authorized modes;
- provider budget/status and fallback indication;
- reconnect/resync handling.

Player mode must not expose watcher-only beliefs, secrets, or Director plans.

### S2-QA-001 — Stage gate and evidence

**Deliverables**

- deterministic seven-day seed run;
- multiple fake narrative scripts (quiet, mystery, social conflict, travel);
- 100+ perspective/leakage assertions;
- process termination matrix;
- idempotency/duplicate-delivery suite;
- human story review worksheet;
- live-provider sample report;
- database/event/provenance audit;
- performance/request-count report.

---

## 9. Canonical seven-day flow

For each day:

```text
for phase in ten_phases:
    apply eligible user commands
    advance clock
    execute deterministic world tick
    evaluate scheduled effects
    calculate Director trigger
    optionally propose/validate/commit world event
    seal one phase snapshot
    determine active decisions
    generate primary intents from that snapshot
    assemble scenes
    obtain bounded participant reactions
    resolve and atomically commit scenes
    derive observations, claims, beliefs, relationships, plans, memories
    enqueue derived work
    finalize phase

finalize_day:
    consolidate each character's perspective memory
    generate perspective diary/fallback
    update narrative/trope metrics
    run consistency audit
    write recovery snapshot
    mark day complete
```

Images and vector embeddings are not dependencies.

---

## 10. Hard exit gate

Stage 2 is complete only when all conditions hold:

### 10.1 Simulation integrity

- seven full days and all ten phases complete without manual database repair;
- all active primary intents within one phase reference the same sealed snapshot;
- skipped characters have deterministic skip reasons;
- multi-phase travel/activity resumes correctly after restart;
- no character occupies two primary scenes at once;
- all effects remain typed, validated, sourced, and idempotent;
- day and phase state machines have no illegal transitions.

### 10.2 Knowledge integrity

- no seeded private secret appears in an unauthorized context, observation, diary, API DTO, log, or NPC prompt;
- lies remain claims rather than objective facts;
- beliefs keep confidence and provenance;
- two observers may retain different accounts without forced reconciliation;
- every daily summary/diary fact is source-backed and perspective-allowed.

### 10.3 Character continuity

- all four characters maintain distinguishable speech/behavior in human review;
- goals/plans influence actions and update after evidence;
- commitments can be remembered and acted upon;
- relationship movement is directional, bounded, and source-supported;
- characters can refuse, rest, wait, and abandon a plan;
- no automatic romance from generic social contact.

### 10.4 Director/NPC integrity

- Director calls occur only when triggered or explicitly commanded;
- Director does not choose scene outcomes;
- at least one temporary NPC is created, used, and archived or retained coherently;
- NPC context excludes omniscient Director knowledge;
- active NPC budgets and deduplication hold.

### 10.5 Reliability and operations

- process termination/restart at every major boundary yields no duplicate canonical effects;
- provider outage degrades safely;
- quota is checked/reserved before unsafe partial work;
- failed optional prose work cannot leave canonical day incomplete;
- daily audit reports zero hard invariant violations;
- previous Stage 0 and Stage 1 gates remain green;
- lint, formatting, type, migration, security, and architecture checks pass.

---

## 11. Human review rubric

Review at least three complete fake-model weeks and one sampled live week or representative live subset.

Rate `1–5`:

- character voice separation;
- causal continuity;
- memory/commitment recall;
- believable quiet time;
- proportionate emotional reactions;
- non-cringe dialogue;
- Director restraint;
- NPC usefulness;
- relationship pacing;
- absence of accidental omniscience;
- scene/trope repetition;
- story engagement.

Any average below `3`, or any leakage/invariant failure, blocks promotion.

---

## 12. Handoff to Stage 3

Freeze and version:

- claims/beliefs/relationships/goals/plans contracts;
- observer-access policy v2;
- daily consolidation/source model;
- Director trigger/proposal v1;
- NPC registry/lifecycle v1;
- activity/travel and full-calendar semantics;
- seven-day fixture database and event bundle;
- Stage 2 prompt/model corpus and quality report.

Stage 3 may add long-term vector retrieval, magic/combat/injuries, factions/arcs, monthly reflection, and stronger evaluation without changing the foundational event/observation separation.
