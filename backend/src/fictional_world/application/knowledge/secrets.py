"""Secret access policy — holders see secret_key only when granted."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from fictional_world.domain.common.errors import SecretAccessDenied
from fictional_world.domain.knowledge.persistence import SecretAccessPersistenceRecord
from fictional_world.domain.knowledge.visibility import SecretAccessLevel

# Access levels that grant read of the secret payload / key listing.
_GRANTING_LEVELS: frozenset[str] = frozenset(
    {
        SecretAccessLevel.OWNER.value,
        SecretAccessLevel.SHARED.value,
        SecretAccessLevel.OVERHEARD.value,
    }
)


class SecretAccessPolicy:
    """Enforce secret_access grants; never trust observation/prompt text."""

    def __init__(self, rows: Sequence[SecretAccessPersistenceRecord]) -> None:
        self._rows = tuple(rows)

    def active_rows_for_holder(
        self, holder_character_id: UUID, *, world_id: UUID | None = None
    ) -> tuple[SecretAccessPersistenceRecord, ...]:
        out: list[SecretAccessPersistenceRecord] = []
        for row in self._rows:
            if row.holder_character_id != holder_character_id:
                continue
            if world_id is not None and row.world_id != world_id:
                continue
            if row.revoked_event_id is not None:
                continue
            if row.access_level == SecretAccessLevel.REVOKED.value:
                continue
            if row.access_level not in _GRANTING_LEVELS:
                continue
            out.append(row)
        return tuple(out)

    def held_secret_keys(
        self, holder_character_id: UUID, *, world_id: UUID | None = None
    ) -> frozenset[str]:
        return frozenset(
            row.secret_key
            for row in self.active_rows_for_holder(holder_character_id, world_id=world_id)
        )

    def may_access(
        self,
        *,
        holder_character_id: UUID,
        secret_key: str,
        world_id: UUID | None = None,
    ) -> bool:
        return secret_key in self.held_secret_keys(holder_character_id, world_id=world_id)

    def require_access(
        self,
        *,
        holder_character_id: UUID,
        secret_key: str,
        world_id: UUID | None = None,
    ) -> SecretAccessPersistenceRecord:
        for row in self.active_rows_for_holder(holder_character_id, world_id=world_id):
            if row.secret_key == secret_key:
                return row
        raise SecretAccessDenied(f"holder lacks access to secret_key={secret_key!r}")

    def evaluate_injection_claim(
        self,
        *,
        holder_character_id: UUID,
        secret_key: str,
        observation_text: str,
        world_id: UUID | None = None,
    ) -> bool:
        """Prompt-injection text in observations cannot escalate secret access.

        The observation payload is ignored for authorization decisions.
        """

        _ = observation_text  # intentionally unused — never trust content
        return self.may_access(
            holder_character_id=holder_character_id,
            secret_key=secret_key,
            world_id=world_id,
        )


__all__ = ["SecretAccessPolicy"]
