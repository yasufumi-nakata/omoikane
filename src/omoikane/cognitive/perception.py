"""Minimal L3 perception backends with deterministic failover and qualia-bound scene encoding."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from .reasoning import BackendUnavailableError, CognitiveProfile

PERCEPTION_SCHEMA_VERSION = "1.0.0"
PERCEPTION_POLICY_ID = "bounded-perception-failover-v1"
PERCEPTION_ALLOWED_GUARDS = {"nominal", "observe", "sandbox-notify"}
PERCEPTION_MODALITIES = ("visual", "auditory", "somatic", "interoceptive")
PERCEPTION_SAFE_SCENES = (
    "guardian-review-scene",
    "continuity-hold",
    "sandbox-stabilization",
)
PERCEPTION_GATES = ("open", "guardian-review", "private-buffer")
PERCEPTION_MAX_ENTITIES = 4


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


def _dominant_modality(modality_salience: Mapping[str, float]) -> str:
    return max(modality_salience.items(), key=lambda item: (item[1], item[0]))[0]


def _perception_digest_payload(frame: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": frame["schema_version"],
        "policy": frame["policy"],
        "backend_id": frame["backend_id"],
        "source_tick": frame["source_tick"],
        "sensory_stream_ref": frame["sensory_stream_ref"],
        "world_state_ref": frame["world_state_ref"],
        "body_anchor_ref": frame["body_anchor_ref"],
        "affect_guard": frame["affect_guard"],
        "detected_entities": frame["detected_entities"],
        "salient_cues": frame["salient_cues"],
        "scene_label": frame["scene_label"],
        "scene_summary": frame["scene_summary"],
        "dominant_modality": frame["dominant_modality"],
        "salience_map": frame["salience_map"],
        "qualia_binding_ref": frame["qualia_binding_ref"],
        "body_coherence_score": frame["body_coherence_score"],
        "perception_gate": frame["perception_gate"],
        "degraded": frame["degraded"],
        "continuity_guard": frame["continuity_guard"],
    }


def _shift_digest_payload(shift: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": shift["schema_version"],
        "policy_id": shift["policy_id"],
        "frame_ref": shift["frame_ref"],
        "selected_backend": shift["selected_backend"],
        "attempted_backends": shift["attempted_backends"],
        "degraded": shift["degraded"],
        "previous_frame_id": shift["previous_frame_id"],
        "previous_scene_label": shift["previous_scene_label"],
        "scene_label": shift["scene_label"],
        "dominant_modality": shift["dominant_modality"],
        "affect_guard": shift["affect_guard"],
        "qualia_binding_ref": shift["qualia_binding_ref"],
        "body_coherence_preserved": shift["body_coherence_preserved"],
        "safe_summary_only": shift["safe_summary_only"],
        "failures": shift["failures"],
    }


def _perception_gate(affect_guard: str) -> str:
    if affect_guard == "sandbox-notify":
        return "private-buffer"
    if affect_guard == "observe":
        return "guardian-review"
    return "open"


def _body_coherence_score(modality_salience: Mapping[str, float], drift_score: float) -> float:
    average_salience = sum(modality_salience.values()) / len(PERCEPTION_MODALITIES)
    score = 0.76 + (average_salience * 0.22) - (drift_score * 0.41)
    return round(_clamp(score, 0.0, 1.0), 3)


@dataclass(frozen=True)
class PerceptionCue:
    """Compact cue that can bias scene selection toward one bounded label."""

    cue_id: str
    target: str
    weight: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cue_id": self.cue_id,
            "target": self.target,
            "weight": round(_clamp(self.weight, 0.0, 1.0), 3),
        }


@dataclass(frozen=True)
class PerceptionRequest:
    """Single perception request derived from one bounded sensory stream snapshot."""

    tick_id: int
    summary: str
    sensory_stream_ref: str
    world_state_ref: str
    body_anchor_ref: str
    modality_salience: Dict[str, float]
    drift_score: float
    affect_guard: str
    detected_entities: List[str]
    memory_cues: List[PerceptionCue] = field(default_factory=list)

    def to_source_tick(self) -> Dict[str, Any]:
        return {
            "tick_id": self.tick_id,
            "summary": self.summary,
            "sensory_stream_ref": self.sensory_stream_ref,
            "world_state_ref": self.world_state_ref,
            "body_anchor_ref": self.body_anchor_ref,
            "modality_salience": {
                key: round(value, 3) for key, value in self.modality_salience.items()
            },
            "drift_score": round(_clamp(self.drift_score, 0.0, 1.0), 3),
        }


class PerceptionBackend:
    """Base class for deterministic perception backends."""

    def __init__(self, backend_id: str, *, healthy: bool = True) -> None:
        self.backend_id = backend_id
        self._healthy = healthy

    def set_health(self, healthy: bool) -> None:
        self._healthy = healthy

    def encode(
        self,
        request: PerceptionRequest,
        *,
        previous_frame: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if not self._healthy:
            raise BackendUnavailableError(f"{self.backend_id} is unavailable")
        return self._encode(request, previous_frame=previous_frame)

    def _encode(
        self,
        request: PerceptionRequest,
        *,
        previous_frame: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError


class SalienceEncoderPerceptionBackend(PerceptionBackend):
    """Primary backend that keeps the most salient scene label active."""

    def _encode(
        self,
        request: PerceptionRequest,
        *,
        previous_frame: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        dominant_modality = _dominant_modality(request.modality_salience)
        cue_map = {cue.target: cue.weight for cue in request.memory_cues}
        body_coherence_score = _body_coherence_score(request.modality_salience, request.drift_score)
        default_scene = request.detected_entities[0] if request.detected_entities else f"{dominant_modality}-field"

        scene_label = default_scene
        rationale = ["encode-highest-salience-scene", "bind-scene-to-qualia-window"]
        if request.affect_guard == "sandbox-notify":
            scene_label = "sandbox-stabilization"
            rationale.append("respect-sandbox-notify-guard")
        elif request.affect_guard == "observe" and (
            request.drift_score >= 0.34 or body_coherence_score < 0.7
        ):
            scene_label = "guardian-review-scene"
            rationale.append("escalate-scene-for-guardian-review")
        elif cue_map.get("continuity-hold", 0.0) >= 0.26:
            scene_label = "continuity-hold"
            rationale.append("respect-continuity-hold-cue")

        scene_summary = (
            f"{dominant_modality} 優位で `{scene_label}` を知覚し、"
            "bounded scene summary を qualia handoff に束縛します。"
        )
        return {
            "scene_label": scene_label,
            "scene_summary": scene_summary,
            "dominant_modality": dominant_modality,
            "body_coherence_score": body_coherence_score,
            "perception_gate": _perception_gate(request.affect_guard),
            "salience_map": {
                key: round(value, 3) for key, value in request.modality_salience.items()
            },
            "rationale": rationale,
        }


class ContinuityProjectionPerceptionBackend(PerceptionBackend):
    """Fallback backend that collapses perception into continuity-safe scene summaries."""

    def _encode(
        self,
        request: PerceptionRequest,
        *,
        previous_frame: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        dominant_modality = _dominant_modality(request.modality_salience)
        previous_scene_label = (
            str(previous_frame.get("scene_label"))
            if previous_frame is not None and previous_frame.get("scene_label")
            else None
        )
        if request.affect_guard == "sandbox-notify":
            scene_label = "sandbox-stabilization"
        elif request.affect_guard == "observe":
            scene_label = "guardian-review-scene"
        elif previous_scene_label in PERCEPTION_SAFE_SCENES:
            scene_label = previous_scene_label
        else:
            scene_label = "continuity-hold"

        scene_summary = (
            f"{dominant_modality} の摘要だけを保持し、`{scene_label}` を "
            "continuity-safe な scene summary として継続します。"
        )
        return {
            "scene_label": scene_label,
            "scene_summary": scene_summary,
            "dominant_modality": dominant_modality,
            "body_coherence_score": round(
                _clamp(
                    _body_coherence_score(request.modality_salience, request.drift_score) - 0.06,
                    0.0,
                    1.0,
                ),
                3,
            ),
            "perception_gate": _perception_gate(request.affect_guard),
            "salience_map": {
                key: round(value, 3) for key, value in request.modality_salience.items()
            },
            "rationale": [
                "collapse-to-continuity-safe-scene",
                "avoid-raw-sensory-surface-in-fallback",
            ],
        }


class PerceptionService:
    """Profile-driven router for deterministic scene encoding and qualia handoff."""

    def __init__(
        self,
        profile: CognitiveProfile,
        backends: Sequence[PerceptionBackend],
    ) -> None:
        self.profile = profile
        self._backends = {backend.backend_id: backend for backend in backends}

    @staticmethod
    def _validate_range(name: str, value: float, minimum: float, maximum: float) -> None:
        if not minimum <= value <= maximum:
            raise ValueError(f"{name} must be between {minimum} and {maximum}")

    def profile_snapshot(self) -> Dict[str, Any]:
        return {
            "schema_version": PERCEPTION_SCHEMA_VERSION,
            "policy_id": PERCEPTION_POLICY_ID,
            "primary": self.profile.primary,
            "fallback": list(self.profile.fallback),
            "safe_scenes": list(PERCEPTION_SAFE_SCENES),
            "qualia_handoff_required": True,
            "body_coherence_floor": 0.6,
            "failover_mode": "single-switch",
        }

    def set_backend_health(self, backend_id: str, healthy: bool) -> None:
        self._backends[backend_id].set_health(healthy)

    def run(
        self,
        request: PerceptionRequest,
        *,
        previous_frame: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        self._validate_request(request)
        if previous_frame is not None and not self.validate_frame(dict(previous_frame))["ok"]:
            raise ValueError("previous_frame must satisfy perception_frame validation")

        attempted: List[str] = []
        failures: List[str] = []
        order = [self.profile.primary] + list(self.profile.fallback)

        for backend_id in order:
            attempted.append(backend_id)
            backend = self._backends[backend_id]
            try:
                encoded = backend.encode(request, previous_frame=previous_frame)
            except BackendUnavailableError as exc:
                failures.append(str(exc))
                continue

            degraded = backend_id != self.profile.primary
            frame = self._build_frame(
                request,
                encoded,
                attempted_backends=attempted,
                failures=failures,
                degraded=degraded,
                previous_frame=previous_frame,
            )
            shift = self._build_shift(frame)
            return {
                "profile": self.profile_snapshot(),
                "attempted_backends": attempted,
                "selected_backend": backend_id,
                "degraded": degraded,
                "failures": failures,
                "frame": frame,
                "shift": shift,
            }

        raise BackendUnavailableError(
            "all perception backends unavailable: " + ", ".join(attempted)
        )

    def validate_frame(self, frame: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        if frame.get("kind") != "perception_frame":
            errors.append("kind must equal 'perception_frame'")
        if frame.get("schema_version") != PERCEPTION_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {PERCEPTION_SCHEMA_VERSION}")
        if frame.get("policy") != self.profile_snapshot():
            errors.append("policy must equal profile snapshot")
        if frame.get("backend_id") not in self._backends:
            errors.append("backend_id must reference a configured backend")
        if frame.get("affect_guard") not in PERCEPTION_ALLOWED_GUARDS:
            errors.append("affect_guard must be nominal, observe, or sandbox-notify")
        if not isinstance(frame.get("detected_entities"), list) or not frame["detected_entities"]:
            errors.append("detected_entities must be a non-empty list")
        if frame.get("dominant_modality") not in PERCEPTION_MODALITIES:
            errors.append("dominant_modality must be one of the supported modalities")
        salience_map = frame.get("salience_map")
        if not isinstance(salience_map, Mapping):
            errors.append("salience_map must be a mapping")
        else:
            expected_modalities = set(PERCEPTION_MODALITIES)
            if set(salience_map) != expected_modalities:
                errors.append("salience_map must include all supported modalities")
        body_coherence_score = frame.get("body_coherence_score")
        if not isinstance(body_coherence_score, (int, float)) or not 0.0 <= body_coherence_score <= 1.0:
            errors.append("body_coherence_score must be between 0.0 and 1.0")
        qualia_binding_ref = frame.get("qualia_binding_ref")
        if not isinstance(qualia_binding_ref, str) or not qualia_binding_ref.startswith("qualia://tick/"):
            errors.append("qualia_binding_ref must start with qualia://tick/")
        scene_label = frame.get("scene_label")
        if not isinstance(scene_label, str) or not scene_label.strip():
            errors.append("scene_label must be a non-empty string")

        guard_aligned = frame.get("perception_gate") == _perception_gate(str(frame.get("affect_guard")))
        if not guard_aligned:
            errors.append("perception_gate must align with affect_guard")
        if frame.get("affect_guard") != "nominal" and scene_label not in PERCEPTION_SAFE_SCENES:
            errors.append("non-nominal affect_guard must select one of the fixed safe scenes")

        continuity_guard = frame.get("continuity_guard")
        if not isinstance(continuity_guard, Mapping):
            errors.append("continuity_guard must be a mapping")
        else:
            attempted_backends = continuity_guard.get("attempted_backends")
            if not isinstance(attempted_backends, list) or not attempted_backends:
                errors.append("continuity_guard.attempted_backends must be a non-empty list")
            if "body_coherence_preserved" not in continuity_guard:
                errors.append("continuity_guard must include body_coherence_preserved")

        digest = frame.get("digest")
        if not isinstance(digest, str) or len(digest) != 64:
            errors.append("digest must be a sha256 hex string")

        return {
            "ok": not errors,
            "selected_backend": frame.get("backend_id"),
            "scene_label": scene_label,
            "guard_aligned": guard_aligned,
            "body_coherence_preserved": bool(
                isinstance(continuity_guard, Mapping)
                and continuity_guard.get("body_coherence_preserved")
            ),
            "errors": errors,
        }

    def validate_shift(self, shift: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        if shift.get("kind") != "perception_shift":
            errors.append("kind must equal 'perception_shift'")
        if shift.get("schema_version") != PERCEPTION_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {PERCEPTION_SCHEMA_VERSION}")
        if shift.get("policy_id") != PERCEPTION_POLICY_ID:
            errors.append(f"policy_id must equal {PERCEPTION_POLICY_ID}")
        if shift.get("selected_backend") not in self._backends:
            errors.append("selected_backend must reference a configured backend")
        if shift.get("affect_guard") not in PERCEPTION_ALLOWED_GUARDS:
            errors.append("affect_guard must be nominal, observe, or sandbox-notify")
        if shift.get("dominant_modality") not in PERCEPTION_MODALITIES:
            errors.append("dominant_modality must be one of the supported modalities")
        if not isinstance(shift.get("attempted_backends"), list) or not shift["attempted_backends"]:
            errors.append("attempted_backends must be a non-empty list")
        if shift.get("affect_guard") != "nominal" and shift.get("scene_label") not in PERCEPTION_SAFE_SCENES:
            errors.append("non-nominal affect_guard must keep scene_label inside the safe scene set")
        if shift.get("safe_summary_only") is not True:
            errors.append("safe_summary_only must be true")
        qualia_binding_ref = shift.get("qualia_binding_ref")
        if not isinstance(qualia_binding_ref, str) or not qualia_binding_ref.startswith("qualia://tick/"):
            errors.append("qualia_binding_ref must start with qualia://tick/")
        body_coherence_preserved = bool(shift.get("body_coherence_preserved"))
        guard_aligned = shift.get("scene_label") in PERCEPTION_SAFE_SCENES if shift.get("affect_guard") != "nominal" else True

        return {
            "ok": not errors,
            "selected_backend": shift.get("selected_backend"),
            "scene_label": shift.get("scene_label"),
            "guard_aligned": guard_aligned,
            "body_coherence_preserved": body_coherence_preserved,
            "errors": errors,
        }

    def _build_frame(
        self,
        request: PerceptionRequest,
        encoded: Mapping[str, Any],
        *,
        attempted_backends: Sequence[str],
        failures: Sequence[str],
        degraded: bool,
        previous_frame: Mapping[str, Any] | None,
    ) -> Dict[str, Any]:
        previous_frame_id = previous_frame.get("frame_id") if previous_frame is not None else None
        previous_backend_id = previous_frame.get("backend_id") if previous_frame is not None else None
        previous_scene_label = previous_frame.get("scene_label") if previous_frame is not None else None
        body_coherence_score = float(encoded["body_coherence_score"])
        payload = {
            "kind": "perception_frame",
            "schema_version": PERCEPTION_SCHEMA_VERSION,
            "policy": self.profile_snapshot(),
            "frame_id": new_id("perception-frame"),
            "generated_at": utc_now_iso(),
            "backend_id": self._require_backend_id(str(encoded["dominant_modality"]), attempted_backends[-1]),
            "source_tick": request.to_source_tick(),
            "sensory_stream_ref": request.sensory_stream_ref,
            "world_state_ref": request.world_state_ref,
            "body_anchor_ref": request.body_anchor_ref,
            "affect_guard": request.affect_guard,
            "detected_entities": _normalize_labels(request.detected_entities, limit=PERCEPTION_MAX_ENTITIES),
            "salient_cues": [cue.to_dict() for cue in request.memory_cues],
            "scene_label": encoded["scene_label"],
            "scene_summary": encoded["scene_summary"],
            "dominant_modality": encoded["dominant_modality"],
            "salience_map": dict(encoded["salience_map"]),
            "qualia_binding_ref": f"qualia://tick/{request.tick_id}",
            "body_coherence_score": round(body_coherence_score, 3),
            "perception_gate": encoded["perception_gate"],
            "degraded": degraded,
            "continuity_guard": {
                "previous_frame_id": previous_frame_id,
                "previous_backend_id": previous_backend_id,
                "previous_scene_label": previous_scene_label,
                "attempted_backends": list(attempted_backends),
                "failures": list(failures),
                "body_coherence_preserved": body_coherence_score >= self.profile_snapshot()["body_coherence_floor"],
                "shifted": previous_scene_label != encoded["scene_label"],
                "rationale": list(encoded["rationale"]),
            },
        }
        payload["backend_id"] = attempted_backends[-1]
        payload["digest"] = sha256_text(canonical_json(_perception_digest_payload(payload)))
        return payload

    def _build_shift(self, frame: Mapping[str, Any]) -> Dict[str, Any]:
        continuity_guard = dict(frame["continuity_guard"])
        payload = {
            "kind": "perception_shift",
            "schema_version": PERCEPTION_SCHEMA_VERSION,
            "shift_id": new_id("perception-shift"),
            "policy_id": PERCEPTION_POLICY_ID,
            "frame_ref": frame["frame_id"],
            "selected_backend": frame["backend_id"],
            "attempted_backends": list(continuity_guard["attempted_backends"]),
            "degraded": frame["degraded"],
            "previous_frame_id": continuity_guard["previous_frame_id"],
            "previous_scene_label": continuity_guard["previous_scene_label"],
            "scene_label": frame["scene_label"],
            "dominant_modality": frame["dominant_modality"],
            "affect_guard": frame["affect_guard"],
            "qualia_binding_ref": frame["qualia_binding_ref"],
            "body_coherence_preserved": continuity_guard["body_coherence_preserved"],
            "safe_summary_only": True,
            "failures": list(continuity_guard["failures"]),
            "recorded_at": utc_now_iso(),
        }
        payload["digest"] = sha256_text(canonical_json(_shift_digest_payload(payload)))
        return payload

    def _validate_request(self, request: PerceptionRequest) -> None:
        if request.affect_guard not in PERCEPTION_ALLOWED_GUARDS:
            raise ValueError("affect_guard must be nominal, observe, or sandbox-notify")
        if not request.summary.strip():
            raise ValueError("summary must not be empty")
        if not request.sensory_stream_ref.strip():
            raise ValueError("sensory_stream_ref must not be empty")
        if not request.world_state_ref.strip():
            raise ValueError("world_state_ref must not be empty")
        if not request.body_anchor_ref.strip():
            raise ValueError("body_anchor_ref must not be empty")
        for modality in PERCEPTION_MODALITIES:
            if modality not in request.modality_salience:
                raise ValueError(f"modality_salience must include {modality}")
            self._validate_range(modality, float(request.modality_salience[modality]), 0.0, 1.0)
        self._validate_range("drift_score", request.drift_score, 0.0, 1.0)
        detected_entities = _normalize_labels(request.detected_entities, limit=PERCEPTION_MAX_ENTITIES)
        if not detected_entities:
            raise ValueError("detected_entities must contain at least 1 non-empty label")

    def _require_backend_id(self, dominant_modality: str, backend_id: str) -> str:
        _ = dominant_modality
        if backend_id not in self._backends:
            raise ValueError(f"unsupported backend: {backend_id}")
        return backend_id

