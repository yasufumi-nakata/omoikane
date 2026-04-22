"""Sensory Loopback reference model."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

SENSORY_LOOPBACK_SCHEMA_VERSION = "1.0"
DEFAULT_LOOPBACK_CHANNELS = ("visual", "auditory", "haptic")
SENSORY_LOOPBACK_ALLOWED_CHANNELS = set(DEFAULT_LOOPBACK_CHANNELS)
SENSORY_LOOPBACK_ALLOWED_SESSION_STATUS = {"active", "stabilizing", "held", "closed"}
SENSORY_LOOPBACK_ALLOWED_CLASSIFICATIONS = {
    "coherent",
    "attenuated",
    "held",
    "stabilized",
}
SENSORY_LOOPBACK_ALLOWED_DELIVERY_STATUS = {
    "delivered",
    "attenuate-to-safe-baseline",
    "guardian-hold",
    "stabilized",
}
SENSORY_LOOPBACK_ALLOWED_GUARDIAN_ACTIONS = {
    "continue-loopback",
    "stabilize-session",
    "freeze-loopback",
    "resume-loopback",
}
SENSORY_LOOPBACK_LATENCY_BUDGET_MS = 90.0
SENSORY_LOOPBACK_ATTENUATION_LATENCY_MS = 140.0
SENSORY_LOOPBACK_COHERENCE_DRIFT_THRESHOLD = 0.20
SENSORY_LOOPBACK_HOLD_DRIFT_THRESHOLD = 0.35
SENSORY_LOOPBACK_BODY_MAP_PROFILE = "avatar-proprioceptive-map-v1"
SENSORY_LOOPBACK_PROPRIOCEPTIVE_CALIBRATION_POLICY = "ref-bound-avatar-map-v1"
SENSORY_LOOPBACK_BODY_MAP_SEGMENTS = ("core", "left-hand", "right-hand", "stance")
SENSORY_LOOPBACK_BODY_MAP_SEGMENT_SET = set(SENSORY_LOOPBACK_BODY_MAP_SEGMENTS)
SENSORY_LOOPBACK_BODY_MAP_WEIGHTS = {
    "core": 0.4,
    "left-hand": 0.2,
    "right-hand": 0.2,
    "stance": 0.2,
}
SENSORY_LOOPBACK_ARTIFACT_FAMILY_POLICY = "multi-scene-artifact-family-v1"
SENSORY_LOOPBACK_ARTIFACT_FAMILY_STORAGE_POLICY = "family-digest+scene-summary-ref-only"
SENSORY_LOOPBACK_ARTIFACT_FAMILY_MAX_SCENES = 4


def _dedupe_preserve_order(values: Sequence[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


class SensoryLoopbackService:
    """Deterministic L6 sensory loopback boundary for bounded body-coherent feedback."""

    def __init__(self) -> None:
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.artifact_families: Dict[str, Dict[str, Any]] = {}

    def reference_profile(self) -> Dict[str, Any]:
        return {
            "schema_version": SENSORY_LOOPBACK_SCHEMA_VERSION,
            "channels": list(DEFAULT_LOOPBACK_CHANNELS),
            "latency_budget_ms": SENSORY_LOOPBACK_LATENCY_BUDGET_MS,
            "attenuation_latency_ms": SENSORY_LOOPBACK_ATTENUATION_LATENCY_MS,
            "coherence_drift_threshold": SENSORY_LOOPBACK_COHERENCE_DRIFT_THRESHOLD,
            "hold_drift_threshold": SENSORY_LOOPBACK_HOLD_DRIFT_THRESHOLD,
            "world_anchor_required": True,
            "body_schema_mode": "virtual-self-anchor-v1",
            "body_map_profile": SENSORY_LOOPBACK_BODY_MAP_PROFILE,
            "body_map_segments": list(SENSORY_LOOPBACK_BODY_MAP_SEGMENTS),
            "body_map_weights": dict(SENSORY_LOOPBACK_BODY_MAP_WEIGHTS),
            "proprioceptive_calibration_policy": SENSORY_LOOPBACK_PROPRIOCEPTIVE_CALIBRATION_POLICY,
            "artifact_storage_policy": "artifact-digest+summary-ref-only",
            "qualia_binding_policy": "surrogate-tick-ref",
            "artifact_family_policy": SENSORY_LOOPBACK_ARTIFACT_FAMILY_POLICY,
            "artifact_family_storage_policy": SENSORY_LOOPBACK_ARTIFACT_FAMILY_STORAGE_POLICY,
            "artifact_family_max_scenes": SENSORY_LOOPBACK_ARTIFACT_FAMILY_MAX_SCENES,
            "guardian_recovery_required": True,
        }

    def open_session(
        self,
        *,
        identity_id: str,
        world_state_ref: str,
        body_anchor_ref: str,
        avatar_body_map_ref: str,
        proprioceptive_calibration_ref: str,
        channels: Sequence[str] = DEFAULT_LOOPBACK_CHANNELS,
    ) -> Dict[str, Any]:
        normalized_identity = self._normalize_non_empty_string(identity_id, "identity_id")
        normalized_world_state = self._normalize_non_empty_string(world_state_ref, "world_state_ref")
        normalized_body_anchor = self._normalize_non_empty_string(body_anchor_ref, "body_anchor_ref")
        normalized_body_map_ref = self._normalize_non_empty_string(
            avatar_body_map_ref,
            "avatar_body_map_ref",
        )
        normalized_calibration_ref = self._normalize_non_empty_string(
            proprioceptive_calibration_ref,
            "proprioceptive_calibration_ref",
        )
        normalized_channels = self._normalize_channels(channels)
        body_map_anchor_refs = self._build_body_map_anchor_refs(normalized_body_anchor)
        baseline_alignment_ref = f"alignment://sensory-loopback/{new_id('sl-align')}"

        opened_at = utc_now_iso()
        session_id = new_id("sl")
        session = {
            "schema_version": SENSORY_LOOPBACK_SCHEMA_VERSION,
            "session_id": session_id,
            "identity_id": normalized_identity,
            "opened_at": opened_at,
            "updated_at": opened_at,
            "status": "active",
            "world_state_ref": normalized_world_state,
            "body_anchor_ref": normalized_body_anchor,
            "allowed_channels": normalized_channels,
            "latency_budget_ms": SENSORY_LOOPBACK_LATENCY_BUDGET_MS,
            "attenuation_latency_ms": SENSORY_LOOPBACK_ATTENUATION_LATENCY_MS,
            "coherence_drift_threshold": SENSORY_LOOPBACK_COHERENCE_DRIFT_THRESHOLD,
            "hold_drift_threshold": SENSORY_LOOPBACK_HOLD_DRIFT_THRESHOLD,
            "body_map_profile": SENSORY_LOOPBACK_BODY_MAP_PROFILE,
            "avatar_body_map_ref": normalized_body_map_ref,
            "body_map_anchor_refs": body_map_anchor_refs,
            "body_map_weights": dict(SENSORY_LOOPBACK_BODY_MAP_WEIGHTS),
            "proprioceptive_calibration_ref": normalized_calibration_ref,
            "safe_baseline_ref": "loopback://baseline/guardian-safe-v1",
            "artifact_storage_policy": "artifact-digest+summary-ref-only",
            "qualia_binding_policy": "surrogate-tick-ref",
            "delivery_count": 0,
            "last_delivery_id": "",
            "last_delivery_status": "none",
            "last_guardian_action": "none",
            "last_body_map_alignment_ref": baseline_alignment_ref,
            "last_body_map_alignment": self._default_body_map_alignment(),
            "artifact_family_count": 0,
            "last_artifact_family_id": "",
            "last_artifact_family_ref": "",
            "last_audit_event_ref": "",
        }
        self.sessions[session_id] = session
        return deepcopy(session)

    def deliver_bundle(
        self,
        session_id: str,
        *,
        scene_summary: str,
        artifact_refs: Mapping[str, str],
        latency_ms: float,
        body_map_alignment_ref: str,
        body_map_alignment: Mapping[str, float],
        attention_target: str,
        guardian_observed: bool,
        qualia_binding_ref: str = "",
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        if session["status"] != "active":
            raise ValueError("loopback session must be active before delivering bundles")

        summary = self._normalize_non_empty_string(scene_summary, "scene_summary")
        normalized_artifacts = self._normalize_artifact_refs(
            artifact_refs,
            allowed_channels=session["allowed_channels"],
        )
        if len(normalized_artifacts) < 2:
            raise ValueError("artifact_refs must cover at least 2 channels")
        normalized_latency = self._normalize_non_negative_number(latency_ms, "latency_ms")
        normalized_alignment_ref = self._normalize_non_empty_string(
            body_map_alignment_ref,
            "body_map_alignment_ref",
        )
        normalized_alignment = self._normalize_body_map_alignment(body_map_alignment)
        coherence_score = self._derive_body_coherence_score(normalized_alignment)
        normalized_attention_target = self._normalize_non_empty_string(
            attention_target,
            "attention_target",
        )
        normalized_qualia_ref = (
            self._normalize_non_empty_string(qualia_binding_ref, "qualia_binding_ref")
            if qualia_binding_ref
            else f"qualia://loopback/{new_id('sl-qualia')}"
        )
        if not isinstance(guardian_observed, bool):
            raise ValueError("guardian_observed must be a boolean")

        degraded = (
            coherence_score > session["coherence_drift_threshold"]
            or normalized_latency > session["latency_budget_ms"]
        )
        if degraded and not guardian_observed:
            raise PermissionError("guardian observation is required for degraded loopback bundles")

        if (
            coherence_score <= session["coherence_drift_threshold"]
            and normalized_latency <= session["latency_budget_ms"]
        ):
            classification = "coherent"
            delivery_status = "delivered"
            guardian_action = "continue-loopback"
            immersion_preserved = True
            safe_baseline_applied = False
            requires_council_review = False
            session_status = "active"
        elif (
            coherence_score <= session["hold_drift_threshold"]
            and normalized_latency <= session["attenuation_latency_ms"]
        ):
            classification = "attenuated"
            delivery_status = "attenuate-to-safe-baseline"
            guardian_action = "stabilize-session"
            immersion_preserved = False
            safe_baseline_applied = True
            requires_council_review = False
            session_status = "stabilizing"
        else:
            classification = "held"
            delivery_status = "guardian-hold"
            guardian_action = "freeze-loopback"
            immersion_preserved = False
            safe_baseline_applied = True
            requires_council_review = True
            session_status = "held"

        delivery_id = new_id("sl-delivery")
        recorded_at = utc_now_iso()
        artifact_digest = sha256_text(canonical_json(normalized_artifacts))
        receipt = {
            "schema_version": SENSORY_LOOPBACK_SCHEMA_VERSION,
            "delivery_id": delivery_id,
            "session_id": session_id,
            "recorded_at": recorded_at,
            "scene_summary": summary,
            "delivered_channels": list(normalized_artifacts),
            "artifact_refs": normalized_artifacts,
            "artifact_digest": artifact_digest,
            "latency_ms": round(normalized_latency, 3),
            "body_coherence_score": round(coherence_score, 3),
            "body_map_profile": session["body_map_profile"],
            "avatar_body_map_ref": session["avatar_body_map_ref"],
            "proprioceptive_calibration_ref": session["proprioceptive_calibration_ref"],
            "body_map_alignment_ref": normalized_alignment_ref,
            "body_map_alignment": normalized_alignment,
            "classification": classification,
            "delivery_status": delivery_status,
            "guardian_action": guardian_action,
            "immersion_preserved": immersion_preserved,
            "safe_baseline_applied": safe_baseline_applied,
            "requires_council_review": requires_council_review,
            "qualia_binding_ref": normalized_qualia_ref,
            "attention_target": normalized_attention_target,
            "audit_event_ref": f"ledger://sensory-loopback/{delivery_id}",
        }
        session["updated_at"] = recorded_at
        session["status"] = session_status
        session["delivery_count"] += 1
        session["last_delivery_id"] = delivery_id
        session["last_delivery_status"] = delivery_status
        session["last_guardian_action"] = guardian_action
        session["last_body_map_alignment_ref"] = normalized_alignment_ref
        session["last_body_map_alignment"] = normalized_alignment
        session["last_audit_event_ref"] = receipt["audit_event_ref"]
        return deepcopy(receipt)

    def stabilize(
        self,
        session_id: str,
        *,
        reason: str,
        restored_body_anchor_ref: str,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        if session["status"] not in {"stabilizing", "held"}:
            raise ValueError("stabilize requires a stabilizing or held loopback session")

        reason_text = self._normalize_non_empty_string(reason, "reason")
        restored_body_anchor = self._normalize_non_empty_string(
            restored_body_anchor_ref,
            "restored_body_anchor_ref",
        )
        delivery_id = new_id("sl-delivery")
        recorded_at = utc_now_iso()
        artifact_digest = sha256_text(canonical_json({}))
        restored_alignment_ref = f"alignment://sensory-loopback/{delivery_id}/restored"
        restored_alignment = self._default_body_map_alignment()
        receipt = {
            "schema_version": SENSORY_LOOPBACK_SCHEMA_VERSION,
            "delivery_id": delivery_id,
            "session_id": session_id,
            "recorded_at": recorded_at,
            "scene_summary": reason_text,
            "delivered_channels": [],
            "artifact_refs": {},
            "artifact_digest": artifact_digest,
            "latency_ms": 0.0,
            "body_coherence_score": 0.0,
            "body_map_profile": session["body_map_profile"],
            "avatar_body_map_ref": session["avatar_body_map_ref"],
            "proprioceptive_calibration_ref": session["proprioceptive_calibration_ref"],
            "body_map_alignment_ref": restored_alignment_ref,
            "body_map_alignment": restored_alignment,
            "classification": "stabilized",
            "delivery_status": "stabilized",
            "guardian_action": "resume-loopback",
            "immersion_preserved": True,
            "safe_baseline_applied": True,
            "requires_council_review": False,
            "qualia_binding_ref": f"qualia://loopback-stabilize/{delivery_id}",
            "attention_target": restored_body_anchor,
            "audit_event_ref": f"ledger://sensory-loopback/{delivery_id}",
        }
        session["updated_at"] = recorded_at
        session["status"] = "active"
        session["body_anchor_ref"] = restored_body_anchor
        session["body_map_anchor_refs"] = self._build_body_map_anchor_refs(restored_body_anchor)
        session["delivery_count"] += 1
        session["last_delivery_id"] = delivery_id
        session["last_delivery_status"] = "stabilized"
        session["last_guardian_action"] = "resume-loopback"
        session["last_body_map_alignment_ref"] = restored_alignment_ref
        session["last_body_map_alignment"] = restored_alignment
        session["last_audit_event_ref"] = receipt["audit_event_ref"]
        return deepcopy(receipt)

    def capture_artifact_family(
        self,
        session_id: str,
        *,
        family_label: str,
        receipts: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        normalized_label = self._normalize_non_empty_string(family_label, "family_label")
        if not isinstance(receipts, Sequence) or isinstance(receipts, (str, bytes)):
            raise ValueError("receipts must be a sequence of sensory loopback receipts")
        if len(receipts) < 2:
            raise ValueError("artifact families require at least 2 receipts")
        if len(receipts) > SENSORY_LOOPBACK_ARTIFACT_FAMILY_MAX_SCENES:
            raise ValueError(
                "artifact families may not exceed "
                f"{SENSORY_LOOPBACK_ARTIFACT_FAMILY_MAX_SCENES} receipts",
            )

        scene_summaries: List[Dict[str, Any]] = []
        delivery_ids: List[str] = []
        channels_observed: List[str] = []
        for index, receipt in enumerate(receipts):
            validation = self.validate_receipt(receipt)
            if not validation["ok"]:
                raise ValueError(
                    f"receipt at index {index} must satisfy sensory loopback receipt validation",
                )
            if receipt.get("session_id") != session_id:
                raise ValueError("all receipts must belong to the same sensory loopback session")
            delivery_id = self._normalize_non_empty_string(receipt.get("delivery_id"), "delivery_id")
            if delivery_id in delivery_ids:
                raise ValueError("artifact family receipts must have unique delivery_id values")

            delivered_channels = receipt.get("delivered_channels")
            if not isinstance(delivered_channels, list):
                raise ValueError("receipt.delivered_channels must be a list")
            normalized_channels = self._normalize_family_channels(delivered_channels)
            channels_observed.extend(normalized_channels)
            delivery_ids.append(delivery_id)
            scene_summaries.append(
                {
                    "delivery_id": delivery_id,
                    "scene_summary": self._normalize_non_empty_string(
                        receipt.get("scene_summary"),
                        "scene_summary",
                    ),
                    "delivered_channels": normalized_channels,
                    "classification": receipt["classification"],
                    "delivery_status": receipt["delivery_status"],
                    "guardian_action": receipt["guardian_action"],
                    "artifact_digest": self._normalize_non_empty_string(
                        receipt.get("artifact_digest"),
                        "artifact_digest",
                    ),
                    "body_coherence_score": self._normalize_score(
                        receipt.get("body_coherence_score"),
                        "body_coherence_score",
                    ),
                    "avatar_body_map_ref": self._normalize_non_empty_string(
                        receipt.get("avatar_body_map_ref"),
                        "avatar_body_map_ref",
                    ),
                    "proprioceptive_calibration_ref": self._normalize_non_empty_string(
                        receipt.get("proprioceptive_calibration_ref"),
                        "proprioceptive_calibration_ref",
                    ),
                    "body_map_alignment_ref": self._normalize_non_empty_string(
                        receipt.get("body_map_alignment_ref"),
                        "body_map_alignment_ref",
                    ),
                    "qualia_binding_ref": self._normalize_non_empty_string(
                        receipt.get("qualia_binding_ref"),
                        "qualia_binding_ref",
                    ),
                    "attention_target": self._normalize_non_empty_string(
                        receipt.get("attention_target"),
                        "attention_target",
                    ),
                    "safe_baseline_applied": bool(receipt.get("safe_baseline_applied")),
                    "requires_council_review": bool(receipt.get("requires_council_review")),
                }
            )

        family_id = new_id("sl-family")
        recorded_at = utc_now_iso()
        family_digest = self._artifact_family_digest(
            session_id=session_id,
            family_label=normalized_label,
            scene_summaries=scene_summaries,
            final_session_status=session["status"],
        )
        artifact_family = {
            "schema_version": SENSORY_LOOPBACK_SCHEMA_VERSION,
            "family_id": family_id,
            "family_ref": f"loopback-family://{family_id}",
            "session_id": session_id,
            "recorded_at": recorded_at,
            "family_label": normalized_label,
            "policy_id": SENSORY_LOOPBACK_ARTIFACT_FAMILY_POLICY,
            "scene_count": len(scene_summaries),
            "delivery_ids": delivery_ids,
            "channels_observed": _dedupe_preserve_order(channels_observed),
            "scene_summaries": scene_summaries,
            "guardian_intervention_count": sum(
                1 for scene in scene_summaries if scene["guardian_action"] != "continue-loopback"
            ),
            "stabilization_delivery_ids": [
                scene["delivery_id"]
                for scene in scene_summaries
                if scene["delivery_status"] == "stabilized"
            ],
            "final_session_status": session["status"],
            "artifact_storage_policy": SENSORY_LOOPBACK_ARTIFACT_FAMILY_STORAGE_POLICY,
            "family_digest": family_digest,
            "audit_event_ref": f"ledger://sensory-loopback-family/{family_id}",
        }
        self.artifact_families[family_id] = artifact_family
        session["updated_at"] = recorded_at
        session["artifact_family_count"] += 1
        session["last_artifact_family_id"] = family_id
        session["last_artifact_family_ref"] = artifact_family["family_ref"]
        session["last_audit_event_ref"] = artifact_family["audit_event_ref"]
        return deepcopy(artifact_family)

    def snapshot(self, session_id: str) -> Dict[str, Any]:
        return deepcopy(self._require_session(session_id))

    def snapshot_artifact_family(self, family_id: str) -> Dict[str, Any]:
        normalized_family_id = self._normalize_non_empty_string(family_id, "family_id")
        try:
            return deepcopy(self.artifact_families[normalized_family_id])
        except KeyError as exc:
            raise KeyError(
                f"unknown sensory loopback artifact family: {normalized_family_id}",
            ) from exc

    def validate_session(self, session: Mapping[str, Any]) -> Dict[str, Any]:
        if not isinstance(session, Mapping):
            raise ValueError("session must be a mapping")

        errors: List[str] = []
        self._check_non_empty_string(session.get("session_id"), "session_id", errors)
        self._check_non_empty_string(session.get("identity_id"), "identity_id", errors)
        self._check_non_empty_string(session.get("opened_at"), "opened_at", errors)
        self._check_non_empty_string(session.get("updated_at"), "updated_at", errors)
        self._check_non_empty_string(session.get("world_state_ref"), "world_state_ref", errors)
        self._check_non_empty_string(session.get("body_anchor_ref"), "body_anchor_ref", errors)
        if session.get("schema_version") != SENSORY_LOOPBACK_SCHEMA_VERSION:
            errors.append(f"schema_version must be {SENSORY_LOOPBACK_SCHEMA_VERSION}")

        status = session.get("status")
        if status not in SENSORY_LOOPBACK_ALLOWED_SESSION_STATUS:
            errors.append(
                f"status must be one of {sorted(SENSORY_LOOPBACK_ALLOWED_SESSION_STATUS)}",
            )

        channels = session.get("allowed_channels")
        if not isinstance(channels, list) or len(channels) < 2:
            errors.append("allowed_channels must be a list with at least 2 items")
        else:
            if len(channels) != len(set(channels)):
                errors.append("allowed_channels must be unique")
            invalid = sorted(set(channels) - SENSORY_LOOPBACK_ALLOWED_CHANNELS)
            if invalid:
                errors.append(f"allowed_channels contains unsupported values: {invalid}")

        if session.get("artifact_storage_policy") != "artifact-digest+summary-ref-only":
            errors.append("artifact_storage_policy must be artifact-digest+summary-ref-only")
        if session.get("qualia_binding_policy") != "surrogate-tick-ref":
            errors.append("qualia_binding_policy must be surrogate-tick-ref")
        if session.get("latency_budget_ms") != SENSORY_LOOPBACK_LATENCY_BUDGET_MS:
            errors.append(
                f"latency_budget_ms must be {SENSORY_LOOPBACK_LATENCY_BUDGET_MS}",
            )
        if session.get("attenuation_latency_ms") != SENSORY_LOOPBACK_ATTENUATION_LATENCY_MS:
            errors.append(
                f"attenuation_latency_ms must be {SENSORY_LOOPBACK_ATTENUATION_LATENCY_MS}",
            )
        if session.get("coherence_drift_threshold") != SENSORY_LOOPBACK_COHERENCE_DRIFT_THRESHOLD:
            errors.append(
                "coherence_drift_threshold must match the reference profile",
            )
        if session.get("hold_drift_threshold") != SENSORY_LOOPBACK_HOLD_DRIFT_THRESHOLD:
            errors.append("hold_drift_threshold must match the reference profile")
        if session.get("body_map_profile") != SENSORY_LOOPBACK_BODY_MAP_PROFILE:
            errors.append(f"body_map_profile must be {SENSORY_LOOPBACK_BODY_MAP_PROFILE}")
        self._check_non_empty_string(
            session.get("avatar_body_map_ref"),
            "avatar_body_map_ref",
            errors,
        )
        self._check_non_empty_string(
            session.get("proprioceptive_calibration_ref"),
            "proprioceptive_calibration_ref",
            errors,
        )
        body_map_anchor_refs = session.get("body_map_anchor_refs")
        if not self._mapping_has_exact_segment_keys(body_map_anchor_refs):
            errors.append("body_map_anchor_refs must cover the canonical avatar body map segments")
        else:
            for segment in SENSORY_LOOPBACK_BODY_MAP_SEGMENTS:
                self._check_non_empty_string(
                    body_map_anchor_refs.get(segment),
                    f"body_map_anchor_refs.{segment}",
                    errors,
                )
        body_map_weights = session.get("body_map_weights")
        if body_map_weights != SENSORY_LOOPBACK_BODY_MAP_WEIGHTS:
            errors.append("body_map_weights must match the reference avatar body map weights")
        self._check_non_empty_string(
            session.get("last_body_map_alignment_ref"),
            "last_body_map_alignment_ref",
            errors,
        )
        last_body_map_alignment = session.get("last_body_map_alignment")
        if not self._mapping_has_exact_segment_keys(last_body_map_alignment):
            errors.append("last_body_map_alignment must cover the canonical avatar body map segments")
        else:
            for segment in SENSORY_LOOPBACK_BODY_MAP_SEGMENTS:
                try:
                    self._normalize_score(
                        last_body_map_alignment.get(segment),
                        f"last_body_map_alignment.{segment}",
                    )
                except ValueError as exc:
                    errors.append(str(exc))

        delivery_count = session.get("delivery_count")
        if not isinstance(delivery_count, int) or delivery_count < 0:
            errors.append("delivery_count must be a non-negative integer")
        artifact_family_count = session.get("artifact_family_count")
        if not isinstance(artifact_family_count, int) or artifact_family_count < 0:
            errors.append("artifact_family_count must be a non-negative integer")
        if not isinstance(session.get("last_artifact_family_id"), str):
            errors.append("last_artifact_family_id must be a string")
        if not isinstance(session.get("last_artifact_family_ref"), str):
            errors.append("last_artifact_family_ref must be a string")

        return {
            "ok": not errors,
            "errors": errors,
            "channel_count": len(channels) if isinstance(channels, list) else 0,
            "artifact_digest_only": session.get("artifact_storage_policy")
            == "artifact-digest+summary-ref-only",
            "supports_body_stabilization": session.get("hold_drift_threshold")
            == SENSORY_LOOPBACK_HOLD_DRIFT_THRESHOLD,
            "world_anchor_bound": bool(session.get("world_state_ref")),
            "body_map_bound": bool(session.get("avatar_body_map_ref")),
            "proprioceptive_calibration_bound": bool(session.get("proprioceptive_calibration_ref")),
            "artifact_family_tracking_enabled": isinstance(session.get("last_artifact_family_ref"), str),
        }

    def validate_receipt(self, receipt: Mapping[str, Any]) -> Dict[str, Any]:
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")

        errors: List[str] = []
        self._check_non_empty_string(receipt.get("delivery_id"), "delivery_id", errors)
        self._check_non_empty_string(receipt.get("session_id"), "session_id", errors)
        self._check_non_empty_string(receipt.get("recorded_at"), "recorded_at", errors)
        self._check_non_empty_string(receipt.get("scene_summary"), "scene_summary", errors)
        self._check_non_empty_string(receipt.get("artifact_digest"), "artifact_digest", errors)
        self._check_non_empty_string(receipt.get("qualia_binding_ref"), "qualia_binding_ref", errors)
        self._check_non_empty_string(receipt.get("attention_target"), "attention_target", errors)
        self._check_non_empty_string(receipt.get("audit_event_ref"), "audit_event_ref", errors)
        if receipt.get("schema_version") != SENSORY_LOOPBACK_SCHEMA_VERSION:
            errors.append(f"schema_version must be {SENSORY_LOOPBACK_SCHEMA_VERSION}")

        classification = receipt.get("classification")
        if classification not in SENSORY_LOOPBACK_ALLOWED_CLASSIFICATIONS:
            errors.append(
                f"classification must be one of {sorted(SENSORY_LOOPBACK_ALLOWED_CLASSIFICATIONS)}",
            )
        delivery_status = receipt.get("delivery_status")
        if delivery_status not in SENSORY_LOOPBACK_ALLOWED_DELIVERY_STATUS:
            errors.append(
                f"delivery_status must be one of {sorted(SENSORY_LOOPBACK_ALLOWED_DELIVERY_STATUS)}",
            )
        guardian_action = receipt.get("guardian_action")
        if guardian_action not in SENSORY_LOOPBACK_ALLOWED_GUARDIAN_ACTIONS:
            errors.append(
                f"guardian_action must be one of {sorted(SENSORY_LOOPBACK_ALLOWED_GUARDIAN_ACTIONS)}",
            )

        delivered_channels = receipt.get("delivered_channels")
        if not isinstance(delivered_channels, list):
            errors.append("delivered_channels must be a list")
        else:
            invalid = sorted(set(delivered_channels) - SENSORY_LOOPBACK_ALLOWED_CHANNELS)
            if invalid:
                errors.append(f"delivered_channels contains unsupported values: {invalid}")

        artifact_refs = receipt.get("artifact_refs")
        if not isinstance(artifact_refs, Mapping):
            errors.append("artifact_refs must be a mapping")

        latency_ms = receipt.get("latency_ms")
        if not isinstance(latency_ms, (int, float)) or latency_ms < 0:
            errors.append("latency_ms must be a non-negative number")
        coherence_score = receipt.get("body_coherence_score")
        if not isinstance(coherence_score, (int, float)) or not 0 <= coherence_score <= 1:
            errors.append("body_coherence_score must be between 0 and 1")
        if receipt.get("body_map_profile") != SENSORY_LOOPBACK_BODY_MAP_PROFILE:
            errors.append(f"body_map_profile must be {SENSORY_LOOPBACK_BODY_MAP_PROFILE}")
        self._check_non_empty_string(
            receipt.get("avatar_body_map_ref"),
            "avatar_body_map_ref",
            errors,
        )
        self._check_non_empty_string(
            receipt.get("proprioceptive_calibration_ref"),
            "proprioceptive_calibration_ref",
            errors,
        )
        self._check_non_empty_string(
            receipt.get("body_map_alignment_ref"),
            "body_map_alignment_ref",
            errors,
        )
        body_map_alignment = receipt.get("body_map_alignment")
        if not self._mapping_has_exact_segment_keys(body_map_alignment):
            errors.append("body_map_alignment must cover the canonical avatar body map segments")
        else:
            normalized_alignment: Dict[str, float] | None = {}
            for segment in SENSORY_LOOPBACK_BODY_MAP_SEGMENTS:
                try:
                    normalized_alignment[segment] = self._normalize_score(
                        body_map_alignment.get(segment),
                        f"body_map_alignment.{segment}",
                    )
                except ValueError as exc:
                    errors.append(str(exc))
                    normalized_alignment = None
                    break
            if normalized_alignment is not None:
                expected_coherence_score = self._derive_body_coherence_score(normalized_alignment)
                if round(float(coherence_score), 3) != expected_coherence_score:
                    errors.append("body_coherence_score must match the weighted avatar body map drift")

        return {
            "ok": not errors,
            "errors": errors,
            "guardian_recoverable": delivery_status in {"attenuate-to-safe-baseline", "guardian-hold", "stabilized"},
            "immersion_preserved": bool(receipt.get("immersion_preserved")),
            "safe_baseline_applied": bool(receipt.get("safe_baseline_applied")),
            "body_map_bound": bool(receipt.get("avatar_body_map_ref")),
            "calibration_bound": bool(receipt.get("proprioceptive_calibration_ref")),
        }

    def validate_artifact_family(self, artifact_family: Mapping[str, Any]) -> Dict[str, Any]:
        if not isinstance(artifact_family, Mapping):
            raise ValueError("artifact_family must be a mapping")

        errors: List[str] = []
        self._check_non_empty_string(artifact_family.get("family_id"), "family_id", errors)
        self._check_non_empty_string(artifact_family.get("family_ref"), "family_ref", errors)
        self._check_non_empty_string(artifact_family.get("session_id"), "session_id", errors)
        self._check_non_empty_string(artifact_family.get("recorded_at"), "recorded_at", errors)
        self._check_non_empty_string(artifact_family.get("family_label"), "family_label", errors)
        self._check_non_empty_string(artifact_family.get("family_digest"), "family_digest", errors)
        self._check_non_empty_string(artifact_family.get("audit_event_ref"), "audit_event_ref", errors)
        if artifact_family.get("schema_version") != SENSORY_LOOPBACK_SCHEMA_VERSION:
            errors.append(f"schema_version must be {SENSORY_LOOPBACK_SCHEMA_VERSION}")
        if artifact_family.get("policy_id") != SENSORY_LOOPBACK_ARTIFACT_FAMILY_POLICY:
            errors.append(
                f"policy_id must be {SENSORY_LOOPBACK_ARTIFACT_FAMILY_POLICY}",
            )
        if (
            artifact_family.get("artifact_storage_policy")
            != SENSORY_LOOPBACK_ARTIFACT_FAMILY_STORAGE_POLICY
        ):
            errors.append(
                "artifact_storage_policy must be "
                f"{SENSORY_LOOPBACK_ARTIFACT_FAMILY_STORAGE_POLICY}",
            )

        scene_count = artifact_family.get("scene_count")
        if (
            not isinstance(scene_count, int)
            or scene_count < 2
            or scene_count > SENSORY_LOOPBACK_ARTIFACT_FAMILY_MAX_SCENES
        ):
            errors.append(
                "scene_count must be an integer between 2 and "
                f"{SENSORY_LOOPBACK_ARTIFACT_FAMILY_MAX_SCENES}",
            )

        delivery_ids = artifact_family.get("delivery_ids")
        if not isinstance(delivery_ids, list) or len(delivery_ids) != len(set(delivery_ids)):
            errors.append("delivery_ids must be a unique list")

        channels_observed = artifact_family.get("channels_observed")
        if not isinstance(channels_observed, list):
            errors.append("channels_observed must be a list")
        else:
            invalid = sorted(set(channels_observed) - SENSORY_LOOPBACK_ALLOWED_CHANNELS)
            if invalid:
                errors.append(f"channels_observed contains unsupported values: {invalid}")

        scene_summaries = artifact_family.get("scene_summaries")
        if not isinstance(scene_summaries, list):
            errors.append("scene_summaries must be a list")
            scene_summaries = []
        else:
            for index, scene in enumerate(scene_summaries):
                if not isinstance(scene, Mapping):
                    errors.append(f"scene_summaries[{index}] must be a mapping")
                    continue
                self._check_non_empty_string(scene.get("delivery_id"), f"scene_summaries[{index}].delivery_id", errors)
                self._check_non_empty_string(
                    scene.get("scene_summary"),
                    f"scene_summaries[{index}].scene_summary",
                    errors,
                )
                self._check_non_empty_string(
                    scene.get("artifact_digest"),
                    f"scene_summaries[{index}].artifact_digest",
                    errors,
                )
                coherence_score = scene.get("body_coherence_score")
                if not isinstance(coherence_score, (int, float)) or not 0 <= coherence_score <= 1:
                    errors.append(
                        f"scene_summaries[{index}].body_coherence_score must be between 0 and 1",
                    )
                self._check_non_empty_string(
                    scene.get("avatar_body_map_ref"),
                    f"scene_summaries[{index}].avatar_body_map_ref",
                    errors,
                )
                self._check_non_empty_string(
                    scene.get("proprioceptive_calibration_ref"),
                    f"scene_summaries[{index}].proprioceptive_calibration_ref",
                    errors,
                )
                self._check_non_empty_string(
                    scene.get("body_map_alignment_ref"),
                    f"scene_summaries[{index}].body_map_alignment_ref",
                    errors,
                )
                self._check_non_empty_string(
                    scene.get("qualia_binding_ref"),
                    f"scene_summaries[{index}].qualia_binding_ref",
                    errors,
                )
                self._check_non_empty_string(
                    scene.get("attention_target"),
                    f"scene_summaries[{index}].attention_target",
                    errors,
                )
                if scene.get("classification") not in SENSORY_LOOPBACK_ALLOWED_CLASSIFICATIONS:
                    errors.append(
                        f"scene_summaries[{index}].classification must be one of "
                        f"{sorted(SENSORY_LOOPBACK_ALLOWED_CLASSIFICATIONS)}",
                    )
                if scene.get("delivery_status") not in SENSORY_LOOPBACK_ALLOWED_DELIVERY_STATUS:
                    errors.append(
                        f"scene_summaries[{index}].delivery_status must be one of "
                        f"{sorted(SENSORY_LOOPBACK_ALLOWED_DELIVERY_STATUS)}",
                    )
                if scene.get("guardian_action") not in SENSORY_LOOPBACK_ALLOWED_GUARDIAN_ACTIONS:
                    errors.append(
                        f"scene_summaries[{index}].guardian_action must be one of "
                        f"{sorted(SENSORY_LOOPBACK_ALLOWED_GUARDIAN_ACTIONS)}",
                    )
                delivered_channels = scene.get("delivered_channels")
                if not isinstance(delivered_channels, list):
                    errors.append(f"scene_summaries[{index}].delivered_channels must be a list")
                else:
                    invalid = sorted(set(delivered_channels) - SENSORY_LOOPBACK_ALLOWED_CHANNELS)
                    if invalid:
                        errors.append(
                            f"scene_summaries[{index}].delivered_channels contains unsupported values: {invalid}",
                        )
                if not isinstance(scene.get("safe_baseline_applied"), bool):
                    errors.append(
                        f"scene_summaries[{index}].safe_baseline_applied must be a boolean",
                    )
                if not isinstance(scene.get("requires_council_review"), bool):
                    errors.append(
                        f"scene_summaries[{index}].requires_council_review must be a boolean",
                    )

        if isinstance(scene_count, int) and isinstance(scene_summaries, list) and scene_count != len(scene_summaries):
            errors.append("scene_count must equal len(scene_summaries)")
        if isinstance(scene_count, int) and isinstance(delivery_ids, list) and scene_count != len(delivery_ids):
            errors.append("scene_count must equal len(delivery_ids)")

        guardian_intervention_count = artifact_family.get("guardian_intervention_count")
        if not isinstance(guardian_intervention_count, int) or guardian_intervention_count < 0:
            errors.append("guardian_intervention_count must be a non-negative integer")
        elif isinstance(scene_summaries, list):
            expected_guardian_interventions = sum(
                1
                for scene in scene_summaries
                if isinstance(scene, Mapping) and scene.get("guardian_action") != "continue-loopback"
            )
            if guardian_intervention_count != expected_guardian_interventions:
                errors.append(
                    "guardian_intervention_count must match non-continue guardian actions",
                )

        stabilization_delivery_ids = artifact_family.get("stabilization_delivery_ids")
        if not isinstance(stabilization_delivery_ids, list):
            errors.append("stabilization_delivery_ids must be a list")
        elif isinstance(delivery_ids, list):
            missing = sorted(set(stabilization_delivery_ids) - set(delivery_ids))
            if missing:
                errors.append(
                    f"stabilization_delivery_ids must reference existing delivery_ids: {missing}",
                )

        final_session_status = artifact_family.get("final_session_status")
        if final_session_status not in SENSORY_LOOPBACK_ALLOWED_SESSION_STATUS:
            errors.append(
                "final_session_status must be one of "
                f"{sorted(SENSORY_LOOPBACK_ALLOWED_SESSION_STATUS)}",
            )

        expected_digest = self._artifact_family_digest(
            session_id=artifact_family.get("session_id"),
            family_label=artifact_family.get("family_label"),
            scene_summaries=scene_summaries if isinstance(scene_summaries, list) else [],
            final_session_status=artifact_family.get("final_session_status"),
        )
        if artifact_family.get("family_digest") != expected_digest:
            errors.append("family_digest must match the artifact family payload")

        return {
            "ok": not errors,
            "errors": errors,
            "multi_scene": isinstance(scene_summaries, list) and len(scene_summaries) >= 2,
            "family_digest_bound": artifact_family.get("family_digest") == expected_digest,
            "guardian_recovery_tracked": isinstance(stabilization_delivery_ids, list)
            and bool(stabilization_delivery_ids),
        }

    def _require_session(self, session_id: str) -> Dict[str, Any]:
        normalized_session_id = self._normalize_non_empty_string(session_id, "session_id")
        try:
            return self.sessions[normalized_session_id]
        except KeyError as exc:
            raise KeyError(f"unknown sensory loopback session: {normalized_session_id}") from exc

    @staticmethod
    def _normalize_non_empty_string(value: Any, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")
        return value.strip()

    def _normalize_channels(self, channels: Sequence[str]) -> List[str]:
        if not isinstance(channels, Sequence) or isinstance(channels, (str, bytes)):
            raise ValueError("channels must be a sequence of channel names")
        normalized = [
            self._normalize_non_empty_string(channel, "channel")
            for channel in channels
        ]
        normalized = _dedupe_preserve_order(normalized)
        if len(normalized) < 2:
            raise ValueError("channels must include at least 2 distinct channels")
        invalid = sorted(set(normalized) - SENSORY_LOOPBACK_ALLOWED_CHANNELS)
        if invalid:
            raise ValueError(
                f"unsupported loopback channels: {', '.join(invalid)}",
            )
        return normalized

    def _normalize_artifact_refs(
        self,
        artifact_refs: Mapping[str, str],
        *,
        allowed_channels: Sequence[str],
    ) -> Dict[str, str]:
        if not isinstance(artifact_refs, Mapping) or not artifact_refs:
            raise ValueError("artifact_refs must be a non-empty mapping")
        allowed = set(allowed_channels)
        normalized: Dict[str, str] = {}
        for channel, artifact_ref in artifact_refs.items():
            normalized_channel = self._normalize_non_empty_string(channel, "artifact_ref channel")
            if normalized_channel not in allowed:
                raise ValueError(f"artifact_refs contains unsupported channel: {normalized_channel}")
            normalized[normalized_channel] = self._normalize_non_empty_string(
                artifact_ref,
                f"{normalized_channel} artifact_ref",
            )
        return {
            channel: normalized[channel]
            for channel in allowed_channels
            if channel in normalized
        }

    def _normalize_family_channels(self, channels: Sequence[str]) -> List[str]:
        if not isinstance(channels, Sequence) or isinstance(channels, (str, bytes)):
            raise ValueError("delivered_channels must be a sequence")
        normalized = [
            self._normalize_non_empty_string(channel, "delivered_channel")
            for channel in channels
        ]
        normalized = _dedupe_preserve_order(normalized)
        invalid = sorted(set(normalized) - SENSORY_LOOPBACK_ALLOWED_CHANNELS)
        if invalid:
            raise ValueError(f"delivered_channels contains unsupported values: {invalid}")
        return normalized

    @staticmethod
    def _mapping_has_exact_segment_keys(value: Any) -> bool:
        return isinstance(value, Mapping) and set(value) == SENSORY_LOOPBACK_BODY_MAP_SEGMENT_SET

    @staticmethod
    def _default_body_map_alignment() -> Dict[str, float]:
        return {segment: 1.0 for segment in SENSORY_LOOPBACK_BODY_MAP_SEGMENTS}

    def _build_body_map_anchor_refs(self, body_anchor_ref: str) -> Dict[str, str]:
        trimmed = body_anchor_ref.rstrip("/")
        if "/" in trimmed:
            base_ref, tail = trimmed.rsplit("/", 1)
            if tail not in SENSORY_LOOPBACK_BODY_MAP_SEGMENT_SET:
                base_ref = trimmed
        else:
            base_ref = trimmed
        return {
            segment: trimmed if segment == "core" else f"{base_ref}/{segment}"
            for segment in SENSORY_LOOPBACK_BODY_MAP_SEGMENTS
        }

    def _normalize_body_map_alignment(self, alignment: Mapping[str, float]) -> Dict[str, float]:
        if not self._mapping_has_exact_segment_keys(alignment):
            raise ValueError(
                "body_map_alignment must cover the canonical avatar body map segments",
            )
        return {
            segment: round(
                self._normalize_score(alignment.get(segment), f"body_map_alignment.{segment}"),
                3,
            )
            for segment in SENSORY_LOOPBACK_BODY_MAP_SEGMENTS
        }

    @staticmethod
    def _derive_body_coherence_score(alignment: Mapping[str, float]) -> float:
        return round(
            sum(
                (1.0 - float(alignment[segment])) * SENSORY_LOOPBACK_BODY_MAP_WEIGHTS[segment]
                for segment in SENSORY_LOOPBACK_BODY_MAP_SEGMENTS
            ),
            3,
        )

    @staticmethod
    def _artifact_family_digest(
        *,
        session_id: Any,
        family_label: Any,
        scene_summaries: Sequence[Mapping[str, Any]],
        final_session_status: Any,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "session_id": session_id,
                    "family_label": family_label,
                    "policy_id": SENSORY_LOOPBACK_ARTIFACT_FAMILY_POLICY,
                    "scene_summaries": list(scene_summaries),
                    "final_session_status": final_session_status,
                }
            )
        )

    @staticmethod
    def _normalize_non_negative_number(value: Any, name: str) -> float:
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"{name} must be a non-negative number")
        return float(value)

    @staticmethod
    def _normalize_score(value: Any, name: str) -> float:
        if not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise ValueError(f"{name} must be between 0 and 1")
        return float(value)

    @staticmethod
    def _check_non_empty_string(value: Any, name: str, errors: List[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{name} must be a non-empty string")
