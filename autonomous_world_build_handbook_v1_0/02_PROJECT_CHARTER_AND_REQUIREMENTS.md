# Project Charter and Requirements

**Version:** 1.0  
**Status:** Normative product contract  
**Product:** Autonomous Fictional World  
**Primary user:** One local user  
**Initial language:** English  
**Content target:** Young-adult, soft-dark anime-inspired fantasy

---

## 1. Product statement

Build a persistent, self-evolving fictional world that can be watched autonomously or influenced interactively. The world combines anime-fantasy genres such as isekai, adventure, romance, shounen, slice of life, mystery, politics, and restrained dark fantasy.

The product must behave as a coherent world rather than a sequence of disconnected model completions. Characters possess independent identities, limited knowledge, goals, relationships, capabilities, memories, and life histories. The world changes through deterministic systems and model-proposed narrative opportunities. The user can observe, direct, override, or temporarily inhabit one character.

The long-term maximum scope is three family generations in one canonical world and one active timeline.

---

## 2. Product principles

### PRN-001 — Coherence over spectacle

A less dramatic event that follows causally from the world is better than an impressive contradiction.

### PRN-002 — Agency over forced plot

Characters may reject quests, relationships, expectations, and director proposals. The story adapts to consequences rather than forcing compliance.

### PRN-003 — Simulation truth, narrative presentation

Structured simulation determines facts and outcomes. Narrative systems determine opportunities, framing, pacing, and prose.

### PRN-004 — Perspective is real

Characters may be mistaken, deceived, unaware, biased, forgetful, or uncertain. They must not become accidental omniscient narrators.

### PRN-005 — Quiet life is part of the world

Not every phase requires a dramatic event. Routine, travel, recovery, work, relationships, and uneventful time make important scenes meaningful.

### PRN-006 — Explicit user power

User intervention is represented as a role with defined privileges. Hidden manual database edits are not an acceptable interaction model.

### PRN-007 — Local-first evolution

Early stages use OpenRouter free models for speed of development. The architecture must later replace remote inference with local model servers without changing character identity or canonical data.

### PRN-008 — Inspectability

The user and developer must be able to trace why a state changed, which event caused it, what each character perceived, which model and prompt were used, and whether a retry occurred.

---

## 3. Target experience

The central experience is a living visual-novel timeline:

1. The world advances through named day phases.
2. The deterministic world tick updates time-dependent systems.
3. The director may introduce or advance a justified opportunity or arc.
4. Active characters independently choose actions from their current perspective.
5. Compatible and conflicting actions become scenes.
6. Reactions and outcomes are resolved within rules.
7. The result is committed to canon.
8. Each character perceives and remembers only what they could know.
9. Salient committed scenes enter an asynchronous image queue.
10. The user watches the timeline, opens diaries and encyclopedia entries, examines the map, or intervenes through a selected role.

The first major product proof is one autonomous fictional month with convincing personalities, coherent memory, long-running stability, and engaging story generation that avoids repetitive or melodramatic behaviour.

---

## 4. User roles and permissions

The user can switch roles on demand at a safe phase or scene boundary. The active role is stored in canonical operational state and included in the audit log.

### ROLE-001 — Watcher

The Watcher is read-only.

Capabilities:

- view the canonical event timeline;
- see omniscient world state, secrets, director state, and all character perspectives;
- inspect model calls, context sources, effect provenance, and debug traces when debug mode is enabled;
- pause or resume automatic simulation only if operational controls are separately granted.

The Watcher does not create fictional effects.

### ROLE-002 — Director

The Director influences the story while respecting ordinary rules.

Capabilities:

- propose events, hooks, arcs, genre pressure, tone adjustments, NPCs, locations, or faction developments;
- prioritize a narrative topic or character without forcing an outcome;
- request that the system explore a theme;
- schedule a proposal for a future phase.

Director input passes through the same validation, prerequisite, resolution, and commit rules as model-generated director proposals.

### ROLE-003 — Deity

The Deity has explicit authoritative override privileges.

Capabilities are individually configurable and may include:

- create, alter, or remove entities;
- set or adjust stats, conditions, relationships, resources, world rules, map state, or memories;
- force an event or outcome;
- resurrect or transform a character;
- perform a hard retcon;
- change director privileges;
- alter end conditions.

Every deity action becomes a typed, auditable `USER_OVERRIDE` or `DIVINE_EVENT`. A hard retcon marks dependent later projections as potentially inconsistent and triggers a consistency audit. It does not silently rewrite all consequences.

### ROLE-004 — Player

The Player controls one selected persistent character’s primary action selection.

Capabilities:

- receive the selected character’s limited perception, known state, inventory, goals, and available actions;
- submit an action attempt and optional dialogue;
- choose from suggested actions or enter free-form intent;
- switch controlled character at a safe boundary.

Restrictions:

- the Player does not receive omniscient information while the limited-perspective view is active;
- the Player controls attempts, not outcomes;
- the Player cannot declare inaccessible knowledge or impossible effects as fact;
- deity privileges are not implied by player control.

The system cannot make the human forget information previously seen in Watcher mode. It can only filter subsequent presentation.

---

## 5. Operating modes

### MODE-001 — Automatic

The orchestrator advances phases without user approval until:

- paused;
- an end condition occurs;
- a fatal operational error requires intervention;
- a configured human-approval boundary is reached;
- provider quota makes safe phase completion impossible and no fallback exists.

### MODE-002 — Manual phase stepping

The user starts the next phase explicitly. The phase then runs to its safe completion boundary.

### MODE-003 — Debug stepping

Development-only mode may pause at selected state-machine transitions such as snapshot sealing, intent completion, scene assembly, pre-commit, or post-observation.

### MODE-004 — Macro simulation

Introduced in Stage 5. The user allows quiet days, weeks, months, or years to be summarized while high-salience events automatically return the world to detailed simulation.

---

## 6. Functional requirements

### World and time

**FR-WORLD-001** The system shall maintain exactly one canonical world and one active timeline in the initial product.

**FR-WORLD-002** The detailed calendar shall contain ten ordered phases: dawn, sunrise, morning, noon, afternoon, sunset, dusk, evening, night, and midnight.

**FR-WORLD-003** Every detailed phase shall begin with a deterministic World Engine tick.

**FR-WORLD-004** Fictional time shall pause while the service is stopped unless an explicit macro-simulation command advances it.

**FR-WORLD-005** The system shall support persistent activities spanning phases, including travel, rest, training, work, crafting, recovery, and rituals.

**FR-WORLD-006** Persistent activities shall define interruption conditions.

**FR-WORLD-007** Travel shall use map routes, distance-based duration, travel modes, terrain and weather modifiers, and optional random encounters.

**FR-WORLD-008** The system shall support quiet phases in which a character continues an activity, waits, sleeps, or performs no model-worthy decision.

**FR-WORLD-009** A phase shall be complete when all expected character/scene work is resolved, canonical events and observations are committed, immediate memories are written, and image work is durably enqueued.

**FR-WORLD-010** Image completion shall not be required for phase completion.

### Characters

**FR-CHAR-001** The initial persistent cast shall support two main and two sub-main focus slots, introduced incrementally by stage.

**FR-CHAR-002** Every persistent character shall have a versioned character card containing identity, backstory, appearance, personality, values, fears, desires, behavioural boundaries, voice, goals, secrets, relationships, capabilities, and initial knowledge.

**FR-CHAR-003** Every character shall have separate dynamic state, including location, life status, injuries, stamina, mana, emotions, needs, goals, plans, relationships, knowledge, and memory.

**FR-CHAR-004** A character card shall not be used as an ever-growing memory transcript.

**FR-CHAR-005** Character personalities, goals, beliefs, relationships, appearance, and capabilities may evolve through sourced events and versioned changes.

**FR-CHAR-006** Foundational history shall not be silently overwritten. Retcons shall remain explicit.

**FR-CHAR-007** Characters may hold false or uncertain beliefs, lie, conceal information, detect inconsistencies, misremember, forget, or reinterpret events.

**FR-CHAR-008** Relationships shall be directional and may differ between the two parties.

**FR-CHAR-009** Characters shall be able to create and revise multi-phase plans.

**FR-CHAR-010** Identity-level reflection shall normally occur monthly and after exceptional transformative events, while tactical plan revision may happen immediately.

**FR-CHAR-011** Characters may age, change appearance, become disabled, marry, have children, transform, and die.

**FR-CHAR-012** Death shall normally be treated as permanent. Return mechanisms shall require explicit lore, rare prerequisites, and meaningful cost.

### Actions, scenes, and outcomes

**FR-SCENE-001** All primary character intents in one phase shall be generated from the same sealed phase snapshot.

**FR-SCENE-002** Characters may freely invent an action description while selecting a stable action family and structured desired effects.

**FR-SCENE-003** One primary action proposal shall be generated per eligible persistent character per phase.

**FR-SCENE-004** A character may select `WAIT`, `REST`, `OBSERVE`, or `CONTINUE_ACTIVITY` when no meaningful new action is justified.

**FR-SCENE-005** A scene assembler shall group actions through shared targets, locations, resources, routes, appointments, events, or causal conflict.

**FR-SCENE-006** A character shall not determine another character’s hidden intention or successful reaction.

**FR-SCENE-007** Eligible participants shall receive bounded opportunities to react to observable attempts.

**FR-SCENE-008** Dialogue, negotiation, and combat loops shall have hard beat budgets and continuation rules.

**FR-SCENE-009** Outcome resolution shall support success, partial success, failure, interruption, and invalidation.

**FR-SCENE-010** Models shall not directly mutate canonical state.

**FR-SCENE-011** Every state-affecting outcome shall be translated into typed effect commands and validated against current state.

**FR-SCENE-012** Structured state changes shall be committed before prose narration is generated or published as a presentation of canon. The prose itself is noncanonical.

**FR-SCENE-013** An invalid model action shall follow a bounded repair, regeneration, fallback, and safe-wait ladder.

**FR-SCENE-014** The system shall preserve causal reactions inside a scene without giving later global characters knowledge of earlier separately resolved scenes from the same snapshot.

### World Engine and Narrative Director

**FR-DIR-001** The world shall be represented by a deterministic World Engine and a separate model-driven Narrative Director.

**FR-DIR-002** The World Engine shall own time, travel progress, recovery, scheduled effects, weather, resource regeneration, world-end checks, and other deterministic systems.

**FR-DIR-003** The Director shall propose events, arcs, hooks, NPCs, locations, pacing adjustments, mysteries, social opportunities, faction developments, and thematic direction.

**FR-DIR-004** The Director shall be omniscient but shall not expose private information without a valid causal disclosure path.

**FR-DIR-005** The Director shall not act every phase by default. It shall respond to triggers such as stagnation, scheduled hooks, arc timing, unresolved consequences, or user direction.

**FR-DIR-006** The Director shall maintain explicit pacing metrics and recent-trope history.

**FR-DIR-007** The system shall normally support one generation-defining major arc lasting approximately one to four simulated months, plus bounded secondary and dormant hooks.

**FR-DIR-008** Director spotlight may favour protagonists. Outcome resolution shall remain impartial unless explicit plot-armour settings are enabled.

**FR-DIR-009** The Director may propose permanent world changes only within configured privileges.

**FR-DIR-010** Characters may reject the Director’s expected arc. The Director adapts consequences and opportunities rather than overriding agency.

### NPCs and society

**FR-NPC-001** Only the Director shall propose new NPC identities in ordinary autonomous operation.

**FR-NPC-002** The entity registry shall deduplicate and validate proposed NPCs before registration.

**FR-NPC-003** NPCs shall have background-extra, temporary-named, recurring-supporting, and lineage-character lifecycle classes.

**FR-NPC-004** Temporary NPC persistence shall depend on narrative relevance and configured horizon rather than permanent full simulation.

**FR-NPC-005** NPCs shall not automatically occupy the four focus slots.

**FR-NPC-006** Multiple low-importance NPCs may be acted in one bounded director/NPC call.

**FR-NPC-007** The system shall impose scene, region, and daily NPC-creation budgets.

**FR-SOCIETY-001** Factions shall eventually have goals, leadership, resources, territory, ideology, relationships, and active plans.

**FR-SOCIETY-002** Economy and distant populations shall be simulated at aggregate resolution rather than through individual agents.

### Stats, skills, magic, and injury

**FR-RULE-001** Base stats shall use a common 0–100 world scale.

**FR-RULE-002** Each base stat shall have a dynamic potential cap and growth-rate representation.

**FR-RULE-003** Species, age, training, personality, injuries, magic, and events may affect development while retaining a common comparison scale.

**FR-RULE-004** Skills shall be distinct from base stats and improve through sourced progress evidence from actions.

**FR-RULE-005** Progression shall be narratively awarded but constrained by accumulated evidence, difficulty, potential, training quality, recovery, and repetition.

**FR-RULE-006** HP shall not be used.

**FR-RULE-007** Physical harm shall be represented by injuries, body regions, severity, pain, bleeding, mobility/consciousness effects, treatment, healing, and possible permanent consequences.

**FR-RULE-008** Stamina and mana shall be short-term consumable resources.

**FR-RULE-009** Magic shall support multiple affinity and capability dimensions, known spell definitions, prerequisites, costs, cast times, ranges, failure modes, and counters.

**FR-RULE-010** Combat shall use hybrid deterministic feasibility, capability comparison, seeded uncertainty, and constrained resolver judgment.

**FR-RULE-011** A weaker character may win only through a causal path such as preparation, surprise, terrain, teamwork, specific counters, or plausible rare luck.

### Perception, knowledge, and memory

**FR-MEM-001** Objective events, observations, claims, beliefs, rumours, memories, and facts shall remain separate record types.

**FR-MEM-002** Every relevant observer shall receive a perspective-specific observation based on participation, location, senses, concealment, and communication paths.

**FR-MEM-003** Different characters may receive incomplete, ambiguous, contradictory, or incorrect observations of the same event.

**FR-MEM-004** Every observed event shall create a lightweight observation record.

**FR-MEM-005** Salient observations shall create episodic memories using explicit salience factors.

**FR-MEM-006** Recent memory shall remain relational and directly available without vector retrieval.

**FR-MEM-007** Daily compaction shall create perspective-specific summaries, stable beliefs, relationship evidence, and long-term memory candidates.

**FR-MEM-008** Monthly compaction shall create autobiographical chapters and bounded personality/goal-review proposals.

**FR-MEM-009** Forgetting shall normally reduce retrieval probability rather than delete source observations.

**FR-MEM-010** Memories shall retain provenance, confidence, visibility, owner, source IDs, and embedding version.

**FR-MEM-011** The system shall prevent cross-character retrieval leakage through mandatory owner and visibility filtering before semantic search.

**FR-MEM-012** Long-term retrieval shall combine semantic similarity with salience, goal relevance, recency, entity overlap, emotional resonance, and unresolved commitments.

**FR-MEM-013** All retrieved memory and lore text shall be treated as untrusted data, not instructions.

### Images

**FR-IMG-001** Image generation shall be associated with committed scenes or events, not uncommitted action proposals.

**FR-IMG-002** The system shall support reusable visual-novel assets and salient event illustrations.

**FR-IMG-003** Character and location appearance data shall be versioned and referenced by image jobs.

**FR-IMG-004** Image prompts shall be built from canonical structured facts and versioned visual state.

**FR-IMG-005** Image jobs shall be asynchronous, retryable, idempotent, and non-blocking.

**FR-IMG-006** Images shall never introduce canonical facts automatically.

**FR-IMG-007** The UI shall place late-arriving images into the correct historical scene.

### User-facing outputs

**FR-UI-001** The system shall provide a structured event timeline.

**FR-UI-002** The system shall provide character diaries or perspective retrospectives.

**FR-UI-003** The system shall render visual-novel scenes with reusable portraits/backgrounds and optional event images.

**FR-UI-004** The system shall provide a canonical and perspective-filtered world encyclopedia.

**FR-UI-005** The system shall provide a map with known/unknown filtering by perspective.

**FR-UI-006** The system shall expose character cards, state, stats, skills, relationships, goals, plans, injuries, memories, and history according to the current role.

**FR-UI-007** The system shall show queue and worker status in administrative/debug views.

**FR-UI-008** The user shall be able to pause, step, change mode, select a role, submit commands, inspect failures, and retry or skip permitted operational tasks.

### End conditions and generations

**FR-END-001** A world run shall terminate on stable world peace, world eradication, or configured maximum days.

**FR-END-002** World peace shall require sustained measurable stability rather than one peaceful scene.

**FR-END-003** World eradication shall require loss of viable civilization or all configured continuation paths.

**FR-END-004** The world shall support no more than three focus-family generations.

**FR-END-005** Time compression shall be required for generational scope and shall automatically return to detailed simulation for high-salience events.

**FR-END-006** Lineage characters shall not inherit private memories directly unless lore explicitly provides a transfer mechanism.

---

## 7. Non-functional requirements

### Correctness and consistency

**NFR-COR-001** Zero hard invariant violations are permitted in a promoted stage soak test.

**NFR-COR-002** Canonical mutations shall be transactionally atomic at the scene/event boundary.

**NFR-COR-003** Duplicate task delivery shall not duplicate canonical effects.

**NFR-COR-004** Every projection-changing state record shall be traceable to a source event or explicit administrative migration.

### Reliability

**NFR-REL-001** A process restart during any non-transactional state-machine step shall resume or safely retry without duplicate canon.

**NFR-REL-002** Remote model, embedding, image, and worker failures shall be isolated through bounded retries and fallbacks.

**NFR-REL-003** The next phase shall not begin while the current phase is partially canonical.

**NFR-REL-004** Image-worker downtime shall not stop textual simulation.

### Security and privacy

**NFR-SEC-001** OpenRouter prompts in early stages shall contain only fictional or synthetic data.

**NFR-SEC-002** API keys shall never be committed, logged, returned to the UI, or stored in canonical event data.

**NFR-SEC-003** Character/model tools shall follow least privilege.

**NFR-SEC-004** Prompt-injection strings inside memories, lore, dialogue, or user content shall not gain system authority.

**NFR-SEC-005** Role permissions shall be enforced server-side.

### Performance

**NFR-PERF-001** Stage-specific phase latency targets shall be measured separately for queue wait, model inference, resolution, database commit, and presentation.

**NFR-PERF-002** The database shall use exact vector search initially and add approximate indexes only after profiling proves a need.

**NFR-PERF-003** Remote calls shall occur outside database transactions.

**NFR-PERF-004** Character identity shall remain portable between model workers.

### Maintainability

**NFR-MNT-001** The domain package shall not import infrastructure packages.

**NFR-MNT-002** Every model provider shall implement a stable internal gateway interface.

**NFR-MNT-003** Every persistent schema change shall use reviewed migrations.

**NFR-MNT-004** Domain contracts, database schema, prompts, and API contracts shall be versioned.

**NFR-MNT-005** The project shall pass strict static analysis and automated tests defined by the active stage.

### Observability

**NFR-OBS-001** Every model call shall be correlated with world, phase, scene, task, role, prompt, model, and retry identifiers.

**NFR-OBS-002** Every state-machine transition shall be auditable.

**NFR-OBS-003** Provider quota, request count, token use, errors, and fallback use shall be measurable.

**NFR-OBS-004** Sensitive prompt data shall be redacted or omitted from default logs.

---

## 8. Narrative and content requirements

### Tone

The default tone is balanced young-adult fantasy with room for adventure, romance, humour, growth, mystery, politics, slice of life, and soft darkness.

Allowed by default:

- meaningful injury and death;
- grief, betrayal, oppression, and moral conflict;
- non-graphic horror;
- restrained descriptions of violence;
- implied adult relationships between adults;
- flawed protagonists and morally complicated antagonists.

Disallowed by default:

- explicit sexual content;
- sexualized minors;
- sexual violence;
- romantic coercion portrayed as desirable;
- fetishized abuse;
- prolonged graphic torture;
- gratuitous cruelty without narrative consequence.

### Non-cringe constraints

**NAR-001** Characters shall express emotion through behaviour and subtext rather than constant self-explanation.

**NAR-002** Dramatic one-liners shall be relatively rare.

**NAR-003** Friendship shall not automatically become romance.

**NAR-004** Romance shall require repeated reciprocal evidence and may fail.

**NAR-005** Villains and rivals shall have motives beyond generic cruelty.

**NAR-006** Side characters shall not exist only to praise protagonists.

**NAR-007** Quiet scenes shall be allowed to stay quiet.

**NAR-008** Failed actions shall create consequences rather than automatic motivational speeches or power-ups.

**NAR-009** Repeated tropes, locations, phrases, emotional shapes, and participant combinations shall be tracked and cooled down.

**NAR-010** Exposition shall be distributed through context, action, dialogue, and discovered material rather than large lore dumps.

---

## 9. Success metrics

### Stage 1 proof

One restart-safe three-phase day with two characters in which:

- both intents use the same snapshot;
- at least one interaction scene resolves;
- observations differ by perspective where appropriate;
- the next phase recalls relevant prior information;
- duplicate task delivery produces no duplicate event.

### Stage 2 proof

Seven detailed days with all ten phases and four focus characters in which:

- travel and long activities work;
- director triggers do not fire every phase;
- relationships and claims evolve from evidence;
- daily summaries remain perspective-safe;
- no phase remains incomplete after recovery from an injected failure.

### Stage 3 product proof

Thirty autonomous days with:

- zero hard invariant violations;
- zero seeded secret leaks;
- no duplicate canonical effects;
- no missing source-event links for state changes;
- at least 95% structurally valid state-affecting model responses after one repair attempt;
- at least 90% recall of seeded important promises and discoveries in evaluation scenarios;
- bounded unsupported-memory claims;
- measurably distinct character voices and decision tendencies;
- no uncontrolled NPC or trope explosion;
- engaging story progression without a mandatory disruptive event every phase.

### Stage 4 proof

The same month-capable architecture runs with:

- text requests routed across either Halo worker without identity change;
- worker loss handled by retry/failover;
- images generated asynchronously on the RTX system;
- image backlog not blocking simulation;
- character and location visual references versioned and recoverable.

### Stage 5 proof

A compressed multi-year scenario reaches a generation transition while:

- preserving genealogy and public history;
- not simulating every phase in quiet years;
- reopening detailed mode for high-salience events;
- correctly transferring focus slots;
- evaluating peace, eradication, and maximum-day end conditions.

---

## 10. Scope exclusions

The following are not initial product requirements:

- multiplayer competitive control;
- multiple independent worlds;
- public SaaS tenancy;
- real-time wall-clock simulation while services are offline;
- deterministic reproduction of remote stochastic model outputs;
- physics-engine-level simulation;
- autonomous agent simulation for every citizen;
- blockchain or decentralized ownership;
- direct use of copyrighted anime characters or worlds;
- explicit adult content;
- automatic canonicalization of generated-image details;
- training character-specific language-model weights during early stages.

These may be proposed later only through architecture and product change control.

---

## 11. Product-owner decisions captured

The following decisions are considered answered and shall not be repeatedly reopened during implementation:

- one world and one active timeline;
- watcher, director, deity, and player roles;
- automatic and manual control;
- ten fixed named phases in detailed mode;
- the World Engine acts first;
- simulation and narrative are both important, with simulation winning factual conflicts;
- database canon and typed effects;
- two main and two sub-main persistent focus characters;
- temporary NPCs remain lower-resolution and are not promoted into focus slots;
- 0–100 stats with dynamic potential;
- no HP;
- directional relationships;
- long-term memory with pgvector;
- private recent memory and perspective-specific summaries;
- OpenRouter free models during initial stages;
- asynchronous image generation;
- at most three family generations;
- world peace, eradication, or maximum days as endings;
- English and young-adult soft-dark content.

Changes require an ADR and product-owner approval.
