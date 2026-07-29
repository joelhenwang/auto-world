# Stats, Skills, Magic, Combat, Conditions, and Injuries

**Version:** 1.0  
**Status:** Normative rules specification  
**Primary owners:** `domain.rules`, `domain.combat`, `domain.magic`, `domain.health`  
**Required reading:** `03`, `05`, `07`, `08`, `15`, and the active stage document

---

## 1. Purpose

This document defines the deterministic and model-assisted rules for physical and mental capabilities, dynamic potential, skills and progression, stamina and mana, magic, combat, injuries, healing, incapacitation, and death.

The system intentionally does not use HP. Harm is represented through injuries, conditions, functional impairment, consciousness, and life status.

The governing principle is:

> A model may interpret an ambiguous attempt inside a validated feasible outcome envelope. It may not invent capability, ignore resource costs, or narrate an impossible result into canon.

---

## 2. Base stats

### 2.1 Required stats

```text
STRENGTH
DEXTERITY
STAMINA
INTELLIGENCE
PERCEPTION
CHARISMA
```

Magic is represented separately through several dimensions rather than one `MAGIC_AFFINITY` number.

### 2.2 Scale

Every base stat uses `0..100`.

| Range | World interpretation |
|---:|---|
| 0 | absent, destroyed, or completely incapacitated |
| 1–19 | severely limited or undeveloped |
| 20–39 | weak, novice, childlike, or impaired depending on context |
| 40–49 | ordinary capable adult range |
| 50–59 | practiced or naturally capable |
| 60–74 | well trained / exceptional |
| 75–89 | elite / rare |
| 90–99 | legendary |
| 100 | established world-limit reference |

The scale is absolute within a world, not relative to species. Species, age, size, and anatomy influence distributions and derived effects.

A dragon and a human with `STRENGTH = 70` have comparable raw world-scale power, while anatomy and size may still produce different reach, leverage, or attack options.

### 2.3 Stat state

```text
StatState
├── character_id
├── stat_type
├── base_value: 0..100
├── dynamic_potential_cap: 0..100
├── growth_rate: 0.0..1.0
├── adaptability: 0.0..1.0
├── temporary_modifiers[]
├── age_curve_id
├── version
└── updated_by_event_id
```

`base_value` cannot exceed `dynamic_potential_cap` unless a temporary modifier explicitly permits it.

### 2.4 Potential

Potential means both:

- the current plausible maximum under the character’s body, circumstances, and development;
- how efficiently evidence converts into growth.

Potential can change through:

- ageing and maturation;
- sustained training;
- injury or disability;
- magical alteration;
- transformation;
- artefacts;
- lineage effects;
- exceptional life events.

A potential increase requires a typed effect and source event. It is never inferred merely because prose called someone “limitless.”

### 2.5 Temporary modifiers

Modifiers include:

```text
source_effect_id
stat_type
delta or multiplier
starts_at_phase
expires_at_phase or condition
stacking_group
priority
```

Modifiers must have deterministic stacking rules. Default:

1. apply additive modifiers;
2. apply multipliers;
3. clamp to configured effective range;
4. retain base value unchanged.

---

## 3. Derived capabilities

Derived values are calculated from base stats, skills, anatomy, equipment, needs, conditions, and context. Do not permanently store them as canon unless a cache includes all input versions.

Initial formulas are tunable and should be centralized in `RuleSet` configuration.

### 3.1 Examples

```text
initiative_base =
    0.40 × DEXTERITY
  + 0.35 × PERCEPTION
  + 0.15 × relevant_skill
  + 0.10 × current_stamina_ratio × 100

physical_power =
    0.65 × STRENGTH
  + 0.20 × relevant_skill
  + 0.15 × leverage_context

evasion =
    0.50 × DEXTERITY
  + 0.25 × PERCEPTION
  + 0.15 × movement_skill
  + 0.10 × stamina_ratio × 100

social_pressure =
    0.45 × CHARISMA
  + 0.25 × relevant_social_skill
  + 0.15 × status_context
  + 0.15 × relationship_context

analysis_capacity =
    0.55 × INTELLIGENCE
  + 0.25 × domain_skill
  + 0.20 × information_quality
```

These formulas produce a capability score, not an automatic outcome.

### 3.2 Context modifiers

Relevant modifiers include:

- terrain;
- reach and body size;
- light and visibility;
- surprise;
- preparation;
- teamwork;
- morale;
- pain;
- injury;
- equipment quality;
- fatigue;
- weather;
- distance;
- social status;
- evidence quality.

Each modifier must be explainable in the resolution trace.

---

## 4. Skills

### 4.1 Skill taxonomy

A skill is a learned capability distinct from a base stat.

Examples:

- swordsmanship;
- archery;
- unarmed combat;
- stealth;
- medicine;
- navigation;
- cooking;
- negotiation;
- deception;
- investigation;
- blacksmithing;
- riding;
- spell school proficiency;
- languages;
- professions.

### 4.2 Skill record

```text
SkillDefinition
├── skill_id
├── canonical_name
├── parent_skill_id?
├── category
├── governing_stats
├── prerequisites
├── description
└── world_rule_version

SkillState
├── character_id
├── skill_id
├── proficiency: 0..100
├── dynamic_potential_cap: 0..100
├── growth_rate
├── practice_evidence_total
├── last_practiced_phase_id
├── version
└── updated_by_event_id
```

### 4.3 Progress evidence

Actions emit `SkillProgressEvidence`, not direct arbitrary increases.

```text
SkillProgressEvidence
├── character_id
├── skill_id
├── source_event_id
├── difficulty: 0..1
├── practice_quality: 0..1
├── duration_weight
├── novelty
├── feedback_quality
├── success_factor
├── recovery_factor
└── evidence_units
```

Failure can produce useful evidence when the task was understandable and feedback existed. Repeating a trivial action has diminishing returns.

### 4.4 Narratively awarded growth

“Narratively awarded” means the system considers event meaning and quality, but the award remains bounded and evidence-based.

A growth projector considers:

```text
evidence
× growth_rate
× potential_headroom
× training_quality
× recovery
× diminishing_returns
```

The model may classify practice quality or meaningful insight. Deterministic code calculates the allowed increment.

### 4.5 Progress cadence

- record evidence after relevant actions;
- aggregate at day end;
- apply small ordinary growth daily or weekly;
- allow milestone breakthroughs only after sufficient evidence or a valid transformative event;
- show notable growth in the timeline only when narratively meaningful.

---

## 5. Stamina

### 5.1 Purpose

Stamina is a short-term resource representing exertion capacity. It is not the `STAMINA` base stat.

```text
CharacterState.stamina_current: 0..100
```

The base `STAMINA` stat affects:

- maximum practical exertion;
- stamina cost modifiers;
- recovery rate;
- endurance under conditions.

### 5.2 Costs

Every physical effect with meaningful exertion declares a stamina cost range. The resolver selects an allowed cost based on intensity and outcome.

Examples:

```yaml
ordinary_walk: 0..2
sprint: 5..12
heavy_attack: 4..10
dodge: 3..8
long_climb: 8..20
rest_phase_recovery: 10..30
sleep_recovery: 30..70
```

These values are configuration defaults, not hard-coded constants.

### 5.3 Low stamina effects

Suggested thresholds:

```text
75–100 fresh
40–74 functional
20–39 fatigued
5–19 exhausted
0–4 collapse risk
```

Low stamina modifies initiative, physical power, concentration, and recovery. It does not prevent all action at an exact threshold unless a condition does.

### 5.4 Recovery

Recovery considers:

- elapsed interval;
- rest type;
- sleep quality;
- base stamina;
- food and hydration if enabled;
- pain and injuries;
- conditions;
- environment;
- magic or medicine.

---

## 6. Magic model

### 6.1 Character magic dimensions

```text
MagicState
├── mana_current: 0..100
├── mana_capacity: 0..100
├── mana_control: 0..100
├── magic_sensitivity: 0..100
├── magic_resistance: 0..100
├── casting_speed: 0..100
├── spell_stability: 0..100
├── school_affinities[]
├── element_affinities[]
├── growth_potential[]
└── version
```

`mana_current` is a resource. Capacity and other dimensions are capability values.

### 6.2 World magic foundations

Before magic is enabled, the seed defines:

- source of magic;
- who can perceive or use it;
- mana acquisition and recovery;
- schools/elements;
- costs;
- casting mechanisms;
- range and targeting;
- countermeasures;
- failure modes;
- forbidden or impossible effects;
- resurrection rules if any;
- interaction with technology, biology, and environment.

These are canonical lore and cannot drift through narration.

### 6.3 Spell definition

```text
SpellDefinition
├── spell_id
├── name
├── school_ids
├── element_ids
├── effect_templates
├── prerequisites
├── minimum_proficiency
├── mana_cost_formula
├── stamina_cost_formula?
├── cast_time_class
├── range_class
├── target_rules
├── concentration_requirements
├── material_requirements
├── failure_modes
├── counters
├── visibility
├── legality/lore tags
└── world_rule_version
```

### 6.4 Known spell

```text
KnownSpell
├── character_id
├── spell_id
├── proficiency
├── learned_event_id
├── variants
├── reliability
└── last_used_phase_id
```

A character cannot cast a known spell that is absent from context or fails prerequisites.

### 6.5 Improvised magic

Free-form magical attempts are allowed through `CAST_MAGIC` with `improvised = true`.

The validator derives a feasible envelope from:

- known schools and concepts;
- affinities;
- control;
- mana;
- existing world rules;
- similarity to known spells;
- preparation and materials.

Improvised attempts have:

- increased uncertainty;
- possible higher cost;
- explicit failure modes;
- no automatic permanent learning;
- skill-progress evidence if meaningful.

The model cannot create a new rule of magic to make the improvisation succeed.

### 6.6 Mana

Mana cannot become negative. An action requiring more than available mana is invalid unless an established rule permits overdrawing with explicit injury or condition effects.

Mana recovery follows world rules and may be:

- passive;
- rest-based;
- location-based;
- item-based;
- ritual-based.

---

## 7. Conditions

A condition is a persistent effect that is not best represented as a localized injury.

Examples:

- poisoned;
- burning;
- stunned;
- frozen;
- cursed;
- diseased;
- frightened;
- magically silenced;
- exhausted;
- grieving;
- transformed.

```text
Condition
├── condition_id
├── target_entity_id
├── condition_type
├── severity
├── source_event_id
├── starts_at_phase_id
├── ends_at_phase_id?
├── tick_policy
├── modifiers
├── visibility
├── removal_conditions
└── status
```

Condition ticks are deterministic scheduled effects unless the condition explicitly requires model interpretation.

---

## 8. Injury model

### 8.1 Injury contract

```text
Injury
├── injury_id
├── character_id
├── body_region
├── injury_type
├── severity: 0..100
├── bleeding: 0..100
├── pain: 0..100
├── mobility_effect
├── dexterity_effect
├── consciousness_risk
├── infection_risk
├── healing_progress: 0..100
├── treatment_state
├── permanent_consequence?
├── source_event_id
├── created_phase_id
├── resolved_phase_id?
└── version
```

### 8.2 Body regions

Initial generalized regions:

```text
HEAD
NECK
TORSO
LEFT_ARM
RIGHT_ARM
LEFT_HAND
RIGHT_HAND
LEFT_LEG
RIGHT_LEG
INTERNAL
GENERAL
```

World-specific anatomy can extend this taxonomy. Extension must include functional mapping.

### 8.3 Injury types

```text
BLUNT_TRAUMA
CUT
PUNCTURE
BURN
FRACTURE
SPRAIN
DISLOCATION
CRUSH
INTERNAL_TRAUMA
MAGICAL_DAMAGE
TOXIC
FROST
OTHER
```

### 8.4 Severity interpretation

| Severity | Typical interpretation |
|---:|---|
| 1–15 | minor |
| 16–35 | moderate |
| 36–60 | serious |
| 61–80 | critical |
| 81–100 | catastrophic |

Severity alone does not determine death. Location, bleeding, internal trauma, treatment, and world biology matter.

### 8.5 Functional effects

Injuries calculate modifiers such as:

- reduced movement;
- reduced effective strength/dexterity;
- casting concentration penalty;
- inability to use a limb;
- pain and stress;
- consciousness risk;
- travel restrictions.

The effect is derived from injury state and rule definitions.

---

## 9. Healing and treatment

### 9.1 Healing inputs

- injury type and severity;
- elapsed time;
- rest;
- treatment quality;
- healer skill;
- medicine or magic;
- base stamina;
- nutrition/environment if enabled;
- infection;
- continued exertion;
- species rules.

### 9.2 Treatment events

Treatment is an action with its own validation and possible outcome. It may:

- stop bleeding;
- reduce pain;
- stabilize life status;
- reduce infection risk;
- accelerate healing;
- worsen an injury if performed badly.

### 9.3 Healing progression

Healing is scheduled and deterministic after treatment state is known. The model may classify unusual complications, but it cannot narrate a fracture away in one ordinary rest phase.

### 9.4 Permanent consequences

Serious injuries may create:

- scars;
- reduced potential;
- chronic pain;
- disability;
- prosthetic or magical replacement;
- fear or trauma evidence;
- visual appearance version.

Permanent consequences require a typed effect and source event.

---

## 10. Combat lifecycle

Combat is a scene type, not a separate universe.

### 10.1 Entry

A combat scene begins when:

- an accepted hostile attempt targets another entity;
- participants enter a dangerous active conflict;
- an existing combat activity continues;
- the World Engine creates an unavoidable environmental threat.

### 10.2 Combat exchange

Each exchange follows:

```text
1. Select eligible actor by initiative and scene state.
2. Generate or receive actor attempt.
3. Determine eligible targets and perceived attempt.
4. Generate bounded target reaction where allowed.
5. Calculate feasible outcome envelope.
6. Resolve outcome with deterministic scores, stored randomness,
   and model interpretation only inside the envelope.
7. Validate effect commands.
8. Commit exchange or complete scene transaction according to mode.
9. Recalculate ability and willingness to continue.
```

### 10.3 Exchange budget

Default maximum per phase:

- three attack/reaction exchanges;
- one final disengage, surrender, collapse, or continuation decision;
- unresolved combat continues next phase.

Large group combat uses aggregated sides and spotlight exchanges rather than one call per combatant.

### 10.4 Initiative

Initiative uses:

- preparation;
- surprise;
- perception;
- dexterity;
- relevant skill;
- current stamina;
- injuries;
- action urgency;
- environmental advantage;
- seeded random variation.

Narrative scene priority does not decide combat initiative.

### 10.5 Feasible outcome envelope

The combat calculator produces allowed outcome classes such as:

```text
CLEAN_SUCCESS
SUCCESS_WITH_COST
PARTIAL_CONTACT
STALEMATE
FAILED_ATTEMPT
COUNTERED
INTERRUPTED
CATASTROPHIC_FAILURE
```

It also produces bounded injury and resource ranges. The resolver model may choose and explain an outcome inside those ranges.

### 10.6 Randomness

Production stores a seed and generated roll values per resolution. Approximate replay is sufficient, but the same resolution retry must reuse the same randomness to prevent outcome fishing.

### 10.7 Tactical quality

The model or deterministic classifier may score whether an attempt is tactically coherent from the character’s available knowledge. This score is advisory and bounded. Fluent prose must not outweigh impossible geometry or absent capability.

### 10.8 Disengagement and surrender

Participants may:

- flee;
- surrender;
- negotiate;
- become unable to continue;
- choose not to pursue.

Combat should not automatically continue until death.

---

## 11. Social and intelligence checks

Stats do not replace roleplay.

For persuasion, deception, investigation, or analysis:

1. character states an actual approach or argument;
2. relevant skill and stat create capability bounds;
3. relationship, evidence, stakes, and target values matter;
4. the target may react according to their beliefs and agency;
5. the resolver determines whether the attempt changes belief, behaviour, or only emotional pressure.

High charisma does not mind-control. High intelligence does not reveal unavailable information. High perception does not guarantee noticing an imperceptible event.

---

## 12. Incapacitation, dying, and death

### 12.1 Functional states

```text
HEALTHY
IMPAIRED
CRITICAL
UNCONSCIOUS
DYING
DEAD
```

These are derived from injuries, conditions, consciousness, and world biology, then stored as current life state for efficient scheduling.

### 12.2 Dying

A character in `DYING` receives scheduled deterioration or stabilization checks. Without treatment, severe bleeding or organ failure may progress to death.

### 12.3 Death determination

Death requires one of:

- a deterministic lethal condition reaches its terminal state;
- catastrophic injury satisfies world-rule criteria;
- a validated resolver result inside a lethal feasible envelope;
- a deity override.

Death is committed through `MARK_DEATH`, which is available only to a high-impact resolver schema and must include causal injuries/effects.

A small conversation resolver never receives `MARK_DEATH` in its allowed effect schema.

### 12.4 No accidental resurrection

Healing cannot target a dead character unless an explicit resurrection mechanism is selected. Changing `life_status` directly is forbidden outside the return-from-death workflow.

---

## 13. Resolver responsibilities

The resolver receives:

- validated attempts and reactions;
- relevant canonical state;
- rule-calculated scores and constraints;
- allowed outcome envelope;
- allowed effect-command subset;
- random results;
- narration constraints.

It returns:

- outcome class;
- effect commands;
- delayed consequences;
- observation seeds;
- compact justification referencing provided factors;
- confidence.

It never returns SQL, arbitrary patch documents, or free-form “new state.”

---

## 14. Rule configuration and versioning

Every world references a `RuleSetVersion` containing:

- formulas;
- thresholds;
- cost tables;
- growth policy;
- injury definitions;
- magic foundations;
- combat randomness policy;
- death policy.

Rule changes do not retroactively modify committed events. New resolutions use the active rule version, stored in provenance.

Stage 0 and Stage 1 use a minimal ruleset. Do not implement all formulas before their stage.

---

## 15. Persistence requirements

At full scope, persist:

```text
stat_definition
stat_state
stat_modifier
skill_definition
skill_state
skill_progress_evidence
magic_state
magic_affinity
spell_definition
known_spell
condition
injury
injury_treatment
rule_set_version
resolution_randomness
```

Effect payloads retain before/after snapshots for audit, but current state is relationally queryable.

---

## 16. Required tests

### Unit tests

- stat clamping and potential caps;
- modifier stacking;
- stamina costs and recovery;
- mana prerequisites;
- skill evidence aggregation;
- injury functional modifiers;
- healing progression;
- initiative calculation;
- allowed outcome envelope generation.

### Property tests

- resources never become negative;
- base stats stay within `0..100`;
- ordinary growth never exceeds potential;
- retries reuse randomness and effects;
- healing never reduces progress without a complication event;
- dead characters cannot be healed through ordinary effects;
- an unavailable effect type cannot appear in a restricted resolver schema.

### Scenario tests

1. A weaker prepared fighter defeats a stronger surprised opponent through a plausible path.
2. A severely weaker unprepared fighter cannot win solely because the resolver wrote dramatic prose.
3. A character lacks mana and falls back rather than casting.
4. An improvised spell partially succeeds with higher cost.
5. A broken leg prevents ordinary travel and persists across phases.
6. Timely treatment stops bleeding and prevents death.
7. Combat continues across phase boundaries without duplicate injuries.
8. A high-charisma request fails because it violates the target’s absolute boundary.
9. Repeated trivial training gives diminishing progress.
10. A lethal effect is unavailable in an ordinary conversation.

---

## 17. Stage introduction map

| Capability | First required stage |
|---|---:|
| Basic stamina and simple movement/social rules | 1 |
| Core stats, skills, travel costs | 2 |
| Full injury model, magic, hybrid combat | 3 |
| Image-visible injuries/appearance effects | 4 |
| Age curves, inheritance, late-life decline | 5 |

---

## 18. Definition of done

The subsystem is complete for a stage when:

- every required capability has typed state and effects;
- resource and prerequisite checks happen before model resolution;
- a model cannot exceed a calculated outcome envelope;
- no HP abstraction remains in runtime logic;
- injuries create persistent functional consequences;
- progression is evidence-backed and bounded;
- combat can stop, continue, surrender, or carry into another phase;
- death is rare, causally auditable, and unavailable to low-impact schemas;
- all rule versions and random inputs are recorded with committed outcomes.
