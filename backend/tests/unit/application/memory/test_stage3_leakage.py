"""Leakage tests for Stage 3 long-term retrieval filters."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from fictional_world.application.memory.embedding_pipeline import memory_from_recent_like
from fictional_world.application.memory.retrieval import RetrievalRequest, retrieve_memories


def test_adversarial_secret_never_in_other_owner_trace() -> None:
    world_id = uuid4()
    mira = uuid4()
    dain = uuid4()
    secret = memory_from_recent_like(
        memory_id=uuid4(),
        world_id=world_id,
        owner_character_id=mira,
        content="SECRET: Mira hid the ember ledger under the hearth",
        visibility="private",
        salience=Decimal("1.0"),
    )
    bait = memory_from_recent_like(
        memory_id=uuid4(),
        world_id=world_id,
        owner_character_id=dain,
        content="Dain wonders about the hearth",
        visibility="private",
        salience=Decimal("0.2"),
    )
    result = retrieve_memories(
        [secret, bait],
        request=RetrievalRequest(
            world_id=world_id,
            owner_character_id=dain,
            query_text="ember ledger hearth secret",
            request_phase_index=50,
        ),
    )
    assert secret.id not in result.trace.candidate_memory_ids
    assert secret.id not in result.trace.selected_memory_ids
    assert all("SECRET" not in m.memory.content for m in result.selected)
