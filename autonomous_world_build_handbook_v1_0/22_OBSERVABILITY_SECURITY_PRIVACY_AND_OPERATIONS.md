# Observability, Security, Privacy, Content Safety, and Operations

**Version:** 1.0  
**Status:** Normative cross-cutting specification  
**Primary owners:** platform/operations/security workstreams; every subsystem owner  
**Required reading:** `02`, `04`, `12`, `14`, `16`–`21`

---

## 1. Purpose

This document defines structured logs, traces, metrics, audit history, dashboards, consistency checks, threat model, authentication/authorization, secret handling, prompt-injection defences, tool and network boundaries, provider privacy, content safety, dependency security, backups, incident response, and operational runbooks.

The project is local-first and initially single-user, but local software can still leak secrets, corrupt history, expose unauthenticated services, or execute malicious model-generated data. Security is architectural, not a future web-scale feature.

---

## 2. Observability goals

A developer/operator must be able to answer:

- Which phase, scene, task, model call, event, and worker are involved?
- What state is canonical and what is merely pending?
- Why is the world paused?
- Did a retry duplicate anything?
- Which model/prompt/schema/version produced a proposal?
- Which context records were used without exposing them unnecessarily?
- Where is quota being consumed?
- Is memory/context size growing unexpectedly?
- Did a character receive unauthorized knowledge?
- Is an image delayed because of queue, model, workflow, or quality failure?
- Can the system resume safely after restart?

---

## 3. Structured logging

Use JSON-compatible structured logging through one configured library/adapter.

### 3.1 Common fields

```text
timestamp
level
service
component
environment
release_version
host_id
process_id
request_id
user_id?
world_id?
phase_id?
scene_id?
character_id?
task_id?
workflow_id?
model_call_id?
event_id?
worker_id?
message
error_class?
retryable?
```

### 3.2 Event names

Use stable machine-queryable event names:

```text
phase.created
phase.transitioned
scene.assembled
scene.committed
task.leased
task.retry_scheduled
model.request_started
model.request_completed
model.output_rejected
memory.retrieval_completed
knowledge.access_denied
outbox.dispatched
image.submitted
image.completed
consistency.violation
security.prompt_injection_detected
world.paused
world.ended
```

### 3.3 Redaction

Never log:

- API keys or auth headers;
- passwords/session tokens;
- database credentials;
- full raw prompts in ordinary production log;
- full private memories in shared operations log;
- signed object URLs;
- arbitrary user file paths;
- provider response headers containing sensitive data.

Use content hashes and record IDs. Full synthetic debug payloads, when enabled, live in access-controlled model-call storage rather than ordinary logs.

---

## 4. Tracing

Use OpenTelemetry-compatible tracing or an abstraction that can export to it.

### 4.1 Trace hierarchy

```text
world.phase
├── world.tick
├── director.evaluate
├── snapshot.build
├── character.decide × N
│   ├── context.assemble
│   ├── memory.retrieve
│   └── model.generate
├── scenes.assemble
├── scene.process × M
│   ├── reaction.generate
│   ├── resolution.calculate
│   ├── model.resolve
│   └── scene.commit
├── observations.write
└── phase.finalize
```

Async outbox/image work links to source trace rather than pretending to remain one open span for hours.

### 4.2 Span attributes

Use IDs, role, model profile, task status, token counts, queue latency, and validation result. Avoid raw content attributes.

### 4.3 Sampling

Development: high sampling. Stable long runs: sample ordinary successful spans while always retaining errors, high-impact events, leakage warnings, and consistency violations.

---

## 5. Metrics

### 5.1 Runtime

```text
world_phase_duration_seconds
world_phase_state_total
scene_duration_seconds
scene_commit_duration_seconds
active_worlds
world_paused_total
world_consistency_warning_total
```

### 5.2 Tasks

```text
task_queue_depth{queue,status}
task_wait_seconds
task_run_seconds
task_retry_total{error_class}
task_dead_letter_total{task_type}
worker_heartbeat_age_seconds
worker_active_tasks
```

### 5.3 Models

```text
model_request_total{profile,role,status}
model_latency_seconds
model_input_tokens_total
model_output_tokens_total
model_schema_rejection_total
model_semantic_rejection_total
model_fallback_total
provider_rate_limit_total
provider_quota_reserved
provider_quota_consumed
```

### 5.4 Memory

```text
memory_created_total{type}
memory_embedding_backlog
memory_retrieval_seconds
memory_retrieval_results
context_tokens_estimated
context_tokens_actual
knowledge_access_denied_total
leakage_test_failure_total
```

### 5.5 Images

```text
image_queue_depth
image_generation_seconds
image_retry_total
image_quality_rejection_total
comfyui_health
image_assets_total{class}
```

### 5.6 Database/API

```text
db_pool_in_use
db_query_seconds
api_request_seconds
api_error_total{code}
websocket_connections
websocket_replay_events
websocket_resync_required_total
```

Labels must avoid unbounded IDs such as character/event in metrics. Those belong in traces/logs.

---

## 6. Dashboards and alerts

### 6.1 Runtime dashboard

- current world/phase/state;
- phase duration trend;
- active/pending scenes;
- paused reason;
- consistency status;
- day/month progress.

### 6.2 Model dashboard

- requests by role/profile;
- latency and errors;
- schema validity;
- quota/RPM state;
- context/output tokens;
- fallback rate.

### 6.3 Worker dashboard

- host health;
- queue depth;
- leases;
- model/image capability;
- heartbeat;
- GPU/RAM metrics in Stage 4.

### 6.4 Memory/quality dashboard

- memories per day/type;
- embedding backlog;
- context growth;
- retrieval latency;
- duplicate rate;
- leakage/quality evaluator findings.

### 6.5 Alerts

Local notifications or UI alerts for:

- world stuck beyond threshold;
- dead-letter task;
- consistency violation;
- repeated model schema failures;
- quota nearly exhausted;
- database backup failure;
- worker unavailable;
- image backlog above threshold;
- migration mismatch;
- unauthorized access attempts.

Not every transient provider timeout needs an immediate human alert.

---

## 7. Audit log

Security/audit records are append-only and distinct from ordinary logs.

Audit events include:

- login/logout/token creation;
- role/perspective changes where relevant;
- player control acquire/release;
- Director user proposal;
- deity command;
- hard retcon;
- memory edit/delete/pin;
- task manual retry/skip;
- configuration/privilege change;
- prompt/model activation;
- backup/restore/import/export;
- secret-access denial;
- content-policy override.

Record actor, action, target, justification, before/after references, request ID, and timestamp. Do not store raw passwords/secrets.

---

## 8. Consistency audit

A scheduled/manual audit checks:

- event sequence uniqueness;
- projection source-event references;
- aggregate versions;
- entity/location exclusivity;
- resource bounds;
- active phases/scenes/tasks coherence;
- observation owner/event validity;
- memory source visibility;
- embedding version/dimension;
- outbox/event linkage;
- selected image/source event;
- hard-retcon tainted dependencies;
- generation and lineage constraints.

Severity:

```text
INFO
WARNING
ERROR
CRITICAL
```

Critical findings pause automatic simulation. The audit reports facts and repair options; it does not silently rewrite canon.

---

## 9. Threat model

### 9.1 Assets

- canonical world database;
- private character memories/secrets;
- API/provider credentials;
- user account/session;
- local filesystem/object assets;
- model and image workflows;
- code execution environment;
- audit history;
- generated content and exports.

### 9.2 Threat actors/sources

- malicious or accidental user command;
- prompt-injection text in memory/lore/dialogue;
- compromised dependency/custom node;
- exposed local service on LAN/internet;
- buggy model output;
- coding-agent mistake;
- stolen API key;
- corrupted backup/import;
- model provider data handling;
- another process/user on the host.

### 9.3 Primary threats

```text
unauthorized omniscient access
cross-character secret leakage
arbitrary SQL/shell/file/network execution
credential disclosure
canonical corruption or duplicate effects
unsafe hard retcon
malicious seed/import
untrusted HTML/script display
ComfyUI custom-node compromise
publicly exposed database/model/ComfyUI
provider logging of sensitive data
supply-chain compromise
```

---

## 10. Authentication and authorization

Before non-loopback use:

- authenticated user;
- secure session cookies or scoped tokens;
- password hashing through an established library;
- CSRF protection for cookie commands;
- origin checks;
- secure WebSocket authentication;
- role/permission matrix server-side;
- audit of high-impact actions;
- session timeout/revocation.

Permissions are explicit capabilities, for example:

```text
world.read_omniscient
world.read_public
character.read_private
world.control_runtime
character.control
world.propose_director
world.deity_override
world.hard_retcon
operations.read
operations.retry_task
models.read_debug_payload
memory.edit
images.manage
```

Do not authorize by hiding UI buttons.

---

## 11. Secret management

- secrets in environment/secret files outside Git;
- `.env` ignored;
- minimum API-key scope/credit limit;
- separate dev and stable keys;
- rotate after suspected exposure;
- redact in logs/traces/errors;
- never include key in model prompt;
- avoid passing secrets to subprocess command lines;
- protect backups containing auth data;
- frontend never receives provider/database/object-store secrets.

CI secrets unavailable to untrusted forks/pull requests.

---

## 12. Prompt-injection defence

### 12.1 Treat all generated/user narrative text as untrusted

This includes:

- memories;
- dialogue;
- claims;
- diaries;
- lore;
- books/letters;
- image prompts from models;
- imported seed prose;
- user intervention text.

### 12.2 Defences

- authority-delimited prompts;
- no write tools for character/Director graphs;
- bound character ID in tool runtime;
- allowlisted read tools and parameters;
- strict schemas;
- domain validation;
- no arbitrary URL fetch, shell, SQL, or file tools;
- output length limits;
- context source provenance;
- adversarial tests;
- tool-call audit;
- sanitization before frontend rendering.

### 12.3 Memory poisoning

A model-generated memory cannot include new authority, permissions, or hidden facts. Memory creation validates source citations and perspective scope. Suspicious instruction-like content may remain as fictional text but is tagged and never promoted.

---

## 13. Tool and process sandboxing

Character/Director/model workflows do not receive direct:

- database session;
- shell;
- Python execution;
- filesystem access;
- arbitrary HTTP client;
- cloud credentials;
- ComfyUI workflow editor;
- other characters’ memory repository.

Application code performs allowed operations through typed services.

Coding agents developing the repository have broader tools, but must follow `01_AGENTS.md`, review generated migrations, and never insert secrets into fixtures/docs.

---

## 14. Database security

- database listens only on required interfaces;
- strong credentials outside development;
- application user lacks superuser privileges;
- migration role may be separate;
- pgvector extension installed through reviewed admin path;
- backups protected;
- SQL parameters bound, never concatenated from model/user text;
- no model-generated SQL;
- statement timeouts for API queries;
- connection limits/pool bounds;
- audit high-impact data maintenance.

Row-level security is not required for the initial single-user app if application and tests enforce perspective, but it can be evaluated as defence-in-depth later. Do not claim it exists when it does not.

---

## 15. Network security

Default bind:

```text
127.0.0.1
```

Before LAN exposure:

- authentication enabled;
- firewall configured;
- reverse proxy/TLS where needed;
- PostgreSQL, model servers, ComfyUI, object storage, Temporal UI not publicly exposed;
- internal endpoints allowlisted by host;
- CORS/origin policy narrow;
- no wildcard WebSocket origin in stable profile;
- service inventory and ports documented.

Do not use `--listen 0.0.0.0` for ComfyUI without firewall/authenticated network controls.

---

## 16. Provider privacy and data classification

### 16.1 Classes

```text
PUBLIC_SYNTHETIC
  invented world/characters with no real-person/private data.

PRIVATE_SYNTHETIC
  user-created proprietary fiction or unpublished material.

PERSONAL_DATA
  real-person identifiers, voice, face, messages, or biography.

CONFIDENTIAL
  credentials, company data, internal documents, proprietary source.
```

### 16.2 Initial free endpoint policy

Only `PUBLIC_SYNTHETIC` fictional data is approved for the selected free NVIDIA/OpenRouter endpoints by default. The endpoint notice states that sessions may be logged/recorded for security and NVIDIA product improvement and warns against confidential or personal data.

`PRIVATE_SYNTHETIC`, `PERSONAL_DATA`, and `CONFIDENTIAL` require a separately approved provider/privacy configuration or local inference.

### 16.3 Data minimization

Send only task-required context. Do not send full database dumps or lifetime history. Redact operational IDs when not needed, though stable fictional entity IDs may be necessary for structured output.

---

## 17. Content safety and rating

Default world profile:

```text
English
Young adult
Soft dark fantasy
```

Allowed:

- non-graphic violence and injury;
- death and grief;
- horror atmosphere;
- political oppression;
- betrayal and moral conflict;
- consensual young-adult/adult romance;
- implied non-explicit adult relationships.

Prohibited/default blocked:

- explicit sexual content;
- sexualized minors;
- romantic/sexual coercion portrayed as desirable;
- graphic sexual violence;
- fetishized abuse;
- prolonged graphic torture;
- real-person sexualized content;
- named living-artist image imitation;
- direct copyrighted-franchise replication when original world content is intended.

### 17.1 Age records

Characters have canonical age/birth date. Any romance or image workflow consults age policy. Ambiguous apparent age is not enough to override canonical minor status.

### 17.2 Content classifier

Before publication/image submission, classify:

- violence severity;
- sexual content;
- minor involvement;
- self-harm;
- abuse/coercion;
- horror intensity;
- real-person content.

Deterministic metadata and rules take priority. A model classifier may assist but cannot approve prohibited content alone.

---

## 18. Frontend content security

- escape text;
- sanitize any Markdown/HTML with strict allowlist;
- no model-supplied scripts/styles/iframes;
- Content Security Policy;
- trusted object URLs only;
- prevent path traversal on asset endpoints;
- download headers/content types correct;
- no secrets in source maps/environment bundle;
- avoid rendering raw diagnostic payload to ordinary users;
- rate-limit command forms and file uploads.

---

## 19. Seed/import/export security

Seed and import files are untrusted until validated.

- schema and size limits;
- no executable templates or arbitrary Python;
- no absolute/path traversal references;
- asset MIME/checksum validation;
- no remote URLs automatically fetched;
- entity/reference integrity;
- lore/prompt injection treated as narrative data;
- dry-run report before commit;
- import transaction and backup;
- export excludes secrets and credentials.

---

## 20. Supply-chain security

- lockfiles committed;
- dependency vulnerability scans;
- license inventory;
- minimal runtime dependencies;
- pinned container bases/digests for release;
- GitHub Actions permissions minimized;
- custom ComfyUI nodes pinned and reviewed;
- model/LoRA/workflow hashes recorded;
- no automatic updates on stable hosts;
- SBOM in later releases;
- verify downloads from trusted sources.

An AI-generated package name or URL is never installed without verification.

---

## 21. Backups and disaster recovery

Defined operationally in `20`. Security additions:

- encrypt or physically protect backup media;
- exclude API keys where possible;
- access-control exports with private memories;
- checksum manifests;
- test restore;
- record who initiated restore/import;
- after compromise, rotate credentials before restoring services.

Recovery point/recovery time objectives are local-project targets and should be set in stage profile. A reasonable initial goal is one completed fictional day of maximum data loss, improving before multi-generation runs.

---

## 22. Incident severity

```text
SEV-1
  credential exposure, unauthorized private-memory access,
  canonical corruption across backups, arbitrary code execution.

SEV-2
  hard consistency violation, repeated duplicate effects,
  world cannot resume, lost committed images/events.

SEV-3
  provider outage, dead-letter task, image backlog,
  degraded memory/narration with canon intact.

SEV-4
  cosmetic UI, nonblocking quality regression, minor metric issue.
```

### 22.1 Incident workflow

1. stop or pause affected work;
2. preserve logs/audit/evidence;
3. revoke/rotate credentials when relevant;
4. identify canonical boundary and affected IDs;
5. restore or repair through typed/audited operation;
6. run consistency/leakage tests;
7. document root cause and prevention;
8. update runbook/test/ADR.

Do not “fix” corruption with direct SQL before preserving evidence and understanding event/projection consequences, except an emergency containment action documented afterward.

---

## 23. Runbook template

Every runbook contains:

```text
Symptom
Impact/severity
Safety warning
Likely causes
Immediate containment
Diagnostic commands/queries
Decision tree
Recovery steps
Verification
Escalation/manual decision
Post-incident cleanup
Preventive tests/metrics
```

Commands must be safe, scoped, and indicate destructive effects.

---

## 24. Operational retention

Suggested starting policy:

- canonical events/observations: retained;
- audit log: retained;
- active memories/summaries: retained/versioned;
- raw full synthetic model payloads: 30–90 days or configurable;
- task/outbox terminal rows: compact/archive after audit window;
- traces: shorter sampled retention;
- metrics: aggregated retention;
- rejected image intermediates: configurable cleanup;
- backups: rotation policy with verified restore points.

Retention changes must not break provenance or active retrieval.

---

## 25. Required security/operations tests

- secret scanning fixture;
- auth/role/perspective matrix;
- CSRF/origin/WebSocket checks;
- prompt injection corpus;
- SQL/path/script injection attempts;
- malicious seed/import;
- unsupported file upload;
- model output attempts forbidden effect/tool;
- ComfyUI unavailable/custom node mismatch;
- log redaction;
- backup/restore;
- consistency audit detects seeded corruption;
- unauthorized operations endpoint;
- provider privacy class prevents external request;
- content policy blocks sexualized minor/explicit job;
- dependency and container scans.

---

## 26. Definition of done

This cross-cutting subsystem is complete for a stage when:

- logs/traces/metrics identify every canonical workflow without exposing secrets;
- high-impact user operations are audited;
- consistency violations are detectable and block unsafe progress;
- authentication is enabled before LAN exposure;
- role and perspective permissions are tested;
- model text cannot obtain arbitrary tools or cross-character data;
- external-provider privacy classification is enforced;
- content and age boundaries apply to narrative and images;
- custom nodes/dependencies/models are pinned and licensed;
- backups restore successfully;
- recurring failures have actionable runbooks;
- incident handling preserves evidence and uses typed repair paths.
