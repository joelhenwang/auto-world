"""Narrative Director v1 (S2-WORLD-001).

Boundary: the Director produces *proposals only*. Canonical mutations
(events, effect commands, NPC registration, secret grants) commit solely
through the normal resolver / effect validation path. Persistence helpers
here may upsert Director bookkeeping rows (``hook``, ``narrative_metric``)
but must never write ``world_event`` or apply effect commands directly.
"""

from fictional_world.application.director.config import DirectorTriggerConfig
from fictional_world.application.director.fallback import safe_no_event_fallback
from fictional_world.application.director.persistence import (
    record_narrative_metric,
    upsert_hook,
)
from fictional_world.application.director.triggers import evaluate_director_trigger
from fictional_world.application.director.types import (
    DirectorProposal,
    DirectorWorldSnapshot,
    NoEventFallback,
    ProposedHookStub,
    ProposedNpcStub,
    SecretHandlingPlan,
    TriggerDecision,
    TriggerMetricsSnapshot,
)
from fictional_world.application.director.validate import validate_director_proposal

__all__ = [
    "DirectorProposal",
    "DirectorTriggerConfig",
    "DirectorWorldSnapshot",
    "NoEventFallback",
    "ProposedHookStub",
    "ProposedNpcStub",
    "SecretHandlingPlan",
    "TriggerDecision",
    "TriggerMetricsSnapshot",
    "evaluate_director_trigger",
    "record_narrative_metric",
    "safe_no_event_fallback",
    "upsert_hook",
    "validate_director_proposal",
]
