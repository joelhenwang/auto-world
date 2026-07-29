"""Token trim tests for Stage 1 context budget."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from fictional_world.application.context.assembler import assemble_character_context
from fictional_world.application.context.budget import PACKAGE_SOFT_CAP, estimate_tokens
from fictional_world.application.context.types import ContextTaskType
from fictional_world.domain.characters.records import CharacterStateRecord
from fictional_world.domain.seed.ids import seed_uuid
from fictional_world.domain.seed.records import CharacterCardVersionRecord

MIRA = seed_uuid("character/mira-talren")


@pytest.mark.unit
def test_estimate_tokens_deterministic() -> None:
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("a" * 8) == 2


@pytest.mark.unit
def test_large_memory_is_trimmed() -> None:
    card = CharacterCardVersionRecord(
        id=uuid4(),
        character_id=MIRA,
        version_number=1,
        identity={"name": "Mira"},
        backstory="x" * 500,
        appearance={},
        personality_traits={},
        values={},
        fears={},
        desires={},
        boundaries={},
        voice_profile={},
        initial_capabilities={},
        secret_manifest={},
        change_summary="v1",
        content_hash="h",
    )
    state = CharacterStateRecord(
        character_id=MIRA,
        location_id=None,
        life_status="alive",
        stamina=Decimal("1"),
        mana=Decimal("1"),
        energy=Decimal("1"),
        hunger=Decimal("1"),
        pain=Decimal("0"),
        stress=Decimal("0"),
        social_need=Decimal("0"),
        valence=Decimal("0"),
        arousal=Decimal("0"),
        dominance=Decimal("0"),
        current_card_version_id=card.id,
        version=0,
    )
    huge = tuple(f"memory-{i}-" + ("z" * 400) for i in range(80))
    package = assemble_character_context(
        observer_id=MIRA,
        phase_snapshot_id=uuid4(),
        task_type=ContextTaskType.CHARACTER_DECISION,
        card=card,
        state=state,
        recent_memories=huge,
    )
    assert package.token_estimate <= PACKAGE_SOFT_CAP
    # Perception/state survive trimming
    ids = {s.section_id.value for s in package.sections}
    assert "current_state" in ids
    assert "current_perception" in ids
    assert "allowed_action_families" in ids
