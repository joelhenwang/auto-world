# Model Gateway, OpenRouter Integration, Quotas, and Local Migration

**Version:** 1.0  
**Status:** Normative infrastructure and application specification  
**Primary owners:** `application.models`, `infrastructure.model_gateway`, `infrastructure.openrouter`  
**Required reading:** `03`–`07`, `11`, `13`–`15`, `20`–`22`

---

## 1. Purpose

This document defines the provider-neutral model interface, initial OpenRouter implementation, capability discovery, structured-output strategy, request-budget accounting, retries, observability, privacy boundaries, and later migration to local model servers.

Initial endpoints:

```text
Text:
  nvidia/nemotron-3-super-120b-a12b:free

Embeddings:
  nvidia/nemotron-3-embed-1b:free
```

These slugs are configuration defaults, not domain constants.

As of 2026-07-29, OpenRouter lists the free text endpoint with a 262K served context and the free embedding endpoint with a 33K context. The application deliberately enforces much smaller task-specific limits. Provider capabilities and free-tier availability may change; startup capability probes are authoritative for runtime behaviour.

---

## 2. Design rules

1. Domain and agent code depend on internal protocols, never OpenRouter response classes.
2. Every request has a model role and task type, not just a model slug.
3. Capabilities are probed and cached; they are not assumed from the model name.
4. Provider success does not imply semantic validity. Pydantic and domain validation remain mandatory.
5. Free-quota availability is a scheduler resource.
6. A phase is not started unless it can finish through reserved calls or defined fallbacks.
7. Provider errors never cause duplicate canonical effects.
8. Raw prompts may contain only synthetic fictional-world data during use of endpoints that record data for service improvement.
9. Character identity and workflow semantics survive a provider or model change.
10. Streaming is presentation-only for noncanonical narration; structured decisions use complete responses initially.

---

## 3. Internal model roles

```text
CHARACTER_DECISION
CHARACTER_REACTION
DIRECTOR_PROPOSAL
NPC_ACTOR
SEMANTIC_VALIDATOR
SCENE_RESOLVER
SCENE_NARRATOR
OBSERVATION_WRITER
DAILY_SUMMARIZER
MONTHLY_REFLECTOR
MACRO_SIMULATOR
IMAGE_PROMPT_WRITER
QUALITY_EVALUATOR
RETRIEVAL_QUERY_WRITER
TEXT_EMBEDDER
```

One physical model may serve many roles. Role-specific prompts, schemas, sampling profiles, and limits remain separate.

---

## 4. Provider-neutral protocols

Illustrative Python interfaces:

```python
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel


@dataclass(frozen=True, slots=True)
class ModelMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class SamplingOptions:
    temperature: float
    top_p: float
    max_output_tokens: int
    seed: int | None = None
    stop: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProviderRoutingOptions:
    require_parameters: bool = True
    allow_fallbacks: bool = True
    data_collection: str | None = None


@dataclass(frozen=True, slots=True)
class TextGenerationRequest:
    request_id: str
    role: str
    model_profile_id: str
    messages: tuple[ModelMessage, ...]
    output_schema: type[BaseModel] | None
    sampling: SamplingOptions
    routing: ProviderRoutingOptions
    metadata: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class TextGenerationResult:
    provider_request_id: str | None
    resolved_model: str
    provider_name: str | None
    raw_text: str
    parsed: BaseModel | None
    input_tokens: int | None
    output_tokens: int | None
    finish_reason: str | None
    capability_mode: str
    latency_ms: int


class TextModelGateway(Protocol):
    async def generate(
        self, request: TextGenerationRequest
    ) -> TextGenerationResult: ...


@dataclass(frozen=True, slots=True)
class EmbeddingRequest:
    request_id: str
    model_profile_id: str
    texts: tuple[str, ...]
    input_type: str  # "query" or "passage"
    dimensions: int | None
    metadata: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class EmbeddingResult:
    vectors: tuple[tuple[float, ...], ...]
    resolved_model: str
    dimensions: int
    input_tokens: int | None
    latency_ms: int


class EmbeddingGateway(Protocol):
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult: ...
```

Real code may use domain-specific value objects rather than strings, but provider-neutral boundaries are mandatory.

---

## 5. Model profile

Persist or configure one `ModelProfile` per role/model combination.

```text
ModelProfile
├── profile_id
├── provider_kind
├── model_slug
├── role
├── enabled
├── context_limit
├── application_input_limit
├── max_output_tokens
├── supports_json_schema
├── supports_tools
├── supports_seed
├── supports_streaming
├── supports_embeddings
├── embedding_dimensions?
├── task_prefix_policy?
├── sampling_profile_id
├── provider_routing_policy
├── privacy_class
├── capability_probe_version
└── last_verified_at
```

Do not create one mutable profile called `default`. Profiles are versioned or superseded so old model-call provenance remains interpretable.

---

## 6. OpenRouter client

### 6.1 Transport

Use an async HTTP client or the async OpenAI-compatible SDK pointed at:

```text
https://openrouter.ai/api/v1
```

A thin custom adapter is preferred so the project owns:

- request IDs;
- headers;
- error normalization;
- capability routing;
- response capture;
- quota accounting;
- schema repair;
- provider-independent results.

Do not spread SDK calls across graphs or services.

### 6.2 Required headers

```http
Authorization: Bearer ${OPENROUTER_API_KEY}
Content-Type: application/json
X-Title: Autonomous Fictional World
HTTP-Referer: <optional configured project URL>
```

Use the currently documented OpenRouter attribution headers accepted by the API client. Keep them optional in local development. Never log the authorization header.

### 6.3 Timeout classes

Suggested initial values:

```yaml
connect_seconds: 10
read_character_seconds: 180
read_resolver_seconds: 120
read_summary_seconds: 180
read_embedding_seconds: 60
total_request_seconds: 240
```

All values are configuration. Long timeout does not imply unlimited workflow retries.

### 6.4 Connection pooling

Use one application-scoped async client per process with:

- connection pooling;
- bounded concurrent connections;
- keepalive;
- TLS verification enabled;
- no user-controlled proxy by default.

---

## 7. Text request payload

Conceptual payload:

```json
{
  "model": "nvidia/nemotron-3-super-120b-a12b:free",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "temperature": 0.45,
  "top_p": 0.9,
  "max_tokens": 1200,
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "character_action_proposal",
      "strict": true,
      "schema": {}
    }
  },
  "provider": {
    "require_parameters": true,
    "allow_fallbacks": true
  }
}
```

The adapter generates the JSON Schema from the Pydantic contract and removes unsupported schema features through a tested schema-normalization step.

Do not send `response_format` when the active capability mode says the selected endpoint cannot accept it.

---

## 8. Structured-output capability modes

OpenRouter structured-output support is endpoint-specific and may change. Use four modes:

```text
NATIVE_STRICT
  Send JSON Schema with strict mode and require supporting endpoint parameters.

NATIVE_BEST_EFFORT
  Send JSON Schema, but still expect provider variance.

JSON_OBJECT_PROMPTED
  Request JSON-only output without relying on native schema enforcement.

TEXT_REPAIR_REQUIRED
  Receive text, extract a single JSON document, repair syntax locally,
  then validate. Used only as a last supported mode.
```

### 8.1 Startup capability probe

For each active text profile:

1. fetch model/provider metadata when available;
2. issue a tiny, non-sensitive schema request;
3. verify HTTP acceptance;
4. verify required fields and `additionalProperties = false` behaviour;
5. store the observed mode and timestamp;
6. run a second probe when provider selection can differ materially;
7. fail startup only when the active stage has no fallback mode.

### 8.2 Runtime drift

If a request fails because a parameter is unsupported:

- mark the capability observation stale;
- retry once using the next safe mode if the task permits;
- enqueue a re-probe;
- do not globally downgrade all providers without evidence.

### 8.3 Validation chain

```text
provider response
    ↓
extract one candidate JSON object
    ↓
syntax repair only
    ↓
Pydantic strict validation
    ↓
domain validation
    ↓
semantic validation if required
    ↓
accept or one bounded regeneration
    ↓
fallback or pause
```

Syntax repair may fix quotation, commas, or code fences. It may not invent missing semantic fields or alter values to satisfy domain rules.

---

## 9. Schema minimization

Do not send the universal effect-command union to every resolver request.

The application creates a task-specific schema containing only allowed command variants.

Examples:

```yaml
conversation:
  - CREATE_CLAIM
  - UPDATE_BELIEF_EVIDENCE
  - RELATIONSHIP_EVIDENCE
  - UPDATE_PLAN
  - SCHEDULE_EFFECT

travel:
  - MOVE_ENTITY
  - SPEND_STAMINA
  - ADVANCE_ACTIVITY
  - APPLY_CONDITION
  - SCHEDULE_EFFECT

combat_high_impact:
  - SPEND_STAMINA
  - SPEND_MANA
  - APPLY_INJURY
  - APPLY_CONDITION
  - TRANSFER_ITEM
  - SKILL_PROGRESS_EVIDENCE
  - MARK_DEATH
```

This is both a reliability control and a security boundary.

---

## 10. Embeddings integration

### 10.1 Endpoint

Use OpenRouter’s embeddings API with batched text inputs.

Conceptual payload:

```json
{
  "model": "nvidia/nemotron-3-embed-1b:free",
  "input": [
    "passage: Alex remembers the promise made beneath the bridge.",
    "passage: Sein learned that the eastern gate closes at dusk."
  ],
  "encoding_format": "float"
}
```

Only pass `dimensions` or `input_type` if the active endpoint profile supports the desired parameter and integration tests confirm semantics.

### 10.2 Native representation

Initial configuration:

```yaml
embedding_dimensions: 2048
normalized: true
query_prefix: "query: "
passage_prefix: "passage: "
```

The adapter applies prefixes. Input text stored in memory remains prefix-free.

### 10.3 Batching

Batch by:

- same model profile;
- same prefix/input type;
- maximum item count;
- maximum combined token estimate;
- privacy class.

Preserve request-order mapping. Validate response count equals input count and every vector has the expected dimension and finite values.

### 10.4 Failure behaviour

An embedding failure:

- records a failed task;
- leaves the memory relationally available;
- retries asynchronously;
- never blocks canonical event commit;
- never causes cross-character fallback retrieval.

---

## 11. Free-tier quota and request budgeting

OpenRouter currently documents platform limits for model slugs ending in `:free`, including per-minute and per-day caps that depend on account history. The exact values and account state must be treated as external runtime facts. At the time this handbook was written, the documented baseline was 20 requests per minute, with lower and higher daily tiers commonly documented as 50 and 1,000 requests. Do not hard-code these values as guaranteed service terms.

### 11.1 Runtime checks

Use:

- `GET /api/v1/key` for key credit/usage metadata;
- observed `429` response headers;
- local daily and rolling-minute ledgers;
- explicit operator configuration when the external API does not expose remaining free requests pre-emptively.

### 11.2 Ledger records

```text
RequestBudgetLedger
├── reservation_id
├── provider
├── model_profile_id
├── quota_bucket
├── operation_type
├── world_id
├── phase_id?
├── reservation_key
├── reserved_requests
├── consumed_requests
├── released_requests
├── status
├── window_start
├── window_end
├── created_at
└── updated_at
```

Statuses:

```text
RESERVED
PARTIALLY_CONSUMED
CONSUMED
RELEASED
EXPIRED
```

### 11.3 Phase reservation

Before a phase begins, calculate:

```text
mandatory calls
+ maximum one repair/regeneration where policy requires it
+ optional calls separated from mandatory calls
```

For Stage 1 with two active characters and no Director call, a conservative reservation might include:

```text
2 character decisions
+ 2 possible reaction calls
+ 1 resolver call when model-assisted
+ 2 bounded repair calls
= 7 mandatory-capacity units
```

The exact plan is derived from the active scene strategy. Deterministic fallbacks can reduce the mandatory reservation.

Do not reserve optional narration or embeddings as required to finish a phase.

### 11.4 Degradation ladder

When quota is constrained:

1. disable quality critic;
2. use deterministic narration templates;
3. defer embeddings;
4. use extractive daily summaries;
5. batch NPCs;
6. avoid a non-triggered Director call;
7. replace model-assisted resolver with deterministic resolution where supported;
8. use safe character fallback actions;
9. pause before starting the phase if correctness cannot be preserved.

Never degrade by sharing character context or skipping state validation.

### 11.5 UTC reset

External daily usage may reset in UTC. Store provider windows explicitly and show them in the operations UI. Do not assume the fictional calendar or Europe/Lisbon day boundary matches provider quota reset.

---

## 12. Error taxonomy

Normalize provider failures:

```text
AUTHENTICATION_ERROR
CREDIT_LIMIT_ERROR
RATE_LIMIT_ERROR
PROVIDER_CAPACITY_ERROR
UNSUPPORTED_PARAMETER_ERROR
MODEL_NOT_AVAILABLE
CONTENT_REJECTED
NETWORK_TIMEOUT
NETWORK_ERROR
MALFORMED_RESPONSE
SCHEMA_VALIDATION_ERROR
SEMANTIC_VALIDATION_ERROR
EMBEDDING_DIMENSION_ERROR
CANCELLED
UNKNOWN_PROVIDER_ERROR
```

Preserve sanitized provider code and request ID for diagnostics.

### 12.1 Retry policy

| Error | Retry |
|---|---|
| transient network timeout | up to 2 with exponential backoff and jitter |
| provider capacity | up to 2; allow provider fallback if configured |
| 429 | honor `Retry-After`; do not spin; possibly defer/pause |
| 402/credit limit | no immediate retry; operator/config action |
| auth | no retry |
| unsupported parameter | one capability-mode downgrade |
| malformed/schema output | one repair plus one regeneration |
| semantic invalidity | one regeneration with explicit validation errors |
| content rejection | no blind retry; sanitize only if input policy permits |

Workflow-level retries reuse the same idempotency key and randomness.

### 12.2 Backoff

Suggested base:

```text
delay = min(max_delay, base × 2^attempt) + jitter
```

Use provider `Retry-After` when present. Persist `next_attempt_at`; do not sleep while holding a database transaction or task lease.

---

## 13. Sampling profiles

Initial defaults; tune through evaluation rather than intuition.

| Role | Temperature | Top-p | Output cap |
|---|---:|---:|---:|
| character decision | 0.55 | 0.90 | 1,200 |
| character reaction | 0.45 | 0.90 | 800 |
| Director proposal | 0.65 | 0.92 | 1,500 |
| semantic validator | 0.10 | 0.80 | 700 |
| resolver | 0.20 | 0.85 | 1,200 |
| scene narrator | 0.65 | 0.95 | 2,500 |
| observation writer | 0.15 | 0.85 | 900 |
| daily summarizer | 0.20 | 0.85 | 1,500 |
| monthly reflector | 0.30 | 0.90 | 2,000 |
| quality evaluator | 0.00 | 1.00 | 900 |

Sampling values are recorded with every call. A role may have stage-specific profiles.

---

## 14. Prompt and response logging

`ModelCall` stores:

```text
model_call_id
request_id
world_id
phase_id?
scene_id?
character_id?
role
model_profile_id
prompt_version_id
context_package_id?
input_hash
sanitized_request_payload or object reference
raw_response or object reference
parsed_output
validation_outcome
provider_request_id
resolved_model
provider_name
sampling
input_tokens
output_tokens
latency
attempt_number
error_class
started_at
completed_at
```

### 14.1 Privacy modes

```text
FULL_SYNTHETIC_DEBUG
  Store full fictional prompts and responses locally.

HASHED_PRODUCTION
  Store hashes, schemas, token counts, provenance, and selected safe excerpts.

NO_RAW_CONTENT
  Do not retain provider payload content beyond required operational metadata.
```

Initial development may use `FULL_SYNTHETIC_DEBUG` because content is fictional. Never include API keys, personal data, private company data, or real-person images/voices in free endpoint requests.

### 14.2 External logging warning

The selected free NVIDIA text endpoint states that submitted sessions may be recorded for security and product improvement. Treat this as a hard data-classification constraint. Use only synthetic fictional content until local/private inference is active or contractual privacy is separately established.

---

## 15. Context and output limits

Even though the text endpoint is listed with a large served context, enforce:

```yaml
ordinary_input_target: 18000_to_20000_tokens
hard_application_input_limit: 32000_tokens
ordinary_decision_output_limit: 1200_tokens
narration_output_limit: 2500_tokens
```

Reasons:

- quota and latency;
- clearer instruction hierarchy;
- easier evaluation;
- future compatibility with local models;
- avoidance of lifetime-chat anti-patterns.

Token counting is provider/model-dependent. Use a conservative local estimator and inspect actual usage returned by the provider.

---

## 16. Local model migration

### 16.1 Target shape

```text
Model Gateway
├── OpenRouterTextAdapter
├── OpenRouterEmbeddingAdapter
├── OpenAICompatibleLocalTextAdapter
├── LocalEmbeddingAdapter
└── routing and health registry
```

The rest of the application keeps the same protocols.

### 16.2 Character identity independence

No memory, checkpoint, or model-specific chat session is required to move a character. The gateway receives a complete sealed context package per decision.

### 16.3 Local topology target

```text
Halo A:
  primary text model replica

Halo B:
  second text replica / small-model services / overflow

RTX 4060 Ti host:
  ComfyUI image worker
  optional control-plane services if operationally convenient
```

The exact model and serving stack are benchmark decisions, not frozen in this handbook.

### 16.4 OpenAI-compatible local contract

Prefer local servers exposing an OpenAI-compatible chat endpoint. The adapter still performs:

- capability probes;
- schemas;
- retries;
- health checks;
- token accounting;
- provider-independent error mapping.

“OpenAI-compatible” does not imply equivalent structured-output behaviour.

### 16.5 Migration sequence

1. introduce local adapter behind tests;
2. replay model contract corpus against local endpoint;
3. compare schema validity, narrative quality, latency, and context handling;
4. enable shadow calls for selected noncanonical tasks;
5. route one role at a time;
6. retain OpenRouter fallback temporarily;
7. switch embeddings with versioned re-embedding;
8. remove external fallback only after soak and failure tests.

### 16.6 Model registry health

Track:

- model loaded;
- endpoint reachable;
- supported parameters;
- context limit;
- current queue depth;
- recent latency/error rate;
- available memory;
- last successful probe.

Routing chooses a compatible healthy endpoint, never a character-specific machine.

---

## 17. Capability-probe artifact

Generate:

```text
docs/generated/model-capabilities.json
```

Example:

```json
{
  "generated_at": "2026-07-29T08:00:00Z",
  "profiles": [
    {
      "profile_id": "openrouter-nemotron-super-character-v1",
      "model_slug": "nvidia/nemotron-3-super-120b-a12b:free",
      "json_schema_mode": "NATIVE_STRICT",
      "max_tested_input_tokens": 20000,
      "supports_seed": false,
      "probe_status": "PASS",
      "probe_hash": "..."
    }
  ]
}
```

The generated file is diagnostic and reproducible; it is not hand-edited.

---

## 18. Required tests

### Unit tests

- Pydantic schema normalization;
- error mapping;
- prefix handling;
- request-budget reserve/consume/release;
- retry classification;
- model-profile selection;
- raw-content redaction.

### Contract tests with fake server

- strict JSON success;
- JSON in code fence;
- malformed comma repair;
- missing required field;
- extra property rejection;
- 429 with `Retry-After`;
- provider timeout;
- unsupported `response_format`;
- embedding count mismatch;
- embedding dimension mismatch.

### Live OpenRouter smoke tests

Marked and opt-in:

```text
pytest -m openrouter_live
```

They must:

- use tiny synthetic prompts;
- consume a bounded configured budget;
- never run in ordinary pull-request CI;
- verify text endpoint availability;
- verify current structured-output mode;
- verify embedding dimension and prefix path;
- record sanitized capability output.

### Migration compatibility tests

Run the same model-role corpus against OpenRouter and local adapters. Domain validation results must be comparable even when prose differs.

---

## 19. Stage introduction map

| Capability | First required stage |
|---|---:|
| OpenRouter text adapter, profiles, ledger, fake tests | 0 |
| Live character calls and phase reservation | 1 |
| Embedding adapter in shadow/batch use | 2 |
| Long-term RAG and richer role routing | 3 |
| Local multi-machine model routing | 4 |
| Macro-simulation role and long-horizon batching | 5 |

---

## 20. Definition of done

This subsystem is complete for a stage when:

- no domain or graph module imports provider SDK types;
- capabilities are probed and cached;
- structured outputs pass local validation even when provider enforcement changes;
- request budget is reserved before phase work;
- all retries are bounded, classified, and idempotent;
- raw logs contain no credentials;
- free-endpoint privacy limits are enforced through data classification;
- embedding dimensions and versions are validated;
- provider failures degrade safely or pause before inconsistent partial progress;
- the same role contract can run against a local OpenAI-compatible adapter.

---

## 21. Official references

- OpenRouter text model page: <https://openrouter.ai/nvidia/nemotron-3-super-120b-a12b:free>
- OpenRouter embedding model page: <https://openrouter.ai/nvidia/nemotron-3-embed-1b:free>
- OpenRouter structured outputs: <https://openrouter.ai/docs/guides/features/structured-outputs>
- OpenRouter limits: <https://openrouter.ai/docs/api_reference/limits>
- OpenRouter embeddings API: <https://openrouter.ai/docs/api_reference/embeddings>
- OpenRouter quickstart/OpenAI compatibility: <https://openrouter.ai/docs/quickstart>
- NVIDIA embedding model card: <https://build.nvidia.com/nvidia/nemotron-3-embed-1b/modelcard>
