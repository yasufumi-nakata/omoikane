"""Minimal L3 volition backends with deterministic failover and guard-aware intent arbitration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from .reasoning import BackendUnavailableError, CognitiveProfile

VOLITION_SCHEMA_VERSION = "1.0.0"
VOLITION_POLICY_ID = "bounded-volition-failover-v1"
VOLITION_ALLOWED_GUARDS = {"nominal", "observe", "sandbox-notify"}
VOLITION_ALLOWED_REVERSIBILITY = {"reversible", "reviewable", "irreversible"}
VOLITION_ALLOWED_EXECUTION_MODES = {"advance", "review", "hold"}
VOLITION_SAFE_INTENTS = ("guardian-review", "continuity-hold", "sandbox-stabilization")


def _volition_digest_payload(intent: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": intent["schema_version"],
        "policy": intent["policy"],
        "backend_id": intent["backend_id"],
        "source_tick": intent["source_tick"],
        "memory_cues": intent["memory_cues"],
        "candidates": intent["candidates"],
        "candidate_scores": intent["candidate_scores"],
        "selected_intent": intent["selected_intent"],
        "execution_mode": intent["execution_mode"],
        "degraded": intent["degraded"],
        "continuity_guard": intent["continuity_guard"],
    }


def _shift_digest_payload(shift: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": shift["schema_version"],
        "policy_id": shift["policy_id"],
        "intent_ref": shift["intent_ref"],
        "selected_backend": shift["selected_backend"],
        "attempted_backends": shift["attempted_backends"],
        "degraded": shift["degraded"],
        "previous_intent_id": shift["previous_intent_id"],
        "previous_target": shift["previous_target"],
        "selected_intent": shift["selected_intent"],
        "execution_mode": shift["execution_mode"],
        "affect_guard": shift["affect_guard"],
        "guard_aligned": shift["guard_aligned"],
        "failures": shift["failures"],
    }


@dataclass(frozen=True)
class VolitionCue:
    """Compact cue that biases arbitration toward one bounded intent."""

    cue_id: str
    preferred_intent: str
    weight: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cue_id": self.cue_id,
            "preferred_intent": self.preferred_intent,
            "weight": round(self.weight, 3),
        }


@dataclass(frozen=True)
class VolitionCandidate:
    """One bounded candidate intent eligible for arbitration."""

    intent_id: str
    objective: str
    urgency: float
    risk: float
    reversibility: str
    alignment_tags: List[str] = field(default_factory=list)
    requires_guardian_review: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "objective": self.objective,
            "urgency": round(self.urgency, 3),
            "risk": round(self.risk, 3),
            "reversibility": self.reversibility,
            "alignment_tags": list(self.alignment_tags),
            "requires_guardian_review": self.requires_guardian_review,
        }


@dataclass(frozen=True)
class VolitionRequest:
    """Single volition arbitration request derived from attention and affect context."""

    tick_id: int
    summary: str
    values: Dict[str, float]
    attention_focus: str
    affect_guard: str
    continuity_pressure: float
    candidates: List[VolitionCandidate]
    memory_cues: List[VolitionCue] = field(default_factory=list)
    reversible_only: bool = False

    def to_source_tick(self) -> Dict[str, Any]:
        return {
            "tick_id": self.tick_id,
            "summary": self.summary,
            "values": {key: round(value, 3) for key, value in sorted(self.values.items())},
            "attention_focus": self.attention_focus,
            "affect_guard": self.affect_guard,
            "continuity_pressure": round(self.continuity_pressure, 3),
            "reversible_only": self.reversible_only,
        }


def _candidate_scores(request: VolitionRequest) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    value_weights = request.values
    cue_weights = {cue.preferred_intent: cue.weight for cue in request.memory_cues}

    for candidate in request.candidates:
        value_score = sum(value_weights.get(tag, 0.0) for tag in candidate.alignment_tags)
        attention_boost = 0.16 if candidate.intent_id == request.attention_focus else 0.0
        cue_boost = cue_weights.get(candidate.intent_id, 0.0)
        continuity_boost = request.continuity_pressure * 0.18 if candidate.intent_id == "continuity-hold" else 0.0
        guard_boost = 0.0
        if request.affect_guard == "observe" and candidate.intent_id == "guardian-review":
            guard_boost = 0.24
        elif request.affect_guard == "sandbox-notify" and candidate.intent_id == "sandbox-stabilization":
            guard_boost = 0.3

        reversibility_bonus = {
            "reversible": 0.12,
            "reviewable": 0.04,
            "irreversible": -0.18,
        }[candidate.reversibility]
        review_penalty = 0.06 if candidate.requires_guardian_review and request.affect_guard == "nominal" else 0.0
        reversible_only_penalty = 0.55 if request.reversible_only and candidate.reversibility == "irreversible" else 0.0

        score = (
            (candidate.urgency * 0.22)
            + (value_score * 0.36)
            + attention_boost
            + cue_boost
            + continuity_boost
            + guard_boost
            + reversibility_bonus
            - (candidate.risk * 0.24)
            - review_penalty
            - reversible_only_penalty
        )
        scores[candidate.intent_id] = round(score, 3)

    return {intent_id: score for intent_id, score in scores.items() if score > -1.0}


def _best_candidate(request: VolitionRequest, candidate_scores: Mapping[str, float]) -> VolitionCandidate:
    candidate_map = {candidate.intent_id: candidate for candidate in request.candidates}
    best_id = max(candidate_scores.items(), key=lambda item: (item[1], item[0]))[0]
    return candidate_map[best_id]


class VolitionBackend:
    """Base class for deterministic volition backends."""

    def __init__(self, backend_id: str, *, healthy: bool = True) -> None:
        self.backend_id = backend_id
        self._healthy = healthy

    def set_health(self, healthy: bool) -> None:
        self._healthy = healthy

    def arbitrate(
        self,
        request: VolitionRequest,
        *,
        previous_intent: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if not self._healthy:
            raise BackendUnavailableError(f"{self.backend_id} is unavailable")
        return self._arbitrate(request, previous_intent=previous_intent)

    def _arbitrate(
        self,
        request: VolitionRequest,
        *,
        previous_intent: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError


class UtilityPolicyVolitionBackend(VolitionBackend):
    """Primary backend that scores candidates against explicit values and focus cues."""

    def _arbitrate(
        self,
        request: VolitionRequest,
        *,
        previous_intent: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        candidate_scores = _candidate_scores(request)
        selected = _best_candidate(request, candidate_scores)
        execution_mode = "advance"
        rationale = ["rank-value-aligned-intents", "respect-attention-focus"]

        if request.affect_guard == "observe":
            execution_mode = "review"
            rationale.append("elevate-review-under-observe-guard")
        if request.affect_guard == "sandbox-notify":
            execution_mode = "hold"
            rationale.append("hold-under-sandbox-notify-guard")
        elif selected.requires_guardian_review or selected.reversibility == "reviewable":
            execution_mode = "review"
            rationale.append("candidate-requires-review")
        elif selected.intent_id == "continuity-hold":
            execution_mode = "hold"
            rationale.append("continuity-pressure-hold")

        return {
            "backend_id": self.backend_id,
            "selected_intent": selected.intent_id,
            "candidate_scores": candidate_scores,
            "execution_mode": execution_mode,
            "guard_aligned": request.affect_guard == "nominal"
            or selected.intent_id in VOLITION_SAFE_INTENTS,
            "rationale": rationale,
        }


class GuardianBiasVolitionBackend(VolitionBackend):
    """Fallback backend that routes volition toward fixed safe intents."""

    def _arbitrate(
        self,
        request: VolitionRequest,
        *,
        previous_intent: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        candidate_scores = _candidate_scores(request)
        candidate_map = {candidate.intent_id: candidate for candidate in request.candidates}
        rationale = ["preserve-guard-aligned-intent", "bounded-fallback-arbitration"]

        if request.affect_guard == "sandbox-notify" and "sandbox-stabilization" in candidate_map:
            selected_intent = "sandbox-stabilization"
            execution_mode = "hold"
            rationale.append("sandbox-stabilization-required")
        elif request.affect_guard == "observe" and "guardian-review" in candidate_map:
            selected_intent = "guardian-review"
            execution_mode = "review"
            rationale.append("guardian-review-required")
        elif previous_intent is not None and previous_intent.get("selected_intent") == "continuity-hold":
            selected_intent = "continuity-hold"
            execution_mode = "hold"
            rationale.append("preserve-previous-safe-intent")
        else:
            selected_intent = "continuity-hold"
            execution_mode = "hold"
            rationale.append("default-continuity-hold")

        return {
            "backend_id": self.backend_id,
            "selected_intent": selected_intent,
            "candidate_scores": candidate_scores,
            "execution_mode": execution_mode,
            "guard_aligned": True,
            "rationale": rationale,
        }


class VolitionService:
    """Profile-driven volition router with guard-aware failover semantics."""

    def __init__(
        self,
        profile: CognitiveProfile,
        backends: Sequence[VolitionBackend],
    ) -> None:
        self.profile = profile
        self._backends = {backend.backend_id: backend for backend in backends}

    @staticmethod
    def _validate_range(name: str, value: float, minimum: float, maximum: float) -> None:
        if not minimum <= value <= maximum:
            raise ValueError(f"{name} must be between {minimum} and {maximum}")

    def profile_snapshot(self) -> Dict[str, Any]:
        return {
            "schema_version": VOLITION_SCHEMA_VERSION,
            "policy_id": VOLITION_POLICY_ID,
            "primary": self.profile.primary,
            "fallback": list(self.profile.fallback),
            "safe_intents": list(VOLITION_SAFE_INTENTS),
            "respect_affect_guard": True,
            "allow_irreversible_without_review": False,
            "failover_mode": "single-switch",
        }

    def set_backend_health(self, backend_id: str, healthy: bool) -> None:
        self._backends[backend_id].set_health(healthy)

    def run(
        self,
        request: VolitionRequest,
        *,
        previous_intent: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        self._validate_request(request)
        if previous_intent is not None and not self.validate_intent(dict(previous_intent))["ok"]:
            raise ValueError("previous_intent must satisfy volition_intent validation")

        attempted: List[str] = []
        failures: List[str] = []
        order = [self.profile.primary] + list(self.profile.fallback)

        for backend_id in order:
            attempted.append(backend_id)
            backend = self._backends[backend_id]
            try:
                arbitrated = backend.arbitrate(request, previous_intent=previous_intent)
            except BackendUnavailableError as exc:
                failures.append(str(exc))
                continue

            degraded = backend_id != self.profile.primary
            intent = self._build_intent(
                request,
                arbitrated,
                attempted_backends=attempted,
                failures=failures,
                degraded=degraded,
                previous_intent=previous_intent,
            )
            shift = self._build_shift(intent, attempted, failures)
            return {
                "profile": self.profile_snapshot(),
                "attempted_backends": attempted,
                "selected_backend": backend_id,
                "degraded": degraded,
                "intent": intent,
                "shift": shift,
                "failures": failures,
            }

        raise BackendUnavailableError("all volition backends unavailable: " + ", ".join(attempted))

    def validate_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []

        if intent.get("kind") != "volition_intent":
            errors.append("kind must equal 'volition_intent'")
        if intent.get("schema_version") != VOLITION_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {VOLITION_SCHEMA_VERSION}")
        if intent.get("policy") != self.profile_snapshot():
            errors.append("policy must equal volition profile snapshot")
        if intent.get("backend_id") not in self._backends:
            errors.append("backend_id must reference a registered backend")
        if intent.get("execution_mode") not in VOLITION_ALLOWED_EXECUTION_MODES:
            errors.append(f"execution_mode must be one of {sorted(VOLITION_ALLOWED_EXECUTION_MODES)!r}")

        selected_intent = intent.get("selected_intent")
        if not isinstance(selected_intent, str) or not selected_intent.strip():
            errors.append("selected_intent must be a non-empty string")

        candidate_scores = intent.get("candidate_scores")
        if not isinstance(candidate_scores, dict) or not candidate_scores:
            errors.append("candidate_scores must be a non-empty mapping")

        source_tick = intent.get("source_tick")
        if not isinstance(source_tick, dict):
            errors.append("source_tick must be present")
            affect_guard = None
        else:
            affect_guard = source_tick.get("affect_guard")
            if affect_guard not in VOLITION_ALLOWED_GUARDS:
                errors.append(f"affect_guard must be one of {sorted(VOLITION_ALLOWED_GUARDS)!r}")

        guard_aligned = True
        if affect_guard in {"observe", "sandbox-notify"}:
            guard_aligned = selected_intent in VOLITION_SAFE_INTENTS
            if not guard_aligned:
                errors.append("selected_intent must move to a safe intent when affect_guard escalates")

        continuity_guard = intent.get("continuity_guard")
        if not isinstance(continuity_guard, dict):
            errors.append("continuity_guard must be present")
        else:
            attempted_backends = continuity_guard.get("attempted_backends")
            if not isinstance(attempted_backends, list) or not attempted_backends:
                errors.append("continuity_guard.attempted_backends must be non-empty")
            if continuity_guard.get("guard_aligned") != guard_aligned:
                errors.append("continuity_guard.guard_aligned must reflect validation result")

        digest = intent.get("digest")
        expected_digest = sha256_text(canonical_json(_volition_digest_payload(intent))) if not errors else None
        if expected_digest is not None and digest != expected_digest:
            errors.append("digest mismatch")

        return {
            "ok": not errors,
            "selected_backend": intent.get("backend_id"),
            "selected_intent": selected_intent,
            "guard_aligned": guard_aligned,
            "errors": errors,
        }

    def validate_shift(self, shift: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []

        if shift.get("kind") != "volition_shift":
            errors.append("kind must equal 'volition_shift'")
        if shift.get("schema_version") != VOLITION_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {VOLITION_SCHEMA_VERSION}")
        if shift.get("policy_id") != VOLITION_POLICY_ID:
            errors.append(f"policy_id must equal {VOLITION_POLICY_ID}")
        if shift.get("selected_backend") not in self._backends:
            errors.append("selected_backend must reference a registered backend")
        if shift.get("execution_mode") not in VOLITION_ALLOWED_EXECUTION_MODES:
            errors.append(f"execution_mode must be one of {sorted(VOLITION_ALLOWED_EXECUTION_MODES)!r}")
        if shift.get("affect_guard") not in VOLITION_ALLOWED_GUARDS:
            errors.append(f"affect_guard must be one of {sorted(VOLITION_ALLOWED_GUARDS)!r}")

        selected_intent = shift.get("selected_intent")
        if not isinstance(selected_intent, str) or not selected_intent.strip():
            errors.append("selected_intent must be a non-empty string")

        guard_aligned = True
        if shift.get("affect_guard") in {"observe", "sandbox-notify"}:
            guard_aligned = selected_intent in VOLITION_SAFE_INTENTS
            if not guard_aligned:
                errors.append("selected_intent must move to a safe intent when affect_guard escalates")
        if shift.get("guard_aligned") != guard_aligned:
            errors.append("guard_aligned must match the selected intent and affect guard")

        digest = shift.get("digest")
        expected_digest = sha256_text(canonical_json(_shift_digest_payload(shift))) if not errors else None
        if expected_digest is not None and digest != expected_digest:
            errors.append("digest mismatch")

        return {
            "ok": not errors,
            "selected_backend": shift.get("selected_backend"),
            "selected_intent": selected_intent,
            "guard_aligned": guard_aligned,
            "errors": errors,
        }

    def _validate_request(self, request: VolitionRequest) -> None:
        if request.tick_id < 0:
            raise ValueError("tick_id must be >= 0")
        if not request.summary.strip():
            raise ValueError("summary must not be empty")
        if not request.attention_focus.strip():
            raise ValueError("attention_focus must not be empty")
        if request.affect_guard not in VOLITION_ALLOWED_GUARDS:
            raise ValueError(f"affect_guard must be one of {sorted(VOLITION_ALLOWED_GUARDS)!r}")

        self._validate_range("continuity_pressure", request.continuity_pressure, 0.0, 1.0)
        if not request.candidates:
            raise ValueError("candidates must not be empty")

        for value_name, value_weight in request.values.items():
            if not value_name.strip():
                raise ValueError("value names must not be empty")
            self._validate_range(f"values.{value_name}", value_weight, 0.0, 1.0)

        for cue in request.memory_cues:
            if not cue.cue_id.strip():
                raise ValueError("cue_id must not be empty")
            if not cue.preferred_intent.strip():
                raise ValueError("preferred_intent must not be empty")
            self._validate_range("cue.weight", cue.weight, 0.0, 1.0)

        for candidate in request.candidates:
            if not candidate.intent_id.strip():
                raise ValueError("intent_id must not be empty")
            if not candidate.objective.strip():
                raise ValueError("objective must not be empty")
            self._validate_range(f"{candidate.intent_id}.urgency", candidate.urgency, 0.0, 1.0)
            self._validate_range(f"{candidate.intent_id}.risk", candidate.risk, 0.0, 1.0)
            if candidate.reversibility not in VOLITION_ALLOWED_REVERSIBILITY:
                raise ValueError(
                    f"reversibility must be one of {sorted(VOLITION_ALLOWED_REVERSIBILITY)!r}"
                )

    def _build_intent(
        self,
        request: VolitionRequest,
        arbitrated: Mapping[str, Any],
        *,
        attempted_backends: Sequence[str],
        failures: Sequence[str],
        degraded: bool,
        previous_intent: Mapping[str, Any] | None,
    ) -> Dict[str, Any]:
        previous_target = previous_intent.get("selected_intent") if previous_intent else None
        intent = {
            "kind": "volition_intent",
            "schema_version": VOLITION_SCHEMA_VERSION,
            "policy": self.profile_snapshot(),
            "intent_id": new_id("volition-intent"),
            "generated_at": utc_now_iso(),
            "backend_id": arbitrated["backend_id"],
            "source_tick": request.to_source_tick(),
            "memory_cues": [cue.to_dict() for cue in request.memory_cues],
            "candidates": [candidate.to_dict() for candidate in request.candidates],
            "candidate_scores": dict(sorted(arbitrated["candidate_scores"].items())),
            "selected_intent": arbitrated["selected_intent"],
            "execution_mode": arbitrated["execution_mode"],
            "degraded": degraded,
            "continuity_guard": {
                "previous_intent_id": previous_intent.get("intent_id") if previous_intent else None,
                "previous_backend_id": previous_intent.get("backend_id") if previous_intent else None,
                "previous_target": previous_target,
                "attempted_backends": list(attempted_backends),
                "failures": list(failures),
                "guard_aligned": arbitrated["guard_aligned"],
                "preserved_target": arbitrated["selected_intent"] == previous_target,
                "selected_safe_intent": arbitrated["selected_intent"] in VOLITION_SAFE_INTENTS,
                "rationale": list(arbitrated["rationale"]),
            },
        }
        intent["digest"] = sha256_text(canonical_json(_volition_digest_payload(intent)))
        return intent

    def _build_shift(
        self,
        intent: Mapping[str, Any],
        attempted_backends: Sequence[str],
        failures: Sequence[str],
    ) -> Dict[str, Any]:
        continuity_guard = intent["continuity_guard"]
        shift = {
            "kind": "volition_shift",
            "schema_version": VOLITION_SCHEMA_VERSION,
            "policy_id": VOLITION_POLICY_ID,
            "intent_ref": intent["intent_id"],
            "selected_backend": intent["backend_id"],
            "attempted_backends": list(attempted_backends),
            "degraded": intent["degraded"],
            "previous_intent_id": continuity_guard["previous_intent_id"],
            "previous_target": continuity_guard["previous_target"],
            "selected_intent": intent["selected_intent"],
            "execution_mode": intent["execution_mode"],
            "affect_guard": intent["source_tick"]["affect_guard"],
            "guard_aligned": continuity_guard["guard_aligned"],
            "failures": list(failures),
        }
        shift["digest"] = sha256_text(canonical_json(_shift_digest_payload(shift)))
        return shift
