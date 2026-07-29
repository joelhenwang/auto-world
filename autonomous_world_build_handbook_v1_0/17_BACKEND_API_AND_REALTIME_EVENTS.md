# Backend API and Realtime Events

**Version:** 1.0  
**Status:** Normative API specification  
**Primary owners:** `interfaces.http`, `interfaces.websocket`, application command/query handlers  
**Required reading:** `02`–`07`, `14`, `18`, `22`, and the active stage document

---

## 1. Purpose

This document defines the FastAPI application boundary, REST resources, commands, query projections, role and perspective enforcement, idempotency, error responses, WebSocket event stream, pagination, API versioning, and generated client contracts.

The API does not expose ORM models or accept arbitrary state patches.

---

## 2. API principles

1. REST reads return projections and DTOs, not domain aggregates.
2. World changes use typed commands with idempotency keys.
3. User role determines command authority; perspective determines information visibility.
4. Deity edits are explicit audit events, not direct CRUD endpoints.
5. Long-running commands return task/command IDs and current status.
6. WebSocket is a notification stream; durable state remains queryable over REST.
7. Every list endpoint has cursor pagination and stable ordering.
8. API schemas are generated from Pydantic and exported for TypeScript generation.
9. Public API version is independent from internal table or prompt versions.
10. Error responses are machine-readable and never leak secrets or raw prompts by default.

---

## 3. Application layout

```text
FastAPI app
├── lifespan
│   ├── configuration validation
│   ├── database pools
│   ├── model gateway clients
│   ├── orchestrator/reconciler startup
│   └── graceful shutdown
├── /api/v1 routes
├── /ws/v1/worlds/{world_id}
├── dependency injection
├── auth/session middleware
├── request ID middleware
├── exception mapping
├── OpenAPI generation
└── health/metrics endpoints
```

Business logic lives in application services, not route functions.

---

## 4. Authentication and local-first policy

Stage 0 development may allow loopback-only unauthenticated access. Before binding beyond `127.0.0.1`, require authentication.

Recommended initial local auth:

- one administrator account;
- password hash or external local identity provider;
- secure HTTP-only session cookie;
- CSRF protection for cookie-authenticated commands;
- WebSocket session authentication;
- explicit `user_id` in audit records.

API-token auth may be added for coding-agent automation. Tokens are scoped and stored hashed.

---

## 5. Roles versus perspective

```text
Role:
  WATCHER
  DIRECTOR
  DEITY
  PLAYER
  OPERATOR

Perspective:
  OMNISCIENT
  PUBLIC
  CHARACTER:{character_id}
```

A user may have operational role plus selected presentation perspective.

Examples:

- watcher + omniscient: read all canon/secrets;
- player + character: read only character-known data and submit that character’s action;
- deity + omniscient: issue overrides;
- operator: inspect task/model health but not necessarily private narrative content in restricted deployments.

Server-side query handlers enforce perspective. The frontend cannot request omniscient data and hide it visually as a substitute.

---

## 6. Versioning

Base path:

```text
/api/v1
/ws/v1
```

Breaking external changes create `v2`. Additive fields and new enum variants require client-compatible handling.

Every response may include:

```text
schema_version
world_state_version or event_sequence
```

Use `ETag` or explicit version fields for cache/concurrency where useful.

---

## 7. Common identifiers and timestamps

- UUIDs encoded as lowercase canonical strings;
- operational time in RFC 3339 UTC;
- fictional time as structured world calendar fields;
- event sequence as integer per world;
- cursor is opaque base64url or signed token, not raw SQL offset.

Do not expose sequential database surrogate keys.

---

## 8. Common response envelope

Ordinary resource:

```json
{
  "data": {},
  "meta": {
    "request_id": "...",
    "schema_version": "1",
    "world_event_sequence": 42
  }
}
```

Paginated:

```json
{
  "data": [],
  "page": {
    "next_cursor": "...",
    "has_more": true,
    "limit": 50
  },
  "meta": {}
}
```

Do not wrap WebSocket event payloads in the REST envelope; they have their own contract.

---

## 9. Error model

```json
{
  "error": {
    "code": "WORLD_PHASE_ALREADY_ACTIVE",
    "message": "The world already has an active phase.",
    "details": {
      "active_phase_id": "..."
    },
    "retryable": false
  },
  "meta": {
    "request_id": "..."
  }
}
```

Categories:

```text
VALIDATION_ERROR            422
AUTHENTICATION_REQUIRED     401
FORBIDDEN                   403
NOT_FOUND                   404
CONFLICT                    409
RATE_LIMITED                429
DEPENDENCY_UNAVAILABLE      503
INTERNAL_ERROR              500
```

Domain error codes remain stable. `message` may change and is not used for client branching.

Raw provider errors, SQL, filesystem paths, and stack traces never appear in production responses.

---

## 10. Idempotent commands

State-changing command endpoints require:

```http
Idempotency-Key: <client-generated UUID or stable command key>
```

The server stores:

- authenticated user;
- route/command type;
- request-body hash;
- result/status;
- expiry policy.

Reusing a key with the same body returns the original result. Reusing it with a different body returns `409 IDEMPOTENCY_KEY_REUSED`.

---

## 11. World endpoints

```text
POST   /api/v1/worlds                         # create/seed one world; Stage 0 admin
GET    /api/v1/worlds/{world_id}
GET    /api/v1/worlds/{world_id}/runtime
POST   /api/v1/worlds/{world_id}/start
POST   /api/v1/worlds/{world_id}/pause
POST   /api/v1/worlds/{world_id}/resume
POST   /api/v1/worlds/{world_id}/advance-phase
GET    /api/v1/worlds/{world_id}/clock
GET    /api/v1/worlds/{world_id}/config
PATCH  /api/v1/worlds/{world_id}/config       # whitelisted mutable settings only
GET    /api/v1/worlds/{world_id}/ending-status
```

Because product scope allows one world, the collection may usually contain one row. Keep `world_id` explicit for testing, recovery imports, and domain isolation.

### 11.1 Advance phase response

```json
{
  "data": {
    "command_id": "...",
    "phase_id": "...",
    "status": "ACCEPTED"
  }
}
```

Do not hold the HTTP request until model calls finish.

---

## 12. User mode and intervention endpoints

```text
GET   /api/v1/worlds/{world_id}/session-mode
PUT   /api/v1/worlds/{world_id}/session-mode
POST  /api/v1/worlds/{world_id}/player-control/acquire
POST  /api/v1/worlds/{world_id}/player-control/release
POST  /api/v1/phases/{phase_id}/player-actions
POST  /api/v1/worlds/{world_id}/director-proposals
POST  /api/v1/worlds/{world_id}/deity-commands
POST  /api/v1/worlds/{world_id}/retcons
GET   /api/v1/commands/{command_id}
```

### 12.1 Player action

Accepts an intent/action proposal, not arbitrary effects. Server validates the controlled character, active phase, perspective, and deadline.

### 12.2 Director intervention

Creates a user-authored proposal that still goes through validation/resolution.

### 12.3 Deity command

Uses a discriminated union of explicit commands such as:

```text
SET_CHARACTER_LOCATION
ALTER_STAT
CREATE_ENTITY
ARCHIVE_ENTITY
APPLY_CONDITION
REVEAL_SECRET
ALTER_WORLD_RULE
RESURRECT_CHARACTER
FORCE_EVENT
EDIT_MEMORY
HARD_RETCON
```

Each command requires justification and produces `USER_OVERRIDE`/`DIVINE_EVENT` audit records. No generic JSON patch or SQL.

---

## 13. Timeline, scenes, and events

```text
GET /api/v1/worlds/{world_id}/timeline
GET /api/v1/events/{event_id}
GET /api/v1/scenes/{scene_id}
GET /api/v1/scenes/{scene_id}/narrations
GET /api/v1/phases/{phase_id}
GET /api/v1/phases/{phase_id}/scenes
GET /api/v1/phases/{phase_id}/tasks         # operator/debug permission
```

Timeline filters:

- after/before cursor;
- character IDs;
- location IDs;
- event types;
- arc IDs;
- minimum importance;
- generation;
- perspective;
- has image;
- fictional date range.

Perspective handler returns only visible event representation. A character-perspective timeline may show “unknown figure” where the omniscient timeline identifies an NPC.

---

## 14. Character endpoints

```text
GET /api/v1/worlds/{world_id}/characters
GET /api/v1/characters/{character_id}
GET /api/v1/characters/{character_id}/state
GET /api/v1/characters/{character_id}/card
GET /api/v1/characters/{character_id}/stats
GET /api/v1/characters/{character_id}/skills
GET /api/v1/characters/{character_id}/relationships
GET /api/v1/characters/{character_id}/goals
GET /api/v1/characters/{character_id}/plans
GET /api/v1/characters/{character_id}/injuries
GET /api/v1/characters/{character_id}/memories
GET /api/v1/characters/{character_id}/diary
GET /api/v1/characters/{character_id}/images
```

Editing uses explicit administration/deity commands. Do not expose ordinary `PATCH /characters/{id}`.

### 14.1 Perspective rules

When viewing another character from player perspective:

- show publicly known card data;
- show observed appearance and reputation;
- omit private goals, memories, true relationships, hidden injuries, and secrets;
- allow uncertain labels where the viewer has beliefs.

---

## 15. World encyclopedia and map

```text
GET /api/v1/worlds/{world_id}/encyclopedia
GET /api/v1/lore/{lore_id}
GET /api/v1/worlds/{world_id}/map
GET /api/v1/locations/{location_id}
GET /api/v1/locations/{location_id}/connections
GET /api/v1/worlds/{world_id}/factions
GET /api/v1/factions/{faction_id}
GET /api/v1/worlds/{world_id}/arcs
```

Map response contains only discovered/known nodes in character perspective. Unknown route details and secret locations remain absent.

---

## 16. Memory administration

```text
GET  /api/v1/characters/{character_id}/memories/{memory_id}
POST /api/v1/characters/{character_id}/memories/{memory_id}/pin
POST /api/v1/characters/{character_id}/memories/{memory_id}/unpin
POST /api/v1/characters/{character_id}/memories/{memory_id}/rebuild-embedding
POST /api/v1/characters/{character_id}/memory-rebuild
```

Editing/deleting a memory requires deity or operator permission and creates audit/history records. Deleting a derived memory does not delete source observations or canonical events.

---

## 17. Image and gallery endpoints

```text
GET  /api/v1/worlds/{world_id}/images
GET  /api/v1/image-jobs/{job_id}
GET  /api/v1/images/{asset_id}
POST /api/v1/events/{event_id}/image-jobs
POST /api/v1/image-jobs/{job_id}/cancel
POST /api/v1/image-jobs/{job_id}/regenerate
POST /api/v1/images/{asset_id}/select
POST /api/v1/images/{asset_id}/hide
```

Binaries may be served through signed/local object URLs or a streaming endpoint. Do not expose storage credentials or raw filesystem paths.

---

## 18. Operations endpoints

Protected by operator/deity permission:

```text
GET  /api/v1/operations/health
GET  /api/v1/operations/workers
GET  /api/v1/operations/model-profiles
GET  /api/v1/operations/model-capabilities
GET  /api/v1/operations/request-budget
GET  /api/v1/operations/tasks
GET  /api/v1/operations/dead-letter
POST /api/v1/operations/tasks/{task_id}/retry
POST /api/v1/operations/tasks/{task_id}/cancel
POST /api/v1/operations/reconcile
GET  /api/v1/operations/audit
```

Never return full model prompts by default. A separate debug scope is required.

---

## 19. WebSocket stream

Endpoint:

```text
/ws/v1/worlds/{world_id}?after=<event_cursor>&perspective=<...>
```

FastAPI/Starlette WebSocket support can send JSON messages. The server authenticates before accepting or immediately closes with an application code.

### 19.1 Envelope

```json
{
  "stream_event_id": "evtstream_...",
  "sequence": 982,
  "type": "SCENE_COMMITTED",
  "world_id": "...",
  "occurred_at": "2026-07-29T08:12:00Z",
  "fictional_time": {},
  "payload": {},
  "schema_version": "1"
}
```

### 19.2 Event types

```text
WORLD_RUNTIME_CHANGED
PHASE_CREATED
PHASE_STATE_CHANGED
CHARACTER_ACTION_READY
SCENE_CREATED
SCENE_STATE_CHANGED
SCENE_COMMITTED
TIMELINE_EVENT_AVAILABLE
NARRATION_AVAILABLE
MEMORY_COMPACTION_COMPLETED
PLAYER_INPUT_REQUIRED
COMMAND_STATE_CHANGED
IMAGE_JOB_STATE_CHANGED
IMAGE_AVAILABLE
WORKER_HEALTH_CHANGED
QUOTA_STATE_CHANGED
CONSISTENCY_WARNING
WORLD_ENDED
HEARTBEAT
```

Do not send raw internal task payloads to ordinary clients.

### 19.3 Durable sequence and reconnect

WebSocket events are projections of durable event/outbox records with a monotonically increasing stream sequence. On reconnect, client supplies last sequence/cursor. Server replays allowed missed events up to a limit, then instructs client to resync REST projections.

### 19.4 Backpressure

Each connection has a bounded send queue. If a slow client falls behind:

- drop redundant progress updates where safe;
- never silently drop canonical event notifications without forcing resync;
- close with a specific `RESYNC_REQUIRED` code if the queue cannot recover.

### 19.5 Heartbeat

Send application heartbeat or WebSocket ping at configured interval. Client reconnects with exponential backoff and last cursor.

---

## 20. Command and read consistency

A command response may arrive before projections and WebSocket updates. Include command status and event sequence when complete.

Clients may:

1. submit command;
2. subscribe to `COMMAND_STATE_CHANGED`;
3. query command status after reconnect;
4. refresh affected resources when terminal.

Do not rely only on optimistic UI for canonical state.

---

## 21. OpenAPI and generated types

Export:

```text
docs/generated/openapi.json
```

Generate TypeScript API schemas/client from it. Generated code is not manually edited.

CI checks:

- OpenAPI can be generated without network/provider access;
- committed generated spec matches application output;
- TypeScript generation succeeds;
- no route exposes ORM/internal classes;
- all discriminated unions have stable discriminator fields.

---

## 22. Validation and request limits

- global request body limit;
- stricter deity/seed import limit;
- image upload type/size checks;
- maximum pagination limit, default 50, hard 200;
- text fields have domain-specific length caps;
- no user-supplied SQL/order-by names;
- UUIDs validated;
- enum values explicit;
- WebSocket subscription filters validated;
- rate-limit command endpoints independently from provider quotas.

---

## 23. Health endpoints

```text
GET /health/live
  process alive; no dependency checks.

GET /health/ready
  database reachable, migrations current, critical config valid,
  orchestrator able to accept work; model provider may be degraded.

GET /health/dependencies
  protected detailed status for database, OpenRouter/local models,
  ComfyUI, object storage, workers, and quotas.
```

A model provider outage should normally make simulation degraded/paused, not necessarily make the API unready for read access and operator actions.

---

## 24. Testing

### Route tests

- auth/role matrix;
- perspective filtering;
- command idempotency;
- conflict/error mapping;
- cursor pagination;
- OpenAPI generation;
- request length/type validation;
- no secret fields in DTOs.

### WebSocket tests

FastAPI’s test client can test WebSocket connections. Cover:

- authentication;
- initial replay;
- live event;
- reconnect from cursor;
- perspective redaction;
- backpressure/resync;
- heartbeat;
- close codes;
- duplicate outbox delivery deduplication.

### Contract tests

- generated TypeScript types compile;
- old additive client tolerates new fields/event types where policy says it should;
- all command responses link to durable status.

---

## 25. Definition of done

The API is complete for a stage when:

- every state change is a typed command with idempotency;
- server-side role and perspective checks protect private data;
- long operations survive HTTP disconnects;
- WebSocket reconnect can recover or force explicit resync;
- OpenAPI and TypeScript contracts are generated reproducibly;
- errors are stable and sanitized;
- operations endpoints expose health without exposing secrets;
- tests prove player mode cannot query omniscient data;
- no route directly patches canonical ORM rows.

---

## 26. Official references

- FastAPI WebSockets: <https://fastapi.tiangolo.com/advanced/websockets/>
- FastAPI WebSocket testing: <https://fastapi.tiangolo.com/advanced/testing-websockets/>
- FastAPI OpenAPI: <https://fastapi.tiangolo.com/tutorial/metadata/>
