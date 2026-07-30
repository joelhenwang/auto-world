# `S4-IMG-001` — ComfyUI adapter and workflow registry

**Stage:** 4  
**Workstream:** IMG  
**Status:** READY  
**Priority:** P0  
**Owner:** parent coding agent  
**Branch:** `cursor/s4-integration-8b4a`  
**Depends on:** S4-STORAGE-001

## Objective

ComfyUI health probe, versioned workflow registry, `/prompt` submission, job ID
persistence, status polling, output import, cancellation, idempotent submissions.
Never block phase completion on ComfyUI.

## Acceptance

- [x] Adapter + fake for offline tests (`infrastructure/comfyui/fake.py`, `http_adapter.py`)
- [x] Workflow registry versioned (`infrastructure/comfyui/workflow_registry.py` + `config/comfyui_workflows/stub_v1.json`)
- [x] Idempotent job records (unique constraint on `world_id, idempotency_key`; `enqueue()` returns existing on duplicate key)
- [x] Phase path does not await image completion (`ImageEnqueueService` is a separate call; phase runner never imports it)
