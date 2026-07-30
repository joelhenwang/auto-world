"""Stage 3 world application services (arcs/factions/background + pacing).

Director proposals remain proposals. Deterministic helpers validate slot rules,
apply aggregate updates, and score novelty — they never silently mutate
character private intention or memory.
"""

from fictional_world.application.world.config import (
    DEFAULT_TROPE_COOLDOWNS,
    NoveltyScoringConfig,
)
from fictional_world.application.world.novelty import (
    build_novelty_signature,
    record_trope_usage,
    score_director_proposal_with_novelty,
)
from fictional_world.application.world.pacing import (
    compute_pacing_metrics,
    participant_combo_key,
    repetition_ratio,
    tropes_in_cooldown,
)
from fictional_world.application.world.types import (
    NoveltyHistory,
    NoveltyScoreBreakdown,
    NoveltyScoreResult,
    PacingMetricsSnapshot,
)
from fictional_world.domain.world import (
    activate_arc,
    activate_hook,
    advance_arc_progress,
    apply_faction_daily_update,
    apply_settlement_indicator_update,
    can_activate_major_arc,
    can_activate_secondary_hook,
    close_arc,
    close_hook,
    default_plot_armour_bias,
    expire_hook,
)

__all__ = [
    "DEFAULT_TROPE_COOLDOWNS",
    "NoveltyHistory",
    "NoveltyScoreBreakdown",
    "NoveltyScoreResult",
    "NoveltyScoringConfig",
    "PacingMetricsSnapshot",
    "activate_arc",
    "activate_hook",
    "advance_arc_progress",
    "apply_faction_daily_update",
    "apply_settlement_indicator_update",
    "build_novelty_signature",
    "can_activate_major_arc",
    "can_activate_secondary_hook",
    "close_arc",
    "close_hook",
    "compute_pacing_metrics",
    "default_plot_armour_bias",
    "expire_hook",
    "participant_combo_key",
    "record_trope_usage",
    "repetition_ratio",
    "score_director_proposal_with_novelty",
    "tropes_in_cooldown",
]
