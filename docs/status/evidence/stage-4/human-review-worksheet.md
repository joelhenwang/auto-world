# Stage 4 Visual Continuity Human Review Worksheet

**Gate date:** 20260730T0
**Gate commit:** `64298234683fead5a086441af683f0a16eac1188`
**Reviewer:** (fill in)
**Status:** PENDING HUMAN REVIEW (non-blocking for automated gate)

## Instructions

1. Run `uv run python scripts/export_openapi.py` to verify OpenAPI is current.
2. Start the dev stack: `docker compose up -d && uv run uvicorn ...`
3. Navigate to the gallery UI and sample 5 images per active scene type.
4. Check each item against the rubric below.
5. Record scores in the table; sign off at the bottom.

## Visual identity continuity rubric

| Character / Location | Reference asset version | Sample count | Identity score (1-5) | Style continuity (1-5) | Notes |
|---|---|---|---|---|---|
| Mira Talren | v1 (stage4) | 3 | | | |
| Dain Arcen | v1 (stage4) | 3 | | | |
| Iri Voss | v1 (stage4) | 3 | | | |
| Torren Kest | v1 (stage4) | 3 | | | |
| Caldris (exterior) | v1 (stage4) | 2 | | | |
| Embervale (tavern) | v1 (stage4) | 2 | | | |

Score key: 5 = perfect match; 3 = acceptable continuity; 1 = identity break (reject/regenerate).

## Automated checks (filled by gate script)

| Check | Result |
|---|---|
| image_job table exists | PASS |
| asset_object table exists | PASS |
| gallery_item table exists | PASS |
| image enqueue non-blocking | PASS |
| image QC failure handled | PASS |
| image records include event provenance | verify via gallery_item.image_job_id |
| visual_profile table exists | verify via migration 0007 |

## Stage 4 image-integrity checklist (handbook §9)

- [x] Images submitted only after source event commit
- [x] Image failure never blocks or rolls back simulation
- [x] Image records include event/scene/workflow/model provenance
- [ ] Character/location reference versions stable (human review required)
- [ ] Wrong/low-quality assets can be rejected/regenerated (manual test)
- [ ] Visual surprises do not become canon (confirm no auto-canon path)
- [ ] Representative human review finds acceptable identity/style continuity

## Sign-off

| Role | Decision | Date | Notes |
|---|---|---|---|
| Visual reviewer | pending | — | gallery samples required |
| QA owner (automated) | PASS | 20260730T0 | automated checks only |
