"""Validate Director proposals before resolver handoff."""

from __future__ import annotations

from fictional_world.application.director.config import DirectorTriggerConfig
from fictional_world.application.director.types import (
    ALLOWED_PROPOSAL_KINDS,
    DISCLOSURE_PATHS,
    FORBIDDEN_PUBLIC_SECRET_FIELDS,
    DirectorProposal,
    DirectorWorldSnapshot,
)
from fictional_world.domain.common.result import ValidationIssue, ValidationResult

_ROMANCE_MARKERS: frozenset[str] = frozenset(
    {
        "guaranteed_romance",
        "mandatory_romance",
        "forced_romance",
        "must_fall_in_love",
        "arranged_romance_outcome",
    }
)


def validate_director_proposal(
    proposal: DirectorProposal,
    world_snapshot: DirectorWorldSnapshot,
    *,
    config: DirectorTriggerConfig | None = None,
) -> ValidationResult:
    """Reject illegal Director proposals; valid ones remain proposals only.

    Does not commit state. Callers must pass accepted proposals through the
    normal effect / scene resolver — never apply effects from this function.
    """
    cfg = config or DirectorTriggerConfig()
    issues: list[ValidationIssue] = []

    if proposal.world_id != world_snapshot.world_id:
        issues.append(
            ValidationIssue(
                code="world_mismatch",
                message="proposal world_id does not match snapshot",
                path="world_id",
            )
        )

    if proposal.proposal_kind not in ALLOWED_PROPOSAL_KINDS:
        issues.append(
            ValidationIssue(
                code="unsupported_proposal_kind",
                message=f"proposal_kind {proposal.proposal_kind!r} is not allowed in Stage 2",
                path="proposal_kind",
            )
        )

    if not proposal.causal_basis_event_ids and not proposal.intent.strip():
        issues.append(
            ValidationIssue(
                code="missing_causal_basis",
                message="proposal requires causal_basis_event_ids or a concrete intent",
                path="causal_basis_event_ids",
            )
        )

    issues.extend(_validate_secret_handling(proposal, world_snapshot))
    issues.extend(_validate_romance(proposal))
    issues.extend(_validate_cooldown(proposal, world_snapshot, cfg))
    issues.extend(_validate_public_payload(proposal))
    issues.extend(_validate_trope_cooldown(proposal, world_snapshot))

    return ValidationResult(issues=tuple(issues))


def _validate_secret_handling(
    proposal: DirectorProposal,
    world_snapshot: DirectorWorldSnapshot,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    handling = proposal.secret_handling
    if handling.reveals_secret and not handling.disclosure_path:
        issues.append(
            ValidationIssue(
                code="secret_without_disclosure_path",
                message="secret reveal requires an explicit disclosure_path",
                path="secret_handling.disclosure_path",
            )
        )
    if handling.disclosure_path and handling.disclosure_path not in DISCLOSURE_PATHS:
        issues.append(
            ValidationIssue(
                code="invalid_disclosure_path",
                message=f"unknown disclosure_path {handling.disclosure_path!r}",
                path="secret_handling.disclosure_path",
            )
        )
    protected = {key.casefold() for key in world_snapshot.protected_secret_keys}
    for idx, fact in enumerate(proposal.proposed_event_facts):
        lowered = fact.casefold()
        for secret in protected:
            if secret and secret in lowered:
                issues.append(
                    ValidationIssue(
                        code="secret_key_in_public_payload",
                        message="proposed_event_facts must not embed protected secret keys",
                        path=f"proposed_event_facts[{idx}]",
                    )
                )
                break
    return issues


def _validate_romance(proposal: DirectorProposal) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if proposal.guarantees_romance:
        issues.append(
            ValidationIssue(
                code="mandatory_romance",
                message="Director must not propose mandatory / guaranteed romance",
                path="guarantees_romance",
            )
        )
    blob = " ".join(
        (
            proposal.intent,
            proposal.title,
            *proposal.proposed_event_facts,
            *proposal.narrative_dimensions,
            *proposal.novelty_tags,
        )
    ).casefold()
    for marker in _ROMANCE_MARKERS:
        if marker.replace("_", " ") in blob or marker in blob:
            issues.append(
                ValidationIssue(
                    code="mandatory_romance",
                    message=(
                        f"proposal text contains prohibited romance guarantee marker {marker!r}"
                    ),
                    path="intent",
                )
            )
            break
    return issues


def _validate_cooldown(
    proposal: DirectorProposal,
    world_snapshot: DirectorWorldSnapshot,
    cfg: DirectorTriggerConfig,
) -> list[ValidationIssue]:
    if not proposal.is_disruptive:
        return []
    if world_snapshot.last_disruptive_event_phase is None:
        return []
    elapsed = world_snapshot.current_phase_index - world_snapshot.last_disruptive_event_phase
    remaining = cfg.disruptive_cooldown_phases - elapsed
    if remaining > 0:
        return [
            ValidationIssue(
                code="disruptive_cooldown_active",
                message=(f"disruptive proposal blocked; {remaining} phase(s) of cooldown remain"),
                path="is_disruptive",
            )
        ]
    return []


def _validate_public_payload(proposal: DirectorProposal) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for key in proposal.public_payload:
        lowered = key.casefold()
        if lowered in FORBIDDEN_PUBLIC_SECRET_FIELDS or lowered.endswith("secret_key"):
            issues.append(
                ValidationIssue(
                    code="secret_key_in_public_payload",
                    message=f"public_payload must not include secret field {key!r}",
                    path=f"public_payload.{key}",
                )
            )
    return issues


def _validate_trope_cooldown(
    proposal: DirectorProposal,
    world_snapshot: DirectorWorldSnapshot,
) -> list[ValidationIssue]:
    if world_snapshot.trope_cooldown_remaining <= 0:
        return []
    overlap = set(proposal.trope_tags) & set(world_snapshot.recent_trope_tags)
    if not overlap:
        return []
    return [
        ValidationIssue(
            code="trope_cooldown_active",
            message=f"trope tag(s) still in cooldown: {sorted(overlap)}",
            path="trope_tags",
        )
    ]
