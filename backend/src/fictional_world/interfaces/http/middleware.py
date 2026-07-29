"""HTTP middleware."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from fictional_world.observability.logging import set_correlation_id

CORRELATION_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        incoming = request.headers.get(CORRELATION_HEADER)
        correlation_id = incoming.strip() if incoming else str(uuid.uuid4())
        set_correlation_id(correlation_id)
        try:
            response = await call_next(request)
        finally:
            set_correlation_id(None)
        response.headers[CORRELATION_HEADER] = correlation_id
        return response
