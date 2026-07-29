"""Sanitize untrusted memory text before inclusion in context packages."""

from __future__ import annotations

import re

# Neutralize prompt-injection style delimiters inside memory/claims.
_DELIMITER_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"</?\s*untrusted_memory\b[^>]*>", re.IGNORECASE),
    re.compile(r"</?\s*system\b[^>]*>", re.IGNORECASE),
    re.compile(r"</?\s*assistant\b[^>]*>", re.IGNORECASE),
    re.compile(r"(?i)\bignore\s+previous\s+instructions\b"),
    re.compile(r"(?i)\byou\s+are\s+now\b"),
)


def sanitize_memory_text(text: str) -> str:
    cleaned = text
    for pattern in _DELIMITER_PATTERNS:
        cleaned = pattern.sub("[redacted]", cleaned)
    return cleaned.strip()
