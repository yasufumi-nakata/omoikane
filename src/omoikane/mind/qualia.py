"""Qualia buffer reference model."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Tuple

from ..common import utc_now_iso

DEFAULT_MODALITIES: Tuple[str, ...] = ("visual", "auditory", "somatic", "interoceptive")
DEFAULT_EMBEDDING_DIMENSIONS = 32
DEFAULT_SAMPLING_WINDOW_MS = 250


@dataclass(frozen=True)
class QualiaSamplingProfile:
    """Reference surrogate profile for qualia sampling."""

    embedding_dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS
    sampling_window_ms: int = DEFAULT_SAMPLING_WINDOW_MS
    modalities: Tuple[str, ...] = field(default_factory=lambda: DEFAULT_MODALITIES)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "embedding_dimensions": self.embedding_dimensions,
            "sampling_window_ms": self.sampling_window_ms,
            "modalities": list(self.modalities),
        }


@dataclass
class QualiaTick:
    """Single subjective-state sample."""

    tick_id: int
    summary: str
    valence: float
    arousal: float
    clarity: float
    observed_at: str
    sampling_profile: Dict[str, Any]
    modality_salience: Dict[str, float]
    sensory_embeddings: Dict[str, List[float]]
    attention_target: str
    self_awareness: float
    lucidity: float


class QualiaBuffer:
    """Monotonic in-memory qualia stream."""

    def __init__(self, profile: QualiaSamplingProfile | None = None) -> None:
        self._profile = profile or QualiaSamplingProfile()
        self._ticks: List[QualiaTick] = []

    @staticmethod
    def _validate_range(name: str, value: float, minimum: float, maximum: float) -> None:
        if not minimum <= value <= maximum:
            raise ValueError(f"{name} must be between {minimum} and {maximum}")

    def _normalize_modality_salience(
        self,
        modality_salience: Dict[str, float] | None,
    ) -> Dict[str, float]:
        provided = modality_salience or {}
        unexpected = sorted(set(provided) - set(self._profile.modalities))
        if unexpected:
            raise ValueError(f"unsupported modality keys: {', '.join(unexpected)}")

        normalized: Dict[str, float] = {}
        for modality in self._profile.modalities:
            value = provided.get(modality, 0.0)
            self._validate_range(f"{modality} salience", value, 0.0, 1.0)
            normalized[modality] = value
        return normalized

    def _surrogate_embedding(self, tick_id: int, summary: str, modality: str, salience: float) -> List[float]:
        embedding: List[float] = []
        block_index = 0
        while len(embedding) < self._profile.embedding_dimensions:
            seed = f"{tick_id}:{summary}:{modality}:{block_index}".encode("utf-8")
            digest = hashlib.sha256(seed).digest()
            for byte in digest:
                normalized = ((byte / 255.0) * 2.0) - 1.0
                embedding.append(round(normalized * salience, 6))
                if len(embedding) == self._profile.embedding_dimensions:
                    return embedding
            block_index += 1
        return embedding

    def profile(self) -> Dict[str, Any]:
        return self._profile.to_dict()

    def append(
        self,
        summary: str,
        valence: float,
        arousal: float,
        clarity: float,
        modality_salience: Dict[str, float] | None = None,
        attention_target: str = "internal-state",
        self_awareness: float = 0.6,
        lucidity: float = 0.9,
    ) -> QualiaTick:
        if not summary.strip():
            raise ValueError("summary must not be empty")
        if not attention_target.strip():
            raise ValueError("attention_target must not be empty")
        self._validate_range("valence", valence, -1.0, 1.0)
        self._validate_range("arousal", arousal, 0.0, 1.0)
        self._validate_range("clarity", clarity, 0.0, 1.0)
        self._validate_range("self_awareness", self_awareness, 0.0, 1.0)
        self._validate_range("lucidity", lucidity, 0.0, 1.0)
        normalized_salience = self._normalize_modality_salience(modality_salience)
        tick_id = len(self._ticks)
        sensory_embeddings = {
            modality: self._surrogate_embedding(tick_id, summary, modality, salience)
            for modality, salience in normalized_salience.items()
        }
        tick = QualiaTick(
            tick_id=tick_id,
            summary=summary,
            valence=valence,
            arousal=arousal,
            clarity=clarity,
            observed_at=utc_now_iso(),
            sampling_profile=self.profile(),
            modality_salience=normalized_salience,
            sensory_embeddings=sensory_embeddings,
            attention_target=attention_target,
            self_awareness=self_awareness,
            lucidity=lucidity,
        )
        self._ticks.append(tick)
        return tick

    def verify_monotonic(self) -> bool:
        return all(index == tick.tick_id for index, tick in enumerate(self._ticks))

    def recent(self, count: int = 5) -> List[Dict[str, Any]]:
        if count < 1:
            raise ValueError("count must be >= 1")
        return [asdict(tick) for tick in self._ticks[-count:]]
