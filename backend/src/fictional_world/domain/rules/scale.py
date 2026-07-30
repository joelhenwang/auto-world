"""World scale constants and clamping (handbook ``10`` §2)."""

from __future__ import annotations

STAT_MIN = 0.0
STAT_MAX = 100.0
UNIT_MIN = 0.0
UNIT_MAX = 1.0


def clamp_world_scale(
    value: float, *, minimum: float = STAT_MIN, maximum: float = STAT_MAX
) -> float:
    """Clamp a value to the absolute world scale (default ``0..100``)."""

    if minimum > maximum:
        msg = f"minimum {minimum} exceeds maximum {maximum}"
        raise ValueError(msg)
    return max(minimum, min(maximum, value))


def clamp_unit(value: float) -> float:
    """Clamp a ratio or quality factor to ``0..1``."""

    return clamp_world_scale(value, minimum=UNIT_MIN, maximum=UNIT_MAX)
