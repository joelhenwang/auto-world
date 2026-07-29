# Stage 1 — First Complete Three-Phase Day

**Version:** 1.0  
**Stage outcome:** Mira and Dain autonomously complete a bounded day with three enabled phases, simultaneous primary intents, scene assembly, bounded reactions, validated resolution, perspective observations, recent memories, live API updates, and restart safety.  
**Primary proof:** `stage1-first-day-v1` scenario using fake model; sampled OpenRouter run separately.

---

## 1. Scope

Stage 1 introduces the first true model-driven vertical slice. The full calendar still contains ten phases, but the Stage 1 profile actively simulates three representative phases to keep provider requests and debugging bounded:

```text
dawn
morning
evening
```

Other phase names remain part of contracts and are skipped by the fixture profile only.

Active characters:

- Mira Talren;
- Dain Arcen.

Active locations:

- Cinder Lantern Inn;
- Market Square;
- East Bridge.

---

## 2. Required capabilities

- immutable same-phase snapshot for both characters;
- perspective-safe context package;
- CharacterDecisionGraph;
- one action proposal per active character;
- scene assembly and stable priority;
- bounded CharacterReactionGraph;
- deterministic and simple model-assisted resolution;
- atomic scene event/effects/observations/recent memories;
- simple narration or deterministic fallback;
- player control for either character at an input boundary;
- phase/day barriers;
- minimal timeline/runtime/character UI;
- WebSocket live events;
- quota reservation and safe fallbacks;
- restart at every graph/task/commit boundary.

---

## 3. Allowed action/effect scope

Action families:

```text
WAIT
OBSERVE
REST
CONTINUE_ACTIVITY
MOVE
COMMUNICATE
SOCIALIZE
INTERACT_ENVIRONMENT
```

Effects:

```text
MOVE_ENTITY
SPEND_STAMINA
RECOVER_STAMINA
ADVANCE_ACTIVITY
CREATE_CLAIM            # simple utterance representation; full belief engine Stage 2
CREATE_OBSERVATION
CREATE_RECENT_MEMORY
SCHEDULE_EFFECT
```

No combat, injury, inventory transfer, full magic, death, faction update, or NPC creation.

---

## 4. Task dependency graph

```text
S1-DB-001 stage1 schema extensions
S1-KNOW-001 perception/context assembler
S1-MODEL-001 prompts/schemas/corpus
S1-GRAPH-001 decision graph
S1-SIM-001 activation/scene assembly/priority
S1-GRAPH-002 reaction + resolution graph paths
S1-SIM-002 scene transaction integration
S1-ORCH-001 full phase/day workflow and budget
S1-API-001 commands/queries/WebSocket
S1-UI-001 minimal Vue experience
S1-QA-001 first-day scenarios/fault/leakage gate

DB + context + prompts can begin in parallel after Stage 0 freeze.
Decision graph depends on context/prompts/model gateway.
Scene integration depends on graph outputs and DB.
API/UI depend on stable projections/commands.
```

---

## 5. Parallel lanes

- Lane A: Stage 1 migration/repositories for actions/scenes/reactions/resolutions/stream events.
- Lane B: perception/context assembler and leakage tests.
- Lane C: prompt versions, JSON schemas, fake model scripts, CharacterDecisionGraph.
- Lane D: pure activation/scene assembly/priority/reaction beat logic.
- Lane E: API DTO/OpenAPI stub and Vue shell after command/query contracts freeze.
- Lane F: QA scenarios and process-kill harness extending Stage 0.

Parent agent integrates B+C → D → A transaction → orchestration → API/UI.

---

## 6. Task packets

### S1-DB-001 — Action/scene persistence

**Tables/extensions:** action_proposal, action_target, scene, scene_participant, reaction_proposal, scene_resolution, scene_run, narration, stream_event, player_control_session.  
**Constraints:** one primary action per character/phase/generation; snapshot FK; participant uniqueness; resolution idempotency; scene status transition support.  
**Tests:** migration from Stage 0 fixture; duplicate action/participant rejection.

### S1-KNOW-001 — Perception and context assembler v1

**Deliver:** sealed character context for Mira/Dain using card, snapshot state, current allowed perception, goals, directional relationship seed, recent memory, known local map/capabilities; token trimming; source/hash provenance.  
**No vector search.**  
**Tests:** private belief/other relationship absent; same snapshot ID; malicious memory delimiter; deterministic package hash.

### S1-MODEL-001 — Prompt/schema/corpus v1

**Deliver:** character decision, reaction, simple resolver, narrator/observation prompts; task-specific schemas; fake outputs for quiet/interaction/invalid cases; OpenRouter profile/sampling.  
**Tests:** render variables, schema normalization, output repair, no authored-other-reaction fixtures.

### S1-GRAPH-001 — CharacterDecisionGraph

**Deliver:** nodes/path from `13`, fake and live adapter integration, one regeneration, deterministic fallback.  
**Tests:** valid, malformed, semantic invalid, unknown target, provider outage, fallback order, checkpoint resume.

### S1-SIM-001 — Activation, scene assembly, and priority

**Deliver:** deterministic activation rules; both primary intents generated from same snapshot; scene grouping by target/location/conflict; stable priority/fairness; read/write set calculation; beat budgets.  
**Tests:** merge visit/wait; independent scenes; conflicting target; no model priority for trivial cases.

### S1-GRAPH-002 — Reaction and simple resolution

**Deliver:** CharacterReactionGraph; simple SceneResolutionGraph with restricted effects and deterministic-only path; no retroactive preparation; feasible envelope for social/movement/environment actions.  
**Tests:** perceived attempt only; no outcome by reactor; cap; invalid effect rejection; conservative fallback.

### S1-SIM-002 — Scene commit integration

**Deliver:** accepted proposals/reactions/resolution commit atomically; observations per participant; recent memories; narration outbox/derived record; continuation when beat budget ends.  
**Tests:** transaction failure, retry after commit, two independent scenes, location conflict, observation isolation.

### S1-ORCH-001 — Three-phase day workflow

**Deliver:** day/phase task graph; model-request budget reservation; parallel decision tasks; scene barriers; player `WAITING_INPUT`; phase/day finalization; pause/resume.  
**Tests:** restart at every boundary; quota shortage before phase; one provider failure fallback; no image dependency.

### S1-API-001 — API and WebSocket v1

**Deliver:** world runtime, advance/pause/resume, command status, timeline/phase/scene/character projections, player acquire/release/action, stream sequence/replay. Auth may remain loopback development profile.  
**Tests:** command idempotency, perspective DTO, WebSocket reconnect/replay, player action validation.

### S1-UI-001 — Minimal Vue client

**Deliver:** app shell, runtime header, timeline, scene detail, two character summaries, watcher/player mode, action composer, live connection/status, text/image placeholder.  
**Tests:** generated types, component tests, E2E first-day fake run, player perspective.

### S1-QA-001 — Stage gate

**Deliver:** deterministic fake-model first-day scenario, several alternative scripts, live OpenRouter sample, leakage/fault/performance report, evidence bundle.  
**Gate:** Section 8.

---

## 7. Canonical first-day workflow

For each enabled phase:

1. apply pending user commands;
2. advance clock and deterministic tick;
3. no autonomous Director call;
4. seal one phase snapshot;
5. assemble Mira and Dain contexts;
6. generate both intents from same snapshot;
7. assemble scenes;
8. process reactions within beat budget;
9. resolve and commit scenes;
10. create perspective observations and recent memories;
11. publish timeline/WebSocket records;
12. finalize phase;
13. after evening, finalize day with an extractive day summary if richer compaction is deferred.

---

## 8. Hard exit gate

- one full three-phase day completes without manual database repair;
- both characters’ primary actions reference one snapshot per phase;
- no character authors another’s reaction or outcome;
- all accepted state changes come from typed effects;
- player action is an attempt and can fail validation/resolution;
- perspective contexts/API omit the other character’s private belief and true relationship row;
- invalid/malformed model output follows repair → one regeneration → fallback;
- quota shortfall is detected before unsafe partial phase execution;
- restart after every task/graph/commit checkpoint completes without duplicates;
- WebSocket reconnect replays missed canonical events or requests resync;
- minimal UI remains usable with provider unavailable and no images;
- fake-model scenario is deterministic and passes all invariants;
- at least one live OpenRouter smoke run produces valid action proposals, but live availability is not the deterministic gate;
- lint/type/migration/security/architecture checks remain green.

---

## 9. Quality review

Human review at least three generated first days for:

- distinct voices;
- proportionate actions;
- ability to wait/rest/refuse;
- no automatic romance;
- no exposition-heavy dialogue;
- no unexplained knowledge;
- no repeated dramatic one-liners.

Findings inform prompt v2 only after deterministic gate is stable.

---

## 10. Handoff to Stage 2

Freeze:

- ActionProposal/ReactionProposal/SceneResolution v1;
- context package v1;
- phase/scene orchestration semantics;
- API/WebSocket v1 core;
- first-day model corpus;
- Stage 1 migration fixture and world backup.

Stage 2 expands participants, phases, beliefs, NPCs, travel, and compaction without changing simultaneous-intent fundamentals.
