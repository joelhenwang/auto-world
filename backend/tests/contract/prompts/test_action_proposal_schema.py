"""Stage 1 fake-corpus conformance to the frozen ActionProposal schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from fictional_world.domain.scenes.proposals import ActionProposal, SceneResolution
from fictional_world.prompts import (
    AuthoredOtherReactionError,
    validate_no_authored_other_reaction,
)

CORPUS = Path(__file__).resolve().parents[2] / "fixtures" / "model_corpus" / "stage1"


@pytest.mark.contract
@pytest.mark.parametrize(
    "filename, expected_family",
    [
        ("quiet_mira_wait.json", "wait"),
        ("quiet_dain_rest.json", "rest"),
        ("mira_dain_social_communicate.json", "communicate"),
    ],
)
def test_valid_action_corpus_parses(filename: str, expected_family: str) -> None:
    proposal = ActionProposal.model_validate_json((CORPUS / filename).read_text(encoding="utf-8"))

    assert proposal.action_family == expected_family


@pytest.mark.contract
def test_malformed_and_schema_invalid_corpus_are_rejected() -> None:
    with pytest.raises(ValidationError) as malformed:
        ActionProposal.model_validate_json((CORPUS / "malformed.json").read_text(encoding="utf-8"))
    assert any(error["type"] == "json_invalid" for error in malformed.value.errors())

    with pytest.raises(ValidationError):
        ActionProposal.model_validate_json(
            (CORPUS / "schema_invalid.json").read_text(encoding="utf-8")
        )


@pytest.mark.contract
def test_shape_valid_authored_other_reaction_fails_convention_check() -> None:
    proposal = ActionProposal.model_validate_json(
        (CORPUS / "authored_other_reaction_invalid.json").read_text(encoding="utf-8")
    )

    with pytest.raises(AuthoredOtherReactionError, match="Dain"):
        validate_no_authored_other_reaction(proposal, other_character_names=("Dain",))


@pytest.mark.contract
def test_resolver_and_narrator_corpus_are_well_formed() -> None:
    resolution = SceneResolution.model_validate_json(
        (CORPUS / "resolver_move.json").read_text(encoding="utf-8")
    )
    assert resolution.effects[0].kind == "move_entity"

    narration = json.loads((CORPUS / "narrator_ok.json").read_text(encoding="utf-8"))
    assert narration == {
        "schema_version": "1.0",
        "narration": (
            "Mira checked the route board once more, then stepped into the damp morning "
            "traffic toward Market Square. Nothing pressed her to hurry."
        ),
    }
