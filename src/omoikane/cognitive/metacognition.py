"""Minimal L3 metacognition backends with deterministic failover and bounded self-monitor reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from .reasoning import BackendUnavailableError, CognitiveProfile

METACOGNITION_SCHEMA_VERSION = "1.0.0"
METACOGNITION_POLICY_ID = "bounded-self-monitor-loop-v1"
METACOGNITION_ALLOWED_GUARDS = {"nominal", "observe", "sandbox-notify"}
METACOGNITION_ALLOWED_REFLECTION_MODES = {"self-reflect", "guardian-review", "sandbox-hold"}
METACOGNITION_ALLOWED_ESCALATION_TARGETS = {"none", "guardian-review", "sandbox-stabilization"}
METACOGNITION_ALLOWED_RISK_POSTURES = {"nominal", "guarded", "containment"}
METACOGNITION_MAX_PUBLIC_VALUES = 3
METACOGNITION_MAX_PRIVATE_NOTES = 4
METACOGNITION_DIVERGENCE_ALERT_THRESHOLD = 0.35


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _normalize_labels(values: Sequence[str], *, limit: int) -> List[str]:
    ordered: List[str] = []
    seen = set()
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)
    return ordered[:limit]


def _trait_summary(traits: Mapping[str, float]) -> List[Dict[str, Any]]:
    ranked = sorted(traits.items(), key=lambda item: (-item[1], item[0]))
    return [
        {"trait": trait, "weight": round(_clamp(weight, 0.0, 1.0), 3)}
        for trait, weight in ranked[:3]
    ]


def _coherence_score(request: "MetacognitionRequest") -> float:
    return round(
        _clamp(
            (request.lucidity * 0.45)
            + (request.self_awareness * 0.35)
            + ((1.0 - request.divergence) * 0.20),
            0.0,
            1.0,
        ),
        3,
    )


def _report_digest_payload(report: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": report["schema_version"],
        "policy": report["policy"],
        "backend_id": report["backend_id"],
        "source_tick": report["source_tick"],
        "memory_cues": report["memory_cues"],
        "reflection_summary": report["reflection_summary"],
        "salient_values": report["salient_values"],
        "active_goals": report["active_goals"],
        "trait_summary": report["trait_summary"],
        "qualia_bridge": report["qualia_bridge"],
        "reflection_mode": report["reflection_mode"],
        "escalation_target": report["escalation_target"],
        "risk_posture": report["risk_posture"],
        "sealed_notes": report["sealed_notes"],
        "coherence_score": report["coherence_score"],
        "abrupt_change": report["abrupt_change"],
        "degraded": report["degraded"],
        "continuity_guard": report["continuity_guard"],
    }


def _shift_digest_payload(shift: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": shift["schema_version"],
        "policy_id": shift["policy_id"],
        "report_ref": shift["report_ref"],
        "selected_backend": shift["selected_backend"],
        "attempted_backends": shift["attempted_backends"],
        "degraded": shift["degraded"],
        "previous_report_id": shift["previous_report_id"],
        "previous_reflection_mode": shift["previous_reflection_mode"],
        "reflection_mode": shift["reflection_mode"],
        "escalation_target": shift["escalation_target"],
        "affect_guard": shift["affect_guard"],
        "abrupt_change": shift["abrupt_change"],
        "divergence": shift["divergence"],
        "guard_aligned": shift["guard_aligned"],
        "failures": shift["failures"],
    }


@dataclass(frozen=True)
class MetacognitionCue:
    """Compact cue that biases self-monitoring toward one interpretive anchor."""

    cue_id: str
    focus: str
    weight: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cue_id": self.cue_id,
            "focus": self.focus,
            "weight": round(_clamp(self.weight, 0.0, 1.0), 3),
        }


@dataclass(frozen=True)
class MetacognitionRequest:
    """Single metacognition request derived from self-model and qualia state."""

    tick_id: int
    summary: str
    identity_id: str
    self_values: List[str]
    self_goals: List[str]
    self_traits: Dict[str, float]
    qualia_summary: str
    attention_target: str
    self_awareness: float
    lucidity: float
    affect_guard: str
    continuity_pressure: float
    abrupt_change: bool = False
    divergence: float = 0.0
    memory_cues: List[MetacognitionCue] = field(default_factory=list)

    def to_source_tick(self) -> Dict[str, Any]:
        return {
            "tick_id": self.tick_id,
            "summary": self.summary,
            "identity_id": self.identity_id,
            "self_values": _normalize_labels(self.self_values, limit=METACOGNITION_MAX_PUBLIC_VALUES),
            "self_goals": _normalize_labels(self.self_goals, limit=METACOGNITION_MAX_PUBLIC_VALUES),
            "self_traits": {
                key: round(_clamp(value, 0.0, 1.0), 3)
                for key, value in sorted(self.self_traits.items())
            },
            "qualia_summary": self.qualia_summary,
            "attention_target": self.attention_target,
            "self_awareness": round(_clamp(self.self_awareness, 0.0, 1.0), 3),
            "lucidity": round(_clamp(self.lucidity, 0.0, 1.0), 3),
            "affect_guard": self.affect_guard,
            "continuity_pressure": round(_clamp(self.continuity_pressure, 0.0, 1.0), 3),
            "abrupt_change": self.abrupt_change,
            "divergence": round(_clamp(self.divergence, 0.0, 1.0), 3),
        }


class MetacognitionBackend:
    """Base class for deterministic metacognition backends."""

    def __init__(self, backend_id: str, *, healthy: bool = True) -> None:
        self.backend_id = backend_id
        self._healthy = healthy

    def set_health(self, healthy: bool) -> None:
        self._healthy = healthy

    def reflect(
        self,
        request: MetacognitionRequest,
        *,
        previous_report: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if not self._healthy:
            raise BackendUnavailableError(f"{self.backend_id} is unavailable")
        return self._reflect(request, previous_report=previous_report)

    def _reflect(
        self,
        request: MetacognitionRequest,
        *,
        previous_report: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError


class ReflectiveLoopBackend(MetacognitionBackend):
    """Primary backend that emits one bounded self-reflection report."""

    def _reflect(
        self,
        request: MetacognitionRequest,
        *,
        previous_report: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        salient_values = _normalize_labels(
            request.self_values,
            limit=METACOGNITION_MAX_PUBLIC_VALUES,
        )
        active_goals = _normalize_labels(
            request.self_goals,
            limit=METACOGNITION_MAX_PUBLIC_VALUES,
        )
        coherence_score = _coherence_score(request)
        reflection_mode = "self-reflect"
        escalation_target = "none"
        risk_posture = "nominal"
        rationale = ["summarize-self-state", "retain-bounded-public-reflection"]

        if request.affect_guard == "sandbox-notify":
            reflection_mode = "sandbox-hold"
            escalation_target = "sandbox-stabilization"
            risk_posture = "containment"
            rationale.append("contain-under-sandbox-notify-guard")
        elif (
            request.affect_guard == "observe"
            or request.abrupt_change
            or request.divergence >= METACOGNITION_DIVERGENCE_ALERT_THRESHOLD
            or request.lucidity < 0.65
        ):
            reflection_mode = "guardian-review"
            escalation_target = "guardian-review"
            risk_posture = "guarded"
            rationale.append("elevate-reflection-to-guardian-review")

        private_notes = [
            f"continuity-pressure:{round(request.continuity_pressure, 3)}",
            f"attention-target:{request.attention_target}",
        ]
        if request.abrupt_change:
            private_notes.append("abrupt-change-detected")
        if request.divergence >= METACOGNITION_DIVERGENCE_ALERT_THRESHOLD:
            private_notes.append(f"divergence:{round(request.divergence, 3)}")
        if request.lucidity < 0.7:
            private_notes.append(f"lucidity-floor:{round(request.lucidity, 3)}")

        return {
            "reflection_summary": (
                f"`{request.qualia_summary}` を保ちながら、"
                f"{', '.join(salient_values[:2])} を identity anchor として"
                f"{', '.join(active_goals[:2])} を継続目標に据える自己監視報告"
            ),
            "salient_values": salient_values,
            "active_goals": active_goals,
            "trait_summary": _trait_summary(request.self_traits),
            "reflection_mode": reflection_mode,
            "escalation_target": escalation_target,
            "risk_posture": risk_posture,
            "sealed_notes": private_notes[:METACOGNITION_MAX_PRIVATE_NOTES],
            "coherence_score": coherence_score,
            "rationale": rationale,
        }


class ContinuityMirrorBackend(MetacognitionBackend):
    """Fallback backend that collapses metacognition into a continuity-preserving mirror."""

    def _reflect(
        self,
        request: MetacognitionRequest,
        *,
        previous_report: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        previous_values = list(previous_report.get("salient_values", [])) if previous_report else []
        previous_goals = list(previous_report.get("active_goals", [])) if previous_report else []
        salient_values = _normalize_labels(
            [*request.self_values, *previous_values, "continuity-first"],
            limit=METACOGNITION_MAX_PUBLIC_VALUES,
        )
        active_goals = _normalize_labels(
            [*request.self_goals, *previous_goals, "guardian-review"],
            limit=METACOGNITION_MAX_PUBLIC_VALUES,
        )
        reflection_mode = (
            "sandbox-hold" if request.affect_guard == "sandbox-notify" else "guardian-review"
        )
        escalation_target = (
            "sandbox-stabilization"
            if request.affect_guard == "sandbox-notify"
            else "guardian-review"
        )
        risk_posture = "containment" if request.affect_guard == "sandbox-notify" else "guarded"
        rationale = ["mirror-last-stable-identity-anchor", "preserve-continuity-before-expansion"]
        if previous_report is not None:
            rationale.append("reuse-previous-report-context")

        return {
            "reflection_summary": (
                f"`{request.qualia_summary}` を private self-monitor loop に縮退し、"
                f"{salient_values[0]} と {active_goals[0]} を残して"
                f"{escalation_target} を先行させる continuity mirror report"
            ),
            "salient_values": salient_values,
            "active_goals": active_goals,
            "trait_summary": _trait_summary(request.self_traits),
            "reflection_mode": reflection_mode,
            "escalation_target": escalation_target,
            "risk_posture": risk_posture,
            "sealed_notes": [
                "fallback-continuity-mirror",
                f"divergence:{round(request.divergence, 3)}",
                f"attention-target:{request.attention_target}",
                "preserve-stable-anchor-before-expansion",
            ],
            "coherence_score": round(max(0.42, _coherence_score(request) - 0.08), 3),
            "rationale": rationale,
        }


class MetacognitionService:
    """Profile-driven router that fails over across metacognition backends."""

    def __init__(
        self,
        profile: CognitiveProfile,
        backends: Sequence[MetacognitionBackend],
    ) -> None:
        self.profile = profile
        self._backends = {backend.backend_id: backend for backend in backends}

    @staticmethod
    def _guard_aligned(reflection_mode: str, affect_guard: str) -> bool:
        if affect_guard == "nominal":
            return reflection_mode == "self-reflect"
        if affect_guard == "observe":
            return reflection_mode == "guardian-review"
        return reflection_mode == "sandbox-hold"

    def set_backend_health(self, backend_id: str, healthy: bool) -> None:
        self._backends[backend_id].set_health(healthy)

    def run(
        self,
        request: MetacognitionRequest,
        *,
        previous_report: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        attempted: List[str] = []
        failures: List[str] = []
        order = [self.profile.primary] + list(self.profile.fallback)

        for backend_id in order:
            attempted.append(backend_id)
            backend = self._backends[backend_id]
            try:
                partial = backend.reflect(request, previous_report=previous_report)
            except BackendUnavailableError as exc:
                failures.append(str(exc))
                continue

            degraded = backend_id != self.profile.primary
            guard_aligned = self._guard_aligned(partial["reflection_mode"], request.affect_guard)
            continuity_guard = {
                "previous_report_id": None if previous_report is None else previous_report.get("report_id"),
                "previous_backend_id": None if previous_report is None else previous_report.get("backend_id"),
                "previous_reflection_mode": None
                if previous_report is None
                else previous_report.get("reflection_mode"),
                "attempted_backends": attempted,
                "failures": failures,
                "guard_aligned": guard_aligned,
                "preserved_identity_anchor": bool(
                    partial["salient_values"] and partial["active_goals"]
                ),
                "rationale": partial["rationale"],
            }
            report = {
                "kind": "metacognition_report",
                "schema_version": METACOGNITION_SCHEMA_VERSION,
                "policy": {
                    "schema_version": METACOGNITION_SCHEMA_VERSION,
                    "policy_id": METACOGNITION_POLICY_ID,
                    "primary": self.profile.primary,
                    "fallback": list(self.profile.fallback),
                    "max_public_values": METACOGNITION_MAX_PUBLIC_VALUES,
                    "max_private_notes": METACOGNITION_MAX_PRIVATE_NOTES,
                    "divergence_alert_threshold": METACOGNITION_DIVERGENCE_ALERT_THRESHOLD,
                    "failover_mode": "single-switch",
                },
                "report_id": new_id("metacognition-report"),
                "generated_at": utc_now_iso(),
                "backend_id": backend_id,
                "source_tick": request.to_source_tick(),
                "memory_cues": [cue.to_dict() for cue in request.memory_cues],
                "reflection_summary": partial["reflection_summary"],
                "salient_values": partial["salient_values"],
                "active_goals": partial["active_goals"],
                "trait_summary": partial["trait_summary"],
                "qualia_bridge": {
                    "summary": request.qualia_summary,
                    "attention_target": request.attention_target,
                    "self_awareness": round(request.self_awareness, 3),
                    "lucidity": round(request.lucidity, 3),
                },
                "reflection_mode": partial["reflection_mode"],
                "escalation_target": partial["escalation_target"],
                "risk_posture": partial["risk_posture"],
                "sealed_notes": partial["sealed_notes"][:METACOGNITION_MAX_PRIVATE_NOTES],
                "coherence_score": partial["coherence_score"],
                "abrupt_change": request.abrupt_change,
                "degraded": degraded,
                "continuity_guard": continuity_guard,
            }
            report["digest"] = sha256_text(canonical_json(_report_digest_payload(report)))
            shift = {
                "kind": "metacognition_shift",
                "schema_version": METACOGNITION_SCHEMA_VERSION,
                "policy_id": METACOGNITION_POLICY_ID,
                "report_ref": report["report_id"],
                "selected_backend": backend_id,
                "attempted_backends": attempted,
                "degraded": degraded,
                "previous_report_id": continuity_guard["previous_report_id"],
                "previous_reflection_mode": continuity_guard["previous_reflection_mode"],
                "reflection_mode": report["reflection_mode"],
                "escalation_target": report["escalation_target"],
                "affect_guard": request.affect_guard,
                "abrupt_change": request.abrupt_change,
                "divergence": round(request.divergence, 3),
                "guard_aligned": guard_aligned,
                "failures": failures,
            }
            shift["digest"] = sha256_text(canonical_json(_shift_digest_payload(shift)))
            return {
                "profile": {
                    "primary": self.profile.primary,
                    "fallback": list(self.profile.fallback),
                },
                "attempted_backends": attempted,
                "selected_backend": backend_id,
                "degraded": degraded,
                "failures": failures,
                "report": report,
                "shift": shift,
            }

        raise BackendUnavailableError(
            "all metacognition backends unavailable: " + ", ".join(attempted)
        )

    def validate_report(self, snapshot: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        policy = snapshot.get("policy", {})
        source_tick = snapshot.get("source_tick", {})
        guard = source_tick.get("affect_guard")
        reflection_mode = snapshot.get("reflection_mode")
        escalation_target = snapshot.get("escalation_target")
        guard_aligned = snapshot.get("continuity_guard", {}).get("guard_aligned")

        if snapshot.get("kind") != "metacognition_report":
            errors.append("kind must equal metacognition_report")
        if snapshot.get("schema_version") != METACOGNITION_SCHEMA_VERSION:
            errors.append("schema_version mismatch")
        if policy.get("policy_id") != METACOGNITION_POLICY_ID:
            errors.append("policy.policy_id mismatch")
        if guard not in METACOGNITION_ALLOWED_GUARDS:
            errors.append("source_tick.affect_guard invalid")
        if reflection_mode not in METACOGNITION_ALLOWED_REFLECTION_MODES:
            errors.append("reflection_mode invalid")
        if escalation_target not in METACOGNITION_ALLOWED_ESCALATION_TARGETS:
            errors.append("escalation_target invalid")
        if snapshot.get("risk_posture") not in METACOGNITION_ALLOWED_RISK_POSTURES:
            errors.append("risk_posture invalid")
        if len(snapshot.get("salient_values", [])) < 1:
            errors.append("salient_values must not be empty")
        if len(snapshot.get("active_goals", [])) < 1:
            errors.append("active_goals must not be empty")
        if len(snapshot.get("sealed_notes", [])) > METACOGNITION_MAX_PRIVATE_NOTES:
            errors.append("sealed_notes exceeds max_private_notes")
        if not 0.0 <= snapshot.get("coherence_score", -1.0) <= 1.0:
            errors.append("coherence_score out of range")
        if snapshot.get("abrupt_change") and escalation_target == "none":
            errors.append("abrupt_change requires escalation_target")
        if guard in {"observe", "sandbox-notify"} and escalation_target == "none":
            errors.append("non-nominal guard requires escalation_target")
        if snapshot.get("degraded") and snapshot.get("backend_id") == self.profile.primary:
            errors.append("degraded report cannot use primary backend")
        if guard_aligned is not self._guard_aligned(str(reflection_mode), str(guard)):
            errors.append("continuity_guard.guard_aligned mismatch")

        return {
            "ok": not errors,
            "selected_backend": snapshot.get("backend_id"),
            "reflection_mode": reflection_mode,
            "guard_aligned": guard_aligned,
            "abrupt_change": snapshot.get("abrupt_change", False),
            "errors": errors,
        }

    def validate_shift(self, shift: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        reflection_mode = shift.get("reflection_mode")
        affect_guard = shift.get("affect_guard")

        if shift.get("kind") != "metacognition_shift":
            errors.append("kind must equal metacognition_shift")
        if shift.get("schema_version") != METACOGNITION_SCHEMA_VERSION:
            errors.append("schema_version mismatch")
        if shift.get("policy_id") != METACOGNITION_POLICY_ID:
            errors.append("policy_id mismatch")
        if affect_guard not in METACOGNITION_ALLOWED_GUARDS:
            errors.append("affect_guard invalid")
        if reflection_mode not in METACOGNITION_ALLOWED_REFLECTION_MODES:
            errors.append("reflection_mode invalid")
        if shift.get("escalation_target") not in METACOGNITION_ALLOWED_ESCALATION_TARGETS:
            errors.append("escalation_target invalid")
        if not 0.0 <= shift.get("divergence", -1.0) <= 1.0:
            errors.append("divergence out of range")
        if shift.get("guard_aligned") is not self._guard_aligned(
            str(reflection_mode),
            str(affect_guard),
        ):
            errors.append("guard_aligned mismatch")
        if shift.get("abrupt_change") and shift.get("escalation_target") == "none":
            errors.append("abrupt_change requires escalation_target")
        if shift.get("degraded") and shift.get("selected_backend") == self.profile.primary:
            errors.append("degraded shift cannot use primary backend")

        return {
            "ok": not errors,
            "selected_backend": shift.get("selected_backend"),
            "reflection_mode": reflection_mode,
            "guard_aligned": shift.get("guard_aligned"),
            "abrupt_change": shift.get("abrupt_change", False),
            "errors": errors,
        }
