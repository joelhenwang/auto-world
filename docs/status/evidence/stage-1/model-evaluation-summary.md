# Stage 1 model evaluation summary

## Deterministic acceptance

`stage1-first-day-v1` uses `Stage1FakeModelGateway` and makes exactly 10 model
requests across dawn, morning, and evening. Graph tests cover valid structured
outputs, malformed/schema-invalid output, semantic rejection, timeout, 429,
one regeneration, and deterministic fallback. Default tests make no live
provider calls.

## Separate live smoke

**Command:** `uv run pytest -o addopts='' -m openrouter_live backend/tests/live/test_stage1_openrouter.py backend/tests/unit/test_openrouter_errors.py`
**Result:** 2 passed in 12.58 seconds
**Evidence:** `openrouter-live-smoke.txt`

The Stage 1 smoke sends synthetic fictional context through the versioned
character-decision prompt and strict JSON Schema mode. The returned provider
output parses as `ActionProposal`, passes graph domain validation, preserves
the request/actor IDs, and is returned without deterministic fallback.

This sample proves adapter/schema compatibility only. It does not replace the
deterministic corpus or constitute a narrative-quality benchmark.
