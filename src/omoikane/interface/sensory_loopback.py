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
            "artifact_storage_policy": "artifact-digest+summary-ref-only",
            "qualia_binding_policy": "surrogate-tick-ref",
            "guardian_recovery_required": True,
        }

    def open_session(
        self,
        *,
        identity_id: str,
        world_state_ref: str,
        body_anchor_ref: str,
        channels: Sequence[str] = DEFAULT_LOOPBACK_CHANNELS,
    ) -> Dict[str, Any]:
        normalized_identity = self._normalize_non_empty_string(identity_id, "identity_id")
        normalized_world_state = self._normalize_non_empty_string(world_state_ref, "world_state_ref")
        normalized_body_anchor = self._normalize_non_empty_string(body_anchor_ref, "body_anchor_ref")
        normalized_channels = self._normalize_channels(channels)

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
            "safe_baseline_ref": "loopback://baseline/guardian-safe-v1",
            "artifact_storage_policy": "artifact-digest+summary-ref-only",
            "qualia_binding_policy": "surrogate-tick-ref",
            "delivery_count": 0,
            "last_delivery_id": "",
            "last_delivery_status": "none",
            "last_guardian_action": "none",
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
        body_coherence_score: float,
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
        coherence_score = self._normalize_score(body_coherence_score, "body_coherence_score")
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
        session["delivery_count"] += 1
        session["last_delivery_id"] = delivery_id
        session["last_delivery_status"] = "stabilized"
        session["last_guardian_action"] = "resume-loopback"
        session["last_audit_event_ref"] = receipt["audit_event_ref"]
        return deepcopy(receipt)

    def snapshot(self, session_id: str) -> Dict[str, Any]:
        return deepcopy(self._require_session(session_id))

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

        delivery_count = session.get("delivery_count")
        if not isinstance(delivery_count, int) or delivery_count < 0:
            errors.append("delivery_count must be a non-negative integer")

        return {
            "ok": not errors,
            "errors": errors,
            "channel_count": len(channels) if isinstance(channels, list) else 0,
            "artifact_digest_only": session.get("artifact_storage_policy")
            == "artifact-digest+summary-ref-only",
            "supports_body_stabilization": session.get("hold_drift_threshold")
            == SENSORY_LOOPBACK_HOLD_DRIFT_THRESHOLD,
            "world_anchor_bound": bool(session.get("world_state_ref")),
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

        return {
            "ok": not errors,
            "errors": errors,
            "guardian_recoverable": delivery_status in {"attenuate-to-safe-baseline", "guardian-hold", "stabilized"},
            "immersion_preserved": bool(receipt.get("immersion_preserved")),
            "safe_baseline_applied": bool(receipt.get("safe_baseline_applied")),
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
