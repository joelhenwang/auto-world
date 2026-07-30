"""Abandoned-lease reconciliation service (S4-ORCH-001).

Periodically called (e.g. by a cron task or phase runner) to:
  1. Identify workers whose heartbeat has expired.
  2. Mark them as *lost* in the worker registry.
  3. Reset any tasks they held to PENDING so they can be reclaimed.

This is safe to call concurrently; SKIP LOCKED on worker rows prevents
double-processing and the ``reset_abandoned_leases`` bulk update is
idempotent (tasks already released are unaffected).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fictional_world.application.ports.repositories import UnitOfWork


@dataclass(frozen=True, slots=True)
class ReconcileResult:
    workers_marked_lost: int
    tasks_reset: int


class ReconcileAbandonedService:
    """Find expired workers and reset their held task leases.

    Default heartbeat grace period is 5 minutes; callers may override for
    testing or tighter operational requirements.
    """

    DEFAULT_HEARTBEAT_GRACE = timedelta(minutes=5)

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def reconcile(
        self,
        *,
        now: datetime | None = None,
        heartbeat_grace: timedelta | None = None,
    ) -> ReconcileResult:
        """Find lost workers and reset their claimed tasks.

        Steps:
        1. Lock and load workers with expired heartbeats (SKIP LOCKED).
        2. Mark each as *lost* (idempotent; already-lost workers are skipped
           by the ``find_lost`` query).
        3. Bulk-update ``task_run`` rows owned by the lost worker keys back
           to PENDING state with ``available_at = now``.
        """
        ts = now or datetime.now(UTC)
        grace = heartbeat_grace if heartbeat_grace is not None else self.DEFAULT_HEARTBEAT_GRACE

        lost_workers = await self._uow.workers.find_lost(now=ts, heartbeat_grace=grace)
        if not lost_workers:
            return ReconcileResult(workers_marked_lost=0, tasks_reset=0)

        for worker in lost_workers:
            await self._uow.workers.mark_lost(worker.id)

        worker_keys = [w.worker_key for w in lost_workers]
        tasks_reset = await self._uow.tasks.reset_abandoned_leases(worker_keys=worker_keys, now=ts)

        return ReconcileResult(
            workers_marked_lost=len(lost_workers),
            tasks_reset=tasks_reset,
        )
