# `S4-IMG-003` — Quality control, retries, gallery lifecycle

**Stage:** 4  
**Workstream:** IMG  
**Status:** READY  
**Priority:** P0  

## Objective

Technical QC, optional vision QC stub, bounded retries, approve/reject/regenerate,
gallery provenance. Images remain illustrative; visual surprises never mutate canon.

## Acceptance

- [x] QC policy + retry bounds (`application/images/qc.py`: technical_qc, approve/reject/regenerate, `_next_fail_status`, `mark_regenerate`)
- [x] Gallery metadata lifecycle (`gallery_item` table; `GalleryService`; display_status lifecycle)
- [x] Non-canonical status explicit (`is_canonical_illustration=False` default; handbook §2 enforced in QC service)
- [x] Tests (`test_qc.py` — 8 tests; `test_phase_isolation.py` — 2 tests)
