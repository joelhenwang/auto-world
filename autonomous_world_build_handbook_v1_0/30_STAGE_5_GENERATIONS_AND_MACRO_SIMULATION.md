# Stage 5 — Three Generations and Macro Simulation

**Version:** 1.0  
**Stage outcome:** The world can progress coherently through at most three family generations using adaptive temporal resolution, ageing, genealogy, succession, low-resolution background evolution, generation-scale arcs, explicit end conditions, and complete historical exports while preserving the detailed simulation’s event and perspective rules.  
**Primary proof:** `stage5-three-generations-v1` accelerated deterministic lineage scenario and long-horizon invariant audit.

---

## 1. Purpose

A ten-phase detailed simulation cannot economically execute every day across several decades. Stage 5 introduces deliberate time abstraction while preserving the important distinction between:

- objective state;
- character perspectives;
- causal events;
- derived summaries;
- irreversible consequences.

The main question is:

> Can the system skip quiet time without fabricating unsupported life histories, erasing agency, leaking secrets, or waking up years later with contradictory characters and world state?

---

## 2. Temporal resolution levels

```text
MICRO_BEAT
  One reaction, combat exchange, or dialogue beat.

PHASE
  One of the ten active-day narrative intervals.

DAY
  Detailed or summarized daily activity.

WEEK
  Routine travel, work, training, healing, faction movement.

MONTH
  Background economy/politics, relationship progression, pregnancy/family events,
  long projects, arc milestones.

YEAR
  Ageing, education/career, settlement/faction evolution, generational transitions.
```

The simulation may compress only when the eligibility rules in this document pass. It must expand back to detailed time when a high-salience event, user watch marker, active conflict, or focus-character decision occurs.

---

## 3. Required capabilities

- macro-time eligibility and resolution selection;
- user-configurable watch/detail periods;
- deterministic macro progression envelopes;
- bounded model-assisted macro proposals and summaries;
- scheduled-event preservation across skips;
- ageing and age-dependent capability/state;
- family relationships and genealogy;
- consent-aware partnership/family-planning events within the young-adult content profile;
- births and childhood as lineage entities without full ten-phase simulation;
- education, training, occupation, health, and relationship progression at appropriate resolution;
- focus-slot succession between generations;
- public history, private family history, diaries, and inherited knowledge separation;
- generation-level arcs and world/faction evolution;
- stable peace, eradication, and maximum-day ending evaluation;
- long-horizon consistency/audit/repair workflow;
- complete replay/export bundle with summaries and source event ranges.

---

## 4. Explicit exclusions

- more than three generations in the product contract;
- full agent inference for every child, resident, soldier, or background family;
- genetic realism or medical simulation beyond story-safe abstractions;
- explicit sexual content;
- automatic coercive romance/family formation;
- silent retcon of detailed history to fit a macro summary;
- making a summary authoritative without structured state transitions;
- exact deterministic reproduction of live-model prose.

---

## 5. Stage work packages

```text
S5-DB-001       Genealogy, ageing, macro-run, succession, ending schema
S5-MACRO-001    Resolution eligibility and expansion triggers
S5-MACRO-002    Weekly/monthly/yearly deterministic progression
S5-MACRO-003    Model-assisted macro proposals/summaries and validation
S5-LINEAGE-001  Family, births, childhood, inherited/public knowledge
S5-LINEAGE-002  Focus-slot succession and generation transition
S5-WORLD-001    Generation arcs and long-horizon faction/world evolution
S5-END-001      Peace/eradication/max-day ending evaluator
S5-ORCH-001     Long-horizon workflow, checkpoints, audit, resume
S5-API-001      Generational timeline/genealogy/export API
S5-UI-001       Timeline zoom, family tree, succession/endings UI
S5-QA-001       Accelerated three-generation gate
```

---

## 6. Macro-compression eligibility

A period may be compressed only when all applicable conditions hold:

- no active detailed scene;
- no unresolved character reaction;
- no imminent scheduled high-impact event;
- no active lethal conflict;
- no user player-control session;
- no user watch marker requiring detailed time;
- no due decision that materially changes a focus character’s plan;
- no unstable severe injury requiring phase/day resolution;
- no unresolved world-rule or deity edit;
- all required summaries and audits through current time are complete;
- the proposed horizon does not cross an event deadline unnoticed.

The maximum horizon is the earliest of:

- next scheduled event;
- next plan decision point;
- next recovery milestone;
- next relationship/family milestone;
- next faction/arc milestone;
- user watch boundary;
- configured maximum skip.

---

## 7. Expansion triggers

A compressed run stops and opens detailed simulation when:

- salience exceeds configured threshold;
- a focus character must make a consequential choice;
- a secret may be revealed;
- a relationship reaches a decision boundary;
- an injury/illness becomes critical;
- a birth/death/transformation occurs;
- a faction action directly affects a focus character/location;
- a major arc milestone begins;
- a random encounter passes its promotion threshold;
- the user interrupts;
- validation detects ambiguity that cannot be resolved safely in aggregate.

Expansion creates a normal phase/day snapshot before any character decision.

---

## 8. Task packets

### S5-DB-001 — Long-horizon persistence

Add:

```text
macro_run
macro_interval
macro_proposal
macro_effect
macro_summary
macro_summary_source_range
age_state
life_stage
family_relationship
partnership
family_plan
pregnancy_or_birth_event   # story-safe abstract domain name may be chosen in code
genealogy_edge
lineage_character
education_or_training_period
occupation_period
focus_slot
succession_event
generation_run
generation_summary
ending_evaluation
world_ending
watch_marker
```

Do not store decades solely in one prose blob. Structured state transitions remain sourced by macro events/effects.

Constraints:

- genealogy edges cannot create cycles in biological ancestry;
- parent/child ages must pass configured plausibility checks;
- one entity may occupy one focus slot at a time;
- at most two main and two sub-main active focus slots;
- maximum generation index is three;
- birth/death/partnership events are explicit and auditable;
- ending state is terminal unless deity override explicitly reopens it.

### S5-MACRO-001 — Eligibility and resolution selector

Implement a pure decision service:

```text
current state + upcoming deadlines + user policy + narrative salience
→ highest safe resolution level and horizon
```

The service returns reasons, blocked conditions, next boundary, and required task plan. It must be deterministic for the same snapshot/configuration.

Tests cover every blocker, horizon truncation, watch markers, nested deadlines, and restart.

### S5-MACRO-002 — Deterministic progression

Implement rule-based updates appropriate to each horizon:

**Week**

- routine activity progress;
- travel;
- training evidence;
- recovery;
- modest relationship contact evidence;
- resource consumption/earnings;
- faction action tick.

**Month**

- occupation/project progress;
- settlement/faction indicators;
- relationship/family milestones requiring later validation;
- education/training progression;
- arc/hook deadlines;
- weather/season transition;
- memory chapter boundaries.

**Year**

- ageing/life stage;
- long-term skill/career development;
- family/lineage state;
- leadership succession;
- broad political/economic change;
- character/world chapter creation.

Every aggregate calculation writes source ranges and typed effects. Randomness uses stored seeds.

### S5-MACRO-003 — Model-assisted macro proposals and summaries

The model may propose:

- plausible life developments inside deterministic envelopes;
- relationship/goal choices that trigger detailed expansion;
- background events;
- narrative summaries;
- arc opportunities.

It may not:

- silently decide a focus character’s major choice;
- create a child/partner/death without validated prerequisites and policy;
- overwrite detailed events;
- reveal secrets without causal transfer;
- invent large stat/skill changes beyond evidence;
- bypass generation/end limits.

Use restricted schemas and one bounded validation/regeneration cycle. Deterministic fallback may produce an uneventful interval.

### S5-LINEAGE-001 — Family and childhood

Implement story-safe family mechanics:

- adult partnership state and reciprocal consent evidence;
- family-plan state;
- pregnancy/birth represented as explicit scheduled conditions/events when enabled by world configuration;
- adoption/guardianship alternatives;
- parent/guardian relationships;
- childhood life stage and low-resolution development;
- inherited biological/magical potential rules where lore permits;
- learned public/family knowledge through teaching, stories, diaries, reputation, and objects;
- no inheritance of private memories by default;
- childhood safety/content policy.

A lineage child is a persistent `LINEAGE_CHARACTER`, not a temporary NPC and not automatically a focus character.

### S5-LINEAGE-002 — Focus succession

At a generation boundary:

1. evaluate viable lineage/adult candidates;
2. ensure they have sufficient card/state/history;
3. propose up to two main and two sub-main successors;
4. allow user selection/override;
5. create versioned focus-slot assignments;
6. produce outgoing generation summaries/legacies;
7. derive successor known history from actual information channels;
8. build initial goals/relationships/perspective memory;
9. start a detailed transition scene/day;
10. preserve retired focus characters as lower-resolution persistent entities while alive/relevant.

Do not clone parent personalities or memory prompts into children.

### S5-WORLD-001 — Generational world evolution

Implement:

- one generation-defining major arc lasting approximately one to four simulated months;
- secondary hooks and long dormant causal threads;
- leadership changes;
- settlement/faction growth/decline;
- long projects and infrastructure;
- public historical records;
- cultural/lore change proposals with privilege validation;
- consequences from previous generation choices;
- protagonist spotlight bias without hidden outcome bias.

Background entities remain tiered; no city-wide full agent simulation.

### S5-END-001 — Ending evaluator

Evaluate only from structured indicators and explicit thresholds.

#### Stable peace

Configurable conditions may include:

- no active existential/major war arc;
- major factions below hostility threshold for sustained period;
- settlements viable;
- focus generation has no unresolved world-threatening commitment;
- peace duration threshold;
- Director/evaluator finds no hidden imminent contradiction, with evidence IDs.

The user may choose to continue after a peace ending only through an explicit deity/director override that reopens the world.

#### World eradicated

Examples:

- no viable sapient population/settlement under the world definition;
- irreversible catastrophic world state;
- all survival/recovery paths invalid;
- high-impact audit confirms terminal condition.

#### Maximum days

Stop exactly at configured maximum fictional day after completing the current atomic scene/phase boundary.

Store ending reason, evidence, final state hash, model/rule versions, and export reference.

### S5-ORCH-001 — Long-horizon orchestration

Implement:

- detailed/macro workflow switching;
- horizon planning;
- user interrupt signal;
- scheduled effect wake-ups;
- generation/month/year barriers;
- periodic full audits;
- snapshots before high-impact transitions;
- recovery from interruption midway through a macro interval;
- idempotent interval effects;
- progress visualization;
- maximum day and ending stop;
- no real-time catch-up while services are off unless user explicitly commands a macro run.

### S5-API-001 — Generational API

Add:

- timeline at phase/day/week/month/year zoom;
- macro interval details, reasons, effects, sources;
- genealogy and family relationships;
- life stages/age/history;
- focus-slot history and succession candidates;
- generation summaries/legacies;
- watch markers and detail policy;
- long-horizon run/interrupt;
- ending status/evidence;
- complete archival export.

### S5-UI-001 — Long-horizon experience

Add:

- zoomable chronology;
- detailed-versus-compressed interval visualization;
- family tree;
- focus-character succession view;
- outgoing generation legacies and incoming perspectives;
- watch-marker/detail controls;
- world/faction evolution layers;
- ending progress and final state;
- explicit warnings for deity edits across compressed history;
- export/download management.

### S5-QA-001 — Three-generation gate

Use an accelerated deterministic fixture with shortened life/generation durations for tests, plus selected realistic-scale invariant simulations.

Test:

- detailed → week → month → year → detailed transitions;
- scheduled event truncates skip;
- user interrupt;
- pregnancy/birth/adoption where enabled;
- genealogy cycle/age validation;
- childhood knowledge boundaries;
- successor has no inherited private memory;
- outgoing focus retirement;
- lineage candidate selection;
- high-impact death/return;
- faction/settlement evolution;
- peace, eradication, and max-day endings;
- process failure at each macro checkpoint;
- summary/source reconstruction;
- hard retcon creates downstream taint warnings;
- complete three-generation export.

---

## 9. Long-horizon audit

At least monthly and before every year/generation/ending boundary, audit:

- entity locations and life status;
- age/genealogy plausibility;
- active focus slots;
- unresolved activities/plans/commitments;
- injuries/conditions/recovery;
- inventory ownership;
- relationship evidence;
- faction/settlement resources;
- scheduled effects;
- secrets/knowledge channels;
- summary source ranges;
- event sequence continuity;
- projection hashes;
- ending prerequisites.

A failed hard audit blocks further progression and opens a repair task. Repair is an explicit sourced event or projection rebuild, never a silent data edit.

---

## 10. Hard exit gate

- no more than three generations are created;
- accelerated three-generation scenario completes without manual database repair;
- detailed and macro intervals preserve ordered event/effect/provenance history;
- every compressed summary cites source event ranges and structured changes;
- scheduled high-salience events cannot be skipped;
- major focus-character choices expand to detailed mode or explicit user input;
- age/genealogy/focus-slot invariants hold;
- successors do not inherit inaccessible private memories;
- outgoing generations remain coherent historical entities;
- world/faction change is causal and bounded;
- one configured ending is reached and audited correctly in each dedicated fixture;
- restart/duplicate delivery at macro boundaries cannot double ageing, births, deaths, progression, or faction changes;
- final export reconstructs canonical timeline, perspectives, diaries, encyclopedia/map, genealogy, generations, model/rule versions, images, and audit state;
- all previous stage gates remain green;
- architecture, security, privacy, content, migration, type, test, and operational checks pass.

---

## 11. Product completion checklist

At Stage 5 completion, the product supports:

- automatic or manual observation;
- watcher/director/deity/player roles;
- four focus slots with generational succession;
- ten-phase active days;
- adaptive long-horizon progression;
- coherent character memory and perspective;
- Director-driven opportunities without outcome control;
- bounded NPC population;
- stats, skills, magic, injuries, conflict, factions, arcs;
- local distributed text inference;
- asynchronous generated illustrations;
- timeline, diaries, visual-novel scenes, encyclopedia, map, genealogy;
- peace, eradication, or maximum-day completion;
- auditable canonical history and exports.

Further work should be driven by measured quality and user experience, not by adding more autonomous agents by default.
