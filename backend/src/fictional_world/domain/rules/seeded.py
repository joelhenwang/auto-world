"""Deterministic seeded helpers for pure domain resolution (handbook ``10`` §10.6)."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field


def mix_seed(seed: int, *parts: str | int | float) -> int:
    """Derive a stable 63-bit seed from a base seed and salt parts."""

    material = f"{seed}:" + ":".join(str(part) for part in parts)
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") & 0x7FFF_FFFF_FFFF_FFFF


def seeded_unit_float(seed: int, *parts: str | int | float) -> float:
    """Return a deterministic float in ``[0, 1)`` for the given seed and salts."""

    return random.Random(mix_seed(seed, *parts)).random()  # noqa: S311


@dataclass
class SeededRng:
    """Small deterministic RNG wrapper used by combat/magic resolvers."""

    seed: int
    salt: str = ""
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(mix_seed(self.seed, self.salt))  # noqa: S311

    def unit(self) -> float:
        """Draw the next float in ``[0, 1)``."""

        return self._rng.random()

    def uniform(self, low: float, high: float) -> float:
        """Draw a float in ``[low, high]``."""

        if high < low:
            msg = f"uniform high {high} is below low {low}"
            raise ValueError(msg)
        return low + (high - low) * self.unit()

    def derived(self, salt: str) -> SeededRng:
        """Return a child RNG with a derived seed (does not advance this RNG)."""

        return SeededRng(seed=mix_seed(self.seed, self.salt, salt), salt=salt)
