# `S4-STORAGE-001` — MinIO/object assets, backup, integrity

**Stage:** 4  
**Workstream:** OPS / IMG  
**Status:** IN_PROGRESS  
**Priority:** P0  
**Owner:** parent coding agent  
**Branch:** `cursor/s4-integration-8b4a`  
**Owns migration:** `0007_stage4_object_assets` (image metadata tables included for IMG)

## Objective

Deploy S3-compatible object storage and implement bucket/prefix policy, content-addressed
keys, checksums, PostgreSQL image/asset metadata, orphan reconciliation stubs, backup
notes — no DB BLOBs for full assets.

## Acceptance

- [x] Compose MinIO service (`compose.yaml` minio profile)
- [x] Object storage port + MinIO/fake adapters (`application/ports/storage.py`, `infrastructure/storage/`)
- [x] Migration for asset/image metadata (`0007_stage4_img`)
- [x] Offline tests with fake/in-memory store (48 unit tests, 2 integration migration tests)
- [x] Images never become canon automatically (`is_canonical_illustration=False` default; all gallery items explicit non-canon)
