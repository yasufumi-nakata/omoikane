"""Qualia buffer reference model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List

from ..common import utc_now_iso


@dataclass
class QualiaTick:
    """Single subjective-state sample."""

    tick_id: int
    summary: str
    valence: float
    arousal: float
    clarity: float
    observed_at: str


class QualiaBuffer:
    """Monotonic in-memory qualia stream."""

    def __init__(self) -> None:
        self._ticks: List[QualiaTick] = []

    @staticmethod
    def _validate_range(name: str, value: float, minimum: float, maximum: float) -> None:
        if not minimum <= value <= maximum:
            raise ValueError(f"{name} must be between {minimum} and {maximum}")

    def append(
        self,
        summary: str,
        valence: float,
        arousal: float,
        clarity: float,
    ) -> QualiaTick:
        if not summary.strip():
            raise ValueError("summary must not be empty")
        self._validate_range("valence", valence, -1.0, 1.0)
        self._validate_range("arousal", arousal, 0.0, 1.0)
        self._validate_range("clarity", clarity, 0.0, 1.0)
        tick_id = len(self._ticks)
        tick = QualiaTick(
            tick_id=tick_id,
            summary=summary,
            valence=valence,
            arousal=arousal,
            clarity=clarity,
            observed_at=utc_now_iso(),
        )
        self._ticks.append(tick)
        return tick

    def verify_monotonic(self) -> bool:
        return all(index == tick.tick_id for index, tick in enumerate(self._ticks))

    def recent(self, count: int = 5) -> List[Dict[str, Any]]:
        if count < 1:
            raise ValueError("count must be >= 1")
        return [asdict(tick) for tick in self._ticks[-count:]]
