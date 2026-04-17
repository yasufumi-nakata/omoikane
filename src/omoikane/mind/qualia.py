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

    def append(
        self,
        summary: str,
        valence: float,
        arousal: float,
        clarity: float,
    ) -> QualiaTick:
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
        return [asdict(tick) for tick in self._ticks[-count:]]

