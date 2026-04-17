"""Self-model tracking and abrupt-change detection."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List, Sequence

from ..common import utc_now_iso


@dataclass
class SelfModelSnapshot:
    """Declared self-state at a point in time."""

    identity_id: str
    values: List[str]
    goals: List[str]
    traits: Dict[str, float]
    recorded_at: str = field(default_factory=utc_now_iso)


class SelfModelMonitor:
    """Tracks snapshots and flags abrupt deviations."""

    def __init__(self, abrupt_change_threshold: float = 0.35) -> None:
        self._history: List[SelfModelSnapshot] = []
        self._threshold = abrupt_change_threshold

    @staticmethod
    def _set_distance(left: Sequence[str], right: Sequence[str]) -> float:
        left_set = set(left)
        right_set = set(right)
        universe = left_set | right_set
        if not universe:
            return 0.0
        overlap = len(left_set & right_set)
        return 1.0 - (overlap / float(len(universe)))

    @staticmethod
    def _trait_distance(left: Dict[str, float], right: Dict[str, float]) -> float:
        keys = set(left) | set(right)
        if not keys:
            return 0.0
        total = 0.0
        for key in keys:
            total += abs(left.get(key, 0.0) - right.get(key, 0.0))
        return total / float(len(keys))

    def update(self, snapshot: SelfModelSnapshot) -> Dict[str, object]:
        divergence = 0.0
        abrupt = False

        if self._history:
            previous = self._history[-1]
            divergence = (
                self._set_distance(previous.values, snapshot.values)
                + self._set_distance(previous.goals, snapshot.goals)
                + self._trait_distance(previous.traits, snapshot.traits)
            ) / 3.0
            abrupt = divergence >= self._threshold

        self._history.append(snapshot)
        return {
            "abrupt_change": abrupt,
            "divergence": round(divergence, 4),
            "snapshot": asdict(snapshot),
        }

    def history(self) -> List[Dict[str, object]]:
        return [asdict(snapshot) for snapshot in self._history]

