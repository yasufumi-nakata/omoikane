"""Minimal L3 affect backends with deterministic failover and continuity smoothing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence

from ..common import canonical_json, sha256_text, utc_now_iso
from .reasoning import BackendUnavailableError, CognitiveProfile

AFFECT_SCHEMA_VERSION = "1.0.0"
AFFECT_POLICY_ID = "smooth-affect-failover-v1"
AFFECT_ALLOWED_GUARDS = {"nominal", "observe", "sandbox-notify"}
AFFECT_MAX_VALENCE_DELTA = 0.22
AFFECT_MAX_AROUSAL_DELTA = 0.26


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _quadrant_label(valence: float, arousal: float) -> str:
    if valence <= -0.18 and arousal >= 0.6:
        return "guarded-alert"
    if valence <= -0.18:
        return "somber-focused"
    if valence >= 0.2 and arousal >= 0.55:
        return "energized-positive"
    if valence >= 0.2:
        return "settled-positive"
    return "measured-neutral"


def _state_digest_payload(state: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": state["schema_version"],
        "policy": state["policy"],
        "backend_id": state["backend_id"],
        "source_tick": state["source_tick"],
        "memory_cues": state["memory_cues"],
        "valence": state["valence"],
        "arousal": state["arousal"],
        "mood_label": state["mood_label"],
        "stability": state["stability"],
        "distress_score": state["distress_score"],
        "recommended_guard": state["recommended_guard"],
        "degraded": state["degraded"],
        "continuity_guard": state["continuity_guard"],
    }


def _transition_digest_payload(transition: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": transition["schema_version"],
        "policy_id": transition["policy_id"],
        "state_ref": transition["state_ref"],
        "selected_backend": transition["selected_backend"],
        "attempted_backends": transition["attempted_backends"],
        "degraded": transition["degraded"],
        "previous_state_id": transition["previous_state_id"],
        "smoothed": transition["smoothed"],
        "dampening_applied": transition["dampening_applied"],
        "consent_preserved": transition["consent_preserved"],
        "recommended_guard": transition["recommended_guard"],
        "failures": transition["failures"],
    }


@dataclass(frozen=True)
class AffectCue:
    """Compact cue from memory or context that biases affect regulation."""

    cue_id: str
    valence_bias: float
    arousal_bias: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cue_id": self.cue_id,
            "valence_bias": round(self.valence_bias, 3),
            "arousal_bias": round(self.arousal_bias, 3),
        }


@dataclass(frozen=True)
class AffectRequest:
    """Single affect regulation request derived from qualia and memory cues."""

    tick_id: int
    summary: str
    valence: float
    arousal: float
    clarity: float
    self_awareness: float
    lucidity: float
    memory_cues: List[AffectCue] = field(default_factory=list)
    allow_artificial_dampening: bool = False

    def to_source_tick(self) -> Dict[str, Any]:
        return {
            "tick_id": self.tick_id,
            "summary": self.summary,
            "valence": round(self.valence, 3),
            "arousal": round(self.arousal, 3),
            "clarity": round(self.clarity, 3),
            "self_awareness": round(self.self_awareness, 3),
            "lucidity": round(self.lucidity, 3),
        }


class AffectBackend:
    """Base class for deterministic affect backends."""

    def __init__(self, backend_id: str, *, healthy: bool = True) -> None:
        self.backend_id = backend_id
        self._healthy = healthy

    def set_health(self, healthy: bool) -> None:
        self._healthy = healthy

    def regulate(self, request: AffectRequest) -> Dict[str, Any]:
        if not self._healthy:
            raise BackendUnavailableError(f"{self.backend_id} is unavailable")
        return self._regulate(request)

    def _regulate(self, request: AffectRequest) -> Dict[str, Any]:
        raise NotImplementedError


class HomeostaticAffectBackend(AffectBackend):
    """Primary backend that keeps raw qualia-affect close to observed state."""

    def _regulate(self, request: AffectRequest) -> Dict[str, Any]:
        valence_bias = sum(cue.valence_bias for cue in request.memory_cues) * 0.45
        arousal_bias = sum(cue.arousal_bias for cue in request.memory_cues) * 0.45
        target_valence = _clamp(request.valence + valence_bias, -1.0, 1.0)
        target_arousal = _clamp(
            request.arousal + arousal_bias + max(0.0, -request.valence) * 0.04,
            0.0,
            1.0,
        )
        return {
            "backend_id": self.backend_id,
            "target_valence": round(target_valence, 3),
            "target_arousal": round(target_arousal, 3),
            "dampening_applied": False,
            "rationale": [
                "maintain-homeostatic-continuity",
                "respect-memory-cue-bias",
            ],
        }


class StabilityGuardAffectBackend(AffectBackend):
    """Fallback backend that prioritizes continuity-safe stabilization."""

    def _regulate(self, request: AffectRequest) -> Dict[str, Any]:
        valence_bias = sum(cue.valence_bias for cue in request.memory_cues) * 0.35
        arousal_bias = sum(cue.arousal_bias for cue in request.memory_cues) * 0.35
        target_valence = request.valence + valence_bias
        target_arousal = request.arousal + arousal_bias
        dampening_applied = False
        rationale = [
            "bounded-stability-guard",
            "smooth-transition-before-neutralization",
        ]

        if request.allow_artificial_dampening and target_valence < 0.0 and target_arousal > 0.45:
            target_valence += 0.12
            target_arousal -= 0.14
            dampening_applied = True
            rationale.append("consented-neutralization")

        return {
            "backend_id": self.backend_id,
            "target_valence": round(_clamp(target_valence, -1.0, 1.0), 3),
            "target_arousal": round(_clamp(target_arousal, 0.0, 1.0), 3),
            "dampening_applied": dampening_applied,
            "rationale": rationale,
        }


class AffectService:
    """Profile-driven affect router with smooth failover semantics."""

    def __init__(
        self,
        profile: CognitiveProfile,
        backends: Sequence[AffectBackend],
    ) -> None:
        self.profile = profile
        self._backends = {backend.backend_id: backend for backend in backends}

    def profile_snapshot(self) -> Dict[str, Any]:
        return {
            "schema_version": AFFECT_SCHEMA_VERSION,
            "policy_id": AFFECT_POLICY_ID,
            "primary": self.profile.primary,
            "fallback": list(self.profile.fallback),
            "max_valence_delta": AFFECT_MAX_VALENCE_DELTA,
            "max_arousal_delta": AFFECT_MAX_AROUSAL_DELTA,
            "no_artificial_dampening_without_consent": True,
            "failover_mode": "single-switch",
        }

    def set_backend_health(self, backend_id: str, healthy: bool) -> None:
        self._backends[backend_id].set_health(healthy)

    def run(
        self,
        request: AffectRequest,
        *,
        previous_state: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        self._validate_request(request)
        if previous_state is not None and not self.validate_state(dict(previous_state))["ok"]:
            raise ValueError("previous_state must satisfy affect_state validation")

        attempted: List[str] = []
        failures: List[str] = []
        order = [self.profile.primary] + list(self.profile.fallback)

        for backend_id in order:
            attempted.append(backend_id)
            backend = self._backends[backend_id]
            try:
                regulated = backend.regulate(request)
            except BackendUnavailableError as exc:
                failures.append(str(exc))
                continue

            degraded = backend_id != self.profile.primary
            state = self._build_state(
                request,
                regulated,
                attempted_backends=attempted,
                failures=failures,
                degraded=degraded,
                previous_state=previous_state,
            )
            transition = self._build_transition(state, attempted, failures)
            return {
                "profile": self.profile_snapshot(),
                "attempted_backends": attempted,
                "selected_backend": backend_id,
                "degraded": degraded,
                "state": state,
                "transition": transition,
                "failures": failures,
            }

        raise BackendUnavailableError("all affect backends unavailable: " + ", ".join(attempted))

    def validate_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []

        if state.get("kind") != "affect_state":
            errors.append("kind must equal 'affect_state'")
        if state.get("schema_version") != AFFECT_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {AFFECT_SCHEMA_VERSION}")
        if not isinstance(state.get("state_id"), str) or not state["state_id"].startswith("affect-state-"):
            errors.append("state_id must start with 'affect-state-'")
        policy = state.get("policy")
        if policy != self.profile_snapshot():
            errors.append("policy must match profile_snapshot()")
        if not isinstance(state.get("generated_at"), str) or not state["generated_at"]:
            errors.append("generated_at must be a non-empty string")
        if not isinstance(state.get("backend_id"), str) or not state["backend_id"]:
            errors.append("backend_id must be a non-empty string")

        source_tick = state.get("source_tick")
        if not isinstance(source_tick, dict):
            errors.append("source_tick must be an object")
        else:
            self._require_int_at_least(source_tick.get("tick_id"), 0, "source_tick.tick_id", errors)
            self._require_non_empty_string(source_tick.get("summary"), "source_tick.summary", errors)
            self._require_range(source_tick.get("valence"), -1.0, 1.0, "source_tick.valence", errors)
            self._require_range(source_tick.get("arousal"), 0.0, 1.0, "source_tick.arousal", errors)
            self._require_range(source_tick.get("clarity"), 0.0, 1.0, "source_tick.clarity", errors)
            self._require_range(
                source_tick.get("self_awareness"),
                0.0,
                1.0,
                "source_tick.self_awareness",
                errors,
            )
            self._require_range(source_tick.get("lucidity"), 0.0, 1.0, "source_tick.lucidity", errors)

        memory_cues = state.get("memory_cues")
        if not isinstance(memory_cues, list) or not memory_cues:
            errors.append("memory_cues must be a non-empty list")
        else:
            for index, cue in enumerate(memory_cues):
                if not isinstance(cue, dict):
                    errors.append(f"memory_cues[{index}] must be an object")
                    continue
                self._require_non_empty_string(cue.get("cue_id"), f"memory_cues[{index}].cue_id", errors)
                self._require_range(
                    cue.get("valence_bias"),
                    -1.0,
                    1.0,
                    f"memory_cues[{index}].valence_bias",
                    errors,
                )
                self._require_range(
                    cue.get("arousal_bias"),
                    -1.0,
                    1.0,
                    f"memory_cues[{index}].arousal_bias",
                    errors,
                )

        self._require_range(state.get("valence"), -1.0, 1.0, "valence", errors)
        self._require_range(state.get("arousal"), 0.0, 1.0, "arousal", errors)
        self._require_non_empty_string(state.get("mood_label"), "mood_label", errors)
        self._require_range(state.get("stability"), 0.0, 1.0, "stability", errors)
        self._require_range(state.get("distress_score"), 0.0, 1.0, "distress_score", errors)
        if state.get("recommended_guard") not in AFFECT_ALLOWED_GUARDS:
            errors.append(
                "recommended_guard must be one of: "
                + ", ".join(sorted(AFFECT_ALLOWED_GUARDS))
            )
        if not isinstance(state.get("degraded"), bool):
            errors.append("degraded must be a boolean")

        continuity_guard = state.get("continuity_guard")
        if not isinstance(continuity_guard, dict):
            errors.append("continuity_guard must be an object")
        else:
            previous_state_id = continuity_guard.get("previous_state_id")
            if previous_state_id is not None and not isinstance(previous_state_id, str):
                errors.append("continuity_guard.previous_state_id must be a string or null")
            self._require_range(
                continuity_guard.get("target_before_smoothing", {}).get("valence"),
                -1.0,
                1.0,
                "continuity_guard.target_before_smoothing.valence",
                errors,
            )
            self._require_range(
                continuity_guard.get("target_before_smoothing", {}).get("arousal"),
                0.0,
                1.0,
                "continuity_guard.target_before_smoothing.arousal",
                errors,
            )
            self._require_range(
                continuity_guard.get("applied_delta", {}).get("valence"),
                -1.0,
                1.0,
                "continuity_guard.applied_delta.valence",
                errors,
            )
            self._require_range(
                continuity_guard.get("applied_delta", {}).get("arousal"),
                -1.0,
                1.0,
                "continuity_guard.applied_delta.arousal",
                errors,
            )
            max_allowed_delta = continuity_guard.get("max_allowed_delta")
            if max_allowed_delta != {
                "valence": round(AFFECT_MAX_VALENCE_DELTA, 3),
                "arousal": round(AFFECT_MAX_AROUSAL_DELTA, 3),
            }:
                errors.append("continuity_guard.max_allowed_delta mismatch")
            for field_name in ("smoothed", "dampening_applied", "consent_preserved"):
                if not isinstance(continuity_guard.get(field_name), bool):
                    errors.append(f"continuity_guard.{field_name} must be a boolean")

        digest = state.get("digest")
        if not isinstance(digest, str) or len(digest) != 64:
            errors.append("digest must be a sha256 hex string")
        elif digest != sha256_text(canonical_json(_state_digest_payload(state))):
            errors.append("digest mismatch")

        return {
            "ok": not errors,
            "selected_backend": state.get("backend_id"),
            "recommended_guard": state.get("recommended_guard"),
            "continuity_guard_preserved": bool(
                isinstance(continuity_guard, dict)
                and continuity_guard.get("consent_preserved") is True
            ),
            "errors": errors,
        }

    def validate_transition(self, transition: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []

        if transition.get("kind") != "affect_transition":
            errors.append("kind must equal 'affect_transition'")
        if transition.get("schema_version") != AFFECT_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {AFFECT_SCHEMA_VERSION}")
        if transition.get("policy_id") != AFFECT_POLICY_ID:
            errors.append(f"policy_id must equal {AFFECT_POLICY_ID}")
        if not isinstance(transition.get("transition_id"), str) or not transition["transition_id"].startswith(
            "affect-transition-"
        ):
            errors.append("transition_id must start with 'affect-transition-'")
        self._require_non_empty_string(transition.get("state_ref"), "state_ref", errors)
        self._require_non_empty_string(
            transition.get("selected_backend"),
            "selected_backend",
            errors,
        )
        attempted_backends = transition.get("attempted_backends")
        if not isinstance(attempted_backends, list) or not attempted_backends:
            errors.append("attempted_backends must be a non-empty list")
        else:
            for index, backend_id in enumerate(attempted_backends):
                self._require_non_empty_string(
                    backend_id,
                    f"attempted_backends[{index}]",
                    errors,
                )
        if not isinstance(transition.get("degraded"), bool):
            errors.append("degraded must be a boolean")
        previous_state_id = transition.get("previous_state_id")
        if previous_state_id is not None and not isinstance(previous_state_id, str):
            errors.append("previous_state_id must be a string or null")
        for field_name in ("smoothed", "dampening_applied", "consent_preserved"):
            if not isinstance(transition.get(field_name), bool):
                errors.append(f"{field_name} must be a boolean")
        if transition.get("recommended_guard") not in AFFECT_ALLOWED_GUARDS:
            errors.append(
                "recommended_guard must be one of: " + ", ".join(sorted(AFFECT_ALLOWED_GUARDS))
            )
        failures = transition.get("failures")
        if not isinstance(failures, list):
            errors.append("failures must be a list")
        else:
            for index, item in enumerate(failures):
                self._require_non_empty_string(item, f"failures[{index}]", errors)
        digest = transition.get("digest")
        if not isinstance(digest, str) or len(digest) != 64:
            errors.append("digest must be a sha256 hex string")
        elif digest != sha256_text(canonical_json(_transition_digest_payload(transition))):
            errors.append("digest mismatch")

        return {
            "ok": not errors,
            "selected_backend": transition.get("selected_backend"),
            "recommended_guard": transition.get("recommended_guard"),
            "errors": errors,
        }

    def _build_state(
        self,
        request: AffectRequest,
        regulated: Mapping[str, Any],
        *,
        attempted_backends: Sequence[str],
        failures: Sequence[str],
        degraded: bool,
        previous_state: Mapping[str, Any] | None,
    ) -> Dict[str, Any]:
        previous_valence = float(previous_state["valence"]) if previous_state else request.valence
        previous_arousal = float(previous_state["arousal"]) if previous_state else request.arousal
        target_valence = float(regulated["target_valence"])
        target_arousal = float(regulated["target_arousal"])
        delta_valence = target_valence - previous_valence
        delta_arousal = target_arousal - previous_arousal
        applied_delta_valence = _clamp(delta_valence, -AFFECT_MAX_VALENCE_DELTA, AFFECT_MAX_VALENCE_DELTA)
        applied_delta_arousal = _clamp(delta_arousal, -AFFECT_MAX_AROUSAL_DELTA, AFFECT_MAX_AROUSAL_DELTA)
        smoothed = (
            previous_state is not None
            and (
                round(applied_delta_valence, 3) != round(delta_valence, 3)
                or round(applied_delta_arousal, 3) != round(delta_arousal, 3)
            )
        )
        final_valence = target_valence if previous_state is None else previous_valence + applied_delta_valence
        final_arousal = target_arousal if previous_state is None else previous_arousal + applied_delta_arousal
        final_valence = round(_clamp(final_valence, -1.0, 1.0), 3)
        final_arousal = round(_clamp(final_arousal, 0.0, 1.0), 3)
        dampening_applied = bool(regulated["dampening_applied"])
        consent_preserved = not dampening_applied or request.allow_artificial_dampening
        stability = round(
            _clamp(
                0.38
                + (request.clarity * 0.22)
                + (request.self_awareness * 0.18)
                + (request.lucidity * 0.16)
                - (abs(applied_delta_valence) * 0.25)
                - (abs(applied_delta_arousal) * 0.16),
                0.0,
                1.0,
            ),
            3,
        )
        distress_score = round(
            _clamp(
                (max(0.0, -final_valence) * 0.55)
                + (final_arousal * 0.25)
                + ((1.0 - request.clarity) * 0.12)
                + ((1.0 - request.lucidity) * 0.08),
                0.0,
                1.0,
            ),
            3,
        )
        recommended_guard = "nominal"
        if distress_score >= 0.65 or (degraded and request.arousal >= 0.85):
            recommended_guard = "sandbox-notify"
        elif distress_score >= 0.3 or degraded:
            recommended_guard = "observe"

        state = {
            "kind": "affect_state",
            "schema_version": AFFECT_SCHEMA_VERSION,
            "policy": self.profile_snapshot(),
            "generated_at": utc_now_iso(),
            "backend_id": regulated["backend_id"],
            "source_tick": request.to_source_tick(),
            "memory_cues": [cue.to_dict() for cue in request.memory_cues],
            "valence": final_valence,
            "arousal": final_arousal,
            "mood_label": _quadrant_label(final_valence, final_arousal),
            "stability": stability,
            "distress_score": distress_score,
            "recommended_guard": recommended_guard,
            "degraded": degraded,
            "continuity_guard": {
                "previous_state_id": previous_state.get("state_id") if previous_state else None,
                "previous_backend_id": previous_state.get("backend_id") if previous_state else None,
                "attempted_backends": list(attempted_backends),
                "failures": list(failures),
                "target_before_smoothing": {
                    "valence": round(target_valence, 3),
                    "arousal": round(target_arousal, 3),
                },
                "applied_delta": {
                    "valence": round(final_valence - previous_valence, 3),
                    "arousal": round(final_arousal - previous_arousal, 3),
                },
                "max_allowed_delta": {
                    "valence": round(AFFECT_MAX_VALENCE_DELTA, 3),
                    "arousal": round(AFFECT_MAX_AROUSAL_DELTA, 3),
                },
                "smoothed": smoothed,
                "dampening_applied": dampening_applied,
                "consent_preserved": consent_preserved,
                "rationale": list(regulated["rationale"]),
            },
        }
        digest = sha256_text(canonical_json(_state_digest_payload(state)))
        state["state_id"] = f"affect-state-{digest[:12]}"
        state["digest"] = digest
        return state

    def _build_transition(
        self,
        state: Mapping[str, Any],
        attempted_backends: Sequence[str],
        failures: Sequence[str],
    ) -> Dict[str, Any]:
        transition = {
            "kind": "affect_transition",
            "schema_version": AFFECT_SCHEMA_VERSION,
            "policy_id": AFFECT_POLICY_ID,
            "state_ref": state["state_id"],
            "selected_backend": state["backend_id"],
            "attempted_backends": list(attempted_backends),
            "degraded": state["degraded"],
            "previous_state_id": state["continuity_guard"]["previous_state_id"],
            "smoothed": state["continuity_guard"]["smoothed"],
            "dampening_applied": state["continuity_guard"]["dampening_applied"],
            "consent_preserved": state["continuity_guard"]["consent_preserved"],
            "recommended_guard": state["recommended_guard"],
            "failures": list(failures),
        }
        digest = sha256_text(canonical_json(_transition_digest_payload(transition)))
        transition["transition_id"] = f"affect-transition-{digest[:12]}"
        transition["digest"] = digest
        return transition

    @staticmethod
    def _validate_request(request: AffectRequest) -> None:
        if request.tick_id < 0:
            raise ValueError("tick_id must be >= 0")
        if not request.summary.strip():
            raise ValueError("summary must not be empty")
        for field_name, value, minimum, maximum in (
            ("valence", request.valence, -1.0, 1.0),
            ("arousal", request.arousal, 0.0, 1.0),
            ("clarity", request.clarity, 0.0, 1.0),
            ("self_awareness", request.self_awareness, 0.0, 1.0),
            ("lucidity", request.lucidity, 0.0, 1.0),
        ):
            if not minimum <= value <= maximum:
                raise ValueError(f"{field_name} must be between {minimum} and {maximum}")
        if not request.memory_cues:
            raise ValueError("memory_cues must not be empty")
        for cue in request.memory_cues:
            if not cue.cue_id.strip():
                raise ValueError("cue_id must not be empty")
            if not -1.0 <= cue.valence_bias <= 1.0:
                raise ValueError("cue.valence_bias must be between -1.0 and 1.0")
            if not -1.0 <= cue.arousal_bias <= 1.0:
                raise ValueError("cue.arousal_bias must be between -1.0 and 1.0")

    @staticmethod
    def _require_non_empty_string(value: Any, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty string")

    @staticmethod
    def _require_range(
        value: Any,
        minimum: float,
        maximum: float,
        field_name: str,
        errors: List[str],
    ) -> None:
        if not isinstance(value, (int, float)) or not minimum <= float(value) <= maximum:
            errors.append(f"{field_name} must be between {minimum} and {maximum}")

    @staticmethod
    def _require_int_at_least(value: Any, minimum: int, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, int) or value < minimum:
            errors.append(f"{field_name} must be >= {minimum}")
