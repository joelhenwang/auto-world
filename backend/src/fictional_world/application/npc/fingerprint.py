"""Similarity fingerprint for NPC deduplication (name/location/role/traits/hook)."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence

_WHITESPACE = re.compile(r"\s+")


def normalize_token(value: str) -> str:
    """Casefold and collapse whitespace for stable fingerprint parts."""

    return _WHITESPACE.sub(" ", value.strip()).casefold()


def normalize_token_set(values: Sequence[str]) -> tuple[str, ...]:
    normalized = sorted({normalize_token(v) for v in values if v and v.strip()})
    return tuple(normalized)


def compute_similarity_fingerprint(
    *,
    name: str,
    location_key: str | None = None,
    role_tags: Sequence[str] = (),
    traits: Sequence[str] = (),
    source_hook_key: str | None = None,
) -> str:
    """Stable SHA-256 fingerprint over normalized identity facets.

    Handbook 09 §15.4 / 27 S2-WORLD-002: dedup by name, location, role,
    traits, and source hook.
    """

    parts = (
        normalize_token(name),
        normalize_token(location_key or ""),
        "|".join(normalize_token_set(role_tags)),
        "|".join(normalize_token_set(traits)),
        normalize_token(source_hook_key or ""),
    )
    payload = "\x1f".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


__all__ = [
    "compute_similarity_fingerprint",
    "normalize_token",
    "normalize_token_set",
]
