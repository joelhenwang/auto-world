"""Knowledge/agency checks for Stage 1 character-facing prompt contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from fictional_world.domain.scenes.proposals import ActionProposal
from fictional_world.prompts import (
    AuthoredOtherReactionError,
    PromptRegistry,
    validate_no_authored_other_reaction,
)

CORPUS = Path(__file__).resolve().parents[2] / "fixtures" / "model_corpus" / "stage1"
STAGE1_ACTIONS = (
    "wait",
    "observe",
    "rest",
    "continue_activity",
    "move",
    "communicate",
    "socialize",
    "interact_environment",
)


@pytest.mark.contract
@pytest.mark.security
def test_system_prompts_preserve_stage1_authority_and_knowledge_boundary() -> None:
    registry = PromptRegistry()

    for prompt_meta in registry.list_active():
        system = registry.load(prompt_meta.prompt_id).system_template.lower()
        assert "models propose only" in system
        assert "private knowledge" in system
        assert "json schema" in system
        assert all(action in system for action in STAGE1_ACTIONS)


@pytest.mark.contract
@pytest.mark.security
def test_other_character_reaction_is_rejected_but_open_attempt_is_accepted() -> None:
    invalid = ActionProposal.model_validate_json(
        (CORPUS / "authored_other_reaction_invalid.json").read_text(encoding="utf-8")
    )
    with pytest.raises(AuthoredOtherReactionError):
        validate_no_authored_other_reaction(invalid, other_character_names=("Dain",))

    valid = ActionProposal.model_validate_json(
        (CORPUS / "mira_dain_social_communicate.json").read_text(encoding="utf-8")
    )
    validate_no_authored_other_reaction(valid, other_character_names=("Dain",))
