"""Typed domain exceptions."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for expected domain rule failures."""


class InvalidStateTransition(DomainError):
    """Raised when a phase/scene/task transition is illegal."""

    def __init__(self, *, entity: str, from_state: str, to_state: str) -> None:
        self.entity = entity
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"invalid {entity} transition: {from_state} -> {to_state}")


class InvalidAction(DomainError):
    """Raised when an action proposal violates domain rules."""


class ConcurrencyConflict(DomainError):
    """Raised when an optimistic version check fails."""


class UnknownTarget(DomainError):
    """Raised when a referenced entity cannot be resolved."""


class SecretAccessDenied(DomainError):
    """Raised when a perspective package would leak private knowledge."""


class InsufficientResource(DomainError):
    """Raised when a resource spend exceeds available amount."""

    def __init__(self, *, resource: str, required: float, available: float) -> None:
        self.resource = resource
        self.required = required
        self.available = available
        super().__init__(f"insufficient {resource}: required={required}, available={available}")
