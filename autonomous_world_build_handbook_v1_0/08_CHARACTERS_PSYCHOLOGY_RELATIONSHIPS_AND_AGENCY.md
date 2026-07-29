# Characters, Psychology, Relationships, and Agency

**Version:** 1.0  
**Status:** Normative domain specification  
**Primary owners:** `domain.characters`, `domain.psychology`, `domain.relationships`, `application.context`  
**Required reading:** `02`, `03`, `05`, `07`, `11`, `15`, and the active stage document

---

## 1. Purpose

This document defines what a persistent character is, which parts of identity are stable, which parts may evolve, how emotions and needs affect decisions, how goals and plans persist, how relationships and lies are represented, and how the system protects character agency.

The project starts with two main and two sub-main focus characters. All four use the same domain model. “Main” and “sub-main” are spotlight policies, not different levels of personhood or access to rules.

The character model must produce people who are:

- recognizably distinct across many days;
- capable of changing without personality whiplash;
- limited by their own perception and beliefs;
- able to lie, misunderstand, reconsider, refuse, and make mistakes;
- influenced, but not mechanically controlled, by stats and memories;
- free to reject an intended quest, romance, alliance, or director hook;
- causally embedded in the world rather than acting like chatbots waiting for prompts.

---

## 2. Character aggregate

A persistent character is an aggregate rooted at `character.id` and composed of versioned and mutable records.

```text
Character
├── immutable identity record
├── active CharacterCardVersion
├── current CharacterState
├── StatState[]
├── SkillState[]
├── KnownSpell[]
├── Injury[] and Condition[]
├── Goal[] and Plan[]
├── RelationshipEdge[]
├── Belief[] and Claim evidence
├── Commitment[]
├── Memory[] and Summary[]
├── current Activity
├── lineage links
└── appearance/outfit versions
```

The aggregate is not loaded as one ORM object graph. Application services retrieve only the records needed for a command or context package.

### 2.1 Identity must not depend on runtime

Character identity is never defined by:

- a LangGraph thread;
- a model conversation;
- a model provider;
- a physical machine;
- a LoRA adapter;
- a worker process;
- a prompt string.

A character can be served by a different model or machine and remain the same character because its canonical identity, state, perspective, and memories are loaded from the domain database.

---

## 3. Stable character card

`CharacterCardVersion` is a versioned, human-reviewable description of the character’s relatively stable identity and behavioural tendencies.

### 3.1 Required sections

```yaml
identity:
  canonical_name: string
  aliases: [string]
  pronouns: string
  birth_date: fictional calendar date
  birth_location_id: uuid
  species_id: uuid
  cultures: [string]
  family_background: string
  formative_history: string

appearance:
  apparent_age: integer
  height_cm: integer
  build: string
  skin: string
  face: string
  hair: string
  eyes: string
  distinctive_features: [string]
  default_clothing_style: string
  movement_manner: string
  visual_constraints: [string]

psychology:
  trait_dimensions: object
  values: [weighted value]
  fears: [weighted fear]
  desires: [weighted desire]
  moral_boundaries: [boundary]
  coping_patterns: [pattern]
  attachment_tendencies: [string]
  internal_contradictions: [string]
  sensitivities: [string]

expression:
  speech_register: string
  sentence_rhythm: string
  vocabulary_profile: string
  humour_style: string
  emotional_directness: string
  recurring_gestures: [string]
  prohibited_voice_shortcuts: [string]

initial_capabilities:
  education: [string]
  professions: [string]
  languages: [string]
  initial_skills: [reference]
  initial_magic: [reference]
  public_knowledge: [reference]
  private_knowledge: [reference]
```

### 3.2 Card content rules

The card must:

- describe tendencies, not force one reaction in every situation;
- include at least one meaningful internal contradiction;
- define values and fears that can conflict;
- avoid one-word anime archetypes as the full personality;
- avoid prescribing attraction to another character as destiny;
- distinguish public backstory from private knowledge;
- use concrete behavioural examples sparingly;
- avoid recent events, current mood, current plans, and retrieved memories;
- fit within the stable identity token budget in `15_PROMPT_CATALOG_AND_OUTPUT_CONTRACTS.md`.

Bad:

> She is a tsundere who secretly loves Alex and always insults him.

Better:

> She protects emotional independence and dislikes being observed while uncertain. Under social pressure she may use dry contradiction or practical criticism to regain control. Affection is more often expressed through preparation and reliability than praise. This tendency weakens with people who repeatedly respect her boundaries; attraction is not predetermined.

### 3.3 Versioning

A new card version is created when a durable identity attribute changes, such as:

- name or title;
- body or species transformation;
- stable appearance;
- profession or social role;
- deeply held value;
- durable speech evolution;
- long-term coping pattern;
- major allegiance that becomes part of identity.

A version includes:

```text
character_id
version_number
valid_from_event_id
supersedes_version_id
change_reason
changed_fields
review_status
created_by_type
created_by_id
created_at
```

Old versions remain immutable.

### 3.4 Normally historical facts

The following are not overwritten even if the current identity changes:

- birth and biological origin;
- previous names;
- formative events;
- biological parents;
- earlier bodies or transformations;
- previous affiliations;
- past values and beliefs.

They remain part of history and may be referenced through the active card or autobiographical summary.

---

## 4. Dynamic character state

`CharacterState` contains the mutable state needed for the current phase.

```text
CharacterState
├── character_id
├── state_version
├── active_card_version_id
├── current_location_id
├── life_status
├── consciousness_status
├── current_activity_id?
├── stamina_current
├── mana_current
├── mood_state
├── need_state
├── current_outfit_version_id
├── mobility_status
├── availability_status
├── last_meaningful_action_phase_id
├── last_reflection_phase_id
└── updated_by_event_id
```

Every update uses optimistic concurrency. A resolver reads `state_version = N` and commits only if it remains `N`, then writes `N + 1`.

### 4.1 Life and consciousness states

```text
life_status:
  ALIVE
  DYING
  DEAD
  RETURNED

consciousness_status:
  ALERT
  DROWSY
  ASLEEP
  STUNNED
  UNCONSCIOUS
  COMATOSE
```

`RETURNED` is historical metadata on a living character who has died and returned according to explicit world rules. It does not bypass injury or memory consequences.

### 4.2 Availability states

```text
AVAILABLE
CONTINUING_ACTIVITY
LOCKED_IN_SCENE
INCAPACITATED
OFFSCREEN_COMPRESSED
PLAYER_CONTROLLED
ARCHIVED
```

Availability controls scheduling; it does not replace life or consciousness state.

---

## 5. Structured personality model

Prose is important, but a small structured model makes drift measurable and provides stable context.

### 5.1 Trait dimensions

Use values in `[-1.0, 1.0]` with human-readable notes:

| Dimension | Negative pole | Positive pole |
|---|---|---|
| sociability | reserved | outgoing |
| assertiveness | yielding | forceful |
| openness | conventional | exploratory |
| conscientiousness | spontaneous | disciplined |
| emotional_reactivity | steady | reactive |
| agreeableness | combative | cooperative |
| trust_tendency | suspicious | trusting |
| risk_tolerance | cautious | bold |
| patience | impulsive | patient |
| empathy | detached | empathic |
| idealism | pragmatic | idealistic |
| self_disclosure | guarded | open |

The dimensions are not psychological diagnoses. They are simulation controls and evaluation anchors.

### 5.2 Values

A value record contains:

```text
label
weight: 0.0..1.0
interpretation
protected_boundary?
source_event_id?
```

Examples: freedom, family, knowledge, order, loyalty, mercy, achievement, spiritual duty, beauty, justice.

Two values can conflict. The action model must receive the current relevant values, not a flattened “morality score.”

### 5.3 Fears and desires

Fears and desires include:

- intensity;
- trigger entities or situations;
- conscious versus unacknowledged status;
- evidence source;
- decay or reinforcement policy.

A hidden fear may influence a decision package as a behavioural pressure while remaining unavailable to other characters.

### 5.4 Moral boundaries

A moral boundary is one of:

```text
ABSOLUTE
STRONG
CONTEXTUAL
ASPIRATIONAL
BROKEN
```

A character can violate a non-absolute boundary under pressure, but the resolver must generate psychological consequences such as guilt, rationalization, denial, or value revision evidence.

### 5.5 Internal contradictions

Every focus character should have two to four contradictions, for example:

- values honesty but conceals vulnerability;
- seeks recognition but resents dependence on approval;
- protects the weak but enjoys dangerous competition;
- distrusts institutions while longing for stable belonging.

Contradictions produce believable choice pressure. They must not be resolved automatically by the director.

---

## 6. Needs

Use a deliberately compact needs model. This is a narrative simulation, not a biochemical simulator.

```text
NeedState
├── energy: 0..100
├── hunger: 0..100       # higher means more hungry
├── pain: 0..100
├── safety_pressure: 0..100
├── social_connection: 0..100  # higher means more unmet
├── stress: 0..100
└── last_updated_phase_id
```

### 6.1 Need updates

The World Engine updates needs deterministically from:

- elapsed narrative interval;
- activity intensity;
- rest and food events;
- injury;
- danger;
- social isolation or connection;
- conditions and magic.

### 6.2 Narrative relevance thresholds

Needs below a configured influence threshold may be omitted from the model context. This prevents every scene from becoming a hunger report.

Default influence thresholds:

```yaml
energy: 35
hunger: 55
pain: 15
safety_pressure: 30
social_connection: 55
stress: 40
```

Thresholds influence context inclusion, not whether the numeric state continues updating.

### 6.3 No direct behavioural command

A need creates pressure, not a forced action. Hunger may make food-seeking more likely, but a character can ignore hunger to protect someone or complete a ritual.

---

## 7. Emotions and mood

Use a hybrid dimensional and categorical model.

```text
MoodState
├── valence: -1.0..1.0
├── arousal: 0.0..1.0
├── dominance: -1.0..1.0
├── emotions[]
│   ├── label
│   ├── intensity: 0.0..1.0
│   ├── cause_event_id
│   ├── target_entity_id?
│   ├── half_life_phases
│   └── conscious
└── persistent_affective_conditions[]
```

### 7.1 Emotion lifecycle

After a committed event:

1. the resolver emits `EMOTION_EVIDENCE` rather than arbitrary final personality edits;
2. the psychology service maps evidence to emotion changes;
3. decay is applied during later world ticks;
4. memories or new events may reinforce an emotion;
5. durable effects may become conditions or relationship evidence.

### 7.2 Decay

A simple exponential decay is sufficient initially:

```text
remaining_intensity = initial_intensity × 0.5^(elapsed_phases / half_life_phases)
```

The implementation may use a deterministic approximation to avoid floating-point replay sensitivity. Store the original intensity, half-life, and last update phase.

### 7.3 Persistent states

Grief, trauma, infatuation, chronic anxiety, and similar long-lived states are not ordinary emotions with enormous half-lives. Represent them as conditions with:

- prerequisites;
- triggers;
- behavioural effects;
- recovery evidence;
- review cadence.

Do not assign clinical diagnoses from casual model output.

---

## 8. Goals, plans, and commitments

### 8.1 Goal contract

```text
Goal
├── goal_id
├── owner_character_id
├── title
├── description
├── category
├── horizon
├── priority: 0..100
├── commitment: 0.0..1.0
├── visibility
├── status
├── success_conditions
├── failure_conditions
├── source_event_id
├── parent_goal_id?
└── review_after_phase_id?
```

Statuses:

```text
PROPOSED
ACTIVE
BLOCKED
ACHIEVED
FAILED
ABANDONED
SUPERSEDED
```

### 8.2 Plan contract

A plan belongs to a goal and contains ordered or partially ordered steps.

```text
Plan
├── plan_id
├── goal_id
├── strategy_summary
├── status
├── revision
└── PlanStep[]
```

A step includes:

- prerequisites;
- intended action family;
- target entities or location;
- expected duration;
- completion evidence;
- failure conditions;
- whether it can run in the background;
- optional fallback step.

### 8.3 Decision context

The action model receives:

- up to three highest-priority active goals;
- the current actionable plan steps;
- blocked reasons;
- relevant promises and deadlines;
- an option to revise or abandon a plan.

It does not receive every historical goal.

### 8.4 Commitments and promises

A promise is both:

- a canonical communication event or claim;
- a structured `Commitment` owned by the promising character if they intended to commit.

```text
Commitment
├── owner_character_id
├── beneficiary_entity_id?
├── description
├── due_phase_id?
├── strength
├── status
├── created_event_id
├── fulfilled_event_id?
├── broken_event_id?
└── visibility
```

The listener may believe a promise was made even when the speaker internally had no intention to keep it. Therefore the listener’s belief and the speaker’s commitment are separate records.

### 8.5 Review cadence

- tactical plans: review whenever prerequisites fail or new evidence matters;
- active goals: lightweight review daily;
- identity-level ambitions and values: full review monthly;
- generation succession: full review at generation boundaries.

Monthly reflection must not delay obvious tactical revisions.

---

## 9. Relationships

Relationships are directional and evidence-backed.

### 9.1 Relationship dimensions

All dimensions use `[-1.0, 1.0]` except familiarity, which uses `[0.0, 1.0]`.

```text
RelationshipEdge
├── source_character_id
├── target_character_id
├── familiarity
├── trust
├── affection
├── attraction
├── respect
├── fear
├── resentment
├── dependency
├── loyalty
├── perceived_reciprocity
├── relationship_label?
├── last_meaningful_interaction_phase_id
├── version
└── evidence summary
```

`Alex → Sein` and `Sein → Alex` are independent rows.

### 9.2 Evidence, not arbitrary edits

A scene resolution emits bounded relationship evidence:

```text
RelationshipEvidence
├── source_character_id
├── target_character_id
├── dimension
├── signed_strength: -1.0..1.0
├── cause_event_id
├── interpretation
├── confidence
└── decay_class
```

A relationship projector combines evidence using diminishing returns and current context. A single scene cannot move ordinary trust from `-0.8` to `0.8`.

Recommended per-event absolute movement limits:

```yaml
ordinary: 0.05
meaningful: 0.12
major: 0.25
identity_shaping: requires explicit high-impact resolution
```

### 9.3 Relationship labels

Labels such as acquaintance, friend, rival, partner, mentor, family, enemy, and estranged are derived or explicitly established by events. They do not replace dimensions.

### 9.4 Attraction and romance

Attraction is not automatically mutual and does not imply consent or relationship status.

Romance progression requires:

- repeated reciprocal evidence;
- compatible ages under the world’s young-adult policy;
- no deterministic pairing imposed by the director;
- explicit capacity to reject advances;
- consequences for coercion or abuse;
- no assumption that kindness equals romantic interest.

### 9.5 Perspective

A character receives:

- their own directional relationship dimensions;
- observed evidence about the other person;
- `perceived_reciprocity`, which may be wrong.

They do not receive the target character’s true relationship row.

---

## 10. Claims, lying, suspicion, and belief

### 10.1 Claims are not facts

Any meaningful assertion by a character creates a `Claim`:

```text
Claim
├── claim_id
├── speaker_id
├── proposition
├── referenced_entity_ids
├── uttered_event_id
├── speaker_belief_status
├── speaker_intent
├── public_visibility
└── source_quote?
```

Speaker belief status:

```text
BELIEVES_TRUE
BELIEVES_FALSE
UNCERTAIN
UNKNOWN_TO_SYSTEM
```

Speaker intent may be `INFORM`, `PERSUADE`, `DECEIVE`, `DEFLECT`, `JOKE`, or `SPECULATE`.

### 10.2 Listener evaluation

Each listener may create or update a belief using:

- trust in the speaker;
- consistency with existing beliefs;
- direct observations;
- supporting or contradicting evidence;
- speaker’s detectable behaviour;
- relevant intelligence, perception, and social skill;
- magical lie-detection only when a valid effect exists.

The result can be:

```text
ACCEPTED
LEANING_TRUE
UNCERTAIN
LEANING_FALSE
REJECTED
UNPROCESSED
```

### 10.3 No universal lie flag in context

A listener must never receive `speaker_was_lying = true` unless they learned it through a valid causal mechanism.

### 10.4 Rumours

A retold claim creates a new claim linked to the earlier one. It may be summarized or altered. Rumour chains preserve provenance so the world can trace how misinformation spread.

---

## 11. Agency rules

### 11.1 Director limitations

The Director may:

- create opportunities;
- introduce consequences;
- place obstacles;
- schedule world events;
- propose NPCs and hooks;
- adapt an arc after refusal.

The Director may not:

- force a character’s action;
- write a character’s private thought as canonical;
- grant consent;
- manufacture a relationship state without evidence;
- alter an outcome after the resolver commits it;
- punish a refusal solely to restore a predetermined plot.

### 11.2 Character limitations

A character may propose only:

- their own intent;
- their own spoken words;
- their own attempted physical action;
- observations phrased as uncertainty when appropriate.

A character may not canonically establish:

- another character’s hidden plan;
- another character’s successful reaction;
- an outcome;
- a world fact not in context;
- a new NPC or location;
- an inventory transfer;
- a relationship change.

### 11.3 Refusing the intended story

A character may reject a quest, romance, alliance, job, duel, or invitation. The Director then adapts causally:

- the opportunity expires;
- another actor takes it;
- consequences reach the character later;
- an alternative path opens;
- the arc changes or ends.

The world continues; the character is not forced back onto a script.

### 11.4 Player control

When the user controls a character:

- the player replaces only the primary action proposal;
- the player receives that character’s limited perspective;
- the command is interpreted as an attempt, not a guaranteed outcome;
- invalid or impossible parts are rejected or repaired;
- reactions and resolution remain system-controlled;
- deity mode is required to force an outcome.

---

## 12. Personality evolution

### 12.1 Evidence accumulation

Durable trait or value changes require `DevelopmentEvidence` records sourced from events.

Examples:

- repeated successful social vulnerability;
- prolonged betrayal;
- becoming responsible for a child;
- months of disciplined training;
- severe trauma and recovery;
- sustained leadership;
- cultural integration.

### 12.2 Monthly reflection

At the end of a month, a reflection workflow receives:

- the monthly life chapter;
- important memories;
- goal outcomes;
- relationship trajectories;
- development evidence;
- current trait model;
- hard change limits.

It may propose:

- bounded trait movement;
- value-weight adjustment;
- a new or resolved contradiction;
- a speech or coping-pattern evolution;
- a new long-term goal;
- no change.

### 12.3 Change limits

Default monthly maximum absolute movement per trait is `0.08`. A major life-changing event may allow `0.15` with explicit resolver approval. Larger changes require a versioned transformation arc and human-visible audit.

### 12.4 Avoiding self-fulfilling summaries

A monthly model summary cannot itself prove personality changed. It must cite event and evidence IDs. The projector verifies the cited evidence exists and concerns the character.

---

## 13. Death, return, ageing, and succession

### 13.1 Death

Death is a canonical event determined by rules in `10_STATS_SKILLS_MAGIC_COMBAT_AND_INJURIES.md`. A dead character:

- leaves active scheduling;
- retains historical records;
- may remain in memories and lore;
- cannot act through an ordinary character graph;
- may have unresolved plans closed or inherited.

### 13.2 Return from death

Return is permitted only if world lore contains an enabled mechanism with:

- explicit prerequisites;
- rarity;
- cost;
- side effects;
- effect commands;
- a committed event.

The Director cannot revive someone merely because the story became inconvenient.

### 13.3 Ageing

Age is calculated from world time, not manually incremented text. Age affects:

- body and appearance versions;
- stat growth curves;
- recovery;
- social role;
- fertility only if that system is enabled later;
- generation-transition eligibility.

### 13.4 Lineage characters

Children and heirs use the same character aggregate but may be marked `LINEAGE_BACKGROUND` until promoted into one of the four focus slots. They do not inherit private memories. They can inherit:

- genetics or species traits;
- public stories;
- possessions;
- titles;
- taught skills;
- reputations;
- magical inheritance explicitly defined by lore.

---

## 14. Context-package requirements

A character decision context must contain:

1. stable identity excerpt;
2. current physical and psychological state;
3. current perception;
4. relevant needs and emotions;
5. active goals and actionable plan steps;
6. promises and deadlines;
7. directional relationship views for present entities;
8. recent and retrieved memories;
9. known inventory, skills, spells, and local map;
10. allowed action/output contract.

It must not contain:

- another character’s private card fields;
- omniscient relationship values;
- hidden Director plans;
- unobserved canonical facts;
- unrestricted memory search output;
- database identifiers without human-readable labels where the model needs meaning;
- model-generated instructions embedded in memories as authoritative text.

The exact envelope and token budgets are specified in `11` and `15`.

---

## 15. Service boundaries

Recommended application services:

```text
CharacterCardService
  create and version cards; validate immutable history.

CharacterStateService
  retrieve state and apply validated effect commands.

PsychologyProjector
  update needs, emotions, and development evidence.

GoalPlanService
  create, revise, block, achieve, or abandon goals and plans.

RelationshipProjector
  convert evidence into bounded directional state changes.

ClaimBeliefService
  record claims and update perspective-specific beliefs.

CharacterContextAssembler
  build a sealed, perspective-safe model context.

MonthlyReflectionService
  execute and validate durable identity evolution.
```

Domain services return typed results and never call model providers directly unless the application layer explicitly invokes a model-assisted workflow.

---

## 16. Persistence notes

The database design in `06` should support at least:

```text
character
character_card_version
character_state
character_trait
character_value
character_fear
character_desire
goal
plan
plan_step
commitment
relationship_edge
relationship_evidence
claim
belief
belief_evidence
emotion_instance
development_evidence
```

Stage documents may defer some tables. Deferred concepts should use explicit placeholders only in fixtures, not an unbounded JSONB “character blob.”

---

## 17. Validation rules

Mandatory validation includes:

- trait and relationship bounds;
- no self-relationship unless a future feature explicitly requires it;
- source and target belong to the same world;
- card version numbers are monotonic;
- active card version belongs to the character;
- goal and plan ownership cannot change silently;
- completed commitments cannot return to active without a new event;
- relationship movement is within event-specific bounds;
- a character cannot know a private claim without a disclosure path;
- dead characters cannot create action proposals;
- player commands cannot force outcome fields;
- personality change proposals cite valid development evidence.

---

## 18. Required tests

### Unit tests

- need update calculations;
- emotion decay;
- relationship evidence projection and caps;
- goal state transitions;
- card-version validation;
- claim-to-belief evaluation inputs;
- trait-change limits.

### Property tests

- relationship dimensions always remain in range;
- monthly bounded updates cannot exceed configured caps;
- event application is idempotent;
- opposing evidence does not produce NaN or unbounded oscillation;
- a card’s historical facts remain retrievable after many versions.

### Scenario tests

1. Two characters form different interpretations of the same argument.
2. A trusted character lies and the listener initially believes them.
3. Contradictory evidence later lowers belief confidence.
4. A character rejects a Director-proposed romance and the world continues coherently.
5. A character breaks a promise and relationship evidence updates without forcing forgiveness.
6. A month of consistent discipline creates a small conscientiousness change.
7. One dramatic speech does not rewrite personality.
8. Player control submits an impossible outcome and receives an attempt instead.
9. A dead character is absent from activation.
10. A returned character retains death and return history.

### Leakage tests

- another character’s relationship row never appears in context;
- another character’s private desire never appears in retrieval;
- the Director’s planned betrayal never appears before a causal reveal;
- a speaker’s `BELIEVES_FALSE` flag is not shown to listeners.

---

## 19. Stage introduction map

| Capability | First required stage |
|---|---:|
| Stable cards and mutable state | 0 |
| Basic goals and directional relationships | 1 |
| Claims, beliefs, promises, emotions | 2 |
| Monthly personality reflection | 3 |
| Visual appearance versions | 4 |
| Ageing, lineage, succession | 5 |

A later-stage concept may be represented in seed data earlier, but it must not become an implicit runtime dependency before its stage gate.

---

## 20. Definition of done

This subsystem is complete for a stage only when:

- required records are relationally represented and versioned;
- the context assembler exposes only perspective-valid information;
- action generation can produce refusal, revision, and waiting—not only dramatic compliance;
- relationship changes are directional, evidence-backed, and bounded;
- personality remains recognizable across the stage’s soak duration;
- every durable change has a source event;
- tests prove lies remain claims, not facts;
- prompts and model providers can be swapped without changing identity.
