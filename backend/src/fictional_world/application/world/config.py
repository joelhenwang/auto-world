"""Configurable cooldowns and novelty scoring weights (Stage 3)."""

from __future__ import annotations

from dataclasses import dataclass, field

# Default cooldown lengths for common anime/fantasy clichés (phases).
DEFAULT_TROPE_COOLDOWNS: dict[str, int] = {
    "MYSTERIOUS_STRANGER": 20,
    "TAVERN_INTRODUCTION": 15,
    "SURPRISE_ATTACK": 25,
    "KIDNAPPING": 30,
    "FALSE_ACCUSATION": 25,
    "LOVE_TRIANGLE": 40,
    "ACCIDENTAL_INTIMACY": 30,
    "TRAINING_MONTAGE": 20,
    "HIDDEN_ROYAL": 40,
    "LAST_SECOND_RESCUE": 25,
    "FORGOTTEN_PROPHECY": 35,
    "SECRET_POWER_AWAKENING": 40,
    "BETRAYAL_REVEAL": 30,
    "MONSTER_OF_THE_WEEK": 15,
}


@dataclass(frozen=True, slots=True)
class NoveltyScoringConfig:
    """Soft anti-repetition scoring — cooldown reduces score, never hard-bans."""

    default_trope_cooldown_phases: int = 20
    trope_cooldowns: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_TROPE_COOLDOWNS))
    # Penalty applied per overlapping trope still in cooldown (multiplicative soft factor).
    trope_cooldown_penalty: float = 0.35
    location_repetition_penalty: float = 0.25
    participant_combo_penalty: float = 0.20
    action_family_penalty: float = 0.20
    quiet_dramatic_imbalance_penalty: float = 0.15
    signature_hash_penalty: float = 0.30
    # Rolling window size for repetition ratios.
    repetition_window: int = 8
    repetition_ratio_threshold: float = 0.5
    # Quiet kinds preferred over arbitrary attacks (handbook opportunity ladder).
    quiet_proposal_kinds: frozenset[str] = frozenset(
        {
            "SOCIAL_OPPORTUNITY",
            "DISCOVERY",
            "MYSTERY_HOOK",
            "RELATIONSHIP_OPPORTUNITY",
            "PERSONAL_DILEMMA",
            "QUEST_HOOK",
            "NEW_LOCATION_DETAIL",
        }
    )
    dramatic_proposal_kinds: frozenset[str] = frozenset(
        {
            "ENVIRONMENTAL_EVENT",
            "NPC_BLUEPRINT",
        }
    )
    disruptive_kinds_extra_penalty: float = 0.15
    # When causality forces recurrence, restore score toward baseline.
    causality_forced_floor: float = 0.55
    min_score: float = 0.0
    max_score: float = 1.0
