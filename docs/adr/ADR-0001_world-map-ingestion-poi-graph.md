# ADR-0001 — World-map image ingestion into a canonical Point-of-Interest graph

**Status:** PROPOSED
**Date:** 2026-07-29
**Decision owners:** architecture/contract owner (parent agent), `domain.map` owner
**Reviewers:** `domain.world`, `infrastructure.models`, `application.memory`, security/data reviewer, QA/stage owner
**Decision deadline/checkpoint:** Stage 4 kickoff (multimodal gateway + object storage become available)
**Supersedes:** NONE
**Superseded by:** NONE
**Related change request:** NONE (this ADR opens the design line; a CR will accompany the implementing stage)
**Related requirements:** map/travel topology in `09_WORLD_DIRECTOR_NPCS_LORE_MAP_AND_GENERATIONS.md` §11–§12; canon rule README §2 and `AGENTS.md` §4.1; model boundaries `AGENTS.md` §4.4
**Related tasks/stages:** `MAP-INGEST-001` (task packet `docs/tasks/active/MAP-INGEST-001_world-map-ingestion.md`); Future workstream `WORLD/MAP`, dependent on Stage 4 (`29_STAGE_4_LOCAL_DISTRIBUTION_AND_IMAGES.md`)

## Context

A user has supplied a rendered fantasy world map (`seed/assets/world-map.png`, 1586×992 PNG) with labelled regions and points of interest. The product intent is that, at production scale, a user can input a world map image and the system will (1) use a multimodal model to *read* the map, (2) extract meaningful points of interest (POIs) and the sub-points/waypoints between them, and (3) turn that into a canonical map graph the simulation can traverse.

The handbook already defines the *canonical* map as a graph of `Location` nodes and `Route` edges maintained by the deterministic World Engine, where the Narrative Director "may propose only" and validation commits (`09` §2, §11). It does **not** yet define how an *image* becomes such a graph. This ADR records how that ingestion must be structured so it never violates the canon boundary.

Observed facts: pgvector is available (verified locally); the model gateway is provider-neutral and versioned (`12`); image/object-storage infrastructure arrives in Stage 4 (`29`). Hypothesis (to validate later): a multimodal model can extract labelled POIs from a single map image at usable precision with a crop-and-zoom pass per label.

## Decision drivers

1. correctness/canon safety — extraction output must be a proposal, never authoritative;
2. knowledge isolation/security — a map extractor sees only the supplied image + world config, never omniscient character state;
3. restart/idempotency — ingestion is a retryable job with an idempotency key; re-running must not duplicate locations/routes;
4. contract stability — the extraction contract must map cleanly onto the existing `Location`/`Route` shapes;
5. quality/cost — multimodal calls are expensive; ingestion is offline/batch, not on a simulation hot path;
6. reversibility — an imported map version must be reviewable and revertible before it becomes canon.

## Constraints

- Must obey the non-negotiable canon rule (README §2): only deterministic validation + atomic commit changes the world.
- Must obey model boundaries (`AGENTS.md` §4.4): structured output + local validation; no raw DB/filesystem/shell to the model.
- Canonical shapes are fixed by `09` §11 (`Location`, `Route`); the extraction contract adapts to them, it does not redefine them.
- Image handling depends on Stage 4 object storage; do not commit generated imagery to git (`AGENTS.md` §9). Seed *source* art may live under `seed/assets/` (`19` §2).
- Out of the Stage 0–5 committed scope as an automated capability; this is a future workstream introduced behind an ADR.

## Options considered

### Option A — Multimodal proposal → deterministic validation → atomic commit (proposes-only ingestion)

**Description:** A dedicated, offline ingestion pipeline. A multimodal adapter returns a structured `MapExtraction` (candidate POIs + edges + waypoints, all with confidence and provenance). A deterministic validator checks the world boundary, region/parent references, graph connectivity, and budgets, then a commit service inserts `Location`/`Route` rows inside one transaction, emitting a `WORLD_MAP_IMPORTED` event. Human/Director review gates promotion of a map version to canon. Embeddings (pgvector) are computed from committed POI text for later retrieval, not from the model's raw output.

**Advantages:** preserves the canon boundary exactly like character/Director actions; reuses the existing effect/commit + task/outbox + model-gateway machinery; idempotent and reviewable; embeddings stay a projection.

**Disadvantages/risks:** more moving parts than a direct import; requires the Stage 4 multimodal capability and object storage; extraction precision needs evaluation.

**Evidence:** POI extraction feasibility demonstrated informally by the parent agent reading `world-map.png`; a proposal-schema + fake-adapter contract-test prototype ships with this ADR under `prototypes/map_ingestion/`.

**Migration/rollback:** map versions are additive; a bad import is rejected pre-commit or reverted by not promoting the version. No destructive change to prior canon.

### Option B — Model writes locations/routes directly (LLM-authored canon)

**Description:** Let the multimodal model emit and persist map rows directly.

**Advantages:** fewer components; fastest to a demo.

**Disadvantages/risks:** violates README §2 and `AGENTS.md` §4.1/§4.4 (model mutating canon); no idempotency or validation guarantee; unreviewable; unsafe. **Rejected on principle.**

### Option C — Manual authoring only (no image ingestion)

**Description:** Humans transcribe maps into the seed format (`23`) by hand; no multimodal step.

**Advantages:** simplest; fully controlled.

**Disadvantages/risks:** does not deliver the requested capability; does not scale to user-supplied maps.

## Decision

Adopt **Option A**. World-map image ingestion is an **offline, proposal-only pipeline**: a multimodal adapter produces a validated `MapExtraction` proposal; deterministic validation plus an atomic commit create canonical `Location`/`Route` records under a reviewable, idempotent map-import version; pgvector embeddings are a downstream projection of committed POIs. The multimodal model never writes canon and never receives omniscient or per-character state.

Default configuration: ingestion disabled until Stage 4; one image → one map-import version; commit gated behind explicit promotion; per-label crop-and-zoom extraction pass; confidence threshold and duplicate-radius are config, not hardcoded.

## Detailed consequences

### Positive
- The requested capability is expressible without weakening canon, isolation, or restart guarantees.
- Extraction contract aligns 1:1 with `Location`/`Route`, so the committer is thin.

### Negative/trade-offs
- Adds a new workstream and depends on Stage 4 infrastructure; not deliverable in Stage 0.

### New risks and mitigations
- *Hallucinated/misread POIs become canon* → confidence threshold + mandatory review before promotion + provenance stored per node.
- *Duplicate imports* → idempotency key over (image content hash + config version); duplicate-radius dedup.
- *Coordinate/label noise* → coordinates optional (`09` §11.1); normalized 0–1 image space; names validated against length/charset rules.

### Operational consequences
- New retryable ingestion job type; new object-storage object (the source image); new `WORLD_MAP_IMPORTED` event and map-version record.

### Security, privacy, and content consequences
- Model input is limited to the image + world config; no character perspective data. Untrusted model text is treated as untrusted (names sanitized). No secrets in prompts/logs.

### Data/schema/API/prompt consequences
- New map-import version + provenance columns; new prompt contract for the map-extraction role (versioned per `15`); no change to the `Location`/`Route` canonical shapes.

## Implementation plan

| Task | Owner | Dependency | Deliverable/test |
|---|---|---|---|
| `MAP-INGEST-001` extraction contract + fake adapter (prototype now) | `infrastructure.models` | none | `prototypes/map_ingestion/**` + contract tests (this PR) |
| `MAP-INGEST-002` deterministic validator (boundary/refs/connectivity/budgets) | `domain.map` | S0 domain + `09` §11 | property/unit tests |
| `MAP-INGEST-003` atomic map-import commit + `WORLD_MAP_IMPORTED` event | `application.simulation` | S0 event-commit service | integration + idempotency tests |
| `MAP-INGEST-004` multimodal adapter + object storage wiring | `infrastructure.models` | Stage 4 (`29`) | opt-in live smoke, capped |
| `MAP-INGEST-005` POI embedding projection (pgvector) | `application.memory` | `11` retrieval | integration test |
| `MAP-INGEST-006` review/promotion + revert | `domain.world` | above | scenario test |

## Migration and rollback

No existing map data exists yet, so there is nothing to migrate. Rollback boundary: a map-import version is only canon after explicit promotion; un-promoted or reverted versions never affect a running world. Not applicable for Stage 0 data.

## Validation evidence

```text
commands: cd prototypes/map_ingestion && uv run pytest -q
fixture/seed: seed/assets/world-map.png (content hash recorded in prototype fixtures)
software versions: Python 3.12, Pydantic v2, pytest
results: contract tests green (see PR walkthrough); covers well-formed, malformed JSON, missing fields, unknown POI type, out-of-range coordinate, duplicate delivery
failure cases: rejects unknown location_type, coordinate outside [0,1], empty name, duplicate extraction_id
artefact paths: prototypes/map_ingestion/**, PR walkthrough
```

## Acceptance criteria

- [ ] Extraction is proposal-only; no path lets the model write `Location`/`Route` rows.
- [ ] Extraction contract maps onto `09` §11 `Location`/`Route` shapes without redefining them.
- [ ] Ingestion job is idempotent over (image hash + config version).
- [ ] Contract/schema changes reviewed by `domain.map` + security/data reviewer.
- [ ] Prototype contract tests pass; malformed/missing/unknown/duplicate cases covered.
- [ ] Affected docs/status/registry updated when the implementing stage lands.

## Revisit triggers

- Multimodal extraction precision below a usable threshold in Stage 4 evaluation.
- A decision to allow real-time (non-offline) map edits.
- Any requirement to store per-character map knowledge inside the map node (would violate `09` §11.4 — revisit).

## Affected files and registries

- code paths: `prototypes/map_ingestion/**` (now); future `backend/src/fictional_world/{domain/map,infrastructure/models,application/simulation,application/memory}` and `prompts/map_extractor/`.
- migrations: future map-import version + provenance (Alembic).
- generated schemas/OpenAPI: future `MapExtraction` JSON Schema export.
- prompt/model/workflow registry: new versioned map-extractor prompt + multimodal model profile.
- deployment/configuration: Stage 4 object storage; ingestion feature flag.
- handbook/project docs: `09` §11 (reference), this ADR, task packet.

## Decision log

| Date | Event | Author |
|---|---|---|
| 2026-07-29 | Proposed; prototype contract + fake adapter shipped alongside | parent agent |
