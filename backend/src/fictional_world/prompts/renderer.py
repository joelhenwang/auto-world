"""Strict Jinja rendering for sealed prompt sections."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass

from jinja2 import StrictUndefined, TemplateError, meta
from jinja2.sandbox import SandboxedEnvironment

from fictional_world.prompts.registry import PromptAsset


class PromptRenderError(ValueError):
    """Raised when a prompt or sealed variable mapping cannot be rendered."""


@dataclass(frozen=True, slots=True)
class RenderedPrompt:
    """Rendered messages with reproducible prompt-plus-variable provenance."""

    prompt_id: str
    system: str
    user: str
    content_hash: str


class PromptRenderer:
    """Render prompt assets without undeclared or dynamically appended sections."""

    def __init__(self) -> None:
        self._environment = SandboxedEnvironment(
            undefined=StrictUndefined,
            autoescape=False,
            keep_trailing_newline=True,
        )

    def render(
        self,
        asset: PromptAsset,
        variables: Mapping[str, str],
    ) -> RenderedPrompt:
        """Render an asset only when template, metadata, and variables exactly agree."""

        expected = set(asset.meta.input_sections)
        declared = self._declared_variables(asset)
        if declared != expected:
            missing_from_meta = sorted(declared - expected)
            unused_metadata = sorted(expected - declared)
            raise PromptRenderError(
                "template/metadata variable mismatch: "
                f"undeclared={missing_from_meta}, unused={unused_metadata}"
            )

        supplied = set(variables)
        if supplied != expected:
            missing = sorted(expected - supplied)
            extra = sorted(supplied - expected)
            raise PromptRenderError(
                f"sealed prompt variables mismatch: missing={missing}, extra={extra}"
            )

        render_variables = dict(variables)
        try:
            system = self._environment.from_string(asset.system_template).render(render_variables)
            user = self._environment.from_string(asset.user_template).render(render_variables)
        except TemplateError as exc:
            raise PromptRenderError(f"could not render {asset.meta.prompt_id}") from exc

        hash_payload = json.dumps(
            {
                "prompt_source_hash": asset.source_hash,
                "variables": dict(sorted(render_variables.items())),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        content_hash = hashlib.sha256(hash_payload.encode()).hexdigest()
        return RenderedPrompt(
            prompt_id=asset.meta.prompt_id,
            system=system,
            user=user,
            content_hash=content_hash,
        )

    def _declared_variables(self, asset: PromptAsset) -> set[str]:
        declared: set[str] = set()
        try:
            for source in (asset.system_template, asset.user_template):
                declared.update(meta.find_undeclared_variables(self._environment.parse(source)))
        except TemplateError as exc:
            raise PromptRenderError(f"invalid template for {asset.meta.prompt_id}") from exc
        return declared
