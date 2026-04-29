"""Sensory Loopback reference model."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from .biodata_transmitter import (
    BDT_CONFIDENCE_GATE_PROFILE_ID,
    CONFIDENCE_GATE_TARGET_THRESHOLDS,
)

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
SENSORY_LOOPBACK_CALIBRATION_CONFIDENCE_POLICY = (
    "biodata-calibration-gated-drift-threshold-v1"
)
SENSORY_LOOPBACK_CONFIDENCE_GATE_TARGET = "sensory-loopback"
SENSORY_LOOPBACK_CALIBRATION_THRESHOLD_MAX_ADJUSTMENT = 0.04
SENSORY_LOOPBACK_BODY_MAP_PROFILE = "avatar-proprioceptive-map-v1"
SENSORY_LOOPBACK_PROPRIOCEPTIVE_CALIBRATION_POLICY = "ref-bound-avatar-map-v1"
SENSORY_LOOPBACK_PUBLIC_SCHEMA_CONTRACT_PROFILE = "sensory-loopback-public-schema-contract-v1"
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
SENSORY_LOOPBACK_SHARED_SPACE_MAX_PARTICIPANTS = 4
SENSORY_LOOPBACK_SHARED_SPACE_MODES = {"self-only", "imc-shared", "collective-shared"}
SENSORY_LOOPBACK_ARBITRATION_POLICY = "guardian-mediated-multi-self-loopback-v1"
SENSORY_LOOPBACK_BIODATA_ARBITRATION_POLICY = (
    "participant-biodata-gate-arbitration-v1"
)
SENSORY_LOOPBACK_BIODATA_ARBITRATION_STORAGE_POLICY = (
    "participant-gate-digest+drift-threshold-digest-only"
)
SENSORY_LOOPBACK_ALLOWED_ARBITRATION_STATUSES = {
    "self-exclusive",
    "shared-aligned",
    "guardian-mediated",
    "guardian-hold",
}


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
        self.biodata_arbitration_bindings: Dict[str, Dict[str, Any]] = {}

    def reference_profile(self) -> Dict[str, Any]:
        return {
            "schema_version": SENSORY_LOOPBACK_SCHEMA_VERSION,
            "channels": list(DEFAULT_LOOPBACK_CHANNELS),
            "latency_budget_ms": SENSORY_LOOPBACK_LATENCY_BUDGET_MS,
            "attenuation_latency_ms": SENSORY_LOOPBACK_ATTENUATION_LATENCY_MS,
            "coherence_drift_threshold": SENSORY_LOOPBACK_COHERENCE_DRIFT_THRESHOLD,
            "hold_drift_threshold": SENSORY_LOOPBACK_HOLD_DRIFT_THRESHOLD,
            "calibration_confidence_policy": {
                "policy_id": SENSORY_LOOPBACK_CALIBRATION_CONFIDENCE_POLICY,
                "required_target_gate": SENSORY_LOOPBACK_CONFIDENCE_GATE_TARGET,
                "minimum_confidence": CONFIDENCE_GATE_TARGET_THRESHOLDS[
                    SENSORY_LOOPBACK_CONFIDENCE_GATE_TARGET
                ],
                "max_threshold_adjustment": (
                    SENSORY_LOOPBACK_CALIBRATION_THRESHOLD_MAX_ADJUSTMENT
                ),
                "replaces_body_map_calibration": False,
                "replaces_guardian_hold": False,
                "raw_calibration_payload_stored": False,
                "raw_gate_payload_stored": False,
            },
            "world_anchor_required": True,
            "body_schema_mode": "virtual-self-anchor-v1",
            "body_map_profile": SENSORY_LOOPBACK_BODY_MAP_PROFILE,
            "body_map_segments": list(SENSORY_LOOPBACK_BODY_MAP_SEGMENTS),
            "body_map_weights": dict(SENSORY_LOOPBACK_BODY_MAP_WEIGHTS),
            "proprioceptive_calibration_policy": SENSORY_LOOPBACK_PROPRIOCEPTIVE_CALIBRATION_POLICY,
            "public_schema_contract_profile": SENSORY_LOOPBACK_PUBLIC_SCHEMA_CONTRACT_PROFILE,
            "artifact_storage_policy": "artifact-digest+summary-ref-only",
            "qualia_binding_policy": "surrogate-tick-ref",
            "artifact_family_policy": SENSORY_LOOPBACK_ARTIFACT_FAMILY_POLICY,
            "artifact_family_storage_policy": SENSORY_LOOPBACK_ARTIFACT_FAMILY_STORAGE_POLICY,
            "artifact_family_max_scenes": SENSORY_LOOPBACK_ARTIFACT_FAMILY_MAX_SCENES,
            "guardian_recovery_required": True,
            "shared_space_modes": sorted(SENSORY_LOOPBACK_SHARED_SPACE_MODES),
            "arbitration_policy": {
                "policy_id": SENSORY_LOOPBACK_ARBITRATION_POLICY,
                "max_participants": SENSORY_LOOPBACK_SHARED_SPACE_MAX_PARTICIPANTS,
                "collective_requires_imc_binding": True,
                "guardian_required_on_conflict": True,
            },
            "biodata_arbitration_policy": {
                "policy_id": SENSORY_LOOPBACK_BIODATA_ARBITRATION_POLICY,
                "storage_policy": SENSORY_LOOPBACK_BIODATA_ARBITRATION_STORAGE_POLICY,
                "requires_shared_session": True,
                "requires_participant_gate_coverage": True,
                "requires_series_drift_gate_pass": True,
                "raw_biodata_payload_stored": False,
                "raw_calibration_payload_stored": False,
                "raw_drift_payload_stored": False,
                "raw_gate_payload_stored": False,
            },
        }

    def open_session(
        self,
        *,
        identity_id: str,
        world_state_ref: str,
        body_anchor_ref: str,
        avatar_body_map_ref: str,
        proprioceptive_calibration_ref: str,
        participant_identity_ids: Optional[Sequence[str]] = None,
        shared_imc_session_id: str = "",
        shared_collective_id: str = "",
        channels: Sequence[str] = DEFAULT_LOOPBACK_CHANNELS,
        calibration_confidence_gate: Optional[Mapping[str, Any]] = None,
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
        participant_ids = self._normalize_participant_ids(
            identity_id=normalized_identity,
            participant_identity_ids=participant_identity_ids,
        )
        (
            shared_space_mode,
            normalized_shared_imc_session_id,
            normalized_shared_collective_id,
            arbitration_required,
        ) = self._derive_shared_space_binding(
            participant_identity_ids=participant_ids,
            shared_imc_session_id=shared_imc_session_id,
            shared_collective_id=shared_collective_id,
        )
        body_map_anchor_refs = self._build_body_map_anchor_refs(normalized_body_anchor)
        baseline_alignment_ref = f"alignment://sensory-loopback/{new_id('sl-align')}"
        calibration_confidence = self._derive_calibration_confidence_binding(
            calibration_confidence_gate,
        )

        opened_at = utc_now_iso()
        session_id = new_id("sl")
        session = {
            "schema_version": SENSORY_LOOPBACK_SCHEMA_VERSION,
            "session_id": session_id,
            "identity_id": normalized_identity,
            "opened_at": opened_at,
            "updated_at": opened_at,
            "status": "active",
            "participant_identity_ids": participant_ids,
            "shared_space_mode": shared_space_mode,
            "shared_imc_session_id": normalized_shared_imc_session_id,
            "shared_collective_id": normalized_shared_collective_id,
            "arbitration_policy_id": SENSORY_LOOPBACK_ARBITRATION_POLICY,
            "arbitration_required": arbitration_required,
            "current_owner_identity_id": normalized_identity,
            "world_state_ref": normalized_world_state,
            "body_anchor_ref": normalized_body_anchor,
            "allowed_channels": normalized_channels,
            "latency_budget_ms": SENSORY_LOOPBACK_LATENCY_BUDGET_MS,
            "attenuation_latency_ms": SENSORY_LOOPBACK_ATTENUATION_LATENCY_MS,
            "coherence_drift_threshold": SENSORY_LOOPBACK_COHERENCE_DRIFT_THRESHOLD,
            "hold_drift_threshold": SENSORY_LOOPBACK_HOLD_DRIFT_THRESHOLD,
            "calibration_confidence_policy_id": calibration_confidence["policy_id"],
            "calibration_confidence_gate_ref": calibration_confidence["gate_ref"],
            "calibration_confidence_gate_digest": calibration_confidence["gate_digest"],
            "calibration_confidence_score": calibration_confidence["confidence_score"],
            "calibration_confidence_minimum": calibration_confidence[
                "minimum_confidence"
            ],
            "calibration_confidence_gate_status": calibration_confidence["gate_status"],
            "calibration_confidence_gate_bound": calibration_confidence["gate_bound"],
            "calibration_threshold_adjustment": calibration_confidence[
                "threshold_adjustment"
            ],
            "calibration_adjusted_coherence_drift_threshold": calibration_confidence[
                "adjusted_coherence_drift_threshold"
            ],
            "calibration_adjusted_hold_drift_threshold": calibration_confidence[
                "adjusted_hold_drift_threshold"
            ],
            "raw_calibration_payload_stored": False,
            "raw_gate_payload_stored": False,
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
            "last_arbitration_status": (
                "self-exclusive" if not arbitration_required else "shared-aligned"
            ),
            "last_arbitration_ref": f"loopback-arbitration://{session_id}/open",
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
        owner_identity_id: str = "",
        participant_attention_targets: Optional[Mapping[str, str]] = None,
        participant_presence_refs: Optional[Mapping[str, str]] = None,
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
        participant_ids = list(session["participant_identity_ids"])
        owner_identity = self._normalize_non_empty_string(
            owner_identity_id or session["current_owner_identity_id"],
            "owner_identity_id",
        )
        if owner_identity not in participant_ids:
            raise ValueError("owner_identity_id must be one of the session participants")
        arbitration_required = bool(session["arbitration_required"])
        participant_target_map = self._normalize_participant_attention_targets(
            participant_attention_targets,
            participant_identity_ids=participant_ids,
            default_target=normalized_attention_target,
            require_explicit=arbitration_required,
        )
        participant_presence_map = self._normalize_participant_presence_refs(
            participant_presence_refs,
            participant_identity_ids=participant_ids,
            session_id=session_id,
            require_explicit=arbitration_required,
        )
        selected_attention_target = participant_target_map[owner_identity]
        if normalized_attention_target != selected_attention_target:
            raise ValueError(
                "attention_target must match the selected owner target for the loopback delivery",
            )
        attention_target_conflict = len(set(participant_target_map.values())) > 1

        applied_coherence_threshold = float(
            session["calibration_adjusted_coherence_drift_threshold"]
        )
        applied_hold_threshold = float(session["calibration_adjusted_hold_drift_threshold"])
        degraded = (
            coherence_score > applied_coherence_threshold
            or normalized_latency > session["latency_budget_ms"]
        )
        if degraded and not guardian_observed:
            raise PermissionError("guardian observation is required for degraded loopback bundles")
        if attention_target_conflict and not guardian_observed:
            raise PermissionError("guardian observation is required for multi-self loopback arbitration")

        if (
            coherence_score <= applied_coherence_threshold
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
            coherence_score <= applied_hold_threshold
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

        if arbitration_required:
            if delivery_status == "guardian-hold":
                arbitration_status = "guardian-hold"
            elif attention_target_conflict:
                arbitration_status = "guardian-mediated"
            else:
                arbitration_status = "shared-aligned"
        else:
            arbitration_status = "self-exclusive"

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
            "calibration_confidence_policy_id": session[
                "calibration_confidence_policy_id"
            ],
            "calibration_confidence_gate_ref": session[
                "calibration_confidence_gate_ref"
            ],
            "calibration_confidence_gate_digest": session[
                "calibration_confidence_gate_digest"
            ],
            "calibration_confidence_score": session["calibration_confidence_score"],
            "calibration_confidence_minimum": session[
                "calibration_confidence_minimum"
            ],
            "calibration_confidence_gate_status": session[
                "calibration_confidence_gate_status"
            ],
            "calibration_confidence_gate_bound": session[
                "calibration_confidence_gate_bound"
            ],
            "calibration_threshold_adjustment": session[
                "calibration_threshold_adjustment"
            ],
            "applied_coherence_drift_threshold": applied_coherence_threshold,
            "applied_hold_drift_threshold": applied_hold_threshold,
            "raw_calibration_payload_stored": session["raw_calibration_payload_stored"],
            "raw_gate_payload_stored": session["raw_gate_payload_stored"],
            "body_map_alignment_ref": normalized_alignment_ref,
            "body_map_alignment": normalized_alignment,
            "classification": classification,
            "delivery_status": delivery_status,
            "guardian_action": guardian_action,
            "immersion_preserved": immersion_preserved,
            "safe_baseline_applied": safe_baseline_applied,
            "requires_council_review": requires_council_review,
            "participant_identity_ids": participant_ids,
            "shared_space_mode": session["shared_space_mode"],
            "shared_imc_session_id": session["shared_imc_session_id"],
            "shared_collective_id": session["shared_collective_id"],
            "arbitration_policy_id": session["arbitration_policy_id"],
            "arbitration_ref": f"loopback-arbitration://{delivery_id}",
            "arbitration_status": arbitration_status,
            "owner_identity_id": owner_identity,
            "participant_attention_targets": participant_target_map,
            "participant_presence_refs": participant_presence_map,
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
        session["current_owner_identity_id"] = owner_identity
        session["last_arbitration_status"] = arbitration_status
        session["last_arbitration_ref"] = receipt["arbitration_ref"]
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
        participant_ids = list(session["participant_identity_ids"])
        owner_identity = session["current_owner_identity_id"]
        participant_target_map = {
            participant_identity_id: restored_body_anchor
            for participant_identity_id in participant_ids
        }
        participant_presence_map = self._normalize_participant_presence_refs(
            None,
            participant_identity_ids=participant_ids,
            session_id=session_id,
            require_explicit=False,
        )
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
            "calibration_confidence_policy_id": session[
                "calibration_confidence_policy_id"
            ],
            "calibration_confidence_gate_ref": session[
                "calibration_confidence_gate_ref"
            ],
            "calibration_confidence_gate_digest": session[
                "calibration_confidence_gate_digest"
            ],
            "calibration_confidence_score": session["calibration_confidence_score"],
            "calibration_confidence_minimum": session[
                "calibration_confidence_minimum"
            ],
            "calibration_confidence_gate_status": session[
                "calibration_confidence_gate_status"
            ],
            "calibration_confidence_gate_bound": session[
                "calibration_confidence_gate_bound"
            ],
            "calibration_threshold_adjustment": session[
                "calibration_threshold_adjustment"
            ],
            "applied_coherence_drift_threshold": session[
                "calibration_adjusted_coherence_drift_threshold"
            ],
            "applied_hold_drift_threshold": session[
                "calibration_adjusted_hold_drift_threshold"
            ],
            "raw_calibration_payload_stored": session["raw_calibration_payload_stored"],
            "raw_gate_payload_stored": session["raw_gate_payload_stored"],
            "body_map_alignment_ref": restored_alignment_ref,
            "body_map_alignment": restored_alignment,
            "classification": "stabilized",
            "delivery_status": "stabilized",
            "guardian_action": "resume-loopback",
            "immersion_preserved": True,
            "safe_baseline_applied": True,
            "requires_council_review": False,
            "participant_identity_ids": participant_ids,
            "shared_space_mode": session["shared_space_mode"],
            "shared_imc_session_id": session["shared_imc_session_id"],
            "shared_collective_id": session["shared_collective_id"],
            "arbitration_policy_id": session["arbitration_policy_id"],
            "arbitration_ref": f"loopback-arbitration://{delivery_id}",
            "arbitration_status": (
                "self-exclusive" if not session["arbitration_required"] else "shared-aligned"
            ),
            "owner_identity_id": owner_identity,
            "participant_attention_targets": participant_target_map,
            "participant_presence_refs": participant_presence_map,
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
        session["last_arbitration_status"] = receipt["arbitration_status"]
        session["last_arbitration_ref"] = receipt["arbitration_ref"]
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
                    "calibration_confidence_gate_ref": self._normalize_string(
                        receipt.get("calibration_confidence_gate_ref"),
                        "calibration_confidence_gate_ref",
                    ),
                    "calibration_confidence_gate_digest": self._normalize_string(
                        receipt.get("calibration_confidence_gate_digest"),
                        "calibration_confidence_gate_digest",
                    ),
                    "calibration_confidence_score": self._normalize_score(
                        receipt.get("calibration_confidence_score"),
                        "calibration_confidence_score",
                    ),
                    "calibration_confidence_minimum": self._normalize_score(
                        receipt.get("calibration_confidence_minimum"),
                        "calibration_confidence_minimum",
                    ),
                    "calibration_confidence_gate_status": self._normalize_non_empty_string(
                        receipt.get("calibration_confidence_gate_status"),
                        "calibration_confidence_gate_status",
                    ),
                    "calibration_confidence_gate_bound": bool(
                        receipt.get("calibration_confidence_gate_bound")
                    ),
                    "calibration_confidence_policy_id": self._normalize_non_empty_string(
                        receipt.get("calibration_confidence_policy_id"),
                        "calibration_confidence_policy_id",
                    ),
                    "calibration_threshold_adjustment": self._normalize_score(
                        receipt.get("calibration_threshold_adjustment"),
                        "calibration_threshold_adjustment",
                    ),
                    "applied_coherence_drift_threshold": self._normalize_score(
                        receipt.get("applied_coherence_drift_threshold"),
                        "applied_coherence_drift_threshold",
                    ),
                    "applied_hold_drift_threshold": self._normalize_score(
                        receipt.get("applied_hold_drift_threshold"),
                        "applied_hold_drift_threshold",
                    ),
                    "raw_calibration_payload_stored": bool(
                        receipt.get("raw_calibration_payload_stored")
                    ),
                    "raw_gate_payload_stored": bool(receipt.get("raw_gate_payload_stored")),
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
                    "participant_identity_ids": self._normalize_participant_ids(
                        identity_id=self._normalize_non_empty_string(
                            receipt.get("owner_identity_id"),
                            "owner_identity_id",
                        ),
                        participant_identity_ids=receipt.get("participant_identity_ids"),
                    ),
                    "shared_space_mode": self._normalize_shared_space_mode(
                        receipt.get("shared_space_mode"),
                        "shared_space_mode",
                    ),
                    "arbitration_ref": self._normalize_non_empty_string(
                        receipt.get("arbitration_ref"),
                        "arbitration_ref",
                    ),
                    "arbitration_status": self._normalize_arbitration_status(
                        receipt.get("arbitration_status"),
                        "arbitration_status",
                    ),
                    "owner_identity_id": self._normalize_non_empty_string(
                        receipt.get("owner_identity_id"),
                        "owner_identity_id",
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
            participant_identity_ids=session["participant_identity_ids"],
            shared_space_mode=session["shared_space_mode"],
            shared_imc_session_id=session["shared_imc_session_id"],
            shared_collective_id=session["shared_collective_id"],
        )
        artifact_family = {
            "schema_version": SENSORY_LOOPBACK_SCHEMA_VERSION,
            "family_id": family_id,
            "family_ref": f"loopback-family://{family_id}",
            "session_id": session_id,
            "recorded_at": recorded_at,
            "family_label": normalized_label,
            "policy_id": SENSORY_LOOPBACK_ARTIFACT_FAMILY_POLICY,
            "participant_identity_ids": list(session["participant_identity_ids"]),
            "shared_space_mode": session["shared_space_mode"],
            "shared_imc_session_id": session["shared_imc_session_id"],
            "shared_collective_id": session["shared_collective_id"],
            "scene_count": len(scene_summaries),
            "delivery_ids": delivery_ids,
            "channels_observed": _dedupe_preserve_order(channels_observed),
            "scene_summaries": scene_summaries,
            "arbitration_scene_count": sum(
                1
                for scene in scene_summaries
                if scene["arbitration_status"] != "self-exclusive"
            ),
            "guardian_arbitration_count": sum(
                1
                for scene in scene_summaries
                if scene["arbitration_status"] in {"guardian-mediated", "guardian-hold"}
            ),
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

    def bind_participant_biodata_arbitration(
        self,
        session_id: str,
        *,
        participant_gate_receipts: Mapping[str, Mapping[str, Any]],
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        if not session["arbitration_required"]:
            raise ValueError("participant BioData arbitration requires a shared loopback session")
        if not isinstance(participant_gate_receipts, Mapping):
            raise ValueError("participant_gate_receipts must be a mapping")

        participant_ids = list(session["participant_identity_ids"])
        if set(participant_gate_receipts) != set(participant_ids):
            raise ValueError(
                "participant_gate_receipts must cover exactly participant_identity_ids",
            )

        participant_bindings: List[Dict[str, Any]] = []
        for participant_identity_id in participant_ids:
            gate_receipt = participant_gate_receipts[participant_identity_id]
            if not isinstance(gate_receipt, Mapping):
                raise ValueError(
                    f"participant_gate_receipts.{participant_identity_id} must be a mapping",
                )
            if gate_receipt.get("identity_id") != participant_identity_id:
                raise ValueError(
                    "participant BioData confidence gate identity_id must match the participant",
                )
            confidence_binding = self._derive_calibration_confidence_binding(gate_receipt)
            if gate_receipt.get("feature_window_series_drift_gate_bound") is not True:
                raise ValueError(
                    "participant BioData confidence gate must bind a feature-window series drift gate",
                )
            if gate_receipt.get("feature_window_series_drift_gate_status") != "pass":
                raise ValueError("participant BioData feature-window series drift gate must pass")
            if gate_receipt.get("raw_drift_payload_stored") is not False:
                raise ValueError(
                    "participant BioData confidence gate raw_drift_payload_stored must be false",
                )

            participant_bindings.append(
                {
                    "participant_identity_id": participant_identity_id,
                    "gate_ref": confidence_binding["gate_ref"],
                    "gate_receipt_digest": confidence_binding["gate_digest"],
                    "confidence_score": confidence_binding["confidence_score"],
                    "minimum_confidence": confidence_binding["minimum_confidence"],
                    "confidence_gate_status": confidence_binding["gate_status"],
                    "feature_window_series_drift_gate_ref": self._normalize_non_empty_string(
                        gate_receipt.get("feature_window_series_drift_gate_ref"),
                        "feature_window_series_drift_gate_ref",
                    ),
                    "feature_window_series_drift_gate_digest": self._normalize_non_empty_string(
                        gate_receipt.get("feature_window_series_drift_gate_digest"),
                        "feature_window_series_drift_gate_digest",
                    ),
                    "feature_window_series_drift_threshold_digest": self._normalize_non_empty_string(
                        gate_receipt.get("feature_window_series_drift_threshold_digest"),
                        "feature_window_series_drift_threshold_digest",
                    ),
                    "feature_window_series_drift_gate_status": "pass",
                    "target_gate_set_digest": self._normalize_non_empty_string(
                        gate_receipt.get("target_gate_set_digest"),
                        "target_gate_set_digest",
                    ),
                    "sensory_loopback_gate_bound": True,
                    "raw_calibration_payload_stored": False,
                    "raw_drift_payload_stored": False,
                    "raw_gate_payload_stored": False,
                    "subjective_equivalence_claimed": False,
                    "semantic_thought_content_generated": False,
                }
            )

        binding_id = new_id("sl-biodata-arb")
        binding = {
            "schema_version": SENSORY_LOOPBACK_SCHEMA_VERSION,
            "binding_ref": f"loopback-biodata-arbitration://{binding_id}",
            "created_at": utc_now_iso(),
            "policy_id": SENSORY_LOOPBACK_BIODATA_ARBITRATION_POLICY,
            "session_id": session_id,
            "participant_identity_ids": participant_ids,
            "shared_space_mode": session["shared_space_mode"],
            "shared_imc_session_id": session["shared_imc_session_id"],
            "shared_collective_id": session["shared_collective_id"],
            "arbitration_policy_id": session["arbitration_policy_id"],
            "participant_gate_bindings": participant_bindings,
            "participant_gate_count": len(participant_bindings),
            "participant_gate_digest_set": self._participant_biodata_gate_digest_set(
                participant_bindings,
            ),
            "all_participant_gates_bound": True,
            "all_drift_gates_passed": True,
            "arbitration_gate_status": "pass",
            "storage_policy": SENSORY_LOOPBACK_BIODATA_ARBITRATION_STORAGE_POLICY,
            "raw_biodata_payload_stored": False,
            "raw_calibration_payload_stored": False,
            "raw_drift_payload_stored": False,
            "raw_gate_payload_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
        }
        binding["binding_digest"] = sha256_text(
            canonical_json(self._participant_biodata_arbitration_digest_payload(binding))
        )
        self.biodata_arbitration_bindings[binding_id] = binding
        return deepcopy(binding)

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
        participant_identity_ids = session.get("participant_identity_ids")
        if not isinstance(participant_identity_ids, list) or not participant_identity_ids:
            errors.append("participant_identity_ids must be a non-empty list")
            participant_identity_ids = []
        elif len(participant_identity_ids) != len(set(participant_identity_ids)):
            errors.append("participant_identity_ids must be unique")
        shared_space_mode = session.get("shared_space_mode")
        if shared_space_mode not in SENSORY_LOOPBACK_SHARED_SPACE_MODES:
            errors.append(
                f"shared_space_mode must be one of {sorted(SENSORY_LOOPBACK_SHARED_SPACE_MODES)}",
            )
        shared_imc_session_id = session.get("shared_imc_session_id")
        if not isinstance(shared_imc_session_id, str):
            errors.append("shared_imc_session_id must be a string")
            shared_imc_session_id = ""
        shared_collective_id = session.get("shared_collective_id")
        if not isinstance(shared_collective_id, str):
            errors.append("shared_collective_id must be a string")
            shared_collective_id = ""
        if session.get("arbitration_policy_id") != SENSORY_LOOPBACK_ARBITRATION_POLICY:
            errors.append(
                f"arbitration_policy_id must be {SENSORY_LOOPBACK_ARBITRATION_POLICY}",
            )
        if not isinstance(session.get("arbitration_required"), bool):
            errors.append("arbitration_required must be a boolean")
        elif bool(session.get("arbitration_required")) != (len(participant_identity_ids) > 1):
            errors.append("arbitration_required must match the participant count")
        current_owner_identity_id = session.get("current_owner_identity_id")
        if not isinstance(current_owner_identity_id, str) or (
            participant_identity_ids and current_owner_identity_id not in participant_identity_ids
        ):
            errors.append("current_owner_identity_id must be one of participant_identity_ids")
        if session.get("last_arbitration_status") not in SENSORY_LOOPBACK_ALLOWED_ARBITRATION_STATUSES:
            errors.append(
                "last_arbitration_status must be one of "
                f"{sorted(SENSORY_LOOPBACK_ALLOWED_ARBITRATION_STATUSES)}",
            )
        self._check_non_empty_string(
            session.get("last_arbitration_ref"),
            "last_arbitration_ref",
            errors,
        )
        if shared_space_mode == "self-only":
            if len(participant_identity_ids) != 1:
                errors.append("self-only sessions must bind exactly 1 participant")
            if shared_imc_session_id or shared_collective_id:
                errors.append("self-only sessions must not bind IMC or collective refs")
        elif shared_space_mode == "imc-shared":
            if len(participant_identity_ids) < 2:
                errors.append("imc-shared sessions must bind at least 2 participants")
            if not shared_imc_session_id:
                errors.append("imc-shared sessions must bind shared_imc_session_id")
            if shared_collective_id:
                errors.append("imc-shared sessions must not bind shared_collective_id")
        elif shared_space_mode == "collective-shared":
            if len(participant_identity_ids) < 2:
                errors.append("collective-shared sessions must bind at least 2 participants")
            if not shared_imc_session_id:
                errors.append("collective-shared sessions must bind shared_imc_session_id")
            if not shared_collective_id:
                errors.append("collective-shared sessions must bind shared_collective_id")

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
        confidence_validation = self._validate_calibration_confidence_fields(
            session,
            errors,
            field_prefix="session",
            threshold_fields=(
                "calibration_adjusted_coherence_drift_threshold",
                "calibration_adjusted_hold_drift_threshold",
            ),
        )
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
            "calibration_confidence_gate_bound": confidence_validation[
                "gate_bound"
            ],
            "calibration_confidence_threshold_adjusted": confidence_validation[
                "threshold_adjusted"
            ],
            "calibration_confidence_gate_digest_bound": confidence_validation[
                "gate_digest_bound"
            ],
            "raw_calibration_payload_stored": False,
            "raw_gate_payload_stored": False,
            "participant_count": len(participant_identity_ids),
            "shared_space_bound": shared_space_mode in SENSORY_LOOPBACK_SHARED_SPACE_MODES,
            "shared_imc_bound": bool(shared_imc_session_id) or shared_space_mode == "self-only",
            "shared_collective_bound": bool(shared_collective_id)
            or shared_space_mode != "collective-shared",
            "arbitration_ready": bool(session.get("last_arbitration_ref"))
            and session.get("arbitration_policy_id") == SENSORY_LOOPBACK_ARBITRATION_POLICY,
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
        participant_identity_ids = receipt.get("participant_identity_ids")
        if not isinstance(participant_identity_ids, list) or not participant_identity_ids:
            errors.append("participant_identity_ids must be a non-empty list")
            participant_identity_ids = []
        elif len(participant_identity_ids) != len(set(participant_identity_ids)):
            errors.append("participant_identity_ids must be unique")
        shared_space_mode = receipt.get("shared_space_mode")
        if shared_space_mode not in SENSORY_LOOPBACK_SHARED_SPACE_MODES:
            errors.append(
                f"shared_space_mode must be one of {sorted(SENSORY_LOOPBACK_SHARED_SPACE_MODES)}",
            )
        shared_imc_session_id = receipt.get("shared_imc_session_id")
        if not isinstance(shared_imc_session_id, str):
            errors.append("shared_imc_session_id must be a string")
            shared_imc_session_id = ""
        shared_collective_id = receipt.get("shared_collective_id")
        if not isinstance(shared_collective_id, str):
            errors.append("shared_collective_id must be a string")
            shared_collective_id = ""
        if receipt.get("arbitration_policy_id") != SENSORY_LOOPBACK_ARBITRATION_POLICY:
            errors.append(
                f"arbitration_policy_id must be {SENSORY_LOOPBACK_ARBITRATION_POLICY}",
            )
        self._check_non_empty_string(receipt.get("arbitration_ref"), "arbitration_ref", errors)
        arbitration_status = receipt.get("arbitration_status")
        if arbitration_status not in SENSORY_LOOPBACK_ALLOWED_ARBITRATION_STATUSES:
            errors.append(
                "arbitration_status must be one of "
                f"{sorted(SENSORY_LOOPBACK_ALLOWED_ARBITRATION_STATUSES)}",
            )
        owner_identity_id = receipt.get("owner_identity_id")
        if not isinstance(owner_identity_id, str) or (
            participant_identity_ids and owner_identity_id not in participant_identity_ids
        ):
            errors.append("owner_identity_id must be one of participant_identity_ids")
        participant_attention_targets = receipt.get("participant_attention_targets")
        if not isinstance(participant_attention_targets, Mapping):
            errors.append("participant_attention_targets must be a mapping")
            participant_attention_targets = {}
        participant_presence_refs = receipt.get("participant_presence_refs")
        if not isinstance(participant_presence_refs, Mapping):
            errors.append("participant_presence_refs must be a mapping")
            participant_presence_refs = {}
        if participant_identity_ids:
            if set(participant_attention_targets) != set(participant_identity_ids):
                errors.append(
                    "participant_attention_targets must cover exactly participant_identity_ids",
                )
            if set(participant_presence_refs) != set(participant_identity_ids):
                errors.append(
                    "participant_presence_refs must cover exactly participant_identity_ids",
                )
            for participant_identity_id in participant_identity_ids:
                self._check_non_empty_string(
                    participant_attention_targets.get(participant_identity_id),
                    f"participant_attention_targets.{participant_identity_id}",
                    errors,
                )
                self._check_non_empty_string(
                    participant_presence_refs.get(participant_identity_id),
                    f"participant_presence_refs.{participant_identity_id}",
                    errors,
                )
        if shared_space_mode == "self-only":
            if len(participant_identity_ids) != 1:
                errors.append("self-only receipts must bind exactly 1 participant")
            if shared_imc_session_id or shared_collective_id:
                errors.append("self-only receipts must not bind IMC or collective refs")
            if arbitration_status != "self-exclusive":
                errors.append("self-only receipts must keep arbitration_status=self-exclusive")
        elif shared_space_mode == "imc-shared":
            if len(participant_identity_ids) < 2:
                errors.append("imc-shared receipts must bind at least 2 participants")
            if not shared_imc_session_id:
                errors.append("imc-shared receipts must bind shared_imc_session_id")
            if shared_collective_id:
                errors.append("imc-shared receipts must not bind shared_collective_id")
        elif shared_space_mode == "collective-shared":
            if len(participant_identity_ids) < 2:
                errors.append("collective-shared receipts must bind at least 2 participants")
            if not shared_imc_session_id:
                errors.append("collective-shared receipts must bind shared_imc_session_id")
            if not shared_collective_id:
                errors.append("collective-shared receipts must bind shared_collective_id")

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
        confidence_validation = self._validate_calibration_confidence_fields(
            receipt,
            errors,
            field_prefix="receipt",
            threshold_fields=(
                "applied_coherence_drift_threshold",
                "applied_hold_drift_threshold",
            ),
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
        if (
            shared_space_mode != "self-only"
            and delivery_status == "guardian-hold"
            and arbitration_status != "guardian-hold"
        ):
            errors.append(
                "shared guardian-hold receipts must keep arbitration_status=guardian-hold",
            )

        return {
            "ok": not errors,
            "errors": errors,
            "guardian_recoverable": delivery_status in {"attenuate-to-safe-baseline", "guardian-hold", "stabilized"},
            "immersion_preserved": bool(receipt.get("immersion_preserved")),
            "safe_baseline_applied": bool(receipt.get("safe_baseline_applied")),
            "body_map_bound": bool(receipt.get("avatar_body_map_ref")),
            "calibration_bound": bool(receipt.get("proprioceptive_calibration_ref")),
            "calibration_confidence_gate_bound": confidence_validation[
                "gate_bound"
            ],
            "calibration_confidence_threshold_adjusted": confidence_validation[
                "threshold_adjusted"
            ],
            "calibration_confidence_gate_digest_bound": confidence_validation[
                "gate_digest_bound"
            ],
            "raw_calibration_payload_stored": False,
            "raw_gate_payload_stored": False,
            "participant_bindings_complete": bool(participant_identity_ids)
            and set(participant_attention_targets) == set(participant_identity_ids)
            and set(participant_presence_refs) == set(participant_identity_ids),
            "shared_space_bound": shared_space_mode in SENSORY_LOOPBACK_SHARED_SPACE_MODES,
            "shared_imc_bound": bool(shared_imc_session_id) or shared_space_mode == "self-only",
            "shared_collective_bound": bool(shared_collective_id)
            or shared_space_mode != "collective-shared",
            "owner_bound": owner_identity_id in participant_identity_ids if participant_identity_ids else False,
            "guardian_arbitrated": arbitration_status in {"guardian-mediated", "guardian-hold"},
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
        participant_identity_ids = artifact_family.get("participant_identity_ids")
        if not isinstance(participant_identity_ids, list) or not participant_identity_ids:
            errors.append("participant_identity_ids must be a non-empty list")
            participant_identity_ids = []
        elif len(participant_identity_ids) != len(set(participant_identity_ids)):
            errors.append("participant_identity_ids must be unique")
        shared_space_mode = artifact_family.get("shared_space_mode")
        if shared_space_mode not in SENSORY_LOOPBACK_SHARED_SPACE_MODES:
            errors.append(
                f"shared_space_mode must be one of {sorted(SENSORY_LOOPBACK_SHARED_SPACE_MODES)}",
            )
        shared_imc_session_id = artifact_family.get("shared_imc_session_id")
        if not isinstance(shared_imc_session_id, str):
            errors.append("shared_imc_session_id must be a string")
            shared_imc_session_id = ""
        shared_collective_id = artifact_family.get("shared_collective_id")
        if not isinstance(shared_collective_id, str):
            errors.append("shared_collective_id must be a string")
            shared_collective_id = ""
        if shared_space_mode == "self-only":
            if len(participant_identity_ids) != 1:
                errors.append("self-only artifact families must bind exactly 1 participant")
            if shared_imc_session_id or shared_collective_id:
                errors.append("self-only artifact families must not bind IMC or collective refs")
        elif shared_space_mode == "imc-shared":
            if len(participant_identity_ids) < 2:
                errors.append("imc-shared artifact families must bind at least 2 participants")
            if not shared_imc_session_id:
                errors.append("imc-shared artifact families must bind shared_imc_session_id")
            if shared_collective_id:
                errors.append("imc-shared artifact families must not bind shared_collective_id")
        elif shared_space_mode == "collective-shared":
            if len(participant_identity_ids) < 2:
                errors.append(
                    "collective-shared artifact families must bind at least 2 participants",
                )
            if not shared_imc_session_id:
                errors.append("collective-shared artifact families must bind shared_imc_session_id")
            if not shared_collective_id:
                errors.append("collective-shared artifact families must bind shared_collective_id")

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
                self._validate_calibration_confidence_fields(
                    scene,
                    errors,
                    field_prefix=f"scene_summaries[{index}]",
                    threshold_fields=(
                        "applied_coherence_drift_threshold",
                        "applied_hold_drift_threshold",
                    ),
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
                scene_participants = scene.get("participant_identity_ids")
                if (
                    not isinstance(scene_participants, list)
                    or not scene_participants
                    or len(scene_participants) != len(set(scene_participants))
                ):
                    errors.append(
                        f"scene_summaries[{index}].participant_identity_ids must be a unique list",
                    )
                else:
                    if scene_participants != participant_identity_ids:
                        errors.append(
                            f"scene_summaries[{index}].participant_identity_ids must match the family participant list",
                        )
                if scene.get("shared_space_mode") != shared_space_mode:
                    errors.append(
                        f"scene_summaries[{index}].shared_space_mode must match family shared_space_mode",
                    )
                self._check_non_empty_string(
                    scene.get("arbitration_ref"),
                    f"scene_summaries[{index}].arbitration_ref",
                    errors,
                )
                if scene.get("arbitration_status") not in SENSORY_LOOPBACK_ALLOWED_ARBITRATION_STATUSES:
                    errors.append(
                        f"scene_summaries[{index}].arbitration_status must be one of "
                        f"{sorted(SENSORY_LOOPBACK_ALLOWED_ARBITRATION_STATUSES)}",
                    )
                owner_identity_id = scene.get("owner_identity_id")
                if (
                    not isinstance(owner_identity_id, str)
                    or isinstance(scene_participants, list)
                    and scene_participants
                    and owner_identity_id not in scene_participants
                ):
                    errors.append(
                        f"scene_summaries[{index}].owner_identity_id must be one of the scene participants",
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
        arbitration_scene_count = artifact_family.get("arbitration_scene_count")
        if not isinstance(arbitration_scene_count, int) or arbitration_scene_count < 0:
            errors.append("arbitration_scene_count must be a non-negative integer")
        elif isinstance(scene_summaries, list):
            expected_arbitration_scene_count = sum(
                1
                for scene in scene_summaries
                if isinstance(scene, Mapping) and scene.get("arbitration_status") != "self-exclusive"
            )
            if arbitration_scene_count != expected_arbitration_scene_count:
                errors.append(
                    "arbitration_scene_count must match non-self-exclusive scene arbitration statuses",
                )
        guardian_arbitration_count = artifact_family.get("guardian_arbitration_count")
        if not isinstance(guardian_arbitration_count, int) or guardian_arbitration_count < 0:
            errors.append("guardian_arbitration_count must be a non-negative integer")
        elif isinstance(scene_summaries, list):
            expected_guardian_arbitration_count = sum(
                1
                for scene in scene_summaries
                if isinstance(scene, Mapping)
                and scene.get("arbitration_status") in {"guardian-mediated", "guardian-hold"}
            )
            if guardian_arbitration_count != expected_guardian_arbitration_count:
                errors.append(
                    "guardian_arbitration_count must match guardian-mediated or guardian-hold scenes",
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
            participant_identity_ids=artifact_family.get("participant_identity_ids"),
            shared_space_mode=artifact_family.get("shared_space_mode"),
            shared_imc_session_id=artifact_family.get("shared_imc_session_id"),
            shared_collective_id=artifact_family.get("shared_collective_id"),
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
            "shared_space_bound": shared_space_mode in SENSORY_LOOPBACK_SHARED_SPACE_MODES,
            "arbitration_tracked": bool(participant_identity_ids)
            and isinstance(arbitration_scene_count, int)
            and isinstance(guardian_arbitration_count, int),
        }

    def validate_participant_biodata_arbitration(
        self,
        binding: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(binding, Mapping):
            raise ValueError("binding must be a mapping")

        errors: List[str] = []
        self._check_non_empty_string(binding.get("binding_ref"), "binding_ref", errors)
        self._check_non_empty_string(binding.get("created_at"), "created_at", errors)
        self._check_non_empty_string(binding.get("session_id"), "session_id", errors)
        self._check_non_empty_string(
            binding.get("participant_gate_digest_set"),
            "participant_gate_digest_set",
            errors,
        )
        self._check_non_empty_string(binding.get("binding_digest"), "binding_digest", errors)
        if binding.get("schema_version") != SENSORY_LOOPBACK_SCHEMA_VERSION:
            errors.append(f"schema_version must be {SENSORY_LOOPBACK_SCHEMA_VERSION}")
        if binding.get("policy_id") != SENSORY_LOOPBACK_BIODATA_ARBITRATION_POLICY:
            errors.append(
                f"policy_id must be {SENSORY_LOOPBACK_BIODATA_ARBITRATION_POLICY}",
            )
        if binding.get("storage_policy") != SENSORY_LOOPBACK_BIODATA_ARBITRATION_STORAGE_POLICY:
            errors.append(
                "storage_policy must be "
                f"{SENSORY_LOOPBACK_BIODATA_ARBITRATION_STORAGE_POLICY}",
            )
        participant_identity_ids = binding.get("participant_identity_ids")
        if (
            not isinstance(participant_identity_ids, list)
            or len(participant_identity_ids) < 2
            or len(participant_identity_ids) > SENSORY_LOOPBACK_SHARED_SPACE_MAX_PARTICIPANTS
            or len(participant_identity_ids) != len(set(participant_identity_ids))
        ):
            errors.append("participant_identity_ids must be a unique shared participant list")
            participant_identity_ids = []
        if binding.get("shared_space_mode") not in {"imc-shared", "collective-shared"}:
            errors.append("shared_space_mode must be imc-shared or collective-shared")
        if not isinstance(binding.get("shared_imc_session_id"), str) or not binding.get(
            "shared_imc_session_id"
        ):
            errors.append("shared_imc_session_id must be bound")
        if binding.get("shared_space_mode") == "collective-shared" and not binding.get(
            "shared_collective_id"
        ):
            errors.append("collective-shared biodata arbitration must bind shared_collective_id")
        if binding.get("arbitration_policy_id") != SENSORY_LOOPBACK_ARBITRATION_POLICY:
            errors.append(
                f"arbitration_policy_id must be {SENSORY_LOOPBACK_ARBITRATION_POLICY}",
            )

        participant_bindings = binding.get("participant_gate_bindings")
        if not isinstance(participant_bindings, list):
            errors.append("participant_gate_bindings must be a list")
            participant_bindings = []
        if binding.get("participant_gate_count") != len(participant_bindings):
            errors.append("participant_gate_count must match participant_gate_bindings length")
        if participant_identity_ids and [
            item.get("participant_identity_id")
            for item in participant_bindings
            if isinstance(item, Mapping)
        ] != participant_identity_ids:
            errors.append("participant_gate_bindings must follow participant_identity_ids order")

        for index, participant_binding in enumerate(participant_bindings):
            if not isinstance(participant_binding, Mapping):
                errors.append(f"participant_gate_bindings[{index}] must be a mapping")
                continue
            self._check_non_empty_string(
                participant_binding.get("participant_identity_id"),
                f"participant_gate_bindings[{index}].participant_identity_id",
                errors,
            )
            self._check_non_empty_string(
                participant_binding.get("gate_ref"),
                f"participant_gate_bindings[{index}].gate_ref",
                errors,
            )
            self._check_non_empty_string(
                participant_binding.get("gate_receipt_digest"),
                f"participant_gate_bindings[{index}].gate_receipt_digest",
                errors,
            )
            confidence_score = self._normalize_score_for_validation(
                participant_binding.get("confidence_score"),
                f"participant_gate_bindings[{index}].confidence_score",
                errors,
            )
            expected_minimum = CONFIDENCE_GATE_TARGET_THRESHOLDS[
                SENSORY_LOOPBACK_CONFIDENCE_GATE_TARGET
            ]
            if participant_binding.get("minimum_confidence") != expected_minimum:
                errors.append(
                    f"participant_gate_bindings[{index}].minimum_confidence must be {expected_minimum}",
                )
            if confidence_score < expected_minimum:
                errors.append(
                    f"participant_gate_bindings[{index}].confidence_score must meet sensory-loopback minimum",
                )
            if participant_binding.get("confidence_gate_status") != "bound":
                errors.append(
                    f"participant_gate_bindings[{index}].confidence_gate_status must be bound",
                )
            for field_name in (
                "feature_window_series_drift_gate_ref",
                "feature_window_series_drift_gate_digest",
                "feature_window_series_drift_threshold_digest",
                "target_gate_set_digest",
            ):
                self._check_non_empty_string(
                    participant_binding.get(field_name),
                    f"participant_gate_bindings[{index}].{field_name}",
                    errors,
                )
            if participant_binding.get("feature_window_series_drift_gate_status") != "pass":
                errors.append(
                    f"participant_gate_bindings[{index}].feature_window_series_drift_gate_status must be pass",
                )
            if participant_binding.get("sensory_loopback_gate_bound") is not True:
                errors.append(
                    f"participant_gate_bindings[{index}].sensory_loopback_gate_bound must be true",
                )
            for field_name in (
                "raw_calibration_payload_stored",
                "raw_drift_payload_stored",
                "raw_gate_payload_stored",
                "subjective_equivalence_claimed",
                "semantic_thought_content_generated",
            ):
                if participant_binding.get(field_name) is not False:
                    errors.append(f"participant_gate_bindings[{index}].{field_name} must be false")

        participant_gate_digest_set_bound = False
        if all(isinstance(item, Mapping) for item in participant_bindings):
            expected_gate_digest_set = self._participant_biodata_gate_digest_set(
                participant_bindings,
            )
            participant_gate_digest_set_bound = (
                bool(participant_bindings)
                and binding.get("participant_gate_digest_set") == expected_gate_digest_set
            )
        if not participant_gate_digest_set_bound:
            errors.append("participant_gate_digest_set mismatch")
        expected_binding_digest = sha256_text(
            canonical_json(self._participant_biodata_arbitration_digest_payload(binding))
        )
        binding_digest_bound = binding.get("binding_digest") == expected_binding_digest
        if not binding_digest_bound:
            errors.append("binding_digest mismatch")

        all_participant_gates_bound = (
            bool(participant_bindings)
            and all(
                isinstance(item, Mapping)
                and item.get("confidence_gate_status") == "bound"
                and item.get("sensory_loopback_gate_bound") is True
                for item in participant_bindings
            )
        )
        all_drift_gates_passed = (
            bool(participant_bindings)
            and all(
                isinstance(item, Mapping)
                and item.get("feature_window_series_drift_gate_status") == "pass"
                for item in participant_bindings
            )
        )
        if binding.get("all_participant_gates_bound") != all_participant_gates_bound:
            errors.append("all_participant_gates_bound mismatch")
        if binding.get("all_drift_gates_passed") != all_drift_gates_passed:
            errors.append("all_drift_gates_passed mismatch")
        expected_status = (
            "pass"
            if all_participant_gates_bound
            and all_drift_gates_passed
            and participant_gate_digest_set_bound
            else "blocked"
        )
        if binding.get("arbitration_gate_status") != expected_status:
            errors.append("arbitration_gate_status mismatch")
        for field_name in (
            "raw_biodata_payload_stored",
            "raw_calibration_payload_stored",
            "raw_drift_payload_stored",
            "raw_gate_payload_stored",
            "subjective_equivalence_claimed",
            "semantic_thought_content_generated",
        ):
            if binding.get(field_name) is not False:
                errors.append(f"{field_name} must be false")

        session_bound = False
        bound_session_id = binding.get("session_id")
        if isinstance(bound_session_id, str) and bound_session_id in self.sessions:
            session = self.sessions[bound_session_id]
            session_bound = (
                session["arbitration_required"] is True
                and binding.get("participant_identity_ids") == session["participant_identity_ids"]
                and binding.get("shared_space_mode") == session["shared_space_mode"]
                and binding.get("shared_imc_session_id") == session["shared_imc_session_id"]
                and binding.get("shared_collective_id") == session["shared_collective_id"]
            )
            if not session_bound:
                errors.append("binding must match the shared loopback session")

        return {
            "ok": not errors,
            "errors": errors,
            "session_bound": session_bound,
            "participant_gate_count": len(participant_bindings),
            "participant_gate_digest_set_bound": participant_gate_digest_set_bound,
            "binding_digest_bound": binding_digest_bound,
            "all_participant_gates_bound": all_participant_gates_bound,
            "all_drift_gates_passed": all_drift_gates_passed,
            "arbitration_gate_status": binding.get("arbitration_gate_status"),
            "raw_biodata_payload_stored": False,
            "raw_calibration_payload_stored": False,
            "raw_drift_payload_stored": False,
            "raw_gate_payload_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
        }

    def _require_session(self, session_id: str) -> Dict[str, Any]:
        normalized_session_id = self._normalize_non_empty_string(session_id, "session_id")
        try:
            return self.sessions[normalized_session_id]
        except KeyError as exc:
            raise KeyError(f"unknown sensory loopback session: {normalized_session_id}") from exc

    def _derive_calibration_confidence_binding(
        self,
        gate_receipt: Optional[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        default_binding = self._default_calibration_confidence_binding()
        if gate_receipt is None:
            return default_binding
        if not isinstance(gate_receipt, Mapping):
            raise ValueError("calibration_confidence_gate must be a mapping")

        errors: List[str] = []
        if gate_receipt.get("profile_id") != BDT_CONFIDENCE_GATE_PROFILE_ID:
            errors.append(
                "calibration_confidence_gate.profile_id must be "
                f"{BDT_CONFIDENCE_GATE_PROFILE_ID}",
            )
        if gate_receipt.get("confidence_gate_status") != "bound":
            errors.append("calibration_confidence_gate.confidence_gate_status must be bound")
        if gate_receipt.get("sensory_loopback_gate_bound") is not True:
            errors.append("calibration_confidence_gate must bind the sensory-loopback target")
        if gate_receipt.get("raw_calibration_payload_stored") is not False:
            errors.append("calibration_confidence_gate.raw_calibration_payload_stored must be false")
        if gate_receipt.get("raw_gate_payload_stored") is not False:
            errors.append("calibration_confidence_gate.raw_gate_payload_stored must be false")
        if gate_receipt.get("subjective_equivalence_claimed") is not False:
            errors.append("calibration_confidence_gate.subjective_equivalence_claimed must be false")
        if gate_receipt.get("semantic_thought_content_generated") is not False:
            errors.append(
                "calibration_confidence_gate.semantic_thought_content_generated must be false",
            )
        gate_ref = self._normalize_non_empty_string(
            gate_receipt.get("gate_ref"),
            "calibration_confidence_gate.gate_ref",
        )
        gate_digest = self._normalize_non_empty_string(
            gate_receipt.get("gate_receipt_digest"),
            "calibration_confidence_gate.gate_receipt_digest",
        )
        confidence_score = self._normalize_score(
            gate_receipt.get("confidence_score"),
            "calibration_confidence_gate.confidence_score",
        )
        minimum_confidence = CONFIDENCE_GATE_TARGET_THRESHOLDS[
            SENSORY_LOOPBACK_CONFIDENCE_GATE_TARGET
        ]
        if confidence_score < minimum_confidence:
            errors.append(
                "calibration_confidence_gate.confidence_score must meet sensory-loopback minimum",
            )
        bindings = gate_receipt.get("target_gate_bindings")
        if not isinstance(bindings, list):
            bindings = []
        sensory_binding = next(
            (
                binding
                for binding in bindings
                if isinstance(binding, Mapping)
                and binding.get("target_gate") == SENSORY_LOOPBACK_CONFIDENCE_GATE_TARGET
            ),
            None,
        )
        if not isinstance(sensory_binding, Mapping):
            errors.append("calibration_confidence_gate must include a sensory-loopback binding")
        elif (
            sensory_binding.get("status") != "pass"
            or sensory_binding.get("minimum_confidence") != minimum_confidence
            or sensory_binding.get("confidence_score") != confidence_score
        ):
            errors.append("calibration_confidence_gate sensory-loopback binding is invalid")
        if errors:
            raise ValueError("; ".join(errors))

        threshold_adjustment = self._calibration_threshold_adjustment(confidence_score)
        return {
            "policy_id": SENSORY_LOOPBACK_CALIBRATION_CONFIDENCE_POLICY,
            "gate_ref": gate_ref,
            "gate_digest": gate_digest,
            "confidence_score": confidence_score,
            "minimum_confidence": minimum_confidence,
            "gate_status": "bound",
            "gate_bound": True,
            "threshold_adjustment": threshold_adjustment,
            "adjusted_coherence_drift_threshold": round(
                SENSORY_LOOPBACK_COHERENCE_DRIFT_THRESHOLD + threshold_adjustment,
                3,
            ),
            "adjusted_hold_drift_threshold": round(
                SENSORY_LOOPBACK_HOLD_DRIFT_THRESHOLD + threshold_adjustment,
                3,
            ),
        }

    @staticmethod
    def _default_calibration_confidence_binding() -> Dict[str, Any]:
        return {
            "policy_id": SENSORY_LOOPBACK_CALIBRATION_CONFIDENCE_POLICY,
            "gate_ref": "",
            "gate_digest": "",
            "confidence_score": 0.0,
            "minimum_confidence": CONFIDENCE_GATE_TARGET_THRESHOLDS[
                SENSORY_LOOPBACK_CONFIDENCE_GATE_TARGET
            ],
            "gate_status": "not-bound",
            "gate_bound": False,
            "threshold_adjustment": 0.0,
            "adjusted_coherence_drift_threshold": SENSORY_LOOPBACK_COHERENCE_DRIFT_THRESHOLD,
            "adjusted_hold_drift_threshold": SENSORY_LOOPBACK_HOLD_DRIFT_THRESHOLD,
        }

    @staticmethod
    def _calibration_threshold_adjustment(confidence_score: float) -> float:
        minimum_confidence = CONFIDENCE_GATE_TARGET_THRESHOLDS[
            SENSORY_LOOPBACK_CONFIDENCE_GATE_TARGET
        ]
        return round(
            min(
                SENSORY_LOOPBACK_CALIBRATION_THRESHOLD_MAX_ADJUSTMENT,
                max(0.0, confidence_score - minimum_confidence) * 0.1,
            ),
            3,
        )

    def _validate_calibration_confidence_fields(
        self,
        payload: Mapping[str, Any],
        errors: List[str],
        *,
        field_prefix: str,
        threshold_fields: Tuple[str, str],
    ) -> Dict[str, Any]:
        policy_id = payload.get("calibration_confidence_policy_id")
        if policy_id != SENSORY_LOOPBACK_CALIBRATION_CONFIDENCE_POLICY:
            errors.append(
                f"{field_prefix}.calibration_confidence_policy_id must be "
                f"{SENSORY_LOOPBACK_CALIBRATION_CONFIDENCE_POLICY}",
            )
        gate_ref = payload.get("calibration_confidence_gate_ref")
        gate_digest = payload.get("calibration_confidence_gate_digest")
        gate_status = payload.get("calibration_confidence_gate_status")
        if not isinstance(gate_ref, str):
            errors.append(f"{field_prefix}.calibration_confidence_gate_ref must be a string")
            gate_ref = ""
        if not isinstance(gate_digest, str):
            errors.append(f"{field_prefix}.calibration_confidence_gate_digest must be a string")
            gate_digest = ""
        if gate_status not in {"bound", "not-bound"}:
            errors.append(
                f"{field_prefix}.calibration_confidence_gate_status must be bound or not-bound",
            )
        gate_bound = payload.get("calibration_confidence_gate_bound")
        if not isinstance(gate_bound, bool):
            errors.append(f"{field_prefix}.calibration_confidence_gate_bound must be a boolean")
            gate_bound = False
        confidence_score = self._normalize_score_for_validation(
            payload.get("calibration_confidence_score"),
            f"{field_prefix}.calibration_confidence_score",
            errors,
        )
        minimum_confidence = payload.get("calibration_confidence_minimum")
        expected_minimum = CONFIDENCE_GATE_TARGET_THRESHOLDS[
            SENSORY_LOOPBACK_CONFIDENCE_GATE_TARGET
        ]
        if minimum_confidence != expected_minimum:
            errors.append(
                f"{field_prefix}.calibration_confidence_minimum must be {expected_minimum}",
            )
        threshold_adjustment = self._normalize_score_for_validation(
            payload.get("calibration_threshold_adjustment"),
            f"{field_prefix}.calibration_threshold_adjustment",
            errors,
        )
        expected_adjustment = (
            self._calibration_threshold_adjustment(confidence_score)
            if gate_bound
            else 0.0
        )
        if threshold_adjustment != expected_adjustment:
            errors.append(
                f"{field_prefix}.calibration_threshold_adjustment must match confidence score",
            )
        coherence_field, hold_field = threshold_fields
        expected_coherence_threshold = round(
            SENSORY_LOOPBACK_COHERENCE_DRIFT_THRESHOLD + expected_adjustment,
            3,
        )
        expected_hold_threshold = round(
            SENSORY_LOOPBACK_HOLD_DRIFT_THRESHOLD + expected_adjustment,
            3,
        )
        if payload.get(coherence_field) != expected_coherence_threshold:
            errors.append(f"{field_prefix}.{coherence_field} must match calibrated threshold")
        if payload.get(hold_field) != expected_hold_threshold:
            errors.append(f"{field_prefix}.{hold_field} must match calibrated threshold")
        if payload.get("raw_calibration_payload_stored") is not False:
            errors.append(f"{field_prefix}.raw_calibration_payload_stored must be false")
        if payload.get("raw_gate_payload_stored") is not False:
            errors.append(f"{field_prefix}.raw_gate_payload_stored must be false")
        if gate_bound:
            if gate_status != "bound":
                errors.append(f"{field_prefix}.calibration_confidence_gate_status must be bound")
            if confidence_score < expected_minimum:
                errors.append(
                    f"{field_prefix}.calibration_confidence_score must meet the gate minimum",
                )
            if not gate_ref:
                errors.append(f"{field_prefix}.calibration_confidence_gate_ref must be non-empty")
            if not gate_digest:
                errors.append(
                    f"{field_prefix}.calibration_confidence_gate_digest must be non-empty",
                )
        else:
            if gate_status != "not-bound":
                errors.append(
                    f"{field_prefix}.calibration_confidence_gate_status must be not-bound",
                )
            if confidence_score != 0.0:
                errors.append(
                    f"{field_prefix}.calibration_confidence_score must be 0.0 when unbound",
                )
            if gate_ref or gate_digest:
                errors.append(
                    f"{field_prefix}.calibration_confidence gate refs must be empty when unbound",
                )
        return {
            "gate_bound": bool(gate_bound),
            "threshold_adjusted": bool(gate_bound)
            and expected_adjustment > 0
            and payload.get(coherence_field) == expected_coherence_threshold
            and payload.get(hold_field) == expected_hold_threshold,
            "gate_digest_bound": bool(gate_bound and gate_digest),
        }

    @staticmethod
    def _participant_biodata_gate_digest_set(
        participant_bindings: Sequence[Mapping[str, Any]],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "policy_id": SENSORY_LOOPBACK_BIODATA_ARBITRATION_POLICY,
                    "participant_gate_bindings": [
                        {
                            "participant_identity_id": binding.get(
                                "participant_identity_id"
                            ),
                            "gate_receipt_digest": binding.get("gate_receipt_digest"),
                            "feature_window_series_drift_gate_digest": binding.get(
                                "feature_window_series_drift_gate_digest"
                            ),
                            "feature_window_series_drift_threshold_digest": binding.get(
                                "feature_window_series_drift_threshold_digest"
                            ),
                            "target_gate_set_digest": binding.get(
                                "target_gate_set_digest"
                            ),
                        }
                        for binding in participant_bindings
                    ],
                }
            )
        )

    @staticmethod
    def _participant_biodata_arbitration_digest_payload(
        binding: Mapping[str, Any],
    ) -> Dict[str, Any]:
        payload = dict(binding)
        payload.pop("binding_digest", None)
        return payload

    @staticmethod
    def _normalize_score_for_validation(
        value: Any,
        name: str,
        errors: List[str],
    ) -> float:
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not 0 <= float(value) <= 1
        ):
            errors.append(f"{name} must be between 0 and 1")
            return 0.0
        return round(float(value), 3)

    @staticmethod
    def _normalize_string(value: Any, name: str) -> str:
        if not isinstance(value, str):
            raise ValueError(f"{name} must be a string")
        return value.strip()

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

    def _normalize_participant_ids(
        self,
        *,
        identity_id: str,
        participant_identity_ids: Optional[Sequence[str]],
    ) -> List[str]:
        if participant_identity_ids is None:
            participant_identity_ids = [identity_id]
        if not isinstance(participant_identity_ids, Sequence) or isinstance(
            participant_identity_ids,
            (str, bytes),
        ):
            raise ValueError("participant_identity_ids must be a sequence of identity refs")
        normalized = _dedupe_preserve_order(
            [
                self._normalize_non_empty_string(
                    participant_identity_id,
                    "participant_identity_id",
                )
                for participant_identity_id in participant_identity_ids
            ]
        )
        if identity_id not in normalized:
            raise ValueError("participant_identity_ids must include identity_id")
        if not normalized:
            raise ValueError("participant_identity_ids must contain at least 1 identity")
        if len(normalized) > SENSORY_LOOPBACK_SHARED_SPACE_MAX_PARTICIPANTS:
            raise ValueError(
                "participant_identity_ids may not exceed "
                f"{SENSORY_LOOPBACK_SHARED_SPACE_MAX_PARTICIPANTS} identities",
            )
        return normalized

    def _derive_shared_space_binding(
        self,
        *,
        participant_identity_ids: Sequence[str],
        shared_imc_session_id: str,
        shared_collective_id: str,
    ) -> Tuple[str, str, str, bool]:
        normalized_imc_session_id = (
            self._normalize_non_empty_string(shared_imc_session_id, "shared_imc_session_id")
            if shared_imc_session_id
            else ""
        )
        normalized_collective_id = (
            self._normalize_non_empty_string(shared_collective_id, "shared_collective_id")
            if shared_collective_id
            else ""
        )
        arbitration_required = len(participant_identity_ids) > 1
        if not arbitration_required:
            if normalized_imc_session_id or normalized_collective_id:
                raise ValueError("shared IMC/collective bindings require at least 2 participants")
            return ("self-only", "", "", False)
        if not normalized_imc_session_id and not normalized_collective_id:
            raise ValueError(
                "multi-self loopback sessions require shared_imc_session_id or shared_collective_id",
            )
        if normalized_collective_id and not normalized_imc_session_id:
            raise ValueError("collective-shared sessions require shared_imc_session_id")
        if normalized_collective_id:
            return (
                "collective-shared",
                normalized_imc_session_id,
                normalized_collective_id,
                True,
            )
        return ("imc-shared", normalized_imc_session_id, "", True)

    def _normalize_participant_attention_targets(
        self,
        participant_attention_targets: Optional[Mapping[str, str]],
        *,
        participant_identity_ids: Sequence[str],
        default_target: str,
        require_explicit: bool,
    ) -> Dict[str, str]:
        if participant_attention_targets is None:
            if require_explicit:
                raise ValueError(
                    "participant_attention_targets must cover every participant in shared loopback sessions",
                )
            return {
                participant_identity_id: default_target
                for participant_identity_id in participant_identity_ids
            }
        if not isinstance(participant_attention_targets, Mapping):
            raise ValueError("participant_attention_targets must be a mapping")
        if set(participant_attention_targets) != set(participant_identity_ids):
            raise ValueError(
                "participant_attention_targets must cover exactly the session participants",
            )
        return {
            participant_identity_id: self._normalize_non_empty_string(
                participant_attention_targets.get(participant_identity_id),
                f"participant_attention_targets.{participant_identity_id}",
            )
            for participant_identity_id in participant_identity_ids
        }

    def _normalize_participant_presence_refs(
        self,
        participant_presence_refs: Optional[Mapping[str, str]],
        *,
        participant_identity_ids: Sequence[str],
        session_id: str,
        require_explicit: bool,
    ) -> Dict[str, str]:
        if participant_presence_refs is None:
            if require_explicit:
                raise ValueError(
                    "participant_presence_refs must cover every participant in shared loopback sessions",
                )
            return {
                participant_identity_id: self._default_presence_ref(
                    session_id,
                    participant_identity_id,
                )
                for participant_identity_id in participant_identity_ids
            }
        if not isinstance(participant_presence_refs, Mapping):
            raise ValueError("participant_presence_refs must be a mapping")
        if set(participant_presence_refs) != set(participant_identity_ids):
            raise ValueError("participant_presence_refs must cover exactly the session participants")
        return {
            participant_identity_id: self._normalize_non_empty_string(
                participant_presence_refs.get(participant_identity_id),
                f"participant_presence_refs.{participant_identity_id}",
            )
            for participant_identity_id in participant_identity_ids
        }

    @staticmethod
    def _default_presence_ref(session_id: str, participant_identity_id: str) -> str:
        participant_suffix = sha256_text(participant_identity_id)[:12]
        return f"presence://sensory-loopback/{session_id}/{participant_suffix}"

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

    def _normalize_shared_space_mode(self, value: Any, name: str) -> str:
        normalized_value = self._normalize_non_empty_string(value, name)
        if normalized_value not in SENSORY_LOOPBACK_SHARED_SPACE_MODES:
            raise ValueError(
                f"{name} must be one of {sorted(SENSORY_LOOPBACK_SHARED_SPACE_MODES)}",
            )
        return normalized_value

    def _normalize_arbitration_status(self, value: Any, name: str) -> str:
        normalized_value = self._normalize_non_empty_string(value, name)
        if normalized_value not in SENSORY_LOOPBACK_ALLOWED_ARBITRATION_STATUSES:
            raise ValueError(
                f"{name} must be one of {sorted(SENSORY_LOOPBACK_ALLOWED_ARBITRATION_STATUSES)}",
            )
        return normalized_value

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
        participant_identity_ids: Any,
        shared_space_mode: Any,
        shared_imc_session_id: Any,
        shared_collective_id: Any,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "session_id": session_id,
                    "family_label": family_label,
                    "policy_id": SENSORY_LOOPBACK_ARTIFACT_FAMILY_POLICY,
                    "participant_identity_ids": participant_identity_ids,
                    "shared_space_mode": shared_space_mode,
                    "shared_imc_session_id": shared_imc_session_id,
                    "shared_collective_id": shared_collective_id,
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
