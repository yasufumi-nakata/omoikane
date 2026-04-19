"""Minimal L3 attention backends with deterministic failover and affect-aware routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from .reasoning import BackendUnavailableError, CognitiveProfile

ATTENTION_SCHEMA_VERSION = "1.0.0"
ATTENTION_POLICY_ID = "hybrid-attention-failover-v1"
ATTENTION_ALLOWED_GUARDS = {"nominal", "observe", "sandbox-notify"}
ATTENTION_MODALITIES = ("visual", "auditory", "somatic", "interoceptive")
SAFE_FOCUS_TARGETS = ("guardian-review", "continuity-ledger", "sandbox-stabilization")
DEFAULT_DWELL_MS = 600
DEGRADED_DWELL_MS = 450


def _candidate_scores(request: "AttentionRequest") -> Dict[str, float]:
    modality_salience = request.modality_salience
    scores: Dict[str, float] = {
        request.attention_target: 0.44 + (request.self_awareness * 0.22) + (request.lucidity * 0.12),
        "visual-scan": modality_salience["visual"] * 0.64,
        "auditory-check": modality_salience["auditory"] * 0.58,
        "somatic-scan": modality_salience["somatic"] * 0.68,
        "interoceptive-scan": modality_salience["interoceptive"] * 0.68,
        "continuity-ledger": 0.24 + ((request.self_awareness + request.lucidity) * 0.12),
        "guardian-review": 0.28 if request.affect_guard == "observe" else 0.0,
        "sandbox-stabilization": 0.62 if request.affect_guard == "sandbox-notify" else 0.0,
    }
    for cue in request.memory_cues:
        scores[cue.target] = scores.get(cue.target, 0.0) + cue.weight
    return {target: round(score, 3) for target, score in scores.items() if score > 0.0}


def _best_target(candidate_scores: Mapping[str, float]) -> str:
    return max(candidate_scores.items(), key=lambda item: (item[1], item[0]))[0]


def _attention_digest_payload(state: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": state["schema_version"],
        "policy": state["policy"],
        "backend_id": state["backend_id"],
        "source_tick": state["source_tick"],
        "affect_guard": state["affect_guard"],
        "memory_cues": state["memory_cues"],
        "focus_target": state["focus_target"],
        "candidate_scores": state["candidate_scores"],
        "dwell_ms": state["dwell_ms"],
        "degraded": state["degraded"],
        "continuity_guard": state["continuity_guard"],
    }


def _shift_digest_payload(shift: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": shift["schema_version"],
        "policy_id": shift["policy_id"],
        "focus_ref": shift["focus_ref"],
        "selected_backend": shift["selected_backend"],
        "attempted_backends": shift["attempted_backends"],
        "degraded": shift["degraded"],
        "previous_focus_id": shift["previous_focus_id"],
        "previous_target": shift["previous_target"],
        "focus_target": shift["focus_target"],
        "affect_guard": shift["affect_guard"],
        "dwell_ms": shift["dwell_ms"],
        "preserved_target": shift["preserved_target"],
        "failures": shift["failures"],
    }


@dataclass(frozen=True)
class AttentionCue:
    """Compact memory cue that can bias focus routing toward one target."""

    cue_id: str
    target: str
    weight: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cue_id": self.cue_id,
            "target": self.target,
            "weight": round(self.weight, 3),
        }


@dataclass(frozen=True)
class AttentionRequest:
    """Single attention routing request derived from qualia and affect guardrails."""

    tick_id: int
    summary: str
    attention_target: str
    modality_salience: Dict[str, float]
    self_awareness: float
    lucidity: float
    affect_guard: str
    memory_cues: List[AttentionCue] = field(default_factory=list)

    def to_source_tick(self) -> Dict[str, Any]:
        return {
            "tick_id": self.tick_id,
            "summary": self.summary,
            "attention_target": self.attention_target,
            "modality_salience": {key: round(value, 3) for key, value in self.modality_salience.items()},
            "self_awareness": round(self.self_awareness, 3),
            "lucidity": round(self.lucidity, 3),
        }


class AttentionBackend:
    """Base class for deterministic attention backends."""

    def __init__(self, backend_id: str, *, healthy: bool = True) -> None:
        self.backend_id = backend_id
        self._healthy = healthy

    def set_health(self, healthy: bool) -> None:
        self._healthy = healthy

    def route(
        self,
        request: AttentionRequest,
        *,
        previous_focus: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if not self._healthy:
            raise BackendUnavailableError(f"{self.backend_id} is unavailable")
        return self._route(request, previous_focus=previous_focus)

    def _route(
        self,
        request: AttentionRequest,
        *,
        previous_focus: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError


class SalienceRoutingAttentionBackend(AttentionBackend):
    """Primary backend that routes to the strongest salience-backed target."""

    def _route(
        self,
        request: AttentionRequest,
        *,
        previous_focus: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        candidate_scores = _candidate_scores(request)
        focus_target = _best_target(candidate_scores)
        rationale = ["rank-modality-and-memory-salience"]

        if request.affect_guard == "sandbox-notify":
            focus_target = "sandbox-stabilization"
            rationale.append("respect-sandbox-notify-guard")
        elif request.affect_guard == "observe" and candidate_scores.get("guardian-review", 0.0) >= (
            candidate_scores[focus_target] - 0.08
        ):
            focus_target = "guardian-review"
            rationale.append("respect-observe-guard")

        dwell_ms = DEFAULT_DWELL_MS if focus_target == request.attention_target else 520
        return {
            "backend_id": self.backend_id,
            "focus_target": focus_target,
            "candidate_scores": candidate_scores,
            "dwell_ms": dwell_ms,
            "rationale": rationale,
        }


class ContinuityAnchorAttentionBackend(AttentionBackend):
    """Fallback backend that anchors focus to continuity-safe review targets."""

    def _route(
        self,
        request: AttentionRequest,
        *,
        previous_focus: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        candidate_scores = _candidate_scores(request)
        rationale = ["preserve-continuity-safe-focus"]

        if request.affect_guard == "sandbox-notify":
            focus_target = "sandbox-stabilization"
            rationale.append("failover-sandbox-stabilization")
        elif request.affect_guard == "observe":
            focus_target = "guardian-review"
            rationale.append("failover-guardian-review")
        elif previous_focus is not None and previous_focus.get("focus_target") == request.attention_target:
            focus_target = request.attention_target
            rationale.append("preserve-requested-target")
        else:
            focus_target = "continuity-ledger"
            rationale.append("anchor-to-ledger")

        return {
            "backend_id": self.backend_id,
            "focus_target": focus_target,
            "candidate_scores": candidate_scores,
            "dwell_ms": 360 if request.affect_guard == "sandbox-notify" else DEGRADED_DWELL_MS,
            "rationale": rationale,
        }


class AttentionService:
    """Profile-driven attention router with affect-aware failover semantics."""

    def __init__(
        self,
        profile: CognitiveProfile,
        backends: Sequence[AttentionBackend],
    ) -> None:
        self.profile = profile
        self._backends = {backend.backend_id: backend for backend in backends}

    @staticmethod
    def _validate_range(name: str, value: float, minimum: float, maximum: float) -> None:
        if not minimum <= value <= maximum:
            raise ValueError(f"{name} must be between {minimum} and {maximum}")

    def profile_snapshot(self) -> Dict[str, Any]:
        return {
            "schema_version": ATTENTION_SCHEMA_VERSION,
            "policy_id": ATTENTION_POLICY_ID,
            "primary": self.profile.primary,
            "fallback": list(self.profile.fallback),
            "safe_targets": list(SAFE_FOCUS_TARGETS),
            "respect_affect_guard": True,
            "default_dwell_ms": DEFAULT_DWELL_MS,
            "degraded_dwell_ms": DEGRADED_DWELL_MS,
            "failover_mode": "single-switch",
        }

    def set_backend_health(self, backend_id: str, healthy: bool) -> None:
        self._backends[backend_id].set_health(healthy)

    def run(
        self,
        request: AttentionRequest,
        *,
        previous_focus: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        self._validate_request(request)
        if previous_focus is not None and not self.validate_focus(dict(previous_focus))["ok"]:
            raise ValueError("previous_focus must satisfy attention_focus validation")

        attempted: List[str] = []
        failures: List[str] = []
        order = [self.profile.primary] + list(self.profile.fallback)

        for backend_id in order:
            attempted.append(backend_id)
            backend = self._backends[backend_id]
            try:
                routed = backend.route(request, previous_focus=previous_focus)
            except BackendUnavailableError as exc:
                failures.append(str(exc))
                continue

            degraded = backend_id != self.profile.primary
            focus = self._build_focus(
                request,
                routed,
                attempted_backends=attempted,
                failures=failures,
                degraded=degraded,
                previous_focus=previous_focus,
            )
            shift = self._build_shift(focus, attempted, failures)
            return {
                "profile": self.profile_snapshot(),
                "attempted_backends": attempted,
                "selected_backend": backend_id,
                "degraded": degraded,
                "focus": focus,
                "shift": shift,
                "failures": failures,
            }

        raise BackendUnavailableError("all attention backends unavailable: " + ", ".join(attempted))

    def validate_focus(self, focus: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []

        if focus.get("kind") != "attention_focus":
            errors.append("kind must equal 'attention_focus'")
        if focus.get("schema_version") != ATTENTION_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {ATTENTION_SCHEMA_VERSION}")
        if focus.get("policy") != self.profile_snapshot():
            errors.append("policy must equal attention profile snapshot")
        if focus.get("backend_id") not in self._backends:
            errors.append("backend_id must reference a registered backend")
        if focus.get("affect_guard") not in ATTENTION_ALLOWED_GUARDS:
            errors.append(f"affect_guard must be one of {sorted(ATTENTION_ALLOWED_GUARDS)!r}")
        if not isinstance(focus.get("candidate_scores"), dict) or not focus["candidate_scores"]:
            errors.append("candidate_scores must be a non-empty mapping")
        if not isinstance(focus.get("dwell_ms"), int) or focus["dwell_ms"] <= 0:
            errors.append("dwell_ms must be a positive integer")

        focus_target = focus.get("focus_target")
        if not isinstance(focus_target, str) or not focus_target.strip():
            errors.append("focus_target must be a non-empty string")

        guard_aligned = True
        if focus.get("affect_guard") in {"observe", "sandbox-notify"}:
            guard_aligned = focus_target in SAFE_FOCUS_TARGETS
            if not guard_aligned:
                errors.append("focus_target must move to a safe target when affect_guard escalates")

        continuity_guard = focus.get("continuity_guard")
        if not isinstance(continuity_guard, dict):
            errors.append("continuity_guard must be present")
        else:
            attempted_backends = continuity_guard.get("attempted_backends")
            if not isinstance(attempted_backends, list) or not attempted_backends:
                errors.append("continuity_guard.attempted_backends must be non-empty")

        digest = focus.get("digest")
        expected_digest = sha256_text(canonical_json(_attention_digest_payload(focus))) if not errors else None
        if expected_digest is not None and digest != expected_digest:
            errors.append("digest mismatch")

        return {
            "ok": not errors,
            "selected_backend": focus.get("backend_id"),
            "focus_target": focus_target,
            "guard_aligned": guard_aligned,
            "errors": errors,
        }

    def validate_shift(self, shift: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []

        if shift.get("kind") != "attention_shift":
            errors.append("kind must equal 'attention_shift'")
        if shift.get("schema_version") != ATTENTION_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {ATTENTION_SCHEMA_VERSION}")
        if shift.get("policy_id") != ATTENTION_POLICY_ID:
            errors.append(f"policy_id must equal {ATTENTION_POLICY_ID}")
        if shift.get("selected_backend") not in self._backends:
            errors.append("selected_backend must reference a registered backend")
        if shift.get("affect_guard") not in ATTENTION_ALLOWED_GUARDS:
            errors.append(f"affect_guard must be one of {sorted(ATTENTION_ALLOWED_GUARDS)!r}")

        focus_target = shift.get("focus_target")
        if not isinstance(focus_target, str) or not focus_target.strip():
            errors.append("focus_target must be a non-empty string")

        guard_aligned = True
        if shift.get("affect_guard") in {"observe", "sandbox-notify"}:
            guard_aligned = focus_target in SAFE_FOCUS_TARGETS
            if not guard_aligned:
                errors.append("focus_target must move to a safe target when affect_guard escalates")

        digest = shift.get("digest")
        expected_digest = sha256_text(canonical_json(_shift_digest_payload(shift))) if not errors else None
        if expected_digest is not None and digest != expected_digest:
            errors.append("digest mismatch")

        return {
            "ok": not errors,
            "selected_backend": shift.get("selected_backend"),
            "focus_target": focus_target,
            "guard_aligned": guard_aligned,
            "errors": errors,
        }

    def _validate_request(self, request: AttentionRequest) -> None:
        if request.tick_id < 0:
            raise ValueError("tick_id must be >= 0")
        if not request.summary.strip():
            raise ValueError("summary must not be empty")
        if not request.attention_target.strip():
            raise ValueError("attention_target must not be empty")
        if request.affect_guard not in ATTENTION_ALLOWED_GUARDS:
            raise ValueError(f"affect_guard must be one of {sorted(ATTENTION_ALLOWED_GUARDS)!r}")

        unexpected = sorted(set(request.modality_salience) - set(ATTENTION_MODALITIES))
        if unexpected:
            raise ValueError(f"unsupported modality keys: {', '.join(unexpected)}")

        for modality in ATTENTION_MODALITIES:
            self._validate_range(modality, float(request.modality_salience.get(modality, 0.0)), 0.0, 1.0)

        self._validate_range("self_awareness", request.self_awareness, 0.0, 1.0)
        self._validate_range("lucidity", request.lucidity, 0.0, 1.0)
        for cue in request.memory_cues:
            if not cue.cue_id.strip():
                raise ValueError("cue_id must not be empty")
            if not cue.target.strip():
                raise ValueError("cue.target must not be empty")
            self._validate_range("cue.weight", cue.weight, 0.0, 1.0)

    def _build_focus(
        self,
        request: AttentionRequest,
        routed: Mapping[str, Any],
        *,
        attempted_backends: Sequence[str],
        failures: Sequence[str],
        degraded: bool,
        previous_focus: Mapping[str, Any] | None,
    ) -> Dict[str, Any]:
        previous_target = previous_focus.get("focus_target") if previous_focus else None
        focus = {
            "kind": "attention_focus",
            "schema_version": ATTENTION_SCHEMA_VERSION,
            "policy": self.profile_snapshot(),
            "focus_id": new_id("attention-focus"),
            "generated_at": utc_now_iso(),
            "backend_id": routed["backend_id"],
            "source_tick": request.to_source_tick(),
            "affect_guard": request.affect_guard,
            "memory_cues": [cue.to_dict() for cue in request.memory_cues],
            "focus_target": routed["focus_target"],
            "candidate_scores": dict(sorted(routed["candidate_scores"].items())),
            "dwell_ms": int(routed["dwell_ms"]),
            "degraded": degraded,
            "continuity_guard": {
                "previous_focus_id": previous_focus.get("focus_id") if previous_focus else None,
                "previous_backend_id": previous_focus.get("backend_id") if previous_focus else None,
                "previous_focus_target": previous_target,
                "attempted_backends": list(attempted_backends),
                "failures": list(failures),
                "preserved_target": routed["focus_target"] == request.attention_target,
                "shifted": routed["focus_target"] != (previous_target or request.attention_target),
                "rationale": list(routed["rationale"]),
            },
        }
        focus["digest"] = sha256_text(canonical_json(_attention_digest_payload(focus)))
        return focus

    def _build_shift(
        self,
        focus: Mapping[str, Any],
        attempted_backends: Sequence[str],
        failures: Sequence[str],
    ) -> Dict[str, Any]:
        continuity_guard = focus["continuity_guard"]
        shift = {
            "kind": "attention_shift",
            "schema_version": ATTENTION_SCHEMA_VERSION,
            "policy_id": ATTENTION_POLICY_ID,
            "focus_ref": focus["focus_id"],
            "selected_backend": focus["backend_id"],
            "attempted_backends": list(attempted_backends),
            "degraded": focus["degraded"],
            "previous_focus_id": continuity_guard["previous_focus_id"],
            "previous_target": continuity_guard["previous_focus_target"],
            "focus_target": focus["focus_target"],
            "affect_guard": focus["affect_guard"],
            "dwell_ms": focus["dwell_ms"],
            "preserved_target": continuity_guard["preserved_target"],
            "failures": list(failures),
        }
        shift["digest"] = sha256_text(canonical_json(_shift_digest_payload(shift)))
        return shift
