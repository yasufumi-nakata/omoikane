"""Minimal L3 reasoning backends with deterministic failover."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence


class BackendUnavailableError(RuntimeError):
    """Raised when a configured cognitive backend cannot serve requests."""


@dataclass
class CognitiveProfile:
    """Active backend selection profile for one cognitive service."""

    primary: str
    fallback: List[str] = field(default_factory=list)


@dataclass
class ReasoningResult:
    """Structured reasoning output returned by one backend."""

    backend_id: str
    conclusion: str
    evidence: List[str]
    confidence: float

    def to_dict(self) -> Dict[str, object]:
        return {
            "backend_id": self.backend_id,
            "conclusion": self.conclusion,
            "evidence": list(self.evidence),
            "confidence": round(self.confidence, 3),
        }


class ReasoningBackend:
    """Base class for safe, deterministic reasoning backends."""

    def __init__(self, backend_id: str, *, healthy: bool = True) -> None:
        self.backend_id = backend_id
        self._healthy = healthy

    def set_health(self, healthy: bool) -> None:
        self._healthy = healthy

    def reason(self, query: str, beliefs: Sequence[str]) -> ReasoningResult:
        if not self._healthy:
            raise BackendUnavailableError(f"{self.backend_id} is unavailable")
        return self._reason(query, beliefs)

    def _reason(self, query: str, beliefs: Sequence[str]) -> ReasoningResult:
        raise NotImplementedError


class SymbolicReasoningBackend(ReasoningBackend):
    """Simple rules-first backend that prefers invariants over novelty."""

    def _reason(self, query: str, beliefs: Sequence[str]) -> ReasoningResult:
        ordered_beliefs = list(dict.fromkeys(beliefs))
        conclusion = (
            f"規則系 backend は `{query}` に対して "
            f"{', '.join(ordered_beliefs[:2])} を先に満たす案を優先します。"
        )
        evidence = [f"rule:{belief}" for belief in ordered_beliefs]
        return ReasoningResult(
            backend_id=self.backend_id,
            conclusion=conclusion,
            evidence=evidence,
            confidence=0.81,
        )


class NarrativeReasoningBackend(ReasoningBackend):
    """Fallback backend that summarizes safe next actions in prose."""

    def _reason(self, query: str, beliefs: Sequence[str]) -> ReasoningResult:
        ordered_beliefs = list(dict.fromkeys(beliefs))
        conclusion = (
            "代替 backend は sandbox 維持と failover 記録を条件に、"
            f"`{query}` を継続可能と判断します。"
        )
        evidence = [f"context:{belief}" for belief in ordered_beliefs]
        return ReasoningResult(
            backend_id=self.backend_id,
            conclusion=conclusion,
            evidence=evidence,
            confidence=0.67,
        )


class ReasoningService:
    """Profile-driven router that fails over across reasoning backends."""

    def __init__(
        self,
        profile: CognitiveProfile,
        backends: Sequence[ReasoningBackend],
    ) -> None:
        self.profile = profile
        self._backends = {backend.backend_id: backend for backend in backends}

    def set_backend_health(self, backend_id: str, healthy: bool) -> None:
        self._backends[backend_id].set_health(healthy)

    def run(self, query: str, beliefs: Sequence[str]) -> Dict[str, object]:
        attempted: List[str] = []
        failures: List[str] = []
        order = [self.profile.primary] + list(self.profile.fallback)

        for backend_id in order:
            attempted.append(backend_id)
            backend = self._backends[backend_id]
            try:
                result = backend.reason(query, beliefs)
            except BackendUnavailableError as exc:
                failures.append(str(exc))
                continue

            return {
                "profile": {
                    "primary": self.profile.primary,
                    "fallback": list(self.profile.fallback),
                },
                "attempted_backends": attempted,
                "selected_backend": result.backend_id,
                "degraded": result.backend_id != self.profile.primary,
                "failures": failures,
                "result": result.to_dict(),
            }

        raise BackendUnavailableError(
            "all reasoning backends unavailable: " + ", ".join(attempted)
        )
