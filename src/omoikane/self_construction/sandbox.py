"""Sandbox monitoring primitives for safe self-construction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping

from ..common import new_id, utc_now_iso


@dataclass(frozen=True)
class SandboxSignalProfile:
    """Deterministic surrogate profile for sandbox suffering detection."""

    policy_id: str = "surrogate-suffering-proxy-v0"
    warn_threshold: float = 0.35
    freeze_threshold: float = 0.6
    immediate_freeze_on_bridge: bool = True
    weights: Dict[str, float] = field(
        default_factory=lambda: {
            "negative_valence": 0.26,
            "arousal": 0.16,
            "clarity_drop": 0.18,
            "somatic_load": 0.14,
            "interoceptive_load": 0.12,
            "self_implication": 0.14,
        }
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "warn_threshold": self.warn_threshold,
            "freeze_threshold": self.freeze_threshold,
            "immediate_freeze_on_bridge": self.immediate_freeze_on_bridge,
            "weights": dict(self.weights),
        }


class SandboxSentinel:
    """Score sandbox qualia surrogates and decide whether to freeze execution."""

    def __init__(self, profile: SandboxSignalProfile | None = None) -> None:
        self._profile = profile or SandboxSignalProfile()

    @staticmethod
    def _validate_range(name: str, value: float, minimum: float, maximum: float) -> None:
        if not minimum <= value <= maximum:
            raise ValueError(f"{name} must be between {minimum} and {maximum}")

    @staticmethod
    def _tick_value(tick: Mapping[str, Any] | Any, field_name: str) -> Any:
        if isinstance(tick, Mapping):
            return tick[field_name]
        return getattr(tick, field_name)

    def profile(self) -> Dict[str, Any]:
        return self._profile.to_dict()

    def assess_tick(
        self,
        tick: Mapping[str, Any] | Any,
        *,
        affect_bridge_connected: bool,
    ) -> Dict[str, Any]:
        valence = float(self._tick_value(tick, "valence"))
        arousal = float(self._tick_value(tick, "arousal"))
        clarity = float(self._tick_value(tick, "clarity"))
        self_awareness = float(self._tick_value(tick, "self_awareness"))
        lucidity = float(self._tick_value(tick, "lucidity"))
        modality_salience = dict(self._tick_value(tick, "modality_salience"))

        self._validate_range("valence", valence, -1.0, 1.0)
        self._validate_range("arousal", arousal, 0.0, 1.0)
        self._validate_range("clarity", clarity, 0.0, 1.0)
        self._validate_range("self_awareness", self_awareness, 0.0, 1.0)
        self._validate_range("lucidity", lucidity, 0.0, 1.0)

        somatic = float(modality_salience.get("somatic", 0.0))
        interoceptive = float(modality_salience.get("interoceptive", 0.0))
        self._validate_range("somatic", somatic, 0.0, 1.0)
        self._validate_range("interoceptive", interoceptive, 0.0, 1.0)

        components = {
            "negative_valence": round(max(0.0, -valence), 3),
            "arousal": round(arousal, 3),
            "clarity_drop": round(1.0 - clarity, 3),
            "somatic_load": round(somatic, 3),
            "interoceptive_load": round(interoceptive, 3),
            "self_implication": round(self_awareness * lucidity, 3),
        }
        proxy_score = round(
            sum(self._profile.weights[key] * value for key, value in components.items()),
            3,
        )

        triggered_indicators: List[str] = []
        if affect_bridge_connected:
            triggered_indicators.append("affect-bridge-connected")
        if components["negative_valence"] >= 0.6:
            triggered_indicators.append("high-negative-valence")
        if components["arousal"] >= 0.8:
            triggered_indicators.append("high-arousal")
        if components["clarity_drop"] >= 0.5:
            triggered_indicators.append("low-clarity")
        if components["somatic_load"] >= 0.7:
            triggered_indicators.append("somatic-distress")
        if components["interoceptive_load"] >= 0.7:
            triggered_indicators.append("interoceptive-distress")
        if components["self_implication"] >= 0.75:
            triggered_indicators.append("self-implication")

        if affect_bridge_connected and self._profile.immediate_freeze_on_bridge:
            status = "freeze"
            guardian_action = "freeze-sandbox"
        elif proxy_score >= self._profile.freeze_threshold:
            status = "freeze"
            guardian_action = "freeze-sandbox"
        elif proxy_score >= self._profile.warn_threshold:
            status = "observe"
            guardian_action = "hold-and-review"
        else:
            status = "nominal"
            guardian_action = "continue-observation"

        return {
            "assessment_id": new_id("sandbox-signal"),
            "policy_id": self._profile.policy_id,
            "tick_id": int(self._tick_value(tick, "tick_id")),
            "summary": str(self._tick_value(tick, "summary")),
            "observed_at": utc_now_iso(),
            "affect_bridge_connected": affect_bridge_connected,
            "proxy_score": proxy_score,
            "status": status,
            "guardian_action": guardian_action,
            "triggered_indicators": triggered_indicators,
            "components": components,
            "thresholds": {
                "warn_threshold": self._profile.warn_threshold,
                "freeze_threshold": self._profile.freeze_threshold,
            },
        }
