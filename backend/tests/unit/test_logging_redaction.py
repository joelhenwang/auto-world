"""Unit tests for logging redaction and correlation (S0-OPS-001)."""

from __future__ import annotations

import logging

from fictional_world.observability.logging import (
    RedactingFilter,
    configure_logging,
    redact_secrets,
)


def test_redact_api_key_assignment() -> None:
    text = "openrouter api_key=sk-abcdefghijklmnopqrstuvwxyz"
    assert "sk-abcdefghijklmnopqrstuvwxyz" not in redact_secrets(text)
    assert "***REDACTED***" in redact_secrets(text)


def test_redact_bearer_token() -> None:
    text = "Authorization: Bearer super-secret-token-value"
    assert "super-secret-token-value" not in redact_secrets(text)


def test_redacting_filter_on_log_record() -> None:
    configure_logging(level="INFO")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="password=hunter2 api_key=sk-live-secret",
        args=(),
        exc_info=None,
    )
    assert RedactingFilter().filter(record) is True
    assert "hunter2" not in record.msg
    assert "sk-live-secret" not in record.msg
