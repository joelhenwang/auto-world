# LangGraph Agent Workflows

**Version:** 1.0  
**Status:** Normative application-workflow specification  
**Primary owners:** `agents.*`, `application.workflows`, `infrastructure.langgraph`  
**Required reading:** `03`–`07`, `11`, `12`, `14`, `15`, `21`

---

## 1. Purpose

This document defines where LangGraph is used, where it is deliberately not used, the bounded graphs and state schemas, node responsibilities, checkpoint policy, interrupts, retry boundaries, and graph testing.

LangGraph orchestrates bounded reasoning workflows. It does not own the global fictional clock, canonical world state, distributed job queue, or a character’s lifetime memory.

---

## 2. Hard boundary

Use LangGraph for:

- assembling a bounded task from supplied context;
- invoking a model role;
- validating and repairing structured output;
- optionally invoking narrowly scoped read tools;
- returning a typed proposal or derived artefact;
- resuming an interrupted bounded workflow.

Do not use LangGraph for:

- advancing phases indefinitely;
- storing canonical entity state;
- acting as the relational database;
- holding a character’s lifetime chat transcript;
- coordinating image workers;
- publishing external jobs;
- applying effect commands;
- owning idempotency of canonical commits.

---

## 3. Graph catalog

```text
CharacterDecisionGraph
CharacterReactionGraph
DirectorProposalGraph
NpcActorGraph
SemanticValidationGraph
SceneResolutionGraph
SceneNarrationGraph
ObservationWordingGraph
DailyMemoryConsolidationGraph
MonthlyReflectionGraph
MacroSimulationProposalGraph
QualityEvaluationGraph
RetrievalQueryGraph
```

Stage documents determine which graphs are implemented.

---

## 4. Common graph principles

### 4.1 Typed state

Each graph defines its own `TypedDict` or Pydantic state. Do not use one universal dictionary with optional fields for every workflow.

### 4.2 Minimal state

Graph state contains:

- immutable identifiers;
- sealed input package or reference;
- model call attempts;
- parsed candidate;
- validation errors;
- final typed result;
- workflow status.

It does not contain ORM sessions, database connections, API keys, or mutable canonical entities.

### 4.3 Side-effect placement

Model calls and approved read tools are side effects inside graph nodes. Canonical database writes occur outside the graph in application command handlers.

A graph returns a proposal. The caller validates workflow identity and then sends it to domain services.

### 4.4 One bounded regeneration

Every graph has an explicit maximum attempts field. The default is:

```text
initial generation
+ local syntax repair
+ one model regeneration
```

No graph loops until the model “gets it right.”

### 4.5 No hidden reasoning requirement

Prompts request concise decision summaries or cited factors when needed. Do not request or persist private chain-of-thought. Validation uses observable fields and supplied evidence.

---

## 5. Checkpoint and thread policy

LangGraph checkpoint state is execution state, not canon.

### 5.1 Thread ID

Use a deterministic bounded-workflow identifier:

```text
world:{world_id}:phase:{phase_id}:scene:{scene_id_or_none}:actor:{actor_id_or_none}:task:{task_type}:generation:{generation}
```

A new phase decision uses a new thread ID. Do not use one thread for an entire character lifespan.

### 5.2 Checkpointer

- tests: in-memory checkpointer;
- local durable stages: PostgreSQL checkpointer where resumption is useful;
- later Temporal execution: graph checkpointing remains optional and must not duplicate workflow ownership unnecessarily.

The checkpointer database schema may share PostgreSQL but lives in a separate schema/namespace from canonical domain tables.

### 5.3 Store

LangGraph’s cross-thread store is not the project’s character memory system. If used for framework-specific convenience, it may cache noncanonical artefacts only. Canonical memories remain in project tables and are retrieved by the context assembler.

### 5.4 Resume

Before resuming a graph:

- confirm the task is still active;
- confirm no final result already exists for the idempotency key;
- confirm the phase snapshot is unchanged/sealed;
- do not re-run completed canonical effects.

---

## 6. Common workflow state

Illustrative base fields:

```python
from typing import Any, Literal, NotRequired, TypedDict


class BaseWorkflowState(TypedDict):
    workflow_id: str
    idempotency_key: str
    task_type: str
    model_profile_id: str
    prompt_version_id: str
    context_package_id: str
    attempt: int
    max_attempts: int
    raw_response: NotRequired[str]
    parsed_candidate: NotRequired[dict[str, Any]]
    syntax_errors: NotRequired[list[str]]
    schema_errors: NotRequired[list[str]]
    domain_errors: NotRequired[list[str]]
    final_status: NotRequired[Literal["SUCCEEDED", "FALLBACK", "FAILED"]]
    model_call_ids: list[str]
```

Task graphs extend this with typed input and output fields.

---

## 7. CharacterDecisionGraph

### 7.1 Purpose

Produce exactly one `ActionProposal` for one persistent character from a sealed phase snapshot and limited perspective.

### 7.2 Input

```text
character_id
phase_id
phase_snapshot_id
sealed_context_package
allowed_action_families
output_schema
sampling_profile
```

### 7.3 Nodes

```text
START
  ↓
validate_input_package
  ↓
prepare_prompt
  ↓
invoke_character_model
  ↓
parse_and_schema_validate
  ├── valid → domain_validate
  └── syntax issue → local_repair → parse_and_schema_validate
                               
 domain_validate
  ├── valid → finalize
  ├── retryable invalid and attempt left → prepare_regeneration_prompt
  │                                      → invoke_character_model
  └── terminal invalid → create_safe_fallback

finalize → END
```

### 7.4 Input validation

Verify:

- package observer equals character;
- package snapshot equals requested snapshot;
- package hash verifies;
- character is active or player-controlled;
- allowed action families are nonempty;
- prompt and schema versions are registered.

### 7.5 Domain validation

Checks include:

- actor ID matches character;
- target IDs are visible/known or explicitly inferable;
- action family is allowed;
- no outcome is asserted as an effect;
- resources and capabilities are plausible at proposal level;
- fallback is safe and valid;
- another character’s reaction is not authored;
- estimated duration and interruption conditions are valid.

### 7.6 Fallback

Use, in order:

1. `CONTINUE_ACTIVITY` when a valid activity exists;
2. `REST` when state strongly requires it;
3. `OBSERVE` when meaningful perception is available;
4. `WAIT` otherwise.

The fallback is deterministic and labeled as such.

---

## 8. CharacterReactionGraph

### 8.1 Purpose

Allow a target or participant to react to an accepted attempt within a scene.

### 8.2 Input

- character-specific perception of the attempt;
- current scene state;
- remaining beat budget;
- allowed reaction families;
- relevant abilities/resources;
- no unobserved attacker intent.

### 8.3 Output

One `ReactionProposal`:

```text
REACT
DECLINE_TO_REACT
UNABLE_TO_REACT
CONTINUE_PREPARED_ACTION
```

The graph cannot determine whether the reaction succeeds.

### 8.4 Prepared reactions

A claim such as “Alex had prepared a dodge spell” is accepted only when a pre-existing plan, condition, spell preparation, or earlier committed action supports it. The reaction graph cannot retroactively invent preparation.

---

## 9. DirectorProposalGraph

### 9.1 Purpose

Produce one optional Director proposal after a deterministic trigger.

### 9.2 Context

The Director may receive omniscient summaries, but the package must label:

- canonical facts;
- secrets;
- character-private knowledge;
- active arcs;
- pacing metrics;
- trope cooldowns;
- privileges;
- effect and entity budgets.

### 9.3 Nodes

```text
validate_trigger
  ↓
assemble_director_brief
  ↓
invoke_director
  ↓
parse_validate
  ↓
check_causal_basis
  ↓
check_privileges_budgets_and_tropes
  ├── valid → finalize proposal
  ├── harmless no-event → finalize NO_PROPOSAL
  └── invalid → one regeneration or NO_PROPOSAL
```

A failed Director graph must not block an otherwise valid phase unless a mandatory scheduled world event depends on it.

---

## 10. NpcActorGraph

### 10.1 Purpose

Generate bounded actions or dialogue for one or several temporary NPCs from their limited perspectives.

### 10.2 Isolation

The NPC graph receives no omniscient Director context. A new context package is assembled for each NPC. Batched prompts use clearly separated records and return one result keyed by NPC ID.

### 10.3 Limits

- one primary action per NPC;
- no NPC creation;
- no direct state writes;
- strict beat budget;
- supporting NPCs may use a smaller model profile later.

---

## 11. SemanticValidationGraph

### 11.1 Purpose

Evaluate aspects that deterministic validation cannot fully decide, without resolving the scene.

Examples:

- does the proposed action fit supplied personality and goals?
- is the stated social approach coherent?
- does the free-form magic intent correspond to known magical concepts?
- does a Director event feel causally connected to cited facts?

### 11.2 Output

```text
SemanticValidationResult
├── verdict: ACCEPT | REJECT | ACCEPT_WITH_WARNINGS
├── issue_codes[]
├── cited_input_factors[]
├── correction_constraints[]
└── confidence
```

It cannot add facts, modify the proposal, or produce effects.

### 11.3 Invocation policy

Use only when deterministic validators return `SEMANTIC_REVIEW_REQUIRED`. Do not spend a model call validating trivial `WAIT` actions.

---

## 12. SceneResolutionGraph

### 12.1 Purpose

Select an outcome inside the deterministic feasible envelope and return typed effect commands.

### 12.2 Input

- immutable scene snapshot;
- accepted attempts and reactions;
- deterministic prerequisites;
- capability calculations;
- random values;
- feasible outcome classes and ranges;
- task-specific effect schema;
- delayed-effect rules;
- observer candidates.

### 12.3 Nodes

```text
validate_resolution_input
  ↓
prepare_restricted_schema
  ↓
choose deterministic-only path?
  ├── yes → deterministic_resolution
  └── no  → invoke_resolver_model
              ↓
           parse_validate
              ↓
           envelope_validate
              ↓
           effect_validate
              ├── valid → finalize
              └── retryable → one regeneration

terminal invalid → deterministic conservative fallback or PAUSE
```

### 12.4 Canonical boundary

The graph returns `SceneResolution`. The caller then invokes the transaction service. The graph never marks the scene committed.

### 12.5 Conservative fallback

A fallback cannot invent a dramatic outcome. Prefer:

- invalidated attempt;
- failed attempt with already-paid unavoidable costs;
- no material state change;
- continuation into next phase;
- pause when a safe result cannot be inferred.

---

## 13. SceneNarrationGraph

### 13.1 Purpose

Render already committed facts into prose or visual-novel beats.

### 13.2 Input

- committed event facts;
- accepted dialogue;
- observation/perspective mode;
- character voice guides;
- content and style rules;
- prohibited additions.

### 13.3 Output

Narration is noncanonical. It is validated against:

- named participants;
- outcome class;
- location;
- injuries/effects;
- perspective knowledge;
- no new item, spell, NPC, or relationship fact.

A failed narration uses a deterministic timeline summary. It never rolls back the event.

---

## 14. ObservationWordingGraph

### 14.1 Purpose

Phrase a deterministic allowed-facts payload from one observer’s perspective.

### 14.2 Safety

The graph receives:

- allowed perceived facts;
- explicitly omitted keys;
- sensory channels;
- confidence and uncertainty;
- the observer’s expression style only if appropriate.

After generation, a fact-extraction validator ensures no omitted canonical key is reintroduced. On failure, use a deterministic template.

---

## 15. DailyMemoryConsolidationGraph

### 15.1 Purpose

Group observations into episodes and create a sourced daily summary.

### 15.2 Nodes

```text
load_owner_visible_records
  ↓
cluster_deterministically
  ↓
summarize_clusters
  ↓
validate_source_citations
  ↓
extract_memory_candidates
  ↓
validate_owner_and_fact_scope
  ↓
return derived records
```

Database writes occur in a separate consolidation transaction.

### 15.3 Degradation

When quota is unavailable, use extractive grouping and defer richer prose. The next phase can use raw recent observations.

---

## 16. MonthlyReflectionGraph

### 16.1 Purpose

Propose bounded identity, goal, and personality evolution from verified monthly evidence.

### 16.2 Restrictions

- every change cites development evidence;
- trait deltas remain within configured caps;
- no backstory rewrite;
- no unexplained new skill or relationship;
- `NO_CHANGE` is valid and common;
- output is reviewed by deterministic projection rules before commit.

---

## 17. MacroSimulationProposalGraph

Introduced in Stage 5. It proposes aggregated changes for a week, month, or year from deterministic inputs and constraints. It does not directly create detailed dialogue or silently resolve focus-character life decisions.

The World Engine expands or rejects proposals and stops time compression when a high-salience event requires detailed simulation.

---

## 18. Read tools

Graphs may receive narrowly scoped tools such as:

```text
get_known_entity(character_id, entity_id)
get_known_location(character_id, location_id)
search_character_memories(character_id, query, filters)
get_character_inventory(character_id)
get_character_capabilities(character_id)
get_active_plan_steps(character_id)
get_scene_participants(scene_id)
```

Rules:

- character ID is bound by the runtime, not model-supplied;
- tools are read-only;
- tools return filtered DTOs;
- every call is traced;
- no arbitrary SQL, file, shell, network, or cross-character query;
- most context should be assembled before the graph, avoiding tool loops.

---

## 19. Human interrupts

Possible graph interrupts:

- player must submit a character action;
- deity must approve a privileged world-rule change;
- operator must decide after irrecoverable semantic ambiguity;
- content boundary requires review.

Interrupt state contains a compact reason and typed expected input. It never exposes API secrets or hidden model internals.

The outer orchestrator owns pause state. A graph interrupt does not by itself advance or commit the phase.

---

## 20. Graph construction and dependency injection

Graph factories receive explicit dependencies:

```python
@dataclass(frozen=True)
class CharacterDecisionDependencies:
    model_gateway: TextModelGateway
    prompt_registry: PromptRegistry
    domain_validator: ActionProposalValidator
    repair_service: JsonRepairService
    call_recorder: ModelCallRecorder
```

Do not import global singleton clients inside nodes.

Compile graphs once per compatible configuration where possible. Task-specific effect schemas may be passed as state or created by a safe schema factory.

---

## 21. Error propagation

Nodes raise typed workflow exceptions:

```text
InvalidWorkflowInput
ProviderTransientFailure
ProviderPermanentFailure
SchemaOutputFailure
DomainOutputFailure
CheckpointConflict
WorkflowCancelled
```

Graphs map recoverable errors to state transitions. The outer task runner maps terminal failures to task status and phase policy.

Do not catch `Exception` and return `WAIT` for every failure; infrastructure corruption and invalid snapshot identity must surface.

---

## 22. Testing graphs

### 22.1 Node unit tests

Each node is tested with fake dependencies and immutable state fixtures.

### 22.2 Graph path tests

Cover:

- success first attempt;
- syntax repair;
- one regeneration;
- deterministic fallback;
- provider failure;
- checkpoint resume;
- cancellation;
- stale snapshot rejection;
- prohibited effect output;
- tool scope violation.

### 22.3 Snapshot tests

Persist generated JSON Schemas and key prompt envelopes as reviewed snapshots. Changes require explicit approval; avoid brittle snapshots of whole prose where semantics are unchanged.

### 22.4 No-database-write assertion

Graph tests should use a database spy or architectural import rule proving graph modules cannot import repository write services or ORM models.

### 22.5 Checkpoint tests

- resume after model call but before validation;
- resume after validation without repeating call when result is stored;
- reject resume if task already terminal;
- no canonical effects in checkpoint tables.

---

## 23. Stage introduction map

| Graph | First required stage |
|---|---:|
| CharacterDecisionGraph | 1 |
| CharacterReactionGraph | 1 |
| SceneResolutionGraph | 1, deterministic path first |
| SceneNarrationGraph | 1 optional; required by 2 |
| DirectorProposalGraph | 2 |
| NpcActorGraph | 2 |
| DailyMemoryConsolidationGraph | 2 |
| SemanticValidationGraph | 2–3 |
| ObservationWordingGraph | 2 |
| MonthlyReflectionGraph | 3 |
| QualityEvaluationGraph | 3 |
| MacroSimulationProposalGraph | 5 |

---

## 24. Definition of done

A graph is complete when:

- it has a narrow typed state and one typed result;
- all loops are bounded;
- context and thread identity are validated;
- it cannot mutate canonical state;
- model/provider dependencies are injected;
- every failure path is tested;
- checkpoints contain execution data only;
- no graph relies on a character lifetime chat history;
- the outer orchestrator can retry or resume it idempotently;
- its prompt and schema versions appear in model-call provenance.

---

## 25. Official references

- LangGraph persistence: <https://docs.langchain.com/oss/python/langgraph/persistence>
- LangGraph subgraphs: <https://docs.langchain.com/oss/python/langgraph/use-subgraphs>
- LangGraph checkpointers: <https://docs.langchain.com/oss/python/langgraph/checkpointers>
