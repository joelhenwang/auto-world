"""Deterministic seed identifier helpers (handbook ``23`` §5)."""

from __future__ import annotations

from uuid import UUID, uuid5

DEFAULT_SEED_NAMESPACE = UUID("2ddfdc14-a971-5f68-beb9-7b95eed45d8e")


def seed_uuid(seed_path: str, *, namespace: UUID = DEFAULT_SEED_NAMESPACE) -> UUID:
    """Return UUIDv5 for a canonical seed path such as ``character/mira-talren``."""
    if not seed_path or seed_path != seed_path.strip():
        raise ValueError(f"invalid seed path: {seed_path!r}")
    return uuid5(namespace, seed_path)
