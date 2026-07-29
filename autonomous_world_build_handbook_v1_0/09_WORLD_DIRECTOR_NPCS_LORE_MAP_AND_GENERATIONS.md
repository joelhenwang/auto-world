# World Director, NPCs, Lore, Map, Factions, and Generations

**Version:** 1.0  
**Status:** Normative domain and agent specification  
**Primary owners:** `domain.world`, `domain.lore`, `domain.map`, `domain.factions`, `agents.director`  
**Required reading:** `02`–`07`, `11`, `13`–`15`, and the active stage document

---

## 1. Purpose

This document defines the split between the deterministic World Engine and the model-driven Narrative Director, the lifecycle of generated lore and NPCs, map and travel topology, background faction/economic evolution, story-arc governance, and succession through at most three family generations.

The World Engine determines what is physically and procedurally true. The Director proposes meaningful possibilities and presentation priorities. The Director is omniscient but not authoritative.

---

## 2. World Engine versus Narrative Director

| Responsibility | World Engine | Narrative Director |
|---|---:|---:|
| Advance calendar | yes | no |
| Apply weather/recovery/travel rules | yes | no |
| Maintain map and entity registry | yes | propose only |
| Resolve scheduled deterministic effects | yes | no |
| Propose story hooks and arcs | no | yes |
| Detect narrative stagnation | metrics only | interpret and propose |
| Select dramatic opportunity | no | yes |
| Decide character actions | no | no |
| Decide success or failure | no, except deterministic cases | no |
| Commit state | through validated services | never |
| Generate NPC blueprint | no | yes |
| Validate NPC/lore/map proposal | yes | no |
| Write polished event narration | no | may assist |
| Expose secrets | perception rules only | may propose causal reveal |

The Director receives an omniscient read model. Its output is an untrusted proposal processed by the same validation and resolution architecture as character actions.

---

## 3. Director objectives

The Director optimizes a declared set of goals rather than pretending to be “unbiased.” Default goals are:

```yaml
causal_continuity: 1.0
character_agency: 1.0
world_coherence: 1.0
avoid_stagnation: 0.8
novelty: 0.6
protagonist_relevance: 0.55
genre_balance: 0.5
unresolved_hook_progress: 0.6
quiet_scene_preservation: 0.45
spectacle: 0.25
```

These are prompt policy weights, not numeric guarantees.

### 3.1 Protagonist treatment

Default:

- spotlight bias: enabled;
- opportunity bias: enabled;
- outcome bias: disabled;
- hidden plot armour: prohibited;
- explicit configurable plot armour: allowed only as a visible world setting.

The Director may bring the main characters near consequential events. It cannot secretly make their attacks land or save them from valid consequences.

---

## 4. Director invocation policy

The Director is not called automatically every phase.

### 4.1 Deterministic trigger inputs

The World Engine computes:

- phases since meaningful decision;
- phases since world event;
- active arc progress;
- unresolved hooks and deadlines;
- repeated scene locations;
- repeated participant combinations;
- repeated action families;
- tension trend;
- relationship movement;
- character goal progress;
- recent genre distribution;
- background faction deadlines;
- user-configured event cadence.

### 4.2 Trigger classes

```text
SCHEDULED
CAUSAL_CONSEQUENCE
STAGNATION_RISK
ARC_MILESTONE
BACKGROUND_ESCALATION
USER_REQUESTED
MONTHLY_REVIEW
GENERATION_TRANSITION
```

A trigger creates a Director task. No trigger means the world may have a quiet phase.

### 4.3 Event budget

Default detailed-time budget:

- one generation-defining major arc lasting approximately one to four simulated months;
- at most one dominant major arc at a time;
- at most two active secondary hooks;
- several dormant hooks;
- ordinary minor world events as causally justified;
- at least seven detailed days between unrelated major disruptions unless the previous event caused the next one.

These defaults are configurable per world.

---

## 5. Director proposal contract

```text
DirectorProposal
├── proposal_id
├── phase_id
├── trigger_type
├── proposal_kind
├── title
├── intent
├── causal_basis_event_ids
├── involved_entity_ids
├── target_location_ids
├── prerequisites
├── proposed_event_facts
├── proposed_effect_types
├── observability_plan
├── secret_handling
├── expected_horizon
├── urgency
├── narrative_dimensions
├── novelty_tags
├── trope_tags
├── fallback_or_expiry
└── confidence
```

Proposal kinds:

```text
ENVIRONMENTAL_EVENT
SOCIAL_OPPORTUNITY
FACTION_ACTION
DISCOVERY
MYSTERY_HOOK
RELATIONSHIP_OPPORTUNITY
PERSONAL_DILEMMA
QUEST_HOOK
ARC_MILESTONE
NEW_LOCATION_DETAIL
NEW_LORE_PROPOSAL
NPC_BLUEPRINT
TIME_SKIP_MILESTONE
GENERATION_EVENT
```

A proposal must name its causal basis. “Something dramatic should happen” is insufficient.

---

## 6. Privileges and world-rule changes

Director privileges are configured by category:

```yaml
may_propose_local_lore: true
may_propose_locations_inside_map: true
may_propose_temporary_npcs: true
may_propose_faction_actions: true
may_propose_major_geography_change: false
may_propose_magic_rule_change: false
may_propose_resurrection: false
may_propose_world_ending_event: true
may_commit_anything_directly: false
```

Even when a privilege is enabled, the Director proposes; a validator and resolver commit.

Major changes require one of:

- deity command;
- explicit world configuration;
- an established lore mechanism;
- a privileged high-impact workflow with human-visible audit.

---

## 7. Story arcs and hooks

### 7.1 Arc contract

```text
Arc
├── arc_id
├── title
├── category
├── generation_number
├── scope
├── status
├── premise
├── involved_entities
├── origin_event_id
├── start_phase_id
├── expected_end_window
├── stakes
├── flexible_milestones[]
├── open_questions[]
├── protected_outcomes[]   # normally empty
├── prohibited_shortcuts[]
├── tension_state
├── last_progress_phase_id
└── conclusion_event_id?
```

Statuses:

```text
DORMANT
ACTIVE
PAUSED
CONCLUDING
CONCLUDED
ABANDONED
FAILED
```

### 7.2 Flexible milestones

Milestones describe situations, not required character choices.

Bad:

> Alex accepts the guild mission and falls in love with Sein.

Good:

> The missing caravans become personally relevant to at least one focus character; evidence points toward a conflict between the guild and marsh communities. Relationship developments remain emergent.

### 7.3 Protected outcomes

Normally empty. A protected outcome is allowed only for world configuration such as:

- “the tutorial village cannot be destroyed during Stage 1”; or
- “generation transition must leave at least one viable successor.”

Protected outcomes are explicit, temporary, and visible in debug mode. They must never quietly grant combat success.

### 7.4 Arc conclusion

An arc can conclude through:

- success;
- failure;
- abandonment;
- transformation into another arc;
- loss of relevance;
- world-ending consequence.

The Director must not reopen a concluded conflict solely to restore tension. New conflict needs a new causal basis.

---

## 8. Stagnation and anti-repetition

### 8.1 Stagnation score

A deterministic service computes candidate indicators. The Director interprets them.

Example:

```text
stagnation =
    0.25 × no_meaningful_decision
  + 0.20 × no_goal_progress
  + 0.15 × location_repetition
  + 0.15 × participant_repetition
  + 0.10 × action_family_repetition
  + 0.10 × flat_emotional_trend
  + 0.05 × dormant_hook_count
```

Do not use one threshold as a guarantee of an attack or disaster.

### 8.2 Opportunity ladder

When stagnation is high, prefer the least disruptive useful intervention:

1. new information;
2. invitation or request;
3. personal dilemma;
4. environmental variation;
5. faction consequence;
6. interpersonal conflict;
7. danger;
8. major disruption.

### 8.3 Trope registry

Each Director proposal includes trope tags. Store recent usage with cooldowns.

Initial tags include:

```text
MYSTERIOUS_STRANGER
TAVERN_INTRODUCTION
SURPRISE_ATTACK
KIDNAPPING
FALSE_ACCUSATION
LOVE_TRIANGLE
ACCIDENTAL_INTIMACY
TRAINING_MONTAGE
HIDDEN_ROYAL
LAST_SECOND_RESCUE
FORGOTTEN_PROPHECY
SECRET_POWER_AWAKENING
BETRAYAL_REVEAL
MONSTER_OF_THE_WEEK
```

The registry does not ban tropes. It prevents lazy repetition and requires stronger causal justification during cooldown.

---

## 9. Initial world generation

The initial world is hybrid: procedurally constrained and model-generated.

### 9.1 Generate the skeleton first

Required before the first simulated phase:

- world premise and tone;
- calendar and time units;
- one continent or bounded realm;
- regions and biomes;
- one active region;
- species and cultures;
- magic-system foundations;
- broad technology level;
- three to five major factions globally;
- two or three active regional factions;
- political relationships;
- concise historical timeline;
- basic economy;
- generation-one tensions;
- map boundary and route rules;
- content limits.

### 9.2 Generate detail lazily

Generate when needed:

- neighbourhoods;
- buildings;
- minor settlements;
- shops;
- local customs;
- background families;
- temporary NPCs;
- minor faction branches;
- interior layouts.

Lazy generation must pass lore and map validation before becoming canon.

### 9.3 Stage 1 active-world size

Constrain the first complete day to:

- one settlement;
- three locations;
- two focus characters;
- no autonomous faction simulation;
- at most one temporary NPC.

### 9.4 Stage 3 active-world target

Approximately:

- one region;
- six to ten important locations;
- one settlement plus surrounding routes;
- two or three active factions;
- four focus characters;
- bounded supporting NPC set.

---

## 10. Lore model

### 10.1 Lore entries

```text
LoreEntry
├── lore_id
├── world_id
├── category
├── canonical_title
├── canonical_summary
├── structured_facts
├── scope
├── validity_status
├── introduced_event_id
├── supersedes_lore_id?
├── secrecy_level
├── known_by_entity_ids or knowledge rules
└── source_type
```

Categories include:

- cosmology;
- magic;
- species;
- culture;
- religion;
- history;
- law;
- geography;
- technology;
- institution;
- language;
- custom;
- legend.

### 10.2 Canonical versus believed lore

Canonical lore describes objective world rules. Characters may hold beliefs that differ from it. The encyclopedia therefore supports:

- omniscient canonical view;
- character-specific known or believed view;
- public-world view.

### 10.3 New-lore validation

A proposal is checked for:

- contradiction with active world rules;
- duplicate concept;
- map compatibility;
- timeline compatibility;
- species/culture compatibility;
- privilege level;
- content-policy boundaries;
- unintended exposure of secrets.

If a contradiction is intentionally part of a reveal, represent the old statement as a belief, legend, or incomplete lore entry—not as two simultaneous objective rules.

### 10.4 Lore versioning

World-rule changes create explicit new versions and impact audits. Ordinary additive detail does not rewrite earlier entries.

---

## 11. Map and locations

The canonical map is a graph with optional coordinates.

### 11.1 Location node

```text
Location
├── location_id
├── parent_location_id?
├── location_type
├── canonical_name
├── region_id
├── coordinates?
├── capacity_class
├── ownership_entity_id?
├── environmental_tags
├── access_rules
├── visibility_rules
├── description_lore_id
├── active
└── created_event_id
```

Location types include realm, region, settlement, district, building, room, landmark, wilderness zone, road segment, and extradimensional area.

### 11.2 Route edge

```text
Route
├── route_id
├── origin_location_id
├── destination_location_id
├── directionality
├── distance_units
├── allowed_travel_modes
├── base_duration_phases
├── terrain_tags
├── danger
├── capacity
├── seasonal_modifiers
├── access_requirements
├── active
└── created_event_id
```

### 11.3 Location creation

The Director may propose a new location only:

- inside the configured world boundary;
- under a valid parent region;
- with routes that preserve graph connectivity or deliberate isolation;
- without contradicting known travel times;
- within entity and detail budgets.

### 11.4 Discovery

A location can exist canonically while remaining undiscovered by a character. Knowledge of a location is perspective state, not a property of the location itself.

---

## 12. Travel and encounters

Travel is a persistent activity.

```text
TravelActivity
├── actor_ids
├── route_sequence
├── current_route_id
├── progress
├── travel_mode
├── expected_arrival_phase_id
├── supplies
├── interruption_policy
└── status
```

Each phase:

1. validate continued ability to travel;
2. apply progress from route, mode, weather, stamina, and injuries;
3. consume resources if enabled;
4. evaluate scheduled and seeded encounter chance;
5. pause the activity if an encounter or interruption occurs;
6. commit arrival when progress reaches the endpoint.

Encounter probability may depend on route danger, faction state, weather, visibility, time, and stored seed. A model may propose encounter content after the deterministic engine decides an encounter slot exists.

---

## 13. Factions

### 13.1 Faction aggregate

```text
Faction
├── faction_id
├── name
├── type
├── ideology
├── goals
├── leadership
├── membership rules
├── territories
├── resources
├── capabilities
├── public_reputation
├── secrets
├── active plans
└── status
```

Faction relationships are directional or bilateral records containing trust, hostility, dependency, alliance, trade, and conflict status.

### 13.2 Background simulation

Do not model every member. Simulate aggregates:

- resources;
- influence;
- territory;
- internal stability;
- plan progress;
- relations;
- major leadership state.

Detailed individual simulation occurs only when a named NPC enters an active scene.

### 13.3 Faction action cycle

At configured daily, weekly, or monthly intervals:

1. deterministic services update resources and deadlines;
2. active plans become eligible;
3. a lightweight model may propose one faction action from allowed options;
4. validation checks capacity and causality;
5. the resolver commits aggregate effects;
6. observable consequences are distributed through rumours, reports, prices, patrols, or direct events.

---

## 14. Economy and material life

Use an aggregate economy plus character-level significant possessions.

Track:

- character currency;
- important items and equipment;
- ownership and housing;
- local prosperity;
- scarcity indexes;
- category-level prices;
- faction resources;
- meaningful employment and contracts;
- important food or supplies during travel.

Do not simulate every commodity unit or transaction. Ordinary meals can be summarized unless scarcity, poisoning, hospitality, debt, or another story-relevant factor matters.

---

## 15. NPC lifecycle

### 15.1 Categories

```text
BACKGROUND_EXTRA
TEMPORARY_NAMED
RECURRING_SUPPORT
LINEAGE_BACKGROUND
ARCHIVED
```

A supporting NPC can persist while relevant without occupying a focus-character slot.

### 15.2 Creation authority

Only the Director proposes NPC blueprints. The entity registry validates and creates them. The resolver may approve or reject the proposal but does not invent an unrelated NPC during resolution.

### 15.3 Blueprint contract

```text
NpcBlueprint
├── proposed_name
├── purpose_in_current_context
├── category
├── species
├── age_band
├── location_id
├── affiliation_ids
├── compact_appearance
├── compact_personality
├── capabilities
├── knowledge_scope
├── secret_scope
├── intended_ttl
├── duplicate_search_terms
└── source_proposal_id
```

### 15.4 Deduplication

Before creation:

1. search active and archived entities by normalized name;
2. search by semantic purpose, occupation, location, and affiliation;
3. reuse an existing suitable NPC when possible;
4. reject exact or near duplicates;
5. assign a canonical UUID and unique display-name qualifier if needed.

### 15.5 Budgets

Default:

- at most six individually represented NPCs in one scene;
- at most twenty-four active detailed supporting NPCs in the active region;
- at most three newly named NPCs per ordinary detailed day;
- unlimited aggregate crowds;
- archived NPCs excluded from active budget.

### 15.6 Persistence and TTL

A temporary NPC remains while any of these are true:

- present in an active scene or activity;
- party to an unresolved commitment;
- involved in an active arc or hook;
- has a meaningful relationship with a focus character;
- owns or controls a relevant entity;
- scheduled to appear soon.

Otherwise, at TTL expiry:

- generate a compact exit or background-state summary;
- retain canonical identity and important events;
- archive detailed active state;
- stop regular simulation.

### 15.7 NPC acting

The Director model may act as NPCs only through a separate NPC-actor prompt receiving the NPC’s limited knowledge. Omniscient Director context must not be carried into that call.

Several minor NPCs may be batched in one call if:

- each has a separately delimited context;
- output has one result per NPC ID;
- no NPC receives another’s secret knowledge;
- the beat budget remains bounded.

---

## 16. Background simulation tiers

```text
Tier 1 — Active scene
  Full intent, reaction, resolution, and narration.

Tier 2 — Relevant off-screen entity
  Daily or event-triggered structured update.

Tier 3 — Settlement/faction aggregate
  Weekly or monthly state transition.

Tier 4 — Distant world
  Era-level summary and only high-impact events.
```

Promotion and demotion between tiers depend on proximity, active arcs, relationships, deadlines, and user focus.

No city receives one LLM agent per resident.

---

## 17. Genre and tone governance

Default rolling target for detailed scenes:

```yaml
adventure_discovery: 0.30
relationships_romance: 0.20
slice_of_life: 0.20
conflict_growth: 0.15
mystery_politics: 0.10
soft_dark_fantasy: 0.05
```

These are adaptive targets, not quotas. Isekai is usually a premise or origin, not a scene category.

The Director must preserve quiet scenes and avoid interpreting “engaging” as constant danger.

The young-adult soft-dark content rules from `02` and `22` apply to generated events, NPCs, lore, and images.

---

## 18. Generations

### 18.1 Limit

A world supports at most three family generations unless the product requirement changes through an ADR.

### 18.2 Focus slots

The simulation maintains:

- two main-character slots;
- two sub-main-character slots.

The people occupying those slots may change. Promotion requires a generation-transition workflow; ordinary NPCs are not automatically promoted.

### 18.3 Lineage candidates

A lineage candidate may be:

- biological child;
- adopted child;
- apprentice or chosen heir if the family structure supports it;
- reincarnated successor only under explicit lore.

The candidate is simulated at lower resolution until eligible.

### 18.4 Generation-transition prerequisites

- current generation has reached the configured age or narrative completion threshold;
- at least one viable successor exists unless extinction is an intended ending;
- unresolved inheritance, faction, and family state is summarized;
- current focus-character life summaries are complete;
- public and private knowledge inheritance is separated;
- appearance and stat growth models are available;
- the user has not disabled automatic succession.

### 18.5 Inheritance

Possible inheritance:

- possessions;
- titles and obligations;
- faction memberships;
- reputation;
- public history;
- taught skills;
- genetic/species potential;
- lore-defined magical traits.

Never automatically inherit:

- private episodic memory;
- exact personality;
- relationship values;
- uncommunicated secrets;
- parents’ goals.

### 18.6 Transition output

A transition creates:

- generation summary;
- world-state snapshot;
- outgoing-character status;
- focus-slot assignments;
- successor cards and initial states;
- inherited records with provenance;
- new generation premise and possible arc proposals.

---

## 19. World endings

### 19.1 Peace

World peace is not “no active battle this week.” It requires configurable sustained conditions, for example:

- no active existential conflict;
- major factions at stable non-war relations;
- no unresolved world-ending arc;
- acceptable social stability;
- peace maintained for a configured interval;
- user confirmation or automatic policy.

### 19.2 Eradication

The world is eradicated when no viable population or habitable continuation remains according to lore and rules. It is not triggered merely because all focus characters die.

### 19.3 Maximum days

A configured maximum simulation day creates an ending workflow and final archive, even if the story remains open.

### 19.4 Ending artifact

Produce:

- final canonical timeline summary;
- generation and character outcomes;
- map/faction state;
- unresolved mysteries;
- encyclopedia snapshot;
- final diaries or retrospectives;
- image gallery index;
- operational export manifest.

---

## 20. Required tests

### Director tests

- no trigger produces no Director call;
- stagnation prefers low-disruption opportunities first;
- a proposal cannot commit directly;
- a proposal cites causal basis;
- hidden information requires an observability path;
- repeated trope within cooldown is rejected or requires explicit override;
- Director refusal adaptation does not force the original character action.

### Lore/map tests

- new locations remain within map hierarchy;
- impossible route timings are rejected;
- canonical lore contradiction is detected;
- perspective encyclopedia omits unknown lore;
- intentional legends remain beliefs rather than objective rules.

### NPC tests

- duplicate blacksmith proposal reuses the existing NPC;
- TTL archival preserves event history;
- NPC actor context does not contain Director secrets;
- active-NPC budgets are enforced;
- archived NPC can be reactivated without duplicate identity.

### Generation tests

- private parent memory does not transfer;
- inherited item retains provenance;
- focus slots change without changing entity identity;
- no fourth generation starts;
- lineage extinction can lead to a valid ending rather than an exception loop.

---

## 21. Stage introduction map

| Capability | First required stage |
|---|---:|
| Minimal world skeleton and locations | 0 |
| Triggered Director proposals | 2 |
| Temporary NPC registry and bounded acting | 2 |
| Full lore/map encyclopedia | 2–3 |
| Faction aggregate simulation | 3 |
| Anti-repetition and major arc management | 3 |
| Visual location and NPC references | 4 |
| Macro simulation and generations | 5 |

---

## 22. Definition of done

The subsystem is complete for a stage when:

- deterministic world rules and Director creativity are technically separated;
- every generated entity and lore addition passes validation;
- the Director can create momentum without forcing character choices;
- NPCs have bounded creation, context, lifetime, and memory;
- map topology controls travel rather than narration alone;
- factions evolve without simulating every citizen;
- trope repetition and arc state are observable;
- generation transition preserves provenance and knowledge boundaries;
- all ending conditions produce a stable, exportable terminal state.
