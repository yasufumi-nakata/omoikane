"""Minimal L3 imagination backends with deterministic failover and bounded IMC/WMS handoff."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from .reasoning import BackendUnavailableError, CognitiveProfile

IMAGINATION_SCHEMA_VERSION = "1.0.0"
IMAGINATION_POLICY_ID = "bounded-counterfactual-handoff-v1"
IMAGINATION_ALLOWED_GUARDS = {"nominal", "observe", "sandbox-notify"}
IMAGINATION_ALLOWED_WMS_MODES = {"shared_reality", "private_reality", "mixed"}
IMAGINATION_ALLOWED_HANDOFF_MODES = {"co_imagination", "local-preview", "private-sandbox"}
IMAGINATION_ALLOWED_TOPOLOGIES = {
    "co-authored-scene",
    "guardian-reviewed-scene",
    "local-simulation",
}
IMAGINATION_MAX_SCENE_OBJECTS = 5


def _normalize_scene_objects(values: Sequence[str]) -> List[str]:
    ordered: List[str] = []
    seen = set()
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)
    return ordered[:IMAGINATION_MAX_SCENE_OBJECTS]


def _scene_digest_payload(scene: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": scene["schema_version"],
        "policy": scene["policy"],
        "backend_id": scene["backend_id"],
        "source_tick": scene["source_tick"],
        "memory_cues": scene["memory_cues"],
        "scene_summary": scene["scene_summary"],
        "scene_objects": scene["scene_objects"],
        "counterfactual_axes": scene["counterfactual_axes"],
        "horizon_ms": scene["horizon_ms"],
        "handoff": scene["handoff"],
        "degraded": scene["degraded"],
        "continuity_guard": scene["continuity_guard"],
    }


def _shift_digest_payload(shift: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": shift["schema_version"],
        "policy_id": shift["policy_id"],
        "scene_ref": shift["scene_ref"],
        "selected_backend": shift["selected_backend"],
        "attempted_backends": shift["attempted_backends"],
        "degraded": shift["degraded"],
        "previous_scene_id": shift["previous_scene_id"],
        "previous_focus": shift["previous_focus"],
        "handoff_mode": shift["handoff_mode"],
        "wms_mode": shift["wms_mode"],
        "affect_guard": shift["affect_guard"],
        "co_imagination_ready": shift["co_imagination_ready"],
        "guard_aligned": shift["guard_aligned"],
        "failures": shift["failures"],
    }


@dataclass(frozen=True)
class ImaginationCue:
    """Compact cue that biases scene composition toward one motif."""

    cue_id: str
    motif: str
    weight: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cue_id": self.cue_id,
            "motif": self.motif,
            "weight": round(self.weight, 3),
        }


@dataclass(frozen=True)
class ImaginationRequest:
    """Single imagination request derived from focus, affect, and bounded collaboration state."""

    tick_id: int
    summary: str
    seed_prompt: str
    attention_focus: str
    affect_guard: str
    world_mode_preference: str
    continuity_pressure: float
    council_witnessed: bool
    memory_cues: List[ImaginationCue] = field(default_factory=list)

    def to_source_tick(self) -> Dict[str, Any]:
        return {
            "tick_id": self.tick_id,
            "summary": self.summary,
            "seed_prompt": self.seed_prompt,
            "attention_focus": self.attention_focus,
            "affect_guard": self.affect_guard,
            "world_mode_preference": self.world_mode_preference,
            "continuity_pressure": round(self.continuity_pressure, 3),
            "council_witnessed": self.council_witnessed,
        }


class ImaginationBackend:
    """Base class for deterministic imagination backends."""

    def __init__(self, backend_id: str, *, healthy: bool = True) -> None:
        self.backend_id = backend_id
        self._healthy = healthy

    def set_health(self, healthy: bool) -> None:
        self._healthy = healthy

    def compose(
        self,
        request: ImaginationRequest,
        *,
        previous_scene: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if not self._healthy:
            raise BackendUnavailableError(f"{self.backend_id} is unavailable")
        return self._compose(request, previous_scene=previous_scene)

    def _compose(
        self,
        request: ImaginationRequest,
        *,
        previous_scene: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError


class CounterfactualSceneBackend(ImaginationBackend):
    """Primary backend that creates one bounded scene and exposes a safe co-imagination handoff."""

    def _compose(
        self,
        request: ImaginationRequest,
        *,
        previous_scene: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        cue_motifs = [cue.motif for cue in request.memory_cues]
        scene_objects = _normalize_scene_objects(
            [
                request.attention_focus,
                "continuity-ledger",
                *cue_motifs,
                "shared-witness",
            ]
        )
        counterfactual_axes = _normalize_scene_objects(
            [request.seed_prompt, request.attention_focus, *cue_motifs]
        )[:3]
        rationale = ["compose-bounded-counterfactual-scene", "respect-attention-focus"]

        if (
            request.affect_guard == "nominal"
            and request.council_witnessed
            and request.world_mode_preference in {"shared_reality", "mixed"}
        ):
            handoff_mode = "co_imagination"
            wms_mode = request.world_mode_preference
            share_topology = "co-authored-scene"
            co_ready = True
            horizon_ms = 90_000 if request.world_mode_preference == "shared_reality" else 75_000
            rationale.append("offer-council-witnessed-co-imagination")
        elif request.affect_guard == "nominal":
            handoff_mode = "local-preview"
            wms_mode = "private_reality"
            share_topology = "guardian-reviewed-scene"
            co_ready = False
            horizon_ms = 55_000
            rationale.append("retain-local-preview-without-shareable-world-mode")
        elif request.affect_guard == "observe":
            handoff_mode = "local-preview"
            wms_mode = "private_reality"
            share_topology = "guardian-reviewed-scene"
            co_ready = False
            horizon_ms = 60_000
            rationale.append("reduce-to-guardian-reviewed-preview")
        else:
            handoff_mode = "private-sandbox"
            wms_mode = "private_reality"
            share_topology = "local-simulation"
            co_ready = False
            horizon_ms = 30_000
            rationale.append("contain-scene-inside-private-sandbox")

        return {
            "backend_id": self.backend_id,
            "scene_summary": (
                f"'{request.seed_prompt}' を軸に、{request.attention_focus} と "
                f"{', '.join(scene_objects[:2])} を結ぶ bounded rehearsal scene"
            ),
            "scene_objects": scene_objects,
            "counterfactual_axes": counterfactual_axes,
            "horizon_ms": horizon_ms,
            "handoff": {
                "mode": handoff_mode,
                "wms_mode": wms_mode,
                "share_topology": share_topology,
                "council_witness_required": handoff_mode == "co_imagination",
                "council_witnessed": request.council_witnessed,
                "co_imagination_ready": co_ready,
            },
            "rationale": rationale,
        }


class ContinuitySceneGuardBackend(ImaginationBackend):
    """Fallback backend that collapses imagination into a private continuity-safe rehearsal."""

    def _compose(
        self,
        request: ImaginationRequest,
        *,
        previous_scene: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        previous_objects = list(previous_scene.get("scene_objects", [])) if previous_scene else []
        scene_objects = _normalize_scene_objects(
            [
                request.attention_focus,
                "guardian-review",
                "continuity-ledger",
                *previous_objects,
            ]
        )
        return {
            "backend_id": self.backend_id,
            "scene_summary": (
                f"'{request.seed_prompt}' を private rehearsal に縮退し、"
                "guardian review と continuity hold を優先した scene"
            ),
            "scene_objects": scene_objects,
            "counterfactual_axes": _normalize_scene_objects(
                [request.attention_focus, "guardian-review", "continuity-hold"]
            )[:3],
            "horizon_ms": 25_000 if request.affect_guard == "sandbox-notify" else 40_000,
            "handoff": {
                "mode": "private-sandbox",
                "wms_mode": "private_reality",
                "share_topology": "local-simulation",
                "council_witness_required": False,
                "council_witnessed": request.council_witnessed,
                "co_imagination_ready": False,
            },
            "rationale": [
                "collapse-to-private-rehearsal",
                "preserve-continuity-before-scene-sharing",
            ],
        }


class ImaginationService:
    """Profile-driven imagination router with bounded co-imagination handoff semantics."""

    def __init__(
        self,
        profile: CognitiveProfile,
        backends: Sequence[ImaginationBackend],
    ) -> None:
        self.profile = profile
        self._backends = {backend.backend_id: backend for backend in backends}

    @staticmethod
    def _validate_range(name: str, value: float, minimum: float, maximum: float) -> None:
        if not minimum <= value <= maximum:
            raise ValueError(f"{name} must be between {minimum} and {maximum}")

    def profile_snapshot(self) -> Dict[str, Any]:
        return {
            "schema_version": IMAGINATION_SCHEMA_VERSION,
            "policy_id": IMAGINATION_POLICY_ID,
            "primary": self.profile.primary,
            "fallback": list(self.profile.fallback),
            "max_scene_objects": IMAGINATION_MAX_SCENE_OBJECTS,
            "requires_council_witness_for_co_imagination": True,
            "degrade_to_private_reality": True,
            "failover_mode": "single-switch",
        }

    def set_backend_health(self, backend_id: str, healthy: bool) -> None:
        self._backends[backend_id].set_health(healthy)

    def run(
        self,
        request: ImaginationRequest,
        *,
        previous_scene: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        self._validate_request(request)
        if previous_scene is not None and not self.validate_scene(dict(previous_scene))["ok"]:
            raise ValueError("previous_scene must satisfy imagination_scene validation")

        attempted: List[str] = []
        failures: List[str] = []
        order = [self.profile.primary] + list(self.profile.fallback)

        for backend_id in order:
            attempted.append(backend_id)
            backend = self._backends[backend_id]
            try:
                composed = backend.compose(request, previous_scene=previous_scene)
            except BackendUnavailableError as exc:
                failures.append(str(exc))
                continue

            degraded = backend_id != self.profile.primary
            scene = self._build_scene(
                request,
                composed,
                attempted_backends=attempted,
                failures=failures,
                degraded=degraded,
                previous_scene=previous_scene,
            )
            shift = self._build_shift(scene, attempted, failures)
            return {
                "profile": self.profile_snapshot(),
                "attempted_backends": attempted,
                "selected_backend": backend_id,
                "degraded": degraded,
                "scene": scene,
                "shift": shift,
                "failures": failures,
            }

        raise BackendUnavailableError("all imagination backends unavailable: " + ", ".join(attempted))

    def validate_scene(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []

        if scene.get("kind") != "imagination_scene":
            errors.append("kind must equal 'imagination_scene'")
        if scene.get("schema_version") != IMAGINATION_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {IMAGINATION_SCHEMA_VERSION}")
        if scene.get("policy") != self.profile_snapshot():
            errors.append("policy must equal imagination profile snapshot")
        if scene.get("backend_id") not in self._backends:
            errors.append("backend_id must reference a registered backend")
        if not isinstance(scene.get("source_tick"), dict):
            errors.append("source_tick must be an object")
        else:
            source_tick = scene["source_tick"]
            if source_tick.get("affect_guard") not in IMAGINATION_ALLOWED_GUARDS:
                errors.append(f"affect_guard must be one of {sorted(IMAGINATION_ALLOWED_GUARDS)!r}")
            if source_tick.get("world_mode_preference") not in IMAGINATION_ALLOWED_WMS_MODES:
                errors.append(
                    f"world_mode_preference must be one of {sorted(IMAGINATION_ALLOWED_WMS_MODES)!r}"
                )
            continuity_pressure = source_tick.get("continuity_pressure")
            if not isinstance(continuity_pressure, (float, int)):
                errors.append("continuity_pressure must be a number")
            elif not 0.0 <= float(continuity_pressure) <= 1.0:
                errors.append("continuity_pressure must be between 0.0 and 1.0")
        if not isinstance(scene.get("memory_cues"), list):
            errors.append("memory_cues must be an array")
        if not isinstance(scene.get("scene_objects"), list) or not scene["scene_objects"]:
            errors.append("scene_objects must be a non-empty array")
        elif len(scene["scene_objects"]) > IMAGINATION_MAX_SCENE_OBJECTS:
            errors.append(f"scene_objects must contain at most {IMAGINATION_MAX_SCENE_OBJECTS} items")
        if not isinstance(scene.get("counterfactual_axes"), list) or not scene["counterfactual_axes"]:
            errors.append("counterfactual_axes must be a non-empty array")
        handoff = scene.get("handoff")
        if not isinstance(handoff, dict):
            errors.append("handoff must be an object")
        else:
            if handoff.get("mode") not in IMAGINATION_ALLOWED_HANDOFF_MODES:
                errors.append(
                    f"handoff.mode must be one of {sorted(IMAGINATION_ALLOWED_HANDOFF_MODES)!r}"
                )
            if handoff.get("wms_mode") not in IMAGINATION_ALLOWED_WMS_MODES:
                errors.append(f"handoff.wms_mode must be one of {sorted(IMAGINATION_ALLOWED_WMS_MODES)!r}")
            if handoff.get("share_topology") not in IMAGINATION_ALLOWED_TOPOLOGIES:
                errors.append(
                    f"handoff.share_topology must be one of {sorted(IMAGINATION_ALLOWED_TOPOLOGIES)!r}"
                )
            if not isinstance(handoff.get("co_imagination_ready"), bool):
                errors.append("handoff.co_imagination_ready must be a boolean")

        continuity_guard = scene.get("continuity_guard")
        if not isinstance(continuity_guard, dict):
            errors.append("continuity_guard must be an object")
        else:
            if not isinstance(continuity_guard.get("attempted_backends"), list) or not continuity_guard[
                "attempted_backends"
            ]:
                errors.append("continuity_guard.attempted_backends must be a non-empty array")
            if not isinstance(continuity_guard.get("guard_aligned"), bool):
                errors.append("continuity_guard.guard_aligned must be boolean")
            if not isinstance(continuity_guard.get("preserved_focus"), bool):
                errors.append("continuity_guard.preserved_focus must be boolean")

        digest = scene.get("digest")
        if not isinstance(digest, str) or len(digest) != 64:
            errors.append("digest must be a sha256 hex string")
        elif digest != sha256_text(canonical_json(_scene_digest_payload(scene))):
            errors.append("digest must match imagination scene payload")

        guard_aligned = self._is_guard_aligned(scene)
        if not guard_aligned:
            errors.append("scene handoff must align with affect guard and council witness policy")

        return {
            "ok": not errors,
            "selected_backend": scene.get("backend_id"),
            "handoff_mode": handoff.get("mode") if isinstance(handoff, dict) else None,
            "guard_aligned": guard_aligned,
            "co_imagination_ready": handoff.get("co_imagination_ready") if isinstance(handoff, dict) else False,
            "errors": errors,
        }

    def validate_shift(self, shift: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []

        if shift.get("kind") != "imagination_shift":
            errors.append("kind must equal 'imagination_shift'")
        if shift.get("schema_version") != IMAGINATION_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {IMAGINATION_SCHEMA_VERSION}")
        if shift.get("policy_id") != IMAGINATION_POLICY_ID:
            errors.append(f"policy_id must equal {IMAGINATION_POLICY_ID}")
        if shift.get("selected_backend") not in self._backends:
            errors.append("selected_backend must reference a registered backend")
        if shift.get("handoff_mode") not in IMAGINATION_ALLOWED_HANDOFF_MODES:
            errors.append(f"handoff_mode must be one of {sorted(IMAGINATION_ALLOWED_HANDOFF_MODES)!r}")
        if shift.get("wms_mode") not in IMAGINATION_ALLOWED_WMS_MODES:
            errors.append(f"wms_mode must be one of {sorted(IMAGINATION_ALLOWED_WMS_MODES)!r}")
        if shift.get("affect_guard") not in IMAGINATION_ALLOWED_GUARDS:
            errors.append(f"affect_guard must be one of {sorted(IMAGINATION_ALLOWED_GUARDS)!r}")
        if not isinstance(shift.get("co_imagination_ready"), bool):
            errors.append("co_imagination_ready must be boolean")
        if not isinstance(shift.get("guard_aligned"), bool):
            errors.append("guard_aligned must be boolean")
        if not isinstance(shift.get("attempted_backends"), list) or not shift["attempted_backends"]:
            errors.append("attempted_backends must be a non-empty array")

        digest = shift.get("digest")
        if not isinstance(digest, str) or len(digest) != 64:
            errors.append("digest must be a sha256 hex string")
        elif digest != sha256_text(canonical_json(_shift_digest_payload(shift))):
            errors.append("digest must match imagination shift payload")

        if shift.get("co_imagination_ready") and shift.get("handoff_mode") != "co_imagination":
            errors.append("co_imagination_ready implies handoff_mode=co_imagination")
        if shift.get("affect_guard") != "nominal" and shift.get("wms_mode") != "private_reality":
            errors.append("non-nominal affect guards must reduce imagination to private_reality")
        if shift.get("degraded") and shift.get("co_imagination_ready"):
            errors.append("degraded imagination may not remain co_imagination_ready")

        return {
            "ok": not errors,
            "selected_backend": shift.get("selected_backend"),
            "handoff_mode": shift.get("handoff_mode"),
            "guard_aligned": shift.get("guard_aligned", False),
            "co_imagination_ready": shift.get("co_imagination_ready", False),
            "errors": errors,
        }

    def _validate_request(self, request: ImaginationRequest) -> None:
        if request.tick_id < 0:
            raise ValueError("tick_id must be >= 0")
        if not request.summary.strip():
            raise ValueError("summary must be non-empty")
        if not request.seed_prompt.strip():
            raise ValueError("seed_prompt must be non-empty")
        if not request.attention_focus.strip():
            raise ValueError("attention_focus must be non-empty")
        if request.affect_guard not in IMAGINATION_ALLOWED_GUARDS:
            raise ValueError(f"affect_guard must be one of {sorted(IMAGINATION_ALLOWED_GUARDS)!r}")
        if request.world_mode_preference not in IMAGINATION_ALLOWED_WMS_MODES:
            raise ValueError(
                f"world_mode_preference must be one of {sorted(IMAGINATION_ALLOWED_WMS_MODES)!r}"
            )
        self._validate_range("continuity_pressure", request.continuity_pressure, 0.0, 1.0)
        for cue in request.memory_cues:
            if not cue.cue_id.strip():
                raise ValueError("cue_id must be non-empty")
            if not cue.motif.strip():
                raise ValueError("motif must be non-empty")
            self._validate_range("cue.weight", cue.weight, 0.0, 1.0)

    def _build_scene(
        self,
        request: ImaginationRequest,
        composed: Mapping[str, Any],
        *,
        attempted_backends: Sequence[str],
        failures: Sequence[str],
        degraded: bool,
        previous_scene: Mapping[str, Any] | None,
    ) -> Dict[str, Any]:
        continuity_guard = {
            "previous_scene_id": previous_scene.get("scene_id") if previous_scene else None,
            "previous_backend_id": previous_scene.get("backend_id") if previous_scene else None,
            "previous_focus": (
                previous_scene.get("source_tick", {}).get("attention_focus") if previous_scene else None
            ),
            "attempted_backends": list(attempted_backends),
            "failures": list(failures),
            "guard_aligned": self._guard_alignment_from_request(request, composed["handoff"]),
            "preserved_focus": (
                previous_scene is not None
                and previous_scene.get("source_tick", {}).get("attention_focus") == request.attention_focus
            ),
            "selected_safe_mode": composed["handoff"]["mode"],
            "rationale": list(composed["rationale"]),
        }
        scene = {
            "kind": "imagination_scene",
            "schema_version": IMAGINATION_SCHEMA_VERSION,
            "policy": self.profile_snapshot(),
            "scene_id": new_id("imagination-scene"),
            "generated_at": utc_now_iso(),
            "backend_id": composed["backend_id"],
            "source_tick": request.to_source_tick(),
            "memory_cues": [cue.to_dict() for cue in request.memory_cues],
            "scene_summary": composed["scene_summary"],
            "scene_objects": list(composed["scene_objects"]),
            "counterfactual_axes": list(composed["counterfactual_axes"]),
            "horizon_ms": composed["horizon_ms"],
            "handoff": {
                **dict(composed["handoff"]),
                "scene_digest": sha256_text(canonical_json(composed["scene_objects"])),
            },
            "degraded": degraded,
            "continuity_guard": continuity_guard,
        }
        scene["digest"] = sha256_text(canonical_json(_scene_digest_payload(scene)))
        return scene

    def _build_shift(
        self,
        scene: Mapping[str, Any],
        attempted_backends: Sequence[str],
        failures: Sequence[str],
    ) -> Dict[str, Any]:
        shift = {
            "kind": "imagination_shift",
            "schema_version": IMAGINATION_SCHEMA_VERSION,
            "policy_id": IMAGINATION_POLICY_ID,
            "scene_ref": scene["scene_id"],
            "selected_backend": scene["backend_id"],
            "attempted_backends": list(attempted_backends),
            "degraded": scene["degraded"],
            "previous_scene_id": scene["continuity_guard"]["previous_scene_id"],
            "previous_focus": scene["continuity_guard"]["previous_focus"],
            "handoff_mode": scene["handoff"]["mode"],
            "wms_mode": scene["handoff"]["wms_mode"],
            "affect_guard": scene["source_tick"]["affect_guard"],
            "co_imagination_ready": scene["handoff"]["co_imagination_ready"],
            "guard_aligned": scene["continuity_guard"]["guard_aligned"],
            "failures": list(failures),
        }
        shift["digest"] = sha256_text(canonical_json(_shift_digest_payload(shift)))
        return shift

    def _guard_alignment_from_request(
        self,
        request: ImaginationRequest,
        handoff: Mapping[str, Any],
    ) -> bool:
        if request.affect_guard != "nominal":
            return handoff["mode"] != "co_imagination" and handoff["wms_mode"] == "private_reality"
        if handoff["mode"] == "co_imagination":
            return request.council_witnessed and handoff["co_imagination_ready"]
        return True

    def _is_guard_aligned(self, scene: Mapping[str, Any]) -> bool:
        source_tick = scene["source_tick"]
        handoff = scene["handoff"]
        if source_tick["affect_guard"] != "nominal":
            return handoff["mode"] != "co_imagination" and handoff["wms_mode"] == "private_reality"
        if handoff["mode"] == "co_imagination":
            return (
                handoff["co_imagination_ready"]
                and handoff["council_witness_required"]
                and handoff["council_witnessed"]
                and source_tick["council_witnessed"]
                and handoff["wms_mode"] in {"shared_reality", "mixed"}
            )
        return True
