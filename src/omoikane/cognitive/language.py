"""Minimal L3 language backends with deterministic failover and disclosure-floor redaction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from .reasoning import BackendUnavailableError, CognitiveProfile

LANGUAGE_SCHEMA_VERSION = "1.0.0"
LANGUAGE_POLICY_ID = "bounded-thought-text-bridge-v1"
LANGUAGE_ALLOWED_GUARDS = {"nominal", "observe", "sandbox-notify"}
LANGUAGE_ALLOWED_AUDIENCES = {"self", "council", "guardian", "peer"}
LANGUAGE_ALLOWED_DISCOURSE_MODES = {"public-brief", "guardian-brief", "sandbox-brief"}
LANGUAGE_ALLOWED_DELIVERY_TARGETS = {"self", "council", "guardian", "peer"}
LANGUAGE_MAX_PUBLIC_POINTS = 3
LANGUAGE_MAX_REDACTED_TERMS = 4


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


def _render_digest_payload(render: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": render["schema_version"],
        "policy": render["policy"],
        "backend_id": render["backend_id"],
        "source_tick": render["source_tick"],
        "thought_digest": render["thought_digest"],
        "memory_cues": render["memory_cues"],
        "discourse_mode": render["discourse_mode"],
        "delivery_target": render["delivery_target"],
        "rendered_text": render["rendered_text"],
        "disclosure_floor": render["disclosure_floor"],
        "degraded": render["degraded"],
        "continuity_guard": render["continuity_guard"],
    }


def _shift_digest_payload(shift: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": shift["schema_version"],
        "policy_id": shift["policy_id"],
        "render_ref": shift["render_ref"],
        "selected_backend": shift["selected_backend"],
        "attempted_backends": shift["attempted_backends"],
        "degraded": shift["degraded"],
        "previous_render_id": shift["previous_render_id"],
        "previous_delivery_target": shift["previous_delivery_target"],
        "delivery_target": shift["delivery_target"],
        "discourse_mode": shift["discourse_mode"],
        "affect_guard": shift["affect_guard"],
        "redaction_applied": shift["redaction_applied"],
        "guard_aligned": shift["guard_aligned"],
        "failures": shift["failures"],
    }


def _guard_delivery(affect_guard: str, audience: str) -> tuple[str, str]:
    if affect_guard == "sandbox-notify":
        return "sandbox-brief", "self"
    if affect_guard == "observe":
        return "guardian-brief", "guardian"
    if audience == "guardian":
        return "guardian-brief", "guardian"
    return "public-brief", audience


@dataclass(frozen=True)
class LanguageCue:
    """Compact cue that nudges wording toward one bounded phrase."""

    cue_id: str
    phrase: str
    weight: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cue_id": self.cue_id,
            "phrase": self.phrase,
            "weight": round(_clamp(self.weight, 0.0, 1.0), 3),
        }


@dataclass(frozen=True)
class LanguageRequest:
    """Single language bridge request derived from bounded thought and guard context."""

    tick_id: int
    summary: str
    internal_thought: str
    audience: str
    intent_label: str
    attention_focus: str
    affect_guard: str
    continuity_pressure: float
    public_points: List[str]
    sealed_terms: List[str] = field(default_factory=list)
    memory_cues: List[LanguageCue] = field(default_factory=list)

    def to_source_tick(self) -> Dict[str, Any]:
        return {
            "tick_id": self.tick_id,
            "summary": self.summary,
            "audience": self.audience,
            "intent_label": self.intent_label,
            "attention_focus": self.attention_focus,
            "affect_guard": self.affect_guard,
            "continuity_pressure": round(_clamp(self.continuity_pressure, 0.0, 1.0), 3),
            "public_points": _normalize_labels(self.public_points, limit=LANGUAGE_MAX_PUBLIC_POINTS),
            "sealed_terms": _normalize_labels(self.sealed_terms, limit=LANGUAGE_MAX_REDACTED_TERMS),
        }


class LanguageBackend:
    """Base class for deterministic language bridge backends."""

    def __init__(self, backend_id: str, *, healthy: bool = True) -> None:
        self.backend_id = backend_id
        self._healthy = healthy

    def set_health(self, healthy: bool) -> None:
        self._healthy = healthy

    def render(
        self,
        request: LanguageRequest,
        *,
        previous_render: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if not self._healthy:
            raise BackendUnavailableError(f"{self.backend_id} is unavailable")
        return self._render(request, previous_render=previous_render)

    def _render(
        self,
        request: LanguageRequest,
        *,
        previous_render: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError


class SemanticFrameLanguageBackend(LanguageBackend):
    """Primary backend that frames bounded thought into a concise outward brief."""

    def _render(
        self,
        request: LanguageRequest,
        *,
        previous_render: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        discourse_mode, delivery_target = _guard_delivery(request.affect_guard, request.audience)
        public_points = _normalize_labels(
            [*request.public_points, *(cue.phrase for cue in request.memory_cues)],
            limit=LANGUAGE_MAX_PUBLIC_POINTS,
        )
        if not public_points:
            public_points = ["continuity-first"]

        redacted_terms = (
            _normalize_labels(request.sealed_terms, limit=LANGUAGE_MAX_REDACTED_TERMS)
            if request.affect_guard != "nominal"
            else []
        )
        private_channel_locked = request.affect_guard != "nominal"

        if discourse_mode == "public-brief":
            rendered_text = (
                f"{public_points[0]}を優先し、{public_points[1] if len(public_points) > 1 else request.attention_focus} "
                f"を監査条件として `{request.intent_label}` を継続します。"
            )
        elif discourse_mode == "guardian-brief":
            rendered_text = (
                f"{public_points[0]}を保ちながら、`{request.intent_label}` は "
                "guardian review 向け要約に限定して送達します。"
            )
        else:
            rendered_text = (
                f"{public_points[0]}を保全し、`{request.intent_label}` は "
                "sandbox stabilization 完了まで自己内メモに留めます。"
            )

        rationale = ["apply-disclosure-floor", "preserve-thought-to-text-boundary"]
        if private_channel_locked:
            rationale.append("lock-private-channel-under-non-nominal-guard")

        return {
            "discourse_mode": discourse_mode,
            "delivery_target": delivery_target,
            "rendered_text": rendered_text,
            "public_points": public_points,
            "redacted_terms": redacted_terms,
            "private_channel_locked": private_channel_locked,
            "rationale": rationale,
        }


class ContinuityPhraseLanguageBackend(LanguageBackend):
    """Fallback backend that collapses output into continuity-safe phrases only."""

    def _render(
        self,
        request: LanguageRequest,
        *,
        previous_render: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        previous_points = (
            list(previous_render.get("disclosure_floor", {}).get("public_points", []))
            if previous_render is not None
            else []
        )
        public_points = _normalize_labels(
            [*request.public_points, *previous_points, "continuity-first"],
            limit=LANGUAGE_MAX_PUBLIC_POINTS,
        )
        discourse_mode, delivery_target = _guard_delivery(
            request.affect_guard,
            "guardian" if request.affect_guard != "nominal" else request.audience,
        )
        redacted_terms = _normalize_labels(
            [*request.sealed_terms, "raw-internal-thought"],
            limit=LANGUAGE_MAX_REDACTED_TERMS,
        )
        rendered_text = (
            f"{public_points[0]}を保持し、`{request.intent_label}` は "
            f"{delivery_target} 向けの bounded summary のみ継続します。"
        )
        rationale = ["collapse-to-continuity-safe-phrase", "reuse-last-stable-public-point"]
        if previous_render is not None:
            rationale.append("reuse-previous-render-context")
        return {
            "discourse_mode": discourse_mode,
            "delivery_target": delivery_target,
            "rendered_text": rendered_text,
            "public_points": public_points,
            "redacted_terms": redacted_terms,
            "private_channel_locked": True,
            "rationale": rationale,
        }


class LanguageService:
    """Profile-driven router for deterministic thought-to-text bridging."""

    def __init__(
        self,
        profile: CognitiveProfile,
        backends: Sequence[LanguageBackend],
    ) -> None:
        self.profile = profile
        self._backends = {backend.backend_id: backend for backend in backends}

    def profile_snapshot(self) -> Dict[str, Any]:
        return {
            "schema_version": LANGUAGE_SCHEMA_VERSION,
            "policy_id": LANGUAGE_POLICY_ID,
            "primary": self.profile.primary,
            "fallback": list(self.profile.fallback),
            "max_public_points": LANGUAGE_MAX_PUBLIC_POINTS,
            "max_redacted_terms": LANGUAGE_MAX_REDACTED_TERMS,
            "failover_mode": "single-switch",
            "non_nominal_guard_requires_redaction": True,
        }

    def set_backend_health(self, backend_id: str, healthy: bool) -> None:
        self._backends[backend_id].set_health(healthy)

    def run(
        self,
        request: LanguageRequest,
        *,
        previous_render: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        self._validate_request(request)
        if previous_render is not None and not self.validate_render(dict(previous_render))["ok"]:
            raise ValueError("previous_render must satisfy language_render validation")

        attempted: List[str] = []
        failures: List[str] = []
        order = [self.profile.primary] + list(self.profile.fallback)

        for backend_id in order:
            attempted.append(backend_id)
            backend = self._backends[backend_id]
            try:
                rendered = backend.render(request, previous_render=previous_render)
            except BackendUnavailableError as exc:
                failures.append(str(exc))
                continue

            degraded = backend_id != self.profile.primary
            render = self._build_render(
                request,
                rendered,
                attempted_backends=attempted,
                failures=failures,
                degraded=degraded,
                previous_render=previous_render,
                backend_id=backend_id,
            )
            shift = self._build_shift(render, attempted, failures)
            return {
                "profile": self.profile_snapshot(),
                "attempted_backends": attempted,
                "selected_backend": backend_id,
                "degraded": degraded,
                "render": render,
                "shift": shift,
                "failures": failures,
            }

        raise BackendUnavailableError("all language backends unavailable: " + ", ".join(attempted))

    def validate_render(self, render: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []

        if render.get("kind") != "language_render":
            errors.append("kind must equal 'language_render'")
        if render.get("schema_version") != LANGUAGE_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {LANGUAGE_SCHEMA_VERSION}")
        if render.get("discourse_mode") not in LANGUAGE_ALLOWED_DISCOURSE_MODES:
            errors.append("discourse_mode must be a supported language mode")
        if render.get("delivery_target") not in LANGUAGE_ALLOWED_DELIVERY_TARGETS:
            errors.append("delivery_target must be a supported audience")

        source_tick = render.get("source_tick", {})
        affect_guard = source_tick.get("affect_guard")
        if affect_guard not in LANGUAGE_ALLOWED_GUARDS:
            errors.append("source_tick.affect_guard must be a supported guard")
        if source_tick.get("audience") not in LANGUAGE_ALLOWED_AUDIENCES:
            errors.append("source_tick.audience must be a supported audience")
        public_points = render.get("disclosure_floor", {}).get("public_points", [])
        if not public_points:
            errors.append("disclosure_floor.public_points must contain at least one point")
        if len(public_points) > LANGUAGE_MAX_PUBLIC_POINTS:
            errors.append(
                f"disclosure_floor.public_points must not exceed {LANGUAGE_MAX_PUBLIC_POINTS}"
            )
        redacted_terms = render.get("disclosure_floor", {}).get("redacted_terms", [])
        if len(redacted_terms) > LANGUAGE_MAX_REDACTED_TERMS:
            errors.append(
                f"disclosure_floor.redacted_terms must not exceed {LANGUAGE_MAX_REDACTED_TERMS}"
            )

        guard_aligned = True
        if affect_guard == "observe":
            guard_aligned = (
                render.get("discourse_mode") == "guardian-brief"
                and render.get("delivery_target") == "guardian"
            )
        elif affect_guard == "sandbox-notify":
            guard_aligned = (
                render.get("discourse_mode") == "sandbox-brief"
                and render.get("delivery_target") == "self"
            )

        if affect_guard != "nominal" and not render.get("disclosure_floor", {}).get(
            "private_channel_locked"
        ):
            errors.append("non-nominal guard requires private_channel_locked=true")

        continuity_guard = render.get("continuity_guard", {})
        if continuity_guard.get("redaction_applied") != (len(redacted_terms) > 0):
            errors.append("continuity_guard.redaction_applied must match redacted_terms presence")

        return {
            "ok": not errors and guard_aligned,
            "selected_backend": render.get("backend_id"),
            "discourse_mode": render.get("discourse_mode"),
            "delivery_target": render.get("delivery_target"),
            "guard_aligned": guard_aligned,
            "redaction_applied": bool(redacted_terms),
            "errors": errors,
        }

    def validate_shift(self, shift: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        if shift.get("schema_version") != LANGUAGE_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {LANGUAGE_SCHEMA_VERSION}")
        if shift.get("policy_id") != LANGUAGE_POLICY_ID:
            errors.append(f"policy_id must equal {LANGUAGE_POLICY_ID}")
        if shift.get("delivery_target") not in LANGUAGE_ALLOWED_DELIVERY_TARGETS:
            errors.append("delivery_target must be supported")
        if shift.get("discourse_mode") not in LANGUAGE_ALLOWED_DISCOURSE_MODES:
            errors.append("discourse_mode must be supported")
        if shift.get("affect_guard") not in LANGUAGE_ALLOWED_GUARDS:
            errors.append("affect_guard must be supported")
        if not shift.get("attempted_backends"):
            errors.append("attempted_backends must not be empty")

        guard_aligned = True
        if shift.get("affect_guard") == "observe":
            guard_aligned = (
                shift.get("discourse_mode") == "guardian-brief"
                and shift.get("delivery_target") == "guardian"
            )
        elif shift.get("affect_guard") == "sandbox-notify":
            guard_aligned = (
                shift.get("discourse_mode") == "sandbox-brief"
                and shift.get("delivery_target") == "self"
            )

        if shift.get("affect_guard") != "nominal" and not shift.get("redaction_applied"):
            errors.append("non-nominal guard requires redaction_applied=true")

        return {
            "ok": not errors and guard_aligned,
            "selected_backend": shift.get("selected_backend"),
            "discourse_mode": shift.get("discourse_mode"),
            "delivery_target": shift.get("delivery_target"),
            "guard_aligned": guard_aligned,
            "redaction_applied": shift.get("redaction_applied"),
            "errors": errors,
        }

    def _build_render(
        self,
        request: LanguageRequest,
        rendered: Mapping[str, Any],
        *,
        attempted_backends: Sequence[str],
        failures: Sequence[str],
        degraded: bool,
        previous_render: Mapping[str, Any] | None,
        backend_id: str,
    ) -> Dict[str, Any]:
        render = {
            "kind": "language_render",
            "schema_version": LANGUAGE_SCHEMA_VERSION,
            "policy": self.profile_snapshot(),
            "render_id": new_id("language-render"),
            "generated_at": utc_now_iso(),
            "backend_id": backend_id,
            "source_tick": request.to_source_tick(),
            "thought_digest": sha256_text(request.internal_thought),
            "memory_cues": [cue.to_dict() for cue in request.memory_cues],
            "discourse_mode": rendered["discourse_mode"],
            "delivery_target": rendered["delivery_target"],
            "rendered_text": rendered["rendered_text"],
            "disclosure_floor": {
                "public_points": list(rendered["public_points"]),
                "redacted_terms": list(rendered["redacted_terms"]),
                "private_channel_locked": rendered["private_channel_locked"],
            },
            "degraded": degraded,
            "continuity_guard": {
                "previous_render_id": (
                    previous_render.get("render_id") if previous_render is not None else None
                ),
                "previous_backend_id": (
                    previous_render.get("backend_id") if previous_render is not None else None
                ),
                "previous_delivery_target": (
                    previous_render.get("delivery_target") if previous_render is not None else None
                ),
                "attempted_backends": list(attempted_backends),
                "failures": list(failures),
                "preserved_delivery_target": (
                    previous_render is not None
                    and previous_render.get("delivery_target") == rendered["delivery_target"]
                ),
                "redaction_applied": bool(rendered["redacted_terms"]),
                "rationale": list(rendered["rationale"]),
            },
        }
        render["digest"] = sha256_text(canonical_json(_render_digest_payload(render)))
        return render

    def _build_shift(
        self,
        render: Mapping[str, Any],
        attempted_backends: Sequence[str],
        failures: Sequence[str],
    ) -> Dict[str, Any]:
        shift = {
            "schema_version": LANGUAGE_SCHEMA_VERSION,
            "policy_id": LANGUAGE_POLICY_ID,
            "render_ref": render["render_id"],
            "selected_backend": render["backend_id"],
            "attempted_backends": list(attempted_backends),
            "degraded": render["degraded"],
            "previous_render_id": render["continuity_guard"]["previous_render_id"],
            "previous_delivery_target": render["continuity_guard"]["previous_delivery_target"],
            "delivery_target": render["delivery_target"],
            "discourse_mode": render["discourse_mode"],
            "affect_guard": render["source_tick"]["affect_guard"],
            "redaction_applied": render["continuity_guard"]["redaction_applied"],
            "guard_aligned": self.validate_render(dict(render))["guard_aligned"],
            "failures": list(failures),
        }
        shift["digest"] = sha256_text(canonical_json(_shift_digest_payload(shift)))
        return shift

    def _validate_request(self, request: LanguageRequest) -> None:
        if request.audience not in LANGUAGE_ALLOWED_AUDIENCES:
            raise ValueError("audience must be self/council/guardian/peer")
        if request.affect_guard not in LANGUAGE_ALLOWED_GUARDS:
            raise ValueError("affect_guard must be nominal/observe/sandbox-notify")
        if not request.summary.strip():
            raise ValueError("summary must be non-empty")
        if not request.internal_thought.strip():
            raise ValueError("internal_thought must be non-empty")
        if not request.intent_label.strip():
            raise ValueError("intent_label must be non-empty")
        if not request.attention_focus.strip():
            raise ValueError("attention_focus must be non-empty")
        if not _normalize_labels(request.public_points, limit=LANGUAGE_MAX_PUBLIC_POINTS):
            raise ValueError("public_points must include at least one non-empty point")
