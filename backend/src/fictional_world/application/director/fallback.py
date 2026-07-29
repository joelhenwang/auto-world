"""Safe quiet-phase fallback when Director validation fails."""

from __future__ import annotations

from fictional_world.application.director.types import DirectorProposal, NoEventFallback
from fictional_world.domain.common.result import ValidationResult


def safe_no_event_fallback(
    *,
    validation: ValidationResult | None = None,
    proposal: DirectorProposal | None = None,
    reason: str | None = None,
) -> NoEventFallback:
    """Return a no-event outcome that never mutates canon.

    Used when ``validate_director_proposal`` fails, when the Director abstains,
    or when orchestration chooses a quiet phase. Callers must not invent
    compensatory world events from this fallback.
    """
    if reason is not None:
        message = reason
    elif validation is not None and not validation.ok:
        codes = ", ".join(issue.code for issue in validation.issues)
        message = f"director proposal rejected: {codes}"
    elif proposal is None:
        message = "no director proposal; quiet phase"
    else:
        message = "director abstained; quiet phase"

    codes_tuple: tuple[str, ...] = ()
    if validation is not None:
        codes_tuple = tuple(issue.code for issue in validation.issues)

    return NoEventFallback(
        reason=message,
        validation_issue_codes=codes_tuple,
        proposal_id=None if proposal is None else proposal.proposal_id,
    )
