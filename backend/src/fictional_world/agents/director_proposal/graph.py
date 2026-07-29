"""DirectorProposalGraph — thin async wrapper around Director validate/trigger helpers.

Never commits domain state. Accepted proposals remain proposals for the resolver.
"""

from __future__ import annotations

from dataclasses import dataclass

from fictional_world.application.director import (
    DirectorProposal,
    DirectorTriggerConfig,
    DirectorWorldSnapshot,
    NoEventFallback,
    TriggerDecision,
    evaluate_director_trigger,
    safe_no_event_fallback,
    validate_director_proposal,
)
from fictional_world.domain.common.result import ValidationResult


@dataclass(frozen=True, slots=True)
class DirectorProposalGraphInput:
    """Trigger snapshot plus an optional pre-parsed Director proposal."""

    world_snapshot: DirectorWorldSnapshot
    proposal: DirectorProposal | None = None
    config: DirectorTriggerConfig | None = None


@dataclass(frozen=True, slots=True)
class DirectorProposalGraphResult:
    """Bounded Director outcome. Callers must not treat this as a commit."""

    trigger: TriggerDecision
    accepted_proposal: DirectorProposal | None
    validation: ValidationResult | None
    fallback: NoEventFallback | None


async def run_director_proposal_graph(
    graph_input: DirectorProposalGraphInput,
) -> DirectorProposalGraphResult:
    """Evaluate trigger → validate proposal → accept or safe no-event fallback.

    Plain async function (LangGraph is not required). Does not write hooks,
    metrics, world events, or effect commands.
    """

    trigger = evaluate_director_trigger(
        graph_input.world_snapshot,
        config=graph_input.config,
    )
    if not trigger.should_call:
        return DirectorProposalGraphResult(
            trigger=trigger,
            accepted_proposal=None,
            validation=None,
            fallback=safe_no_event_fallback(reason="director not triggered; quiet phase"),
        )

    proposal = graph_input.proposal
    if proposal is None:
        return DirectorProposalGraphResult(
            trigger=trigger,
            accepted_proposal=None,
            validation=None,
            fallback=safe_no_event_fallback(reason="no director proposal; quiet phase"),
        )

    validation = validate_director_proposal(
        proposal,
        graph_input.world_snapshot,
        config=graph_input.config,
    )
    if not validation.ok:
        return DirectorProposalGraphResult(
            trigger=trigger,
            accepted_proposal=None,
            validation=validation,
            fallback=safe_no_event_fallback(validation=validation, proposal=proposal),
        )

    return DirectorProposalGraphResult(
        trigger=trigger,
        accepted_proposal=proposal,
        validation=validation,
        fallback=None,
    )


__all__ = [
    "DirectorProposalGraphInput",
    "DirectorProposalGraphResult",
    "run_director_proposal_graph",
]
