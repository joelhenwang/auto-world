"""Contract tests for prompt metadata, registry, and strict rendering."""

from __future__ import annotations

import re

import pytest

from fictional_world.prompts import PromptRegistry, PromptRenderer, PromptRenderError


@pytest.mark.contract
def test_all_active_prompts_render_from_declared_variables() -> None:
    registry = PromptRegistry()
    renderer = PromptRenderer()

    active = registry.list_active()
    assert tuple(meta.prompt_id for meta in active) == (
        "character_decision_v1",
        "character_reaction_v1",
        "scene_narrator_v1",
        "scene_resolver_v1",
    )

    for prompt_meta in active:
        asset = registry.load(prompt_meta.prompt_id)
        variables = {section: f"value::{section}" for section in prompt_meta.input_sections}
        rendered = renderer.render(asset, variables)

        assert rendered.prompt_id == prompt_meta.prompt_id
        assert re.fullmatch(r"[0-9a-f]{64}", rendered.content_hash)
        assert all(value in rendered.user for value in variables.values())


@pytest.mark.contract
def test_renderer_rejects_unsealed_variables() -> None:
    asset = PromptRegistry().load("character_decision_v1")
    renderer = PromptRenderer()
    complete = {section: section for section in asset.meta.input_sections}

    missing = dict(complete)
    missing.pop("current_perception")
    with pytest.raises(PromptRenderError, match=r"missing=.*current_perception"):
        renderer.render(asset, missing)

    extra = complete | {"omniscient_appendix": "must not be accepted"}
    with pytest.raises(PromptRenderError, match=r"extra=.*omniscient_appendix"):
        renderer.render(asset, extra)


@pytest.mark.contract
def test_render_hash_covers_prompt_and_variables() -> None:
    asset = PromptRegistry().load("character_decision_v1")
    renderer = PromptRenderer()
    variables = {section: section for section in asset.meta.input_sections}

    first = renderer.render(asset, variables)
    repeated = renderer.render(asset, variables)
    changed = renderer.render(asset, variables | {"phase_label": "evening"})

    assert first.content_hash == repeated.content_hash
    assert first.content_hash != changed.content_hash
