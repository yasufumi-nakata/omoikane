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
    "participant-gate+drift+refresh-digest-only"
)
SENSORY_LOOPBACK_PARTICIPANT_REFRESH_PROPAGATION_PROFILE = (
    "participant-calibration-refresh-propagation-v1"
)
SENSORY_LOOPBACK_PARTICIPANT_LATENCY_DRIFT_PROFILE = (
    "participant-hardware-timing-latency-drift-gate-v1"
)
SENSORY_LOOPBACK_PARTICIPANT_LATENCY_STORAGE_POLICY = (
    "participant-timing-ref+latency-drift-digest-only"
)
SENSORY_LOOPBACK_MAX_PARTICIPANT_LATENCY_DRIFT_MS = 12.0
SENSORY_LOOPBACK_LATENCY_QUORUM_STRICT_PROFILE = "all-participant-latency-pass-v1"
SENSORY_LOOPBACK_LATENCY_QUORUM_WEIGHTED_PROFILE = "weighted-latency-quorum-v1"
SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_PROFILE = (
    "weighted-latency-quorum-authority-v1"
)
SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_PROFILE = (
    "weighted-latency-policy-live-verifier-quorum-v1"
)
SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_THRESHOLD = 2
SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_FRESHNESS_HOURS = 24
SENSORY_LOOPBACK_WEIGHTED_LATENCY_MIN_PARTICIPANTS = 3
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
        self.participant_latency_drift_gates: Dict[str, Dict[str, Any]] = {}
        self.latency_weight_policy_verifier_quorums: Dict[str, Dict[str, Any]] = {}

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
                "requires_participant_calibration_refresh": True,
                "calibration_refresh_propagation_profile": (
                    SENSORY_LOOPBACK_PARTICIPANT_REFRESH_PROPAGATION_PROFILE
                ),
                "requires_participant_latency_drift_gate": True,
                "latency_drift_profile": (
                    SENSORY_LOOPBACK_PARTICIPANT_LATENCY_DRIFT_PROFILE
                ),
                "latency_storage_policy": (
                    SENSORY_LOOPBACK_PARTICIPANT_LATENCY_STORAGE_POLICY
                ),
                "latency_quorum_profiles": [
                    SENSORY_LOOPBACK_LATENCY_QUORUM_STRICT_PROFILE,
                    SENSORY_LOOPBACK_LATENCY_QUORUM_WEIGHTED_PROFILE,
                ],
                "latency_weight_policy_profile": (
                    SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_PROFILE
                ),
                "latency_weight_policy_verifier_profile": (
                    SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_PROFILE
                ),
                "requires_latency_weight_policy_authority_for_weighted_quorum": True,
                "requires_latency_weight_policy_verifier_for_weighted_quorum": True,
                "latency_weight_policy_verifier_quorum_threshold": (
                    SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_THRESHOLD
                ),
                "latency_weight_policy_freshness_hours": (
                    SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_FRESHNESS_HOURS
                ),
                "weighted_latency_min_participants": (
                    SENSORY_LOOPBACK_WEIGHTED_LATENCY_MIN_PARTICIPANTS
                ),
                "max_participant_latency_drift_ms": (
                    SENSORY_LOOPBACK_MAX_PARTICIPANT_LATENCY_DRIFT_MS
                ),
                "raw_biodata_payload_stored": False,
                "raw_calibration_payload_stored": False,
                "raw_drift_payload_stored": False,
                "raw_refresh_payload_stored": False,
                "raw_gate_payload_stored": False,
                "raw_timing_payload_stored": False,
                "raw_hardware_adapter_payload_stored": False,
                "raw_latency_weight_policy_payload_stored": False,
                "raw_latency_weight_authority_payload_stored": False,
                "raw_latency_weight_policy_verifier_payload_stored": False,
                "raw_latency_weight_policy_verifier_response_payload_stored": False,
                "raw_latency_weight_policy_verifier_signature_payload_stored": False,
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
        participant_latency_drift_gates: Mapping[str, Mapping[str, Any]],
        participant_latency_weights: Optional[Mapping[str, float]] = None,
        latency_quorum_threshold: Optional[float] = None,
        latency_weight_policy_authority_ref: str = "",
        latency_weight_policy_authority_digest: str = "",
        latency_weight_policy_source_digest_set: str = "",
        latency_weight_policy_verifier_quorum: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        if not session["arbitration_required"]:
            raise ValueError("participant BioData arbitration requires a shared loopback session")
        if not isinstance(participant_gate_receipts, Mapping):
            raise ValueError("participant_gate_receipts must be a mapping")
        if not isinstance(participant_latency_drift_gates, Mapping):
            raise ValueError("participant_latency_drift_gates must be a mapping")

        participant_ids = list(session["participant_identity_ids"])
        if set(participant_gate_receipts) != set(participant_ids):
            raise ValueError(
                "participant_gate_receipts must cover exactly participant_identity_ids",
            )
        if set(participant_latency_drift_gates) != set(participant_ids):
            raise ValueError(
                "participant_latency_drift_gates must cover exactly participant_identity_ids",
            )
        latency_quorum_policy = self._derive_latency_quorum_policy(
            participant_ids=participant_ids,
            participant_latency_weights=participant_latency_weights,
            latency_quorum_threshold=latency_quorum_threshold,
            latency_weight_policy_authority_ref=latency_weight_policy_authority_ref,
            latency_weight_policy_authority_digest=latency_weight_policy_authority_digest,
            latency_weight_policy_source_digest_set=(
                latency_weight_policy_source_digest_set
            ),
            latency_weight_policy_verifier_quorum=(
                latency_weight_policy_verifier_quorum
            ),
        )

        participant_bindings: List[Dict[str, Any]] = []
        participant_latency_bindings: List[Dict[str, Any]] = []
        participant_latency_passed: Dict[str, bool] = {}
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
            threshold_policy_authority_bound = (
                gate_receipt.get(
                    "feature_window_series_threshold_policy_authority_bound"
                )
                is True
            )
            threshold_policy_authority_ref = self._normalize_string(
                gate_receipt.get(
                    "feature_window_series_threshold_policy_authority_ref",
                    "",
                ),
                "feature_window_series_threshold_policy_authority_ref",
            )
            threshold_policy_authority_digest = self._normalize_string(
                gate_receipt.get(
                    "feature_window_series_threshold_policy_authority_digest",
                    "",
                ),
                "feature_window_series_threshold_policy_authority_digest",
            )
            threshold_policy_source_digest_set = self._normalize_string(
                gate_receipt.get(
                    "feature_window_series_threshold_policy_source_digest_set",
                    "",
                ),
                "feature_window_series_threshold_policy_source_digest_set",
            )
            threshold_policy_authority_status = self._normalize_string(
                gate_receipt.get(
                    "feature_window_series_threshold_policy_authority_status",
                    "not-bound",
                ),
                "feature_window_series_threshold_policy_authority_status",
            )
            if threshold_policy_authority_bound:
                if threshold_policy_authority_status != "complete":
                    raise ValueError(
                        "participant BioData confidence gate threshold policy authority must be complete",
                    )
                for field_name, field_value in (
                    (
                        "feature_window_series_threshold_policy_authority_ref",
                        threshold_policy_authority_ref,
                    ),
                    (
                        "feature_window_series_threshold_policy_authority_digest",
                        threshold_policy_authority_digest,
                    ),
                    (
                        "feature_window_series_threshold_policy_source_digest_set",
                        threshold_policy_source_digest_set,
                    ),
                ):
                    if not field_value:
                        raise ValueError(
                            f"participant BioData confidence gate {field_name} must be bound",
                        )
            elif threshold_policy_authority_status != "not-bound":
                raise ValueError(
                    "unbound participant BioData threshold policy authority must use not-bound status",
                )
            refresh_bound = gate_receipt.get("calibration_refresh_bound") is True
            refresh_ref = self._normalize_string(
                gate_receipt.get("calibration_refresh_ref", ""),
                "calibration_refresh_ref",
            )
            refresh_digest = self._normalize_string(
                gate_receipt.get("calibration_refresh_digest", ""),
                "calibration_refresh_digest",
            )
            refresh_source_digest_set = self._normalize_string(
                gate_receipt.get("calibration_refresh_source_digest_set", ""),
                "calibration_refresh_source_digest_set",
            )
            refresh_status = self._normalize_string(
                gate_receipt.get("calibration_refresh_status", "not-bound"),
                "calibration_refresh_status",
            )
            refresh_window_bound = gate_receipt.get("calibration_refresh_window_bound") is True
            if not refresh_bound:
                raise ValueError(
                    "participant BioData confidence gate must bind a calibration refresh receipt",
                )
            if refresh_status != "fresh":
                raise ValueError(
                    "participant BioData calibration refresh receipt must be fresh",
                )
            if not refresh_window_bound:
                raise ValueError(
                    "participant BioData calibration refresh window must be bound",
                )
            for field_name, field_value in (
                ("calibration_refresh_ref", refresh_ref),
                ("calibration_refresh_digest", refresh_digest),
                ("calibration_refresh_source_digest_set", refresh_source_digest_set),
            ):
                if not field_value:
                    raise ValueError(
                        f"participant BioData confidence gate {field_name} must be bound",
                    )
            if gate_receipt.get("raw_refresh_payload_stored") is not False:
                raise ValueError(
                    "participant BioData confidence gate raw_refresh_payload_stored must be false",
                )

            latency_gate = participant_latency_drift_gates[participant_identity_id]
            latency_validation = self.validate_participant_latency_drift_gate(
                latency_gate,
            )
            if not latency_validation["ok"]:
                raise ValueError(
                    "participant latency drift gate is invalid: "
                    + "; ".join(latency_validation["errors"]),
                )
            if latency_gate.get("participant_identity_id") != participant_identity_id:
                raise ValueError(
                    "participant latency drift gate identity must match the participant",
                )
            latency_passed = latency_gate.get("latency_drift_status") == "pass"
            if (
                latency_quorum_policy["profile_id"]
                == SENSORY_LOOPBACK_LATENCY_QUORUM_STRICT_PROFILE
                and not latency_passed
            ):
                raise ValueError("participant latency drift gate must pass")
            participant_latency_passed[participant_identity_id] = latency_passed
            if threshold_policy_authority_bound:
                if (
                    latency_gate.get("threshold_policy_authority_digest")
                    != threshold_policy_authority_digest
                    or latency_gate.get("threshold_policy_authority_ref")
                    != threshold_policy_authority_ref
                ):
                    raise ValueError(
                        "participant latency drift gate must bind the same threshold policy authority as the BioData gate",
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
                    "feature_window_series_threshold_policy_authority_ref": (
                        threshold_policy_authority_ref
                    ),
                    "feature_window_series_threshold_policy_authority_digest": (
                        threshold_policy_authority_digest
                    ),
                    "feature_window_series_threshold_policy_source_digest_set": (
                        threshold_policy_source_digest_set
                    ),
                    "feature_window_series_threshold_policy_authority_status": (
                        threshold_policy_authority_status
                    ),
                    "feature_window_series_threshold_policy_authority_bound": (
                        threshold_policy_authority_bound
                    ),
                    "feature_window_series_drift_gate_status": "pass",
                    "calibration_refresh_ref": refresh_ref,
                    "calibration_refresh_digest": refresh_digest,
                    "calibration_refresh_source_digest_set": refresh_source_digest_set,
                    "calibration_refresh_window_bound": refresh_window_bound,
                    "calibration_refresh_status": refresh_status,
                    "calibration_refresh_bound": refresh_bound,
                    "target_gate_set_digest": self._normalize_non_empty_string(
                        gate_receipt.get("target_gate_set_digest"),
                        "target_gate_set_digest",
                    ),
                    "sensory_loopback_gate_bound": True,
                    "raw_calibration_payload_stored": False,
                    "raw_drift_payload_stored": False,
                    "raw_refresh_payload_stored": False,
                    "raw_gate_payload_stored": False,
                    "subjective_equivalence_claimed": False,
                    "semantic_thought_content_generated": False,
                }
            )
            participant_latency_bindings.append(
                {
                    "schema_version": SENSORY_LOOPBACK_SCHEMA_VERSION,
                    "profile_id": SENSORY_LOOPBACK_PARTICIPANT_LATENCY_DRIFT_PROFILE,
                    "participant_identity_id": participant_identity_id,
                    "timing_gate_ref": self._normalize_non_empty_string(
                        latency_gate.get("timing_gate_ref"),
                        "timing_gate_ref",
                    ),
                    "created_at": self._normalize_non_empty_string(
                        latency_gate.get("created_at"),
                        "created_at",
                    ),
                    "timing_gate_digest": self._normalize_non_empty_string(
                        latency_gate.get("timing_gate_digest"),
                        "timing_gate_digest",
                    ),
                    "hardware_adapter_ref": self._normalize_non_empty_string(
                        latency_gate.get("hardware_adapter_ref"),
                        "hardware_adapter_ref",
                    ),
                    "timing_evidence_ref": self._normalize_non_empty_string(
                        latency_gate.get("timing_evidence_ref"),
                        "timing_evidence_ref",
                    ),
                    "baseline_latency_ms": self._normalize_non_negative_number(
                        latency_gate.get("baseline_latency_ms"),
                        "baseline_latency_ms",
                    ),
                    "observed_latency_ms": self._normalize_non_negative_number(
                        latency_gate.get("observed_latency_ms"),
                        "observed_latency_ms",
                    ),
                    "absolute_latency_drift_ms": self._normalize_non_negative_number(
                        latency_gate.get("absolute_latency_drift_ms"),
                        "absolute_latency_drift_ms",
                    ),
                    "max_latency_drift_ms": self._normalize_non_negative_number(
                        latency_gate.get("max_latency_drift_ms"),
                        "max_latency_drift_ms",
                    ),
                    "latency_threshold_digest": self._normalize_non_empty_string(
                        latency_gate.get("latency_threshold_digest"),
                        "latency_threshold_digest",
                    ),
                    "threshold_policy_authority_ref": self._normalize_string(
                        latency_gate.get("threshold_policy_authority_ref", ""),
                        "threshold_policy_authority_ref",
                    ),
                    "threshold_policy_authority_digest": self._normalize_string(
                        latency_gate.get("threshold_policy_authority_digest", ""),
                        "threshold_policy_authority_digest",
                    ),
                    "threshold_policy_source_digest_set": self._normalize_string(
                        latency_gate.get("threshold_policy_source_digest_set", ""),
                        "threshold_policy_source_digest_set",
                    ),
                    "threshold_policy_authority_status": self._normalize_string(
                        latency_gate.get(
                            "threshold_policy_authority_status",
                            "not-bound",
                        ),
                        "threshold_policy_authority_status",
                    ),
                    "threshold_policy_authority_bound": bool(
                        latency_gate.get("threshold_policy_authority_bound")
                    ),
                    "latency_drift_status": self._normalize_non_empty_string(
                        latency_gate.get("latency_drift_status"),
                        "latency_drift_status",
                    ),
                    "raw_timing_payload_stored": False,
                    "raw_hardware_adapter_payload_stored": False,
                    "raw_threshold_policy_payload_stored": False,
                    "raw_authority_payload_stored": False,
                }
            )

        participant_latency_digest_set = self._participant_latency_drift_digest_set(
            participant_latency_bindings
        )
        participant_refresh_digest_set = self._participant_calibration_refresh_digest_set(
            participant_bindings
        )
        latency_quorum = self._evaluate_latency_quorum(
            policy=latency_quorum_policy,
            participant_latency_passed=participant_latency_passed,
            participant_latency_digest_set=participant_latency_digest_set,
        )
        if not latency_quorum["satisfied"]:
            raise ValueError("participant latency quorum must be satisfied")
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
            "participant_calibration_refresh_digest_set": participant_refresh_digest_set,
            "all_calibration_refresh_receipts_fresh": True,
            "all_calibration_refresh_windows_bound": True,
            "calibration_refresh_status": "fresh",
            "participant_latency_bindings": participant_latency_bindings,
            "participant_latency_gate_count": len(participant_latency_bindings),
            "participant_latency_digest_set": participant_latency_digest_set,
            "latency_quorum_profile": latency_quorum_policy["profile_id"],
            "latency_quorum_threshold": latency_quorum_policy["threshold"],
            "participant_latency_weights": latency_quorum_policy["weights"],
            "participant_latency_weight_digest": latency_quorum[
                "participant_latency_weight_digest"
            ],
            "latency_weight_policy_profile": latency_quorum_policy[
                "weight_policy_profile"
            ],
            "latency_weight_policy_authority_ref": latency_quorum_policy[
                "weight_policy_authority_ref"
            ],
            "latency_weight_policy_authority_digest": latency_quorum_policy[
                "weight_policy_authority_digest"
            ],
            "latency_weight_policy_source_digest_set": latency_quorum_policy[
                "weight_policy_source_digest_set"
            ],
            "latency_weight_policy_status": latency_quorum_policy[
                "weight_policy_status"
            ],
            "latency_weight_policy_bound": latency_quorum_policy[
                "weight_policy_bound"
            ],
            "latency_weight_policy_digest": latency_quorum[
                "latency_weight_policy_digest"
            ],
            "latency_weight_policy_verifier_profile": latency_quorum_policy[
                "weight_policy_verifier_profile"
            ],
            "latency_weight_policy_verifier_quorum_ref": latency_quorum_policy[
                "weight_policy_verifier_quorum_ref"
            ],
            "latency_weight_policy_verifier_quorum_digest": latency_quorum_policy[
                "weight_policy_verifier_quorum_digest"
            ],
            "latency_weight_policy_verifier_source_digest_set": latency_quorum_policy[
                "weight_policy_verifier_source_digest_set"
            ],
            "latency_weight_policy_verifier_status": latency_quorum_policy[
                "weight_policy_verifier_status"
            ],
            "latency_weight_policy_verifier_freshness_status": latency_quorum_policy[
                "weight_policy_verifier_freshness_status"
            ],
            "latency_weight_policy_verifier_bound": latency_quorum_policy[
                "weight_policy_verifier_bound"
            ],
            "latency_weight_policy_verifier_fresh": latency_quorum_policy[
                "weight_policy_verifier_fresh"
            ],
            "latency_quorum_pass_weight": latency_quorum["pass_weight"],
            "latency_quorum_failed_participant_ids": latency_quorum[
                "failed_participant_ids"
            ],
            "latency_quorum_satisfied": latency_quorum["satisfied"],
            "latency_quorum_status": latency_quorum["status"],
            "latency_quorum_digest": latency_quorum["digest"],
            "all_participant_gates_bound": True,
            "all_drift_gates_passed": True,
            "all_latency_gates_passed": latency_quorum["all_latency_gates_passed"],
            "arbitration_gate_status": "pass",
            "latency_gate_status": latency_quorum["status"],
            "storage_policy": SENSORY_LOOPBACK_BIODATA_ARBITRATION_STORAGE_POLICY,
            "timing_storage_policy": SENSORY_LOOPBACK_PARTICIPANT_LATENCY_STORAGE_POLICY,
            "raw_biodata_payload_stored": False,
            "raw_calibration_payload_stored": False,
            "raw_drift_payload_stored": False,
            "raw_refresh_payload_stored": False,
            "raw_gate_payload_stored": False,
            "raw_timing_payload_stored": False,
            "raw_hardware_adapter_payload_stored": False,
            "raw_latency_threshold_payload_stored": False,
            "raw_latency_weight_policy_payload_stored": False,
            "raw_latency_weight_authority_payload_stored": False,
            "raw_latency_weight_policy_verifier_payload_stored": False,
            "raw_latency_weight_policy_verifier_response_payload_stored": False,
            "raw_latency_weight_policy_verifier_signature_payload_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
        }
        binding["binding_digest"] = sha256_text(
            canonical_json(self._participant_biodata_arbitration_digest_payload(binding))
        )
        self.biodata_arbitration_bindings[binding_id] = binding
        return deepcopy(binding)

    def bind_participant_latency_drift_gate(
        self,
        *,
        participant_identity_id: str,
        hardware_adapter_ref: str,
        timing_evidence_ref: str,
        baseline_latency_ms: float,
        observed_latency_ms: float,
        threshold_policy_authority_ref: str = "",
        threshold_policy_authority_digest: str = "",
        threshold_policy_source_digest_set: str = "",
    ) -> Dict[str, Any]:
        participant_id = self._normalize_non_empty_string(
            participant_identity_id,
            "participant_identity_id",
        )
        adapter_ref = self._normalize_non_empty_string(
            hardware_adapter_ref,
            "hardware_adapter_ref",
        )
        evidence_ref = self._normalize_non_empty_string(
            timing_evidence_ref,
            "timing_evidence_ref",
        )
        baseline_latency = self._normalize_non_negative_number(
            baseline_latency_ms,
            "baseline_latency_ms",
        )
        observed_latency = self._normalize_non_negative_number(
            observed_latency_ms,
            "observed_latency_ms",
        )
        absolute_drift = round(abs(observed_latency - baseline_latency), 3)
        authority_ref = self._normalize_string(
            threshold_policy_authority_ref,
            "threshold_policy_authority_ref",
        )
        authority_digest = self._normalize_string(
            threshold_policy_authority_digest,
            "threshold_policy_authority_digest",
        )
        authority_source_digest_set = self._normalize_string(
            threshold_policy_source_digest_set,
            "threshold_policy_source_digest_set",
        )
        authority_bound = bool(authority_ref or authority_digest or authority_source_digest_set)
        if authority_bound and not (
            authority_ref and authority_digest and authority_source_digest_set
        ):
            raise ValueError(
                "threshold policy authority binding requires ref, digest, and source digest set",
            )
        latency_threshold_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": SENSORY_LOOPBACK_PARTICIPANT_LATENCY_DRIFT_PROFILE,
                    "max_latency_drift_ms": (
                        SENSORY_LOOPBACK_MAX_PARTICIPANT_LATENCY_DRIFT_MS
                    ),
                    "threshold_policy_authority_ref": authority_ref,
                    "threshold_policy_authority_digest": authority_digest,
                    "threshold_policy_source_digest_set": authority_source_digest_set,
                }
            )
        )
        gate = {
            "schema_version": SENSORY_LOOPBACK_SCHEMA_VERSION,
            "profile_id": SENSORY_LOOPBACK_PARTICIPANT_LATENCY_DRIFT_PROFILE,
            "timing_gate_ref": (
                f"loopback-latency-drift-gate://{new_id('sl-latency-gate')}"
            ),
            "created_at": utc_now_iso(),
            "participant_identity_id": participant_id,
            "hardware_adapter_ref": adapter_ref,
            "timing_evidence_ref": evidence_ref,
            "baseline_latency_ms": baseline_latency,
            "observed_latency_ms": observed_latency,
            "absolute_latency_drift_ms": absolute_drift,
            "max_latency_drift_ms": SENSORY_LOOPBACK_MAX_PARTICIPANT_LATENCY_DRIFT_MS,
            "latency_threshold_digest": latency_threshold_digest,
            "threshold_policy_authority_ref": authority_ref,
            "threshold_policy_authority_digest": authority_digest,
            "threshold_policy_source_digest_set": authority_source_digest_set,
            "threshold_policy_authority_status": (
                "complete" if authority_bound else "not-bound"
            ),
            "threshold_policy_authority_bound": authority_bound,
            "latency_drift_status": (
                "pass"
                if absolute_drift <= SENSORY_LOOPBACK_MAX_PARTICIPANT_LATENCY_DRIFT_MS
                else "blocked"
            ),
            "raw_timing_payload_stored": False,
            "raw_hardware_adapter_payload_stored": False,
            "raw_threshold_policy_payload_stored": False,
            "raw_authority_payload_stored": False,
        }
        gate["timing_gate_digest"] = sha256_text(
            canonical_json(self._participant_latency_drift_digest_payload(gate))
        )
        self.participant_latency_drift_gates[gate["timing_gate_ref"]] = gate
        return deepcopy(gate)

    def bind_latency_weight_policy_verifier_quorum(
        self,
        *,
        authority_ref: str,
        authority_digest: str,
        source_digest_set: str,
        verifier_refs: Optional[Sequence[str]] = None,
        verifier_jurisdictions: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        normalized_authority_ref = self._normalize_non_empty_string(
            authority_ref,
            "authority_ref",
        )
        normalized_authority_digest = self._normalize_non_empty_string(
            authority_digest,
            "authority_digest",
        )
        normalized_source_digest_set = self._normalize_non_empty_string(
            source_digest_set,
            "source_digest_set",
        )
        raw_refs = verifier_refs or (
            "latency-weight-policy-verifier://jp-13/primary",
            "latency-weight-policy-verifier://sg-01/backup",
        )
        raw_jurisdictions = verifier_jurisdictions or ("JP-13", "SG-01")
        refs = [
            self._normalize_non_empty_string(verifier_ref, "verifier_ref")
            for verifier_ref in raw_refs
        ]
        jurisdictions = [
            self._normalize_non_empty_string(
                verifier_jurisdiction,
                "verifier_jurisdiction",
            )
            for verifier_jurisdiction in raw_jurisdictions
        ]
        if len(refs) != len(jurisdictions):
            raise ValueError(
                "verifier_refs and verifier_jurisdictions must have the same length"
            )
        if len(refs) < SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_THRESHOLD:
            raise ValueError(
                "latency weight policy verifier quorum requires at least "
                f"{SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_THRESHOLD} verifiers",
            )
        if len(refs) != len(set(refs)) or len(jurisdictions) != len(set(jurisdictions)):
            raise ValueError(
                "latency weight policy verifier quorum refs and jurisdictions must be unique"
            )

        observed_at = utc_now_iso()
        receipts: List[Dict[str, Any]] = []
        for normalized_verifier_ref, normalized_jurisdiction in zip(
            refs,
            jurisdictions,
        ):
            response_digest = sha256_text(
                canonical_json(
                    {
                        "profile_id": SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_PROFILE,
                        "verifier_ref": normalized_verifier_ref,
                        "jurisdiction": normalized_jurisdiction,
                        "authority_ref": normalized_authority_ref,
                        "authority_digest": normalized_authority_digest,
                        "source_digest_set": normalized_source_digest_set,
                        "observed_at": observed_at,
                        "freshness_window_hours": (
                            SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_FRESHNESS_HOURS
                        ),
                        "freshness_status": "fresh",
                        "verifier_status": "accepted",
                    }
                )
            )
            signing_key_ref = (
                f"verifier-key://{normalized_jurisdiction.lower()}/"
                "latency-weight-policy"
            )
            response_signature_digest = sha256_text(
                canonical_json(
                    {
                        "verifier_ref": normalized_verifier_ref,
                        "jurisdiction": normalized_jurisdiction,
                        "response_digest": response_digest,
                        "signing_key_ref": signing_key_ref,
                    }
                )
            )
            receipts.append(
                {
                    "verifier_ref": normalized_verifier_ref,
                    "jurisdiction": normalized_jurisdiction,
                    "observed_at": observed_at,
                    "authority_ref": normalized_authority_ref,
                    "authority_digest": normalized_authority_digest,
                    "source_digest_set": normalized_source_digest_set,
                    "freshness_window_hours": (
                        SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_FRESHNESS_HOURS
                    ),
                    "freshness_status": "fresh",
                    "verifier_status": "accepted",
                    "response_digest": response_digest,
                    "signing_key_ref": signing_key_ref,
                    "response_signature_digest": response_signature_digest,
                    "raw_response_payload_stored": False,
                    "raw_signature_payload_stored": False,
                }
            )

        quorum_id = new_id("sl-latency-policy-quorum")
        quorum = {
            "schema_version": SENSORY_LOOPBACK_SCHEMA_VERSION,
            "profile_id": SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_PROFILE,
            "verifier_quorum_ref": (
                f"latency-weight-policy-verifier-quorum://{quorum_id}"
            ),
            "authority_ref": normalized_authority_ref,
            "authority_digest": normalized_authority_digest,
            "source_digest_set": normalized_source_digest_set,
            "accepted_verifier_refs": refs,
            "verifier_jurisdictions": jurisdictions,
            "verifier_receipts": receipts,
            "verifier_response_digest_set": (
                self._latency_weight_policy_verifier_response_digest_set(receipts)
            ),
            "verifier_signature_digest_set": (
                self._latency_weight_policy_verifier_signature_digest_set(receipts)
            ),
            "quorum_threshold": (
                SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_THRESHOLD
            ),
            "quorum_status": "complete",
            "freshness_window_hours": (
                SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_FRESHNESS_HOURS
            ),
            "freshness_status": "fresh",
            "authority_freshness_bound": True,
            "source_digest_set_bound": True,
            "raw_verifier_payload_stored": False,
            "raw_response_payload_stored": False,
            "raw_signature_payload_stored": False,
        }
        quorum["verifier_quorum_digest"] = sha256_text(
            canonical_json(
                self._latency_weight_policy_verifier_quorum_digest_payload(quorum)
            )
        )
        self.latency_weight_policy_verifier_quorums[
            quorum["verifier_quorum_ref"]
        ] = quorum
        return deepcopy(quorum)

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

    def validate_participant_latency_drift_gate(
        self,
        gate: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(gate, Mapping):
            raise ValueError("gate must be a mapping")

        errors: List[str] = []
        for field_name in (
            "timing_gate_ref",
            "created_at",
            "participant_identity_id",
            "hardware_adapter_ref",
            "timing_evidence_ref",
            "latency_threshold_digest",
            "timing_gate_digest",
        ):
            self._check_non_empty_string(gate.get(field_name), field_name, errors)
        if gate.get("schema_version") != SENSORY_LOOPBACK_SCHEMA_VERSION:
            errors.append(f"schema_version must be {SENSORY_LOOPBACK_SCHEMA_VERSION}")
        if gate.get("profile_id") != SENSORY_LOOPBACK_PARTICIPANT_LATENCY_DRIFT_PROFILE:
            errors.append(
                "profile_id must be "
                f"{SENSORY_LOOPBACK_PARTICIPANT_LATENCY_DRIFT_PROFILE}",
            )
        baseline_latency = self._normalize_non_negative_number(
            gate.get("baseline_latency_ms"),
            "baseline_latency_ms",
        )
        observed_latency = self._normalize_non_negative_number(
            gate.get("observed_latency_ms"),
            "observed_latency_ms",
        )
        absolute_latency_drift = self._normalize_non_negative_number(
            gate.get("absolute_latency_drift_ms"),
            "absolute_latency_drift_ms",
        )
        expected_absolute_drift = round(abs(observed_latency - baseline_latency), 3)
        absolute_drift_bound = absolute_latency_drift == expected_absolute_drift
        if not absolute_drift_bound:
            errors.append("absolute_latency_drift_ms must match observed-baseline drift")
        if gate.get("max_latency_drift_ms") != SENSORY_LOOPBACK_MAX_PARTICIPANT_LATENCY_DRIFT_MS:
            errors.append(
                "max_latency_drift_ms must be "
                f"{SENSORY_LOOPBACK_MAX_PARTICIPANT_LATENCY_DRIFT_MS}",
            )
        authority_ref = gate.get("threshold_policy_authority_ref")
        authority_digest = gate.get("threshold_policy_authority_digest")
        authority_source_digest_set = gate.get("threshold_policy_source_digest_set")
        authority_status = gate.get("threshold_policy_authority_status")
        authority_bound = gate.get("threshold_policy_authority_bound")
        if not isinstance(authority_ref, str):
            errors.append("threshold_policy_authority_ref must be a string")
            authority_ref = ""
        if not isinstance(authority_digest, str):
            errors.append("threshold_policy_authority_digest must be a string")
            authority_digest = ""
        if not isinstance(authority_source_digest_set, str):
            errors.append("threshold_policy_source_digest_set must be a string")
            authority_source_digest_set = ""
        if not isinstance(authority_bound, bool):
            errors.append("threshold_policy_authority_bound must be a boolean")
            authority_bound = False
        if authority_bound:
            if authority_status != "complete":
                errors.append("threshold_policy_authority_status must be complete")
            for field_name, field_value in (
                ("threshold_policy_authority_ref", authority_ref),
                ("threshold_policy_authority_digest", authority_digest),
                ("threshold_policy_source_digest_set", authority_source_digest_set),
            ):
                if not field_value:
                    errors.append(f"{field_name} must be bound")
        else:
            if authority_status != "not-bound":
                errors.append("threshold_policy_authority_status must be not-bound")
            if authority_ref or authority_digest or authority_source_digest_set:
                errors.append("unbound threshold policy authority refs must be empty")
        expected_threshold_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": SENSORY_LOOPBACK_PARTICIPANT_LATENCY_DRIFT_PROFILE,
                    "max_latency_drift_ms": (
                        SENSORY_LOOPBACK_MAX_PARTICIPANT_LATENCY_DRIFT_MS
                    ),
                    "threshold_policy_authority_ref": authority_ref,
                    "threshold_policy_authority_digest": authority_digest,
                    "threshold_policy_source_digest_set": authority_source_digest_set,
                }
            )
        )
        latency_threshold_digest_bound = (
            gate.get("latency_threshold_digest") == expected_threshold_digest
        )
        if not latency_threshold_digest_bound:
            errors.append("latency_threshold_digest mismatch")
        expected_status = (
            "pass"
            if absolute_latency_drift <= SENSORY_LOOPBACK_MAX_PARTICIPANT_LATENCY_DRIFT_MS
            else "blocked"
        )
        if gate.get("latency_drift_status") != expected_status:
            errors.append("latency_drift_status must match latency threshold result")
        for field_name in (
            "raw_timing_payload_stored",
            "raw_hardware_adapter_payload_stored",
            "raw_threshold_policy_payload_stored",
            "raw_authority_payload_stored",
        ):
            if gate.get(field_name) is not False:
                errors.append(f"{field_name} must be false")
        expected_digest = sha256_text(
            canonical_json(self._participant_latency_drift_digest_payload(gate))
        )
        timing_gate_digest_bound = gate.get("timing_gate_digest") == expected_digest
        if not timing_gate_digest_bound:
            errors.append("timing_gate_digest mismatch")

        return {
            "ok": not errors,
            "errors": errors,
            "latency_drift_status": gate.get("latency_drift_status"),
            "absolute_latency_drift_bound": absolute_drift_bound,
            "latency_threshold_digest_bound": latency_threshold_digest_bound,
            "threshold_policy_authority_bound": bool(authority_bound),
            "timing_gate_digest_bound": timing_gate_digest_bound,
            "raw_timing_payload_stored": False,
            "raw_hardware_adapter_payload_stored": False,
            "raw_threshold_policy_payload_stored": False,
            "raw_authority_payload_stored": False,
        }

    def validate_latency_weight_policy_verifier_quorum(
        self,
        quorum: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(quorum, Mapping):
            raise ValueError("quorum must be a mapping")

        errors: List[str] = []
        for field_name in (
            "verifier_quorum_ref",
            "authority_ref",
            "authority_digest",
            "source_digest_set",
            "verifier_response_digest_set",
            "verifier_signature_digest_set",
            "verifier_quorum_digest",
        ):
            self._check_non_empty_string(quorum.get(field_name), field_name, errors)
        if quorum.get("schema_version") != SENSORY_LOOPBACK_SCHEMA_VERSION:
            errors.append(f"schema_version must be {SENSORY_LOOPBACK_SCHEMA_VERSION}")
        if quorum.get("profile_id") != SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_PROFILE:
            errors.append(
                "profile_id must be "
                f"{SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_PROFILE}",
            )
        accepted_refs = quorum.get("accepted_verifier_refs")
        if (
            not isinstance(accepted_refs, list)
            or len(accepted_refs)
            < SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_THRESHOLD
            or len(accepted_refs) != len(set(accepted_refs))
        ):
            errors.append("accepted_verifier_refs must be a unique quorum list")
            accepted_refs = []
        jurisdictions = quorum.get("verifier_jurisdictions")
        if (
            not isinstance(jurisdictions, list)
            or len(jurisdictions)
            < SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_THRESHOLD
            or len(jurisdictions) != len(set(jurisdictions))
        ):
            errors.append("verifier_jurisdictions must be a unique quorum list")
            jurisdictions = []
        receipts = quorum.get("verifier_receipts")
        if not isinstance(receipts, list):
            errors.append("verifier_receipts must be a list")
            receipts = []
        if len(receipts) != len(accepted_refs):
            errors.append("verifier_receipts must match accepted_verifier_refs length")
        if quorum.get("quorum_threshold") != SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_THRESHOLD:
            errors.append(
                "quorum_threshold must be "
                f"{SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_THRESHOLD}",
            )
        if quorum.get("quorum_status") != "complete":
            errors.append("quorum_status must be complete")
        if quorum.get("freshness_window_hours") != SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_FRESHNESS_HOURS:
            errors.append(
                "freshness_window_hours must be "
                f"{SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_FRESHNESS_HOURS}",
            )
        if quorum.get("freshness_status") != "fresh":
            errors.append("freshness_status must be fresh")
        if quorum.get("authority_freshness_bound") is not True:
            errors.append("authority_freshness_bound must be true")
        if quorum.get("source_digest_set_bound") is not True:
            errors.append("source_digest_set_bound must be true")

        authority_ref = quorum.get("authority_ref", "")
        authority_digest = quorum.get("authority_digest", "")
        source_digest_set = quorum.get("source_digest_set", "")
        for index, receipt in enumerate(receipts):
            if not isinstance(receipt, Mapping):
                errors.append(f"verifier_receipts[{index}] must be a mapping")
                continue
            if index < len(accepted_refs) and receipt.get("verifier_ref") != accepted_refs[index]:
                errors.append(
                    f"verifier_receipts[{index}].verifier_ref must follow accepted_verifier_refs order",
                )
            if index < len(jurisdictions) and receipt.get("jurisdiction") != jurisdictions[index]:
                errors.append(
                    f"verifier_receipts[{index}].jurisdiction must follow verifier_jurisdictions order",
                )
            for field_name in (
                "verifier_ref",
                "jurisdiction",
                "observed_at",
                "authority_ref",
                "authority_digest",
                "source_digest_set",
                "response_digest",
                "signing_key_ref",
                "response_signature_digest",
            ):
                self._check_non_empty_string(
                    receipt.get(field_name),
                    f"verifier_receipts[{index}].{field_name}",
                    errors,
                )
            if receipt.get("authority_ref") != authority_ref:
                errors.append(f"verifier_receipts[{index}].authority_ref mismatch")
            if receipt.get("authority_digest") != authority_digest:
                errors.append(f"verifier_receipts[{index}].authority_digest mismatch")
            if receipt.get("source_digest_set") != source_digest_set:
                errors.append(f"verifier_receipts[{index}].source_digest_set mismatch")
            if receipt.get("freshness_window_hours") != SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_FRESHNESS_HOURS:
                errors.append(
                    f"verifier_receipts[{index}].freshness_window_hours mismatch",
                )
            if receipt.get("freshness_status") != "fresh":
                errors.append(f"verifier_receipts[{index}].freshness_status must be fresh")
            if receipt.get("verifier_status") != "accepted":
                errors.append(f"verifier_receipts[{index}].verifier_status must be accepted")
            for field_name in (
                "raw_response_payload_stored",
                "raw_signature_payload_stored",
            ):
                if receipt.get(field_name) is not False:
                    errors.append(f"verifier_receipts[{index}].{field_name} must be false")
            expected_response_digest = sha256_text(
                canonical_json(
                    self._latency_weight_policy_verifier_response_digest_payload(
                        receipt,
                    )
                )
            )
            if receipt.get("response_digest") != expected_response_digest:
                errors.append(f"verifier_receipts[{index}].response_digest mismatch")
            expected_signature_digest = sha256_text(
                canonical_json(
                    self._latency_weight_policy_verifier_signature_digest_payload(
                        receipt,
                    )
                )
            )
            if receipt.get("response_signature_digest") != expected_signature_digest:
                errors.append(
                    f"verifier_receipts[{index}].response_signature_digest mismatch",
                )

        response_digest_set_bound = (
            bool(receipts)
            and quorum.get("verifier_response_digest_set")
            == self._latency_weight_policy_verifier_response_digest_set(receipts)
        )
        if not response_digest_set_bound:
            errors.append("verifier_response_digest_set mismatch")
        signature_digest_set_bound = (
            bool(receipts)
            and quorum.get("verifier_signature_digest_set")
            == self._latency_weight_policy_verifier_signature_digest_set(receipts)
        )
        if not signature_digest_set_bound:
            errors.append("verifier_signature_digest_set mismatch")
        expected_quorum_digest = sha256_text(
            canonical_json(
                self._latency_weight_policy_verifier_quorum_digest_payload(quorum)
            )
        )
        quorum_digest_bound = quorum.get("verifier_quorum_digest") == expected_quorum_digest
        if not quorum_digest_bound:
            errors.append("verifier_quorum_digest mismatch")
        for field_name in (
            "raw_verifier_payload_stored",
            "raw_response_payload_stored",
            "raw_signature_payload_stored",
        ):
            if quorum.get(field_name) is not False:
                errors.append(f"{field_name} must be false")

        return {
            "ok": not errors,
            "errors": errors,
            "quorum_status": quorum.get("quorum_status"),
            "freshness_status": quorum.get("freshness_status"),
            "accepted_verifier_count": len(receipts),
            "response_digest_set_bound": response_digest_set_bound,
            "signature_digest_set_bound": signature_digest_set_bound,
            "quorum_digest_bound": quorum_digest_bound,
            "authority_freshness_bound": quorum.get("authority_freshness_bound") is True,
            "source_digest_set_bound": quorum.get("source_digest_set_bound") is True,
            "raw_verifier_payload_stored": False,
            "raw_response_payload_stored": False,
            "raw_signature_payload_stored": False,
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
        self._check_non_empty_string(
            binding.get("participant_calibration_refresh_digest_set"),
            "participant_calibration_refresh_digest_set",
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
        if binding.get("timing_storage_policy") != SENSORY_LOOPBACK_PARTICIPANT_LATENCY_STORAGE_POLICY:
            errors.append(
                "timing_storage_policy must be "
                f"{SENSORY_LOOPBACK_PARTICIPANT_LATENCY_STORAGE_POLICY}",
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
            if participant_binding.get("calibration_refresh_bound") is not True:
                errors.append(
                    f"participant_gate_bindings[{index}].calibration_refresh_bound must be true",
                )
            if participant_binding.get("calibration_refresh_status") != "fresh":
                errors.append(
                    f"participant_gate_bindings[{index}].calibration_refresh_status must be fresh",
                )
            if participant_binding.get("calibration_refresh_window_bound") is not True:
                errors.append(
                    f"participant_gate_bindings[{index}].calibration_refresh_window_bound must be true",
                )
            for field_name in (
                "calibration_refresh_ref",
                "calibration_refresh_digest",
                "calibration_refresh_source_digest_set",
            ):
                self._check_non_empty_string(
                    participant_binding.get(field_name),
                    f"participant_gate_bindings[{index}].{field_name}",
                    errors,
                )
            authority_bound = participant_binding.get(
                "feature_window_series_threshold_policy_authority_bound"
            )
            authority_status = participant_binding.get(
                "feature_window_series_threshold_policy_authority_status"
            )
            if not isinstance(authority_bound, bool):
                errors.append(
                    f"participant_gate_bindings[{index}].feature_window_series_threshold_policy_authority_bound must be a boolean",
                )
                authority_bound = False
            if authority_bound:
                if authority_status != "complete":
                    errors.append(
                        f"participant_gate_bindings[{index}].feature_window_series_threshold_policy_authority_status must be complete",
                    )
                for field_name in (
                    "feature_window_series_threshold_policy_authority_ref",
                    "feature_window_series_threshold_policy_authority_digest",
                    "feature_window_series_threshold_policy_source_digest_set",
                ):
                    self._check_non_empty_string(
                        participant_binding.get(field_name),
                        f"participant_gate_bindings[{index}].{field_name}",
                        errors,
                    )
            else:
                if authority_status != "not-bound":
                    errors.append(
                        f"participant_gate_bindings[{index}].feature_window_series_threshold_policy_authority_status must be not-bound",
                    )
                for field_name in (
                    "feature_window_series_threshold_policy_authority_ref",
                    "feature_window_series_threshold_policy_authority_digest",
                    "feature_window_series_threshold_policy_source_digest_set",
                ):
                    if participant_binding.get(field_name) not in {"", None}:
                        errors.append(
                            f"participant_gate_bindings[{index}].{field_name} must be empty when unbound",
                        )
            if participant_binding.get("sensory_loopback_gate_bound") is not True:
                errors.append(
                    f"participant_gate_bindings[{index}].sensory_loopback_gate_bound must be true",
                )
            for field_name in (
                "raw_calibration_payload_stored",
                "raw_drift_payload_stored",
                "raw_refresh_payload_stored",
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
        participant_refresh_digest_set_bound = False
        if all(isinstance(item, Mapping) for item in participant_bindings):
            expected_refresh_digest_set = self._participant_calibration_refresh_digest_set(
                participant_bindings,
            )
            participant_refresh_digest_set_bound = (
                bool(participant_bindings)
                and binding.get("participant_calibration_refresh_digest_set")
                == expected_refresh_digest_set
            )
        if not participant_refresh_digest_set_bound:
            errors.append("participant_calibration_refresh_digest_set mismatch")
        participant_latency_bindings = binding.get("participant_latency_bindings")
        if not isinstance(participant_latency_bindings, list):
            errors.append("participant_latency_bindings must be a list")
            participant_latency_bindings = []
        if binding.get("participant_latency_gate_count") != len(participant_latency_bindings):
            errors.append(
                "participant_latency_gate_count must match participant_latency_bindings length",
            )
        if participant_identity_ids and [
            item.get("participant_identity_id")
            for item in participant_latency_bindings
            if isinstance(item, Mapping)
        ] != participant_identity_ids:
            errors.append("participant_latency_bindings must follow participant_identity_ids order")

        latency_validations: List[Dict[str, Any]] = []
        for index, latency_binding in enumerate(participant_latency_bindings):
            if not isinstance(latency_binding, Mapping):
                errors.append(f"participant_latency_bindings[{index}] must be a mapping")
                continue
            latency_validation = self.validate_participant_latency_drift_gate(
                latency_binding,
            )
            latency_validations.append(latency_validation)
            for error in latency_validation["errors"]:
                errors.append(f"participant_latency_bindings[{index}].{error}")
            if isinstance(participant_bindings, list) and index < len(participant_bindings):
                gate_binding = participant_bindings[index]
                if isinstance(gate_binding, Mapping) and gate_binding.get(
                    "feature_window_series_threshold_policy_authority_bound"
                ):
                    if (
                        latency_binding.get("threshold_policy_authority_digest")
                        != gate_binding.get(
                            "feature_window_series_threshold_policy_authority_digest"
                        )
                        or latency_binding.get("threshold_policy_authority_ref")
                        != gate_binding.get(
                            "feature_window_series_threshold_policy_authority_ref"
                        )
                    ):
                        errors.append(
                            f"participant_latency_bindings[{index}] must share the BioData threshold policy authority",
                        )

        participant_latency_digest_set_bound = False
        if all(isinstance(item, Mapping) for item in participant_latency_bindings):
            expected_latency_digest_set = self._participant_latency_drift_digest_set(
                participant_latency_bindings,
            )
            participant_latency_digest_set_bound = (
                bool(participant_latency_bindings)
                and binding.get("participant_latency_digest_set")
                == expected_latency_digest_set
            )
        if not participant_latency_digest_set_bound:
            errors.append("participant_latency_digest_set mismatch")

        (
            latency_quorum_profile,
            latency_quorum_threshold,
            participant_latency_weights,
            participant_latency_weight_digest_bound,
            latency_quorum_pass_weight,
            latency_quorum_failed_participant_ids,
            latency_quorum_satisfied,
            latency_weight_policy_bound,
            latency_weight_policy_digest_bound,
            latency_weight_policy_status,
            latency_weight_policy_verifier_bound,
            latency_weight_policy_verifier_fresh,
            latency_weight_policy_verifier_status,
            latency_weight_policy_verifier_freshness_status,
            latency_quorum_digest_bound,
        ) = self._validate_latency_quorum_fields(
            binding,
            participant_identity_ids,
            participant_latency_bindings,
            binding.get("participant_latency_digest_set", ""),
            errors,
        )
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
        all_calibration_refresh_receipts_fresh = (
            bool(participant_bindings)
            and all(
                isinstance(item, Mapping)
                and item.get("calibration_refresh_bound") is True
                and item.get("calibration_refresh_status") == "fresh"
                for item in participant_bindings
            )
        )
        all_calibration_refresh_windows_bound = (
            bool(participant_bindings)
            and all(
                isinstance(item, Mapping)
                and item.get("calibration_refresh_window_bound") is True
                for item in participant_bindings
            )
        )
        all_latency_gates_passed = (
            bool(participant_latency_bindings)
            and all(
                isinstance(item, Mapping)
                and item.get("latency_drift_status") == "pass"
                for item in participant_latency_bindings
            )
        )
        if (
            latency_quorum_profile == SENSORY_LOOPBACK_LATENCY_QUORUM_STRICT_PROFILE
            and not all_latency_gates_passed
        ):
            errors.append("strict latency quorum requires all participant latency gates to pass")
        if binding.get("all_participant_gates_bound") != all_participant_gates_bound:
            errors.append("all_participant_gates_bound mismatch")
        if binding.get("all_drift_gates_passed") != all_drift_gates_passed:
            errors.append("all_drift_gates_passed mismatch")
        if (
            binding.get("all_calibration_refresh_receipts_fresh")
            != all_calibration_refresh_receipts_fresh
        ):
            errors.append("all_calibration_refresh_receipts_fresh mismatch")
        if (
            binding.get("all_calibration_refresh_windows_bound")
            != all_calibration_refresh_windows_bound
        ):
            errors.append("all_calibration_refresh_windows_bound mismatch")
        if binding.get("calibration_refresh_status") != "fresh":
            errors.append("calibration_refresh_status must be fresh")
        if binding.get("all_latency_gates_passed") != all_latency_gates_passed:
            errors.append("all_latency_gates_passed mismatch")
        expected_status = (
            "pass"
            if all_participant_gates_bound
            and all_drift_gates_passed
            and all_calibration_refresh_receipts_fresh
            and all_calibration_refresh_windows_bound
            and participant_gate_digest_set_bound
            and participant_refresh_digest_set_bound
            and latency_quorum_satisfied
            and participant_latency_digest_set_bound
            and participant_latency_weight_digest_bound
            and latency_weight_policy_digest_bound
            and (
                latency_quorum_profile
                == SENSORY_LOOPBACK_LATENCY_QUORUM_STRICT_PROFILE
                or (
                    latency_weight_policy_verifier_bound
                    and latency_weight_policy_verifier_fresh
                )
            )
            and latency_quorum_digest_bound
            else "blocked"
        )
        if binding.get("arbitration_gate_status") != expected_status:
            errors.append("arbitration_gate_status mismatch")
        if binding.get("latency_gate_status") != expected_status:
            errors.append("latency_gate_status mismatch")
        for field_name in (
            "raw_biodata_payload_stored",
            "raw_calibration_payload_stored",
            "raw_drift_payload_stored",
            "raw_refresh_payload_stored",
            "raw_gate_payload_stored",
            "raw_timing_payload_stored",
            "raw_hardware_adapter_payload_stored",
            "raw_latency_threshold_payload_stored",
            "raw_latency_weight_policy_payload_stored",
            "raw_latency_weight_authority_payload_stored",
            "raw_latency_weight_policy_verifier_payload_stored",
            "raw_latency_weight_policy_verifier_response_payload_stored",
            "raw_latency_weight_policy_verifier_signature_payload_stored",
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
            "participant_calibration_refresh_digest_set_bound": (
                participant_refresh_digest_set_bound
            ),
            "participant_latency_gate_count": len(participant_latency_bindings),
            "participant_latency_digest_set_bound": participant_latency_digest_set_bound,
            "latency_quorum_profile": latency_quorum_profile,
            "latency_quorum_threshold": latency_quorum_threshold,
            "participant_latency_weights": participant_latency_weights,
            "participant_latency_weight_digest_bound": (
                participant_latency_weight_digest_bound
            ),
            "latency_quorum_pass_weight": latency_quorum_pass_weight,
            "latency_quorum_failed_participant_ids": latency_quorum_failed_participant_ids,
            "latency_quorum_satisfied": latency_quorum_satisfied,
            "latency_weight_policy_bound": latency_weight_policy_bound,
            "latency_weight_policy_digest_bound": latency_weight_policy_digest_bound,
            "latency_weight_policy_status": latency_weight_policy_status,
            "latency_weight_policy_verifier_bound": (
                latency_weight_policy_verifier_bound
            ),
            "latency_weight_policy_verifier_fresh": (
                latency_weight_policy_verifier_fresh
            ),
            "latency_weight_policy_verifier_status": (
                latency_weight_policy_verifier_status
            ),
            "latency_weight_policy_verifier_freshness_status": (
                latency_weight_policy_verifier_freshness_status
            ),
            "latency_quorum_digest_bound": latency_quorum_digest_bound,
            "binding_digest_bound": binding_digest_bound,
            "all_participant_gates_bound": all_participant_gates_bound,
            "all_drift_gates_passed": all_drift_gates_passed,
            "all_calibration_refresh_receipts_fresh": (
                all_calibration_refresh_receipts_fresh
            ),
            "all_calibration_refresh_windows_bound": (
                all_calibration_refresh_windows_bound
            ),
            "all_latency_gates_passed": all_latency_gates_passed,
            "arbitration_gate_status": binding.get("arbitration_gate_status"),
            "latency_gate_status": binding.get("latency_gate_status"),
            "raw_biodata_payload_stored": False,
            "raw_calibration_payload_stored": False,
            "raw_drift_payload_stored": False,
            "raw_refresh_payload_stored": False,
            "raw_gate_payload_stored": False,
            "raw_timing_payload_stored": False,
            "raw_hardware_adapter_payload_stored": False,
            "raw_latency_threshold_payload_stored": False,
            "raw_latency_weight_policy_payload_stored": False,
            "raw_latency_weight_authority_payload_stored": False,
            "raw_latency_weight_policy_verifier_payload_stored": False,
            "raw_latency_weight_policy_verifier_response_payload_stored": False,
            "raw_latency_weight_policy_verifier_signature_payload_stored": False,
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

    def _derive_latency_quorum_policy(
        self,
        *,
        participant_ids: Sequence[str],
        participant_latency_weights: Optional[Mapping[str, float]],
        latency_quorum_threshold: Optional[float],
        latency_weight_policy_authority_ref: str,
        latency_weight_policy_authority_digest: str,
        latency_weight_policy_source_digest_set: str,
        latency_weight_policy_verifier_quorum: Optional[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        weight_policy_authority_ref = self._normalize_string(
            latency_weight_policy_authority_ref,
            "latency_weight_policy_authority_ref",
        )
        weight_policy_authority_digest = self._normalize_string(
            latency_weight_policy_authority_digest,
            "latency_weight_policy_authority_digest",
        )
        weight_policy_source_digest_set = self._normalize_string(
            latency_weight_policy_source_digest_set,
            "latency_weight_policy_source_digest_set",
        )
        weighted_requested = (
            participant_latency_weights is not None
            or latency_quorum_threshold is not None
        )
        if not weighted_requested:
            if latency_weight_policy_verifier_quorum is not None:
                raise ValueError(
                    "latency weight policy verifier quorum is only valid for weighted quorum",
                )
            if (
                weight_policy_authority_ref
                or weight_policy_authority_digest
                or weight_policy_source_digest_set
            ):
                raise ValueError(
                    "latency weight policy authority is only valid for weighted quorum",
                )
            return {
                "profile_id": SENSORY_LOOPBACK_LATENCY_QUORUM_STRICT_PROFILE,
                "threshold": 1.0,
                "weights": self._equal_participant_latency_weights(participant_ids),
                "weight_policy_profile": "not-bound",
                "weight_policy_authority_ref": "",
                "weight_policy_authority_digest": "",
                "weight_policy_source_digest_set": "",
                "weight_policy_status": "not-bound",
                "weight_policy_bound": False,
                "weight_policy_verifier_profile": "not-bound",
                "weight_policy_verifier_quorum_ref": "",
                "weight_policy_verifier_quorum_digest": "",
                "weight_policy_verifier_source_digest_set": "",
                "weight_policy_verifier_status": "not-bound",
                "weight_policy_verifier_freshness_status": "not-bound",
                "weight_policy_verifier_bound": False,
                "weight_policy_verifier_fresh": False,
            }
        if participant_latency_weights is None:
            raise ValueError("participant_latency_weights are required for weighted quorum")
        for field_name, field_value in (
            ("latency_weight_policy_authority_ref", weight_policy_authority_ref),
            ("latency_weight_policy_authority_digest", weight_policy_authority_digest),
            ("latency_weight_policy_source_digest_set", weight_policy_source_digest_set),
        ):
            if not field_value:
                raise ValueError(
                    "weighted latency quorum requires "
                    f"{field_name} binding",
                )
        if len(participant_ids) < SENSORY_LOOPBACK_WEIGHTED_LATENCY_MIN_PARTICIPANTS:
            raise ValueError(
                "weighted latency quorum requires at least "
                f"{SENSORY_LOOPBACK_WEIGHTED_LATENCY_MIN_PARTICIPANTS} participants",
            )
        if latency_weight_policy_verifier_quorum is None:
            raise ValueError(
                "weighted latency quorum requires latency_weight_policy_verifier_quorum",
            )
        verifier_validation = self.validate_latency_weight_policy_verifier_quorum(
            latency_weight_policy_verifier_quorum,
        )
        if not verifier_validation["ok"]:
            raise ValueError(
                "latency weight policy verifier quorum is invalid: "
                + "; ".join(verifier_validation["errors"]),
            )
        if (
            latency_weight_policy_verifier_quorum.get("authority_ref")
            != weight_policy_authority_ref
            or latency_weight_policy_verifier_quorum.get("authority_digest")
            != weight_policy_authority_digest
            or latency_weight_policy_verifier_quorum.get("source_digest_set")
            != weight_policy_source_digest_set
        ):
            raise ValueError(
                "latency weight policy verifier quorum must bind the same authority and source digest set",
            )
        weights = self._normalize_participant_latency_weights(
            participant_ids,
            participant_latency_weights,
        )
        threshold = (
            0.67
            if latency_quorum_threshold is None
            else round(
                self._normalize_score(latency_quorum_threshold, "latency_quorum_threshold"),
                6,
            )
        )
        if threshold <= 0:
            raise ValueError("latency_quorum_threshold must be greater than 0")
        return {
            "profile_id": SENSORY_LOOPBACK_LATENCY_QUORUM_WEIGHTED_PROFILE,
            "threshold": threshold,
            "weights": weights,
            "weight_policy_profile": SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_PROFILE,
            "weight_policy_authority_ref": weight_policy_authority_ref,
            "weight_policy_authority_digest": weight_policy_authority_digest,
            "weight_policy_source_digest_set": weight_policy_source_digest_set,
            "weight_policy_status": "complete",
            "weight_policy_bound": True,
            "weight_policy_verifier_profile": (
                SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_PROFILE
            ),
            "weight_policy_verifier_quorum_ref": str(
                latency_weight_policy_verifier_quorum["verifier_quorum_ref"]
            ),
            "weight_policy_verifier_quorum_digest": str(
                latency_weight_policy_verifier_quorum["verifier_quorum_digest"]
            ),
            "weight_policy_verifier_source_digest_set": str(
                latency_weight_policy_verifier_quorum["source_digest_set"]
            ),
            "weight_policy_verifier_status": str(
                latency_weight_policy_verifier_quorum["quorum_status"]
            ),
            "weight_policy_verifier_freshness_status": str(
                latency_weight_policy_verifier_quorum["freshness_status"]
            ),
            "weight_policy_verifier_bound": True,
            "weight_policy_verifier_fresh": True,
        }

    @staticmethod
    def _equal_participant_latency_weights(
        participant_ids: Sequence[str],
    ) -> Dict[str, float]:
        base_weight = round(1.0 / len(participant_ids), 6)
        weights: Dict[str, float] = {}
        assigned = 0.0
        for participant_id in participant_ids[:-1]:
            weights[participant_id] = base_weight
            assigned = round(assigned + base_weight, 6)
        weights[participant_ids[-1]] = round(1.0 - assigned, 6)
        return weights

    def _normalize_participant_latency_weights(
        self,
        participant_ids: Sequence[str],
        participant_latency_weights: Mapping[str, float],
    ) -> Dict[str, float]:
        if not isinstance(participant_latency_weights, Mapping):
            raise ValueError("participant_latency_weights must be a mapping")
        if set(participant_latency_weights) != set(participant_ids):
            raise ValueError(
                "participant_latency_weights must cover exactly participant_identity_ids",
            )
        weights: Dict[str, float] = {}
        for participant_id in participant_ids:
            weight = self._normalize_score(
                participant_latency_weights.get(participant_id),
                f"participant_latency_weights.{participant_id}",
            )
            if weight <= 0:
                raise ValueError("participant latency weights must be greater than 0")
            weights[participant_id] = round(weight, 6)
        if round(sum(weights.values()), 6) != 1.0:
            raise ValueError("participant_latency_weights must sum to 1.0")
        return weights

    def _evaluate_latency_quorum(
        self,
        *,
        policy: Mapping[str, Any],
        participant_latency_passed: Mapping[str, bool],
        participant_latency_digest_set: str,
    ) -> Dict[str, Any]:
        weights = dict(policy["weights"])
        pass_weight = round(
            sum(
                weights[participant_id]
                for participant_id, passed in participant_latency_passed.items()
                if passed
            ),
            6,
        )
        failed_participant_ids = [
            participant_id
            for participant_id, passed in participant_latency_passed.items()
            if not passed
        ]
        all_latency_gates_passed = not failed_participant_ids
        if policy["profile_id"] == SENSORY_LOOPBACK_LATENCY_QUORUM_STRICT_PROFILE:
            satisfied = all_latency_gates_passed
        else:
            satisfied = pass_weight >= policy["threshold"]
        participant_latency_weight_digest = self._participant_latency_weight_digest(
            policy["profile_id"],
            policy["threshold"],
            weights,
        )
        latency_weight_policy_digest = self._latency_weight_policy_digest(
            profile_id=policy["profile_id"],
            threshold=policy["threshold"],
            participant_latency_weights=weights,
            participant_latency_weight_digest=participant_latency_weight_digest,
            weight_policy_profile=str(policy["weight_policy_profile"]),
            weight_policy_authority_ref=str(policy["weight_policy_authority_ref"]),
            weight_policy_authority_digest=str(
                policy["weight_policy_authority_digest"],
            ),
            weight_policy_source_digest_set=str(
                policy["weight_policy_source_digest_set"],
            ),
            weight_policy_status=str(policy["weight_policy_status"]),
            weight_policy_bound=bool(policy["weight_policy_bound"]),
            weight_policy_verifier_profile=str(
                policy["weight_policy_verifier_profile"]
            ),
            weight_policy_verifier_quorum_ref=str(
                policy["weight_policy_verifier_quorum_ref"]
            ),
            weight_policy_verifier_quorum_digest=str(
                policy["weight_policy_verifier_quorum_digest"]
            ),
            weight_policy_verifier_source_digest_set=str(
                policy["weight_policy_verifier_source_digest_set"]
            ),
            weight_policy_verifier_status=str(
                policy["weight_policy_verifier_status"]
            ),
            weight_policy_verifier_freshness_status=str(
                policy["weight_policy_verifier_freshness_status"]
            ),
            weight_policy_verifier_bound=bool(
                policy["weight_policy_verifier_bound"]
            ),
            weight_policy_verifier_fresh=bool(
                policy["weight_policy_verifier_fresh"]
            ),
        )
        latency_quorum_digest = self._latency_quorum_digest(
            profile_id=policy["profile_id"],
            threshold=policy["threshold"],
            participant_latency_weights=weights,
            participant_latency_weight_digest=participant_latency_weight_digest,
            latency_weight_policy_digest=latency_weight_policy_digest,
            participant_latency_digest_set=participant_latency_digest_set,
            pass_weight=pass_weight,
            failed_participant_ids=failed_participant_ids,
            satisfied=satisfied,
        )
        return {
            "all_latency_gates_passed": all_latency_gates_passed,
            "pass_weight": pass_weight,
            "failed_participant_ids": failed_participant_ids,
            "satisfied": satisfied,
            "status": "pass" if satisfied else "blocked",
            "participant_latency_weight_digest": participant_latency_weight_digest,
            "latency_weight_policy_digest": latency_weight_policy_digest,
            "digest": latency_quorum_digest,
        }

    def _validate_latency_quorum_fields(
        self,
        binding: Mapping[str, Any],
        participant_identity_ids: Sequence[str],
        participant_latency_bindings: Sequence[Mapping[str, Any]],
        participant_latency_digest_set: Any,
        errors: List[str],
    ) -> Tuple[
        str,
        float,
        Dict[str, float],
        bool,
        float,
        List[str],
        bool,
        bool,
        bool,
        str,
        bool,
        bool,
        str,
        str,
        bool,
    ]:
        profile = binding.get("latency_quorum_profile")
        if profile not in {
            SENSORY_LOOPBACK_LATENCY_QUORUM_STRICT_PROFILE,
            SENSORY_LOOPBACK_LATENCY_QUORUM_WEIGHTED_PROFILE,
        }:
            errors.append("latency_quorum_profile must be a known profile")
            profile = SENSORY_LOOPBACK_LATENCY_QUORUM_STRICT_PROFILE
        threshold = self._normalize_score_for_validation(
            binding.get("latency_quorum_threshold"),
            "latency_quorum_threshold",
            errors,
        )
        if threshold <= 0:
            errors.append("latency_quorum_threshold must be greater than 0")
        if profile == SENSORY_LOOPBACK_LATENCY_QUORUM_STRICT_PROFILE and threshold != 1.0:
            errors.append("strict latency quorum threshold must be 1.0")
        weights_value = binding.get("participant_latency_weights")
        weights: Dict[str, float] = {}
        if not isinstance(weights_value, Mapping):
            errors.append("participant_latency_weights must be a mapping")
        elif set(weights_value) != set(participant_identity_ids):
            errors.append(
                "participant_latency_weights must cover exactly participant_identity_ids",
            )
        else:
            for participant_id in participant_identity_ids:
                weights[participant_id] = self._normalize_score_for_validation(
                    weights_value.get(participant_id),
                    f"participant_latency_weights.{participant_id}",
                    errors,
                )
                if weights[participant_id] <= 0:
                    errors.append("participant latency weights must be greater than 0")
            if round(sum(weights.values()), 6) != 1.0:
                errors.append("participant_latency_weights must sum to 1.0")
        if not weights and participant_identity_ids:
            weights = self._equal_participant_latency_weights(participant_identity_ids)
        if (
            profile == SENSORY_LOOPBACK_LATENCY_QUORUM_WEIGHTED_PROFILE
            and len(participant_identity_ids)
            < SENSORY_LOOPBACK_WEIGHTED_LATENCY_MIN_PARTICIPANTS
        ):
            errors.append("weighted latency quorum requires at least 3 participants")

        expected_weight_digest = self._participant_latency_weight_digest(
            str(profile),
            threshold,
            weights,
        )
        participant_latency_weight_digest_bound = (
            binding.get("participant_latency_weight_digest") == expected_weight_digest
        )
        if not participant_latency_weight_digest_bound:
            errors.append("participant_latency_weight_digest mismatch")
        weight_policy_profile = binding.get("latency_weight_policy_profile")
        weight_policy_authority_ref = self._normalize_string_for_validation(
            binding.get("latency_weight_policy_authority_ref", ""),
            "latency_weight_policy_authority_ref",
            errors,
        )
        weight_policy_authority_digest = self._normalize_string_for_validation(
            binding.get("latency_weight_policy_authority_digest", ""),
            "latency_weight_policy_authority_digest",
            errors,
        )
        weight_policy_source_digest_set = self._normalize_string_for_validation(
            binding.get("latency_weight_policy_source_digest_set", ""),
            "latency_weight_policy_source_digest_set",
            errors,
        )
        weight_policy_status = binding.get("latency_weight_policy_status")
        if weight_policy_status not in {"complete", "not-bound"}:
            errors.append("latency_weight_policy_status must be complete or not-bound")
            weight_policy_status = "not-bound"
        weight_policy_bound = binding.get("latency_weight_policy_bound")
        if not isinstance(weight_policy_bound, bool):
            errors.append("latency_weight_policy_bound must be a boolean")
            weight_policy_bound = False
        weight_policy_verifier_profile = binding.get(
            "latency_weight_policy_verifier_profile",
        )
        weight_policy_verifier_quorum_ref = self._normalize_string_for_validation(
            binding.get("latency_weight_policy_verifier_quorum_ref", ""),
            "latency_weight_policy_verifier_quorum_ref",
            errors,
        )
        weight_policy_verifier_quorum_digest = self._normalize_string_for_validation(
            binding.get("latency_weight_policy_verifier_quorum_digest", ""),
            "latency_weight_policy_verifier_quorum_digest",
            errors,
        )
        weight_policy_verifier_source_digest_set = self._normalize_string_for_validation(
            binding.get("latency_weight_policy_verifier_source_digest_set", ""),
            "latency_weight_policy_verifier_source_digest_set",
            errors,
        )
        weight_policy_verifier_status = binding.get(
            "latency_weight_policy_verifier_status",
        )
        weight_policy_verifier_freshness_status = binding.get(
            "latency_weight_policy_verifier_freshness_status",
        )
        weight_policy_verifier_bound = binding.get(
            "latency_weight_policy_verifier_bound",
        )
        if not isinstance(weight_policy_verifier_bound, bool):
            errors.append("latency_weight_policy_verifier_bound must be a boolean")
            weight_policy_verifier_bound = False
        weight_policy_verifier_fresh = binding.get(
            "latency_weight_policy_verifier_fresh",
        )
        if not isinstance(weight_policy_verifier_fresh, bool):
            errors.append("latency_weight_policy_verifier_fresh must be a boolean")
            weight_policy_verifier_fresh = False
        if profile == SENSORY_LOOPBACK_LATENCY_QUORUM_WEIGHTED_PROFILE:
            if weight_policy_profile != SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_PROFILE:
                errors.append(
                    "weighted latency quorum must bind latency weight policy profile",
                )
            if weight_policy_status != "complete":
                errors.append(
                    "weighted latency quorum policy authority must be complete",
                )
            if weight_policy_bound is not True:
                errors.append("weighted latency quorum policy authority must be bound")
            for field_name, field_value in (
                ("latency_weight_policy_authority_ref", weight_policy_authority_ref),
                (
                    "latency_weight_policy_authority_digest",
                    weight_policy_authority_digest,
                ),
                (
                    "latency_weight_policy_source_digest_set",
                    weight_policy_source_digest_set,
                ),
            ):
                if not field_value:
                    errors.append(f"{field_name} must be bound for weighted quorum")
            if (
                weight_policy_verifier_profile
                != SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_PROFILE
            ):
                errors.append(
                    "weighted latency quorum must bind live verifier quorum profile",
                )
            if weight_policy_verifier_status != "complete":
                errors.append(
                    "weighted latency quorum verifier quorum must be complete",
                )
            if weight_policy_verifier_freshness_status != "fresh":
                errors.append(
                    "weighted latency quorum verifier quorum must be fresh",
                )
            if weight_policy_verifier_bound is not True:
                errors.append("weighted latency quorum verifier quorum must be bound")
            if weight_policy_verifier_fresh is not True:
                errors.append("weighted latency quorum verifier quorum must be fresh")
            for field_name, field_value in (
                (
                    "latency_weight_policy_verifier_quorum_ref",
                    weight_policy_verifier_quorum_ref,
                ),
                (
                    "latency_weight_policy_verifier_quorum_digest",
                    weight_policy_verifier_quorum_digest,
                ),
                (
                    "latency_weight_policy_verifier_source_digest_set",
                    weight_policy_verifier_source_digest_set,
                ),
            ):
                if not field_value:
                    errors.append(f"{field_name} must be bound for weighted quorum")
            if weight_policy_verifier_source_digest_set != weight_policy_source_digest_set:
                errors.append(
                    "latency_weight_policy_verifier_source_digest_set must match latency_weight_policy_source_digest_set",
                )
        else:
            if weight_policy_profile != "not-bound":
                errors.append("strict latency quorum must not bind weight policy profile")
            if weight_policy_status != "not-bound":
                errors.append("strict latency quorum weight policy status must be not-bound")
            if weight_policy_bound is not False:
                errors.append("strict latency quorum weight policy must not be bound")
            if (
                weight_policy_authority_ref
                or weight_policy_authority_digest
                or weight_policy_source_digest_set
            ):
                errors.append("strict latency quorum weight policy authority must be empty")
            if weight_policy_verifier_profile != "not-bound":
                errors.append("strict latency quorum must not bind verifier profile")
            if weight_policy_verifier_status != "not-bound":
                errors.append("strict latency quorum verifier status must be not-bound")
            if weight_policy_verifier_freshness_status != "not-bound":
                errors.append(
                    "strict latency quorum verifier freshness status must be not-bound",
                )
            if weight_policy_verifier_bound is not False:
                errors.append("strict latency quorum verifier must not be bound")
            if weight_policy_verifier_fresh is not False:
                errors.append("strict latency quorum verifier must not be fresh")
            if (
                weight_policy_verifier_quorum_ref
                or weight_policy_verifier_quorum_digest
                or weight_policy_verifier_source_digest_set
            ):
                errors.append("strict latency quorum verifier refs must be empty")
        expected_weight_policy_digest = self._latency_weight_policy_digest(
            profile_id=str(profile),
            threshold=threshold,
            participant_latency_weights=weights,
            participant_latency_weight_digest=expected_weight_digest,
            weight_policy_profile=str(weight_policy_profile),
            weight_policy_authority_ref=weight_policy_authority_ref,
            weight_policy_authority_digest=weight_policy_authority_digest,
            weight_policy_source_digest_set=weight_policy_source_digest_set,
            weight_policy_status=str(weight_policy_status),
            weight_policy_bound=bool(weight_policy_bound),
            weight_policy_verifier_profile=str(weight_policy_verifier_profile),
            weight_policy_verifier_quorum_ref=weight_policy_verifier_quorum_ref,
            weight_policy_verifier_quorum_digest=(
                weight_policy_verifier_quorum_digest
            ),
            weight_policy_verifier_source_digest_set=(
                weight_policy_verifier_source_digest_set
            ),
            weight_policy_verifier_status=str(weight_policy_verifier_status),
            weight_policy_verifier_freshness_status=str(
                weight_policy_verifier_freshness_status
            ),
            weight_policy_verifier_bound=bool(weight_policy_verifier_bound),
            weight_policy_verifier_fresh=bool(weight_policy_verifier_fresh),
        )
        latency_weight_policy_digest_bound = (
            binding.get("latency_weight_policy_digest") == expected_weight_policy_digest
        )
        if not latency_weight_policy_digest_bound:
            errors.append("latency_weight_policy_digest mismatch")

        passed_by_participant = {
            binding_item.get("participant_identity_id"): (
                binding_item.get("latency_drift_status") == "pass"
            )
            for binding_item in participant_latency_bindings
            if isinstance(binding_item, Mapping)
        }
        failed_participant_ids = [
            participant_id
            for participant_id in participant_identity_ids
            if not passed_by_participant.get(participant_id, False)
        ]
        expected_pass_weight = round(
            sum(
                weights.get(participant_id, 0.0)
                for participant_id in participant_identity_ids
                if passed_by_participant.get(participant_id, False)
            ),
            6,
        )
        if binding.get("latency_quorum_pass_weight") != expected_pass_weight:
            errors.append("latency_quorum_pass_weight mismatch")
        if binding.get("latency_quorum_failed_participant_ids") != failed_participant_ids:
            errors.append("latency_quorum_failed_participant_ids mismatch")
        expected_satisfied = (
            not failed_participant_ids
            if profile == SENSORY_LOOPBACK_LATENCY_QUORUM_STRICT_PROFILE
            else expected_pass_weight >= threshold
        )
        if binding.get("latency_quorum_satisfied") != expected_satisfied:
            errors.append("latency_quorum_satisfied mismatch")
        expected_quorum_status = "pass" if expected_satisfied else "blocked"
        if binding.get("latency_quorum_status") != expected_quorum_status:
            errors.append("latency_quorum_status mismatch")
        expected_quorum_digest = self._latency_quorum_digest(
            profile_id=str(profile),
            threshold=threshold,
            participant_latency_weights=weights,
            participant_latency_weight_digest=expected_weight_digest,
            latency_weight_policy_digest=expected_weight_policy_digest,
            participant_latency_digest_set=str(participant_latency_digest_set),
            pass_weight=expected_pass_weight,
            failed_participant_ids=failed_participant_ids,
            satisfied=expected_satisfied,
        )
        latency_quorum_digest_bound = (
            binding.get("latency_quorum_digest") == expected_quorum_digest
        )
        if not latency_quorum_digest_bound:
            errors.append("latency_quorum_digest mismatch")
        return (
            str(profile),
            threshold,
            weights,
            participant_latency_weight_digest_bound,
            expected_pass_weight,
            failed_participant_ids,
            expected_satisfied,
            bool(weight_policy_bound),
            latency_weight_policy_digest_bound,
            str(weight_policy_status),
            bool(weight_policy_verifier_bound),
            bool(weight_policy_verifier_fresh),
            str(weight_policy_verifier_status),
            str(weight_policy_verifier_freshness_status),
            latency_quorum_digest_bound,
        )

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
                            "feature_window_series_threshold_policy_authority_digest": binding.get(
                                "feature_window_series_threshold_policy_authority_digest"
                            ),
                            "feature_window_series_threshold_policy_source_digest_set": binding.get(
                                "feature_window_series_threshold_policy_source_digest_set"
                            ),
                            "calibration_refresh_digest": binding.get(
                                "calibration_refresh_digest"
                            ),
                            "calibration_refresh_source_digest_set": binding.get(
                                "calibration_refresh_source_digest_set"
                            ),
                            "calibration_refresh_status": binding.get(
                                "calibration_refresh_status"
                            ),
                            "calibration_refresh_window_bound": binding.get(
                                "calibration_refresh_window_bound"
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
    def _participant_calibration_refresh_digest_set(
        participant_bindings: Sequence[Mapping[str, Any]],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": SENSORY_LOOPBACK_PARTICIPANT_REFRESH_PROPAGATION_PROFILE,
                    "participant_calibration_refresh_bindings": [
                        {
                            "participant_identity_id": binding.get(
                                "participant_identity_id"
                            ),
                            "calibration_refresh_digest": binding.get(
                                "calibration_refresh_digest"
                            ),
                            "calibration_refresh_source_digest_set": binding.get(
                                "calibration_refresh_source_digest_set"
                            ),
                            "calibration_refresh_status": binding.get(
                                "calibration_refresh_status"
                            ),
                            "calibration_refresh_window_bound": binding.get(
                                "calibration_refresh_window_bound"
                            ),
                        }
                        for binding in participant_bindings
                    ],
                }
            )
        )

    @staticmethod
    def _participant_latency_drift_digest_set(
        participant_latency_bindings: Sequence[Mapping[str, Any]],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": SENSORY_LOOPBACK_PARTICIPANT_LATENCY_DRIFT_PROFILE,
                    "participant_latency_bindings": [
                        {
                            "participant_identity_id": binding.get(
                                "participant_identity_id"
                            ),
                            "timing_gate_digest": binding.get("timing_gate_digest"),
                            "latency_threshold_digest": binding.get(
                                "latency_threshold_digest"
                            ),
                            "threshold_policy_authority_digest": binding.get(
                                "threshold_policy_authority_digest"
                            ),
                            "threshold_policy_source_digest_set": binding.get(
                                "threshold_policy_source_digest_set"
                            ),
                        }
                        for binding in participant_latency_bindings
                    ],
                }
            )
        )

    @staticmethod
    def _latency_weight_policy_verifier_response_digest_set(
        verifier_receipts: Sequence[Mapping[str, Any]],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_PROFILE,
                    "verifier_response_digests": [
                        {
                            "verifier_ref": receipt.get("verifier_ref"),
                            "jurisdiction": receipt.get("jurisdiction"),
                            "response_digest": receipt.get("response_digest"),
                            "freshness_status": receipt.get("freshness_status"),
                        }
                        for receipt in verifier_receipts
                    ],
                }
            )
        )

    @staticmethod
    def _latency_weight_policy_verifier_signature_digest_set(
        verifier_receipts: Sequence[Mapping[str, Any]],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_PROFILE,
                    "verifier_signature_digests": [
                        {
                            "verifier_ref": receipt.get("verifier_ref"),
                            "jurisdiction": receipt.get("jurisdiction"),
                            "response_signature_digest": receipt.get(
                                "response_signature_digest"
                            ),
                            "signing_key_ref": receipt.get("signing_key_ref"),
                        }
                        for receipt in verifier_receipts
                    ],
                }
            )
        )

    @staticmethod
    def _latency_weight_policy_verifier_response_digest_payload(
        receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        return {
            "profile_id": SENSORY_LOOPBACK_LATENCY_WEIGHT_POLICY_VERIFIER_PROFILE,
            "verifier_ref": receipt.get("verifier_ref"),
            "jurisdiction": receipt.get("jurisdiction"),
            "authority_ref": receipt.get("authority_ref"),
            "authority_digest": receipt.get("authority_digest"),
            "source_digest_set": receipt.get("source_digest_set"),
            "observed_at": receipt.get("observed_at"),
            "freshness_window_hours": receipt.get("freshness_window_hours"),
            "freshness_status": receipt.get("freshness_status"),
            "verifier_status": receipt.get("verifier_status"),
        }

    @staticmethod
    def _latency_weight_policy_verifier_signature_digest_payload(
        receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        return {
            "verifier_ref": receipt.get("verifier_ref"),
            "jurisdiction": receipt.get("jurisdiction"),
            "response_digest": receipt.get("response_digest"),
            "signing_key_ref": receipt.get("signing_key_ref"),
        }

    @staticmethod
    def _latency_weight_policy_verifier_quorum_digest_payload(
        quorum: Mapping[str, Any],
    ) -> Dict[str, Any]:
        payload = dict(quorum)
        payload.pop("verifier_quorum_digest", None)
        return payload

    @staticmethod
    def _participant_latency_weight_digest(
        profile_id: str,
        threshold: float,
        participant_latency_weights: Mapping[str, float],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": profile_id,
                    "latency_quorum_threshold": threshold,
                    "participant_latency_weights": dict(participant_latency_weights),
                }
            )
        )

    @staticmethod
    def _latency_weight_policy_digest(
        *,
        profile_id: str,
        threshold: float,
        participant_latency_weights: Mapping[str, float],
        participant_latency_weight_digest: str,
        weight_policy_profile: str,
        weight_policy_authority_ref: str,
        weight_policy_authority_digest: str,
        weight_policy_source_digest_set: str,
        weight_policy_status: str,
        weight_policy_bound: bool,
        weight_policy_verifier_profile: str,
        weight_policy_verifier_quorum_ref: str,
        weight_policy_verifier_quorum_digest: str,
        weight_policy_verifier_source_digest_set: str,
        weight_policy_verifier_status: str,
        weight_policy_verifier_freshness_status: str,
        weight_policy_verifier_bound: bool,
        weight_policy_verifier_fresh: bool,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": profile_id,
                    "latency_quorum_threshold": threshold,
                    "participant_latency_weights": dict(participant_latency_weights),
                    "participant_latency_weight_digest": (
                        participant_latency_weight_digest
                    ),
                    "latency_weight_policy_profile": weight_policy_profile,
                    "latency_weight_policy_authority_ref": (
                        weight_policy_authority_ref
                    ),
                    "latency_weight_policy_authority_digest": (
                        weight_policy_authority_digest
                    ),
                    "latency_weight_policy_source_digest_set": (
                        weight_policy_source_digest_set
                    ),
                    "latency_weight_policy_status": weight_policy_status,
                    "latency_weight_policy_bound": weight_policy_bound,
                    "latency_weight_policy_verifier_profile": (
                        weight_policy_verifier_profile
                    ),
                    "latency_weight_policy_verifier_quorum_ref": (
                        weight_policy_verifier_quorum_ref
                    ),
                    "latency_weight_policy_verifier_quorum_digest": (
                        weight_policy_verifier_quorum_digest
                    ),
                    "latency_weight_policy_verifier_source_digest_set": (
                        weight_policy_verifier_source_digest_set
                    ),
                    "latency_weight_policy_verifier_status": (
                        weight_policy_verifier_status
                    ),
                    "latency_weight_policy_verifier_freshness_status": (
                        weight_policy_verifier_freshness_status
                    ),
                    "latency_weight_policy_verifier_bound": (
                        weight_policy_verifier_bound
                    ),
                    "latency_weight_policy_verifier_fresh": (
                        weight_policy_verifier_fresh
                    ),
                }
            )
        )

    @staticmethod
    def _latency_quorum_digest(
        *,
        profile_id: str,
        threshold: float,
        participant_latency_weights: Mapping[str, float],
        participant_latency_weight_digest: str,
        latency_weight_policy_digest: str,
        participant_latency_digest_set: str,
        pass_weight: float,
        failed_participant_ids: Sequence[str],
        satisfied: bool,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": profile_id,
                    "latency_quorum_threshold": threshold,
                    "participant_latency_weights": dict(participant_latency_weights),
                    "participant_latency_weight_digest": participant_latency_weight_digest,
                    "latency_weight_policy_digest": latency_weight_policy_digest,
                    "participant_latency_digest_set": participant_latency_digest_set,
                    "latency_quorum_pass_weight": pass_weight,
                    "latency_quorum_failed_participant_ids": list(
                        failed_participant_ids
                    ),
                    "latency_quorum_satisfied": satisfied,
                }
            )
        )

    @staticmethod
    def _participant_latency_drift_digest_payload(
        gate: Mapping[str, Any],
    ) -> Dict[str, Any]:
        payload = dict(gate)
        payload.pop("timing_gate_digest", None)
        return payload

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
    def _normalize_string_for_validation(
        value: Any,
        name: str,
        errors: List[str],
    ) -> str:
        if not isinstance(value, str):
            errors.append(f"{name} must be a string")
            return ""
        return value.strip()

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
