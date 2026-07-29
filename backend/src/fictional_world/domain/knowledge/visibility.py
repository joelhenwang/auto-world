"""Observation visibility and secret-access enums (S2-KNOW-001)."""

from __future__ import annotations

from enum import StrEnum


class ObserverEligibility(StrEnum):
    """Whether a character may receive an observation for an event."""

    DIRECT_WITNESS = "direct_witness"
    HEARING_ONLY = "hearing_only"
    PARTIAL = "partial"
    ABSENT = "absent"


class FactVisibilityRequirement(StrEnum):
    """Requirement that must hold for a structured fact key to be perceived."""

    ALWAYS_PUBLIC = "always_public"
    ACTOR_SEEN = "actor_seen"
    ITEM_SEEN = "item_seen"
    CLOSE_VISUAL_OR_KNOWN_MAGIC = "close_visual_or_known_magic"
    PRECISE_CLOSE_OBSERVATION = "precise_close_observation"
    HEARING_CHANNEL = "hearing_channel"
    NEVER = "never"


class ObservationDirectness(StrEnum):
    """How directly an observation was perceived (handbook 11 §4.2)."""

    DIRECT = "direct"
    PARTIAL = "partial"
    INFERRED = "inferred"
    REPORTED = "reported"
    AFTERMATH = "aftermath"


class ClaimIntentClass(StrEnum):
    """Speaker intent for a communicated proposition."""

    STATEMENT = "statement"
    LIE = "lie"
    RUMOUR = "rumour"
    QUESTION = "question"


class ClaimTruthStatus(StrEnum):
    """Omniscient assessor truth label — never promotes a claim to objective fact."""

    UNKNOWN = "unknown"
    TRUE = "true"
    FALSE = "false"
    MIXED = "mixed"


class SecretAccessLevel(StrEnum):
    """Granted access level on a secret_access row."""

    OWNER = "owner"
    SHARED = "shared"
    OVERHEARD = "overheard"
    REVOKED = "revoked"


class BeliefEvidenceSourceKind(StrEnum):
    OBSERVATION = "observation"
    CLAIM = "claim"
    EVENT = "event"


__all__ = [
    "BeliefEvidenceSourceKind",
    "ClaimIntentClass",
    "ClaimTruthStatus",
    "FactVisibilityRequirement",
    "ObservationDirectness",
    "ObserverEligibility",
    "SecretAccessLevel",
]
