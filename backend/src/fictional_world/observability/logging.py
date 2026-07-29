"""Structured logging helpers with secret redaction (S0-OPS-001)."""

from __future__ import annotations

import logging
import re
from contextvars import ContextVar
from typing import Any

_CORRELATION_ID: ContextVar[str | None] = ContextVar("correlation_id", default=None)

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(api[_-]?key|password|secret)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"(?i)\b(sk-[A-Za-z0-9_-]{8,})\b"),
    re.compile(r"(?i)(Bearer\s+)([A-Za-z0-9._\-+=/]{8,})"),
    re.compile(r"(?i)(Authorization\s*:\s*Bearer\s+)([A-Za-z0-9._\-+=/]{8,})"),
)


def get_correlation_id() -> str | None:
    return _CORRELATION_ID.get()


def set_correlation_id(value: str | None) -> None:
    _CORRELATION_ID.set(value)


def redact_secrets(text: str) -> str:
    """Replace credential-like substrings before they hit sinks."""

    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(_replace_secret, redacted)
    return redacted


def _replace_secret(match: re.Match[str]) -> str:
    if match.lastindex and match.lastindex >= 2:
        return f"{match.group(1)}***REDACTED***"
    return "***REDACTED***"


class RedactingFilter(logging.Filter):
    """Ensure message/args never carry raw API keys or passwords."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    key: redact_secrets(value) if isinstance(value, str) else value
                    for key, value in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_secrets(arg) if isinstance(arg, str) else arg for arg in record.args
                )
        return True


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id() or "-"
        return True


class JsonLogFormatter(logging.Formatter):
    """Minimal JSON-ish single-line formatter (no third-party logger required)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", "-"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        # Stable key order for greppability.
        parts = [f'"{key}": {_json_escape(value)}' for key, value in payload.items()]
        return "{" + ", ".join(parts) + "}"


def _json_escape(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{text}"'


def configure_logging(*, level: str = "INFO") -> None:
    """Install root handlers once with redaction + correlation filters."""

    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    handler.addFilter(RedactingFilter())
    handler.addFilter(CorrelationIdFilter())
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    # Quiet noisy libs in Stage 0 demos.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
