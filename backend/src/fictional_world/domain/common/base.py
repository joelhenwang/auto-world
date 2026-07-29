"""Strict immutable Pydantic base for domain boundary contracts."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StrictContract(BaseModel):
    """Strict immutable contract used at service and model boundaries.

    Follows handbook ``05`` ContractModel (``extra=forbid``, frozen) and ``19``
    naming. ``strict=True`` is intentionally omitted so JSON string inputs can
    coerce to UUID/datetime at boundaries; model-facing parsers may still call
    ``model_validate(..., strict=True)`` where required.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
    )
