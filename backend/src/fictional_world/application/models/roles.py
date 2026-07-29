"""Model role vocabulary (handbook ``12``)."""

from __future__ import annotations

from enum import StrEnum


class ModelRole(StrEnum):
    CHARACTER_DECISION = "character_decision"
    CHARACTER_REACTION = "character_reaction"
    DIRECTOR_PROPOSAL = "director_proposal"
    SEMANTIC_VALIDATOR = "semantic_validator"
    RESOLVER = "resolver"
    SCENE_NARRATOR = "scene_narrator"
    OBSERVATION_WRITER = "observation_writer"
    DAILY_SUMMARIZER = "daily_summarizer"
    MONTHLY_REFLECTOR = "monthly_reflector"
    QUALITY_EVALUATOR = "quality_evaluator"
    EMBEDDING = "embedding"
