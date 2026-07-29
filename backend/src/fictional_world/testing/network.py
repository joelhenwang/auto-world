"""Network isolation helpers for non-live tests."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager


@contextmanager
def block_network() -> Generator[None]:
    """Block outbound sockets except explicitly allowed live tests.

    Prefer ``pytest-socket`` when installed; this context is a lightweight
    fallback used by fixture self-tests.
    """

    try:
        import socket as socket_mod
    except ImportError:  # pragma: no cover
        yield
        return

    original = socket_mod.socket

    def _guarded(*args: object, **kwargs: object) -> object:
        msg = "network disabled in non-live tests"
        raise RuntimeError(msg)

    socket_mod.socket = _guarded  # type: ignore[assignment,misc]
    try:
        yield
    finally:
        socket_mod.socket = original  # type: ignore[assignment,misc]
