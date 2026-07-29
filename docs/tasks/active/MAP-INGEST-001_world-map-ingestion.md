# `MAP-INGEST-001` — World-map image → `MapExtraction` proposal contract + fake adapter

**Stage:** Future (post Stage 5 as a capability; hard dependency on Stage 4 multimodal gateway + object storage). Contract/prototype portion is stage-independent and delivered now.
**Workstream:** WORLD / MODEL
**Status:** IN_PROGRESS (prototype), CONTRACT_DRAFT (canonical integration)
**Priority:** P2
**Owner:** parent agent (prototype)
**Reviewer(s):** `domain.map`, `infrastructure.models`, security/data reviewer
**Branch/worktree:** `cursor/map-ingestion-subsystem-42c3`
**Upstream commit:** ADR-0001
**Target merge order:** after ADR-0001 acceptance; before `MAP-INGEST-002`

---

## 1. Objective

```text
Define a proposal-only contract (MapExtraction) so that a multimodal adapter can turn a
world-map image into candidate Location/Route/waypoint proposals that deterministic
validation can later commit as canon — without the model ever writing canonical state.
```

## 2. Why this task exists

- Requirements: map/travel topology `09` §11–§12; canon rule README §2, `AGENTS.md` §4.1; model boundaries `AGENTS.md` §4.4.
- Stage gate items: not a Stage 0–5 gate item; opens the Future `WORLD/MAP` workstream under ADR-0001.
- Risks mitigated: LLM-authored canon; duplicate/hallucinated map data; unreviewable imports.
- Upstream/downstream tasks: upstream ADR-0001; downstream `MAP-INGEST-002..006`.

## 3. Required reading

1. repository `AGENTS.md` (esp. §4.1 canon, §4.4 model boundaries);
2. `09_WORLD_DIRECTOR_NPCS_LORE_MAP_AND_GENERATIONS.md` §2, §11–§12;
3. `12_MODEL_GATEWAY_OPENROUTER_AND_LOCAL_MIGRATION.md`, `15_PROMPT_CATALOG_AND_OUTPUT_CONTRACTS.md` (structured output);
4. `docs/adr/ADR-0001_world-map-ingestion-poi-graph.md`;
5. `prototypes/map_ingestion/**`.

## 4. Frozen contracts

| Contract | Version/hash/commit | Owner | Allowed change |
|---|---|---|---|
| `Location` shape (`09` §11.1) | handbook v1.0 | `domain.map` | none (extraction adapts to it) |
| `Route` shape (`09` §11.2) | handbook v1.0 | `domain.map` | none |
| Canon rule (README §2) | handbook v1.0 | architecture owner | none |

## 5. Scope

### In scope
- `MapExtraction` / `PointOfInterest` / `MapEdge` / `Waypoint` Pydantic v2 proposal contracts.
- A fake, deterministic multimodal extraction adapter returning scripted synthetic proposals.
- Contract tests for parser robustness (well-formed, malformed JSON, missing fields, unknown type, out-of-range, duplicate delivery).

### Explicitly out of scope
- Any database write, ORM model, or migration (owned by `MAP-INGEST-002/003`).
- Real multimodal/model calls or object storage (owned by `MAP-INGEST-004`, Stage 4).
- Embeddings/retrieval (`MAP-INGEST-005`).
- Review/promotion workflow (`MAP-INGEST-006`).

## 6. File/path ownership

### Writable
```text
prototypes/map_ingestion/**
docs/adr/ADR-0001_world-map-ingestion-poi-graph.md
docs/tasks/active/MAP-INGEST-001_world-map-ingestion.md
seed/assets/world-map.png
seed/assets/README.md
```

### Read-only dependencies
```text
autonomous_world_build_handbook_v1_0/09_*.md
AGENTS.md
```

### Shared/generated files
```text
none in this task (no OpenAPI/JSON-schema export until canonical integration)
```

## 7. Data and migration ownership

```text
New tables/columns/indexes: none
Migration revision reservation: none
Backfill/rebuild: none
Fixture updates: prototypes/map_ingestion fixtures only
No database change: yes
```

## 8. Interface inputs and outputs

### Inputs
```text
image reference (content hash + object key placeholder), world config (boundary, region ids), extraction config (confidence threshold, duplicate radius)
```
### Outputs
```text
MapExtraction proposal: points_of_interest[], edges[], waypoints-per-edge, provenance, model/prompt version, extraction_id (idempotency key)
```
### Errors/fallbacks
```text
typed parse/validation errors; malformed payloads rejected, never partially committed; retryable transport errors are the adapter's concern (not this contract)
```
### Idempotency/concurrency
```text
key = sha256(image_content_hash + config_version); duplicate delivery returns the same logical extraction; no partial state
```

## 9. Security, privacy, perspective, and content constraints

- [x] No cross-character access beyond frozen policy (extractor sees only image + world config).
- [ ] Server-side role authorization (N/A to contract prototype).
- [x] Model/memory/user text treated as untrusted (names sanitized/validated).
- [x] No secret/key/raw sensitive prompt logging.
- [x] Remote-provider data profile is allowed (only the map image + config are sent).
- [x] No model direct state mutation (proposal-only).
- [ ] High-impact effect privilege enforced (N/A until commit task).
- [x] Young-adult/soft-dark content policy maintained.
- [x] Not applicable items explained above.

Notes:
```text
This task defines a contract + fake adapter only. No canon, no DB, no network.
```

## 10. Implementation sequence

1. write failing contract tests for the proposal schema;
2. implement Pydantic v2 contracts (proposal-only, aligned to Location/Route);
3. implement fake deterministic adapter with scripted synthetic responses;
4. add robustness tests (malformed/missing/unknown/out-of-range/duplicate);
5. document canon boundary in prototype README;
6. acceptance run `uv run pytest`.

## 11. Test matrix

| Test type | Scenario | Expected result | File/command |
|---|---|---|---|
| Unit | well-formed extraction parses | POIs/edges populated | `tests/test_map_extraction_contract.py` |
| Contract | malformed JSON | typed parse error, no object | same |
| Contract | missing required field (name) | validation error | same |
| Contract | unknown `location_type` | rejected | same |
| Property/range | coordinate outside [0,1] | rejected | same |
| Fault/idempotency | duplicate extraction_id delivery | same logical result, deduped | same |

## 12. Required commands

```bash
# environment/bootstrap
cd prototypes/map_ingestion && uv sync
# targeted tests
uv run pytest -q
# formatting/lint (optional in prototype)
uv run ruff check .
```

## 13. Acceptance criteria

- [x] `MapExtraction` is proposal-only; no persistence path exists.
- [x] Contract fields map onto `09` §11 `Location`/`Route`.
- [x] Malformed/missing/unknown/out-of-range/duplicate cases are tested and rejected/handled.
- [x] Prototype tests pass under `uv run pytest`.
- [ ] `domain.map` + security review sign-off (pending human review).
- [x] ADR-0001 references this packet.

## 14. Deliverables

- code: `prototypes/map_ingestion/src/map_ingestion/*.py`;
- migrations: none;
- tests: `prototypes/map_ingestion/tests/*.py`;
- fixtures: `prototypes/map_ingestion/tests/fixtures/*`;
- generated artefacts: none;
- docs/ADR: `docs/adr/ADR-0001_*.md`, this packet;
- evidence: PR walkthrough;
- handoff: PR description.

## 15. Known risks and likely pitfalls

- Treating the prototype contract as canonical without the validator/committer — mitigated by explicit "proposal-only" markings and out-of-scope list.
- Redefining `Location`/`Route` — mitigated by frozen-contract table.

## 16. Blocker/escalation rule

- solve local (B0) issues directly;
- stop for any request to let the model write canon (canon-safety stop condition, `AGENTS.md` §16);
- continue independent contract work where safe.

## 17. Handoff requirements

See PR description: commits, commands/results, contract deviations (none), next task (`MAP-INGEST-002`).

## 18. Parent verification

```text
Reviewed by:
Merged commit:
Acceptance commands rerun:
Findings:
Traceability updated:
Status: PENDING
```
