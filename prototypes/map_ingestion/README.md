# `map_ingestion` — prototype (ADR-0001 / MAP-INGEST-001)

**Status:** prototype. Proposal-only. Not wired to canon, not an installable package.

This directory prototypes the **first step** of the world-map ingestion pipeline
described in `docs/adr/ADR-0001_world-map-ingestion-poi-graph.md`: turning a
world-map image into a typed, validated **proposal** that a (future)
deterministic validator and atomic commit service can turn into canonical
`Location`/`Route` records.

## Canon boundary (why this is safe)

Per the non-negotiable rule (README section 2, `AGENTS.md` section 4.1), a model
**proposes**; only deterministic validation + an atomic DB commit change the
world. This prototype therefore:

- performs **no** database, filesystem, or network I/O;
- defines `MapExtraction` / `PointOfInterest` / `MapEdge` / `Waypoint` as strict,
  immutable Pydantic v2 contracts that map onto the canonical `Location` and
  `Route` shapes in `09_...MAP...md` section 11 (it adapts to them, never
  redefines them);
- parses untrusted model output at a single boundary (`parse_map_extraction`)
  that raises one typed error;
- ships a **fake** deterministic adapter with recorded synthetic responses.

The validator (`MAP-INGEST-002`), atomic committer (`MAP-INGEST-003`), the real
multimodal adapter + object storage (`MAP-INGEST-004`, Stage 4), and pgvector
embeddings (`MAP-INGEST-005`) are intentionally **out of scope** here.

## Run

```bash
cd prototypes/map_ingestion
uv sync
uv run pytest
```

## Layout

```text
src/map_ingestion/contracts.py      proposal-only Pydantic v2 contracts + parser
src/map_ingestion/fake_adapter.py   deterministic fake extractor (no network)
tests/                              contract tests (robustness + idempotency)
tests/fixtures/                     recorded synthetic responses
```
