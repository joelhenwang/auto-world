"""Temporal orchestration port (S4-ORCH-002).

Adoption is **DEFERRED** for the Stage 4 gate per ADR-0003. This module defines the
adapter boundary so a future Temporal Python SDK implementation can plug in without
rewriting domain contracts or moving canon out of PostgreSQL.

Architectural invariants (mandatory even while Temporal is deferred):

1. **Workflows coordinate only** — deterministic control flow, signals/timers, and
   child-workflow structure. No network, database, filesystem, or model calls in
   workflow code.
2. **Activities do I/O** — database commands, model gateway calls, and bounded
   LangGraph runs execute inside activities (not inside workflow sandboxes).
3. **Canon stays in PostgreSQL** — committed ``world_event`` history and aggregates
   remain authoritative; Temporal history (if adopted later) is execution durability,
   never fictional truth.
4. **Domain idempotency keys remain** — activity retries must use the same domain keys
   already defined by the phase/task/outbox grammar
   (e.g. ``world:{id}:phase:{n}:…``). Temporal's at-least-once delivery does not
   replace those keys.

Production Stage 4 path: ``DeterministicPhaseRunner`` + PostgreSQL task leases /
fencing (S4-ORCH-001). See ``docs/adr/ADR-0003_temporal_orchestration.md``.
"""

from __future__ import annotations

from typing import Final, Literal, NoReturn, Protocol
from uuid import UUID

from fictional_world.application.orchestration.protocol import (
    PauseMode,
    PhaseAdvanceResult,
    ReconciliationReport,
)
from fictional_world.domain.common.errors import DomainError

TemporalAdoptionStatus = Literal["deferred", "noop", "active"]

TEMPORAL_ADOPTION_STATUS: Final[TemporalAdoptionStatus] = "deferred"
TEMPORAL_DEFER_REASON: Final[str] = (
    "ADR-0003: Temporal Python SDK deferred for Stage 4 gate; "
    "PostgreSQL-backed DeterministicPhaseRunner + task leases/fencing is the "
    "production orchestrator on the three-host LAN."
)


class TemporalDeferredError(DomainError):
    """Raised when a Temporal-backed orchestrator API is invoked while deferred."""


class TemporalOrchestratorPort(Protocol):
    """Optional Temporal-backed outer orchestrator behind ``WorldOrchestrator``.

    A future SDK adapter must satisfy this Protocol while preserving the four
    invariants documented in this module's docstring. The Stage 4 noop
    implementation reports ``adoption_status == "deferred"`` and does not import
    ``temporalio``.
    """

    @property
    def adoption_status(self) -> TemporalAdoptionStatus:
        """Return ``deferred``, ``noop``, or ``active``."""
        ...

    @property
    def defer_reason(self) -> str | None:
        """Human-readable deferral note when Temporal is not active."""
        ...

    async def start_world(self, world_id: UUID) -> None:
        """Start (or resume ownership of) a world's outer workflow."""
        ...

    async def request_phase_advance(self, world_id: UUID) -> PhaseAdvanceResult:
        """Coordinate the next phase; activities perform sealed work + commits."""
        ...

    async def pause_world(self, world_id: UUID, mode: PauseMode) -> None:
        """Signal pause (maps to Temporal Signal/Update if adopted)."""
        ...

    async def resume_world(self, world_id: UUID) -> PhaseAdvanceResult | None:
        """Signal resume after a safe boundary."""
        ...

    async def reconcile(self, world_id: UUID) -> ReconciliationReport:
        """Reconcile durable tasks / workflow state without duplicating canon."""
        ...


class NoopTemporalOrchestrator:
    """No-op Temporal adapter documenting Stage 4 deferral (ADR-0003).

    Does not depend on the Temporal SDK. Callers that need a live orchestrator must
    use ``DeterministicPhaseRunner`` (and S4-ORCH-001 worker leases), not this type.
    """

    __slots__ = ()

    @property
    def adoption_status(self) -> TemporalAdoptionStatus:
        return TEMPORAL_ADOPTION_STATUS

    @property
    def defer_reason(self) -> str | None:
        return TEMPORAL_DEFER_REASON

    def _raise_deferred(self) -> NoReturn:
        raise TemporalDeferredError(TEMPORAL_DEFER_REASON)

    async def start_world(self, world_id: UUID) -> None:
        del world_id
        self._raise_deferred()

    async def request_phase_advance(self, world_id: UUID) -> PhaseAdvanceResult:
        del world_id
        self._raise_deferred()

    async def pause_world(self, world_id: UUID, mode: PauseMode) -> None:
        del world_id, mode
        self._raise_deferred()

    async def resume_world(self, world_id: UUID) -> PhaseAdvanceResult | None:
        del world_id
        self._raise_deferred()

    async def reconcile(self, world_id: UUID) -> ReconciliationReport:
        del world_id
        self._raise_deferred()


__all__ = [
    "TEMPORAL_ADOPTION_STATUS",
    "TEMPORAL_DEFER_REASON",
    "NoopTemporalOrchestrator",
    "TemporalAdoptionStatus",
    "TemporalDeferredError",
    "TemporalOrchestratorPort",
]
