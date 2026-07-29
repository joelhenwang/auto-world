"""Injectable seeded random source for deterministic rule rolls."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field


@dataclass
class SeededRandom:
    """Returns scripted floats in [0, 1) then falls back to a fixed cycle."""

    script: list[float] = field(default_factory=list)
    _index: int = 0
    _fallback: Iterator[float] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._fallback = _cycle_fallback()

    def seed_script(self, values: Iterable[float]) -> None:
        parsed = list(values)
        for value in parsed:
            if not 0.0 <= value < 1.0:
                msg = f"scripted roll must be in [0, 1): {value}"
                raise ValueError(msg)
        self.script = parsed
        self._index = 0

    def random(self) -> float:
        if self._index < len(self.script):
            value = self.script[self._index]
            self._index += 1
            return value
        return next(self._fallback)


def _cycle_fallback() -> Iterator[float]:
    while True:
        yield 0.5
