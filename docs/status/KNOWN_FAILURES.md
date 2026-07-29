# Known Failures

Policy: a known failure is reproducible evidence, not a vague concern. Critical canon, isolation, idempotency, or security failures block stage promotion even when a workaround exists.

## Current

No hard Stage 0 or Stage 1 application failure is open.

Non-blocking maintenance findings:

- Starlette reports that its `httpx` test-client compatibility import is
  deprecated.
- FastAPI/Starlette reports that `HTTP_422_UNPROCESSABLE_ENTITY` naming is
  deprecated in favor of `HTTP_422_UNPROCESSABLE_CONTENT`.

Both warnings are recorded in Stage 1 `pytest.txt`; neither changes runtime
behavior or gate correctness.
