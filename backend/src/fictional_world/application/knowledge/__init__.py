"""Observation → claim → belief pipeline and secret access (S2-KNOW-001)."""

from fictional_world.application.knowledge.beliefs import (
    apply_claim_evidence,
    apply_observation_evidence,
    clamp_confidence,
)
from fictional_world.application.knowledge.claims import (
    claim_is_not_objective_fact,
    create_claim,
    create_lie_claim,
    proposition_key_for,
    rumour_provenance,
    transmit_rumour,
)
from fictional_world.application.knowledge.eligibility import (
    classify_observer_eligibility,
    eligible_observers,
)
from fictional_world.application.knowledge.lookup import (
    DEFAULT_DIRECTOR_ONLY,
    lookup_perspective_knowledge,
    npc_restricted_package_beliefs,
)
from fictional_world.application.knowledge.observable_facts import allowed_observable_facts
from fictional_world.application.knowledge.observation_builder import (
    build_observation_for_observer,
    build_observations,
)
from fictional_world.application.knowledge.secrets import SecretAccessPolicy
from fictional_world.application.knowledge.types import (
    EventObservationInput,
    ObserverPresence,
    PerspectiveKnowledge,
)

__all__ = [
    "DEFAULT_DIRECTOR_ONLY",
    "EventObservationInput",
    "ObserverPresence",
    "PerspectiveKnowledge",
    "SecretAccessPolicy",
    "allowed_observable_facts",
    "apply_claim_evidence",
    "apply_observation_evidence",
    "build_observation_for_observer",
    "build_observations",
    "claim_is_not_objective_fact",
    "clamp_confidence",
    "classify_observer_eligibility",
    "create_claim",
    "create_lie_claim",
    "eligible_observers",
    "lookup_perspective_knowledge",
    "npc_restricted_package_beliefs",
    "proposition_key_for",
    "rumour_provenance",
    "transmit_rumour",
]
