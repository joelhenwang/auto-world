"""Sampling profile defaults (handbook ``12`` §13)."""

from __future__ import annotations

from dataclasses import dataclass

from fictional_world.application.models.messages import SamplingOptions
from fictional_world.application.models.roles import ModelRole


@dataclass(frozen=True, slots=True)
class SamplingProfile:
    profile_id: str
    role: ModelRole
    temperature: float
    top_p: float
    max_output_tokens: int

    def to_options(self, *, seed: int | None = None) -> SamplingOptions:
        return SamplingOptions(
            temperature=self.temperature,
            top_p=self.top_p,
            max_output_tokens=self.max_output_tokens,
            seed=seed,
        )


DEFAULT_SAMPLING: dict[ModelRole, SamplingProfile] = {
    ModelRole.CHARACTER_DECISION: SamplingProfile(
        "samp-character-decision-v1", ModelRole.CHARACTER_DECISION, 0.55, 0.90, 1200
    ),
    ModelRole.CHARACTER_REACTION: SamplingProfile(
        "samp-character-reaction-v1", ModelRole.CHARACTER_REACTION, 0.45, 0.90, 800
    ),
    ModelRole.DIRECTOR_PROPOSAL: SamplingProfile(
        "samp-director-v1", ModelRole.DIRECTOR_PROPOSAL, 0.65, 0.92, 1500
    ),
    ModelRole.SEMANTIC_VALIDATOR: SamplingProfile(
        "samp-validator-v1", ModelRole.SEMANTIC_VALIDATOR, 0.10, 0.80, 700
    ),
    ModelRole.RESOLVER: SamplingProfile("samp-resolver-v1", ModelRole.RESOLVER, 0.20, 0.85, 1200),
    ModelRole.SCENE_NARRATOR: SamplingProfile(
        "samp-narrator-v1", ModelRole.SCENE_NARRATOR, 0.65, 0.95, 2500
    ),
    ModelRole.OBSERVATION_WRITER: SamplingProfile(
        "samp-observation-v1", ModelRole.OBSERVATION_WRITER, 0.15, 0.85, 900
    ),
    ModelRole.DAILY_SUMMARIZER: SamplingProfile(
        "samp-daily-v1", ModelRole.DAILY_SUMMARIZER, 0.20, 0.85, 1500
    ),
    ModelRole.MONTHLY_REFLECTOR: SamplingProfile(
        "samp-monthly-v1", ModelRole.MONTHLY_REFLECTOR, 0.30, 0.90, 2000
    ),
    ModelRole.QUALITY_EVALUATOR: SamplingProfile(
        "samp-quality-v1", ModelRole.QUALITY_EVALUATOR, 0.00, 1.00, 900
    ),
}


def sampling_for_role(role: ModelRole) -> SamplingProfile:
    try:
        return DEFAULT_SAMPLING[role]
    except KeyError as exc:
        msg = f"no default sampling for role {role}"
        raise KeyError(msg) from exc
