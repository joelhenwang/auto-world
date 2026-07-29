# Seed assets

Source (authored/reference) art used as **input** to seed authoring and, in the
future, to world-map ingestion. These are seed *source* materials per the
repository layout in `autonomous_world_build_handbook_v1_0/19_*.md` §2 — not
generated output. Generated imagery must not be committed to git (`AGENTS.md` §9);
runtime-generated images live in object storage (`06`, `16`).

## `world-map.png`

- Size: 1586×992, 8-bit RGB PNG.
- SHA-256: `c64417236e385ca3b51658c4ef7e8e8fe48a8a7a96ad335bc7e0349b26b3ac9f`
- Provenance: supplied by the project owner as a representation of the world map.
  Originally uploaded to the `cursor/setup-dev-environment-42c3` branch; relocated
  here so it is a first-class seed asset rather than a loose top-level blob.
- Role: reference/concept art and the intended first input to the world-map
  ingestion pipeline described in `docs/adr/ADR-0001_world-map-ingestion-poi-graph.md`
  and task packet `docs/tasks/active/MAP-INGEST-001_world-map-ingestion.md`.

### Naming note

The labels on this map (e.g. `Valerion`, `Dawnspire Kingdom`, `The Shadowfell`)
differ from the canonical Stage 0 seed vocabulary `caldris-embervale-v1`
(`23_INITIAL_WORLD_SEED_AND_CONTENT_AUTHORING.md`). Before this map drives canon,
reconcile the two: either re-author the seed from this map, or treat this image as
concept art for a distinct world. This asset is **not** canonical world state.
