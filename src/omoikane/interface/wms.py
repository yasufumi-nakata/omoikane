"""World Model Sync reference model."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

WMS_SCHEMA_VERSION = "1.0"
WMS_MINOR_DIFF_THRESHOLD = 0.05
WMS_DEFAULT_TIME_RATE = 1.0
WMS_TIME_RATE_POLICY_ID = "fixed-time-rate-private-escape-v1"
WMS_TIME_RATE_DEVIATION_DIGEST_PROFILE = "baseline-requested-time-rate-delta-v1"
WMS_TIME_RATE_ATTESTATION_POLICY_ID = "subjective-time-attestation-transport-v1"
WMS_TIME_RATE_ATTESTATION_DIGEST_PROFILE = "participant-subjective-time-attestation-set-v1"
WMS_TIME_RATE_ATTESTATION_KIND = "imc"
WMS_TIME_RATE_ATTESTATION_DECISION = "attest"
WMS_DEFAULT_PHYSICS_RULES_REF = "baseline-physical-consensus-v1"
WMS_PHYSICS_CHANGE_POLICY_ID = "unanimous-reversible-physics-rules-v1"
WMS_APPROVAL_TRANSPORT_POLICY_ID = "imc-participant-approval-transport-v1"
WMS_APPROVAL_COLLECTION_POLICY_ID = "bounded-wms-approval-collection-v1"
WMS_APPROVAL_FANOUT_POLICY_ID = "distributed-council-approval-fanout-v1"
WMS_APPROVAL_FANOUT_DIGEST_PROFILE = "transport-result-bound-approval-fanout-v1"
WMS_APPROVAL_FANOUT_COUNCIL_TIER = "federation"
WMS_APPROVAL_FANOUT_TRANSPORT_PROFILE = "federation-mtls-quorum-v1"
WMS_APPROVAL_FANOUT_RETRY_POLICY_ID = "bounded-distributed-approval-fanout-retry-v1"
WMS_APPROVAL_FANOUT_RETRY_DIGEST_PROFILE = "participant-retry-outage-digest-v1"
WMS_APPROVAL_FANOUT_MAX_RETRY_ATTEMPTS = 2
WMS_APPROVAL_FANOUT_RETRY_WINDOW_MS = 1500
WMS_APPROVAL_FANOUT_OUTAGE_KINDS = {
    "timeout",
    "transport-unavailable",
    "authority-quorum-pending",
}
WMS_REMOTE_AUTHORITY_RETRY_POLICY_ID = (
    "bounded-remote-authority-adaptive-retry-budget-v1"
)
WMS_REMOTE_AUTHORITY_RETRY_DIGEST_PROFILE = (
    "authority-route-health-retry-budget-digest-v1"
)
WMS_REMOTE_AUTHORITY_RETRY_SIGNATURE_POLICY_ID = (
    "signed-jurisdiction-rate-limit-retry-budget-v1"
)
WMS_REMOTE_AUTHORITY_JURISDICTION_RATE_LIMIT_PROFILE = (
    "jurisdiction-aware-authority-retry-rate-limit-v1"
)
WMS_REMOTE_AUTHORITY_SIGNATURE_DIGEST_PROFILE = (
    "authority-retry-budget-signature-digest-v1"
)
WMS_REMOTE_AUTHORITY_RETRY_SCHEDULE_PROFILE = (
    "fixed-exponential-backoff-with-health-cap-v1"
)
WMS_REMOTE_AUTHORITY_RETRY_BASE_DELAY_MS = 250
WMS_REMOTE_AUTHORITY_RETRY_MULTIPLIER = 2
WMS_REMOTE_AUTHORITY_RETRY_TOTAL_BUDGET_MS = WMS_APPROVAL_FANOUT_RETRY_WINDOW_MS
WMS_REMOTE_AUTHORITY_ROUTE_STATUSES = {
    "healthy",
    "degraded",
    "partial-outage",
    "recovered",
}
WMS_APPROVAL_COLLECTION_MAX_BATCH_SIZE = 2
WMS_APPROVAL_TRANSPORT_KIND = "imc"
WMS_APPROVAL_DECISION = "approve"
WMS_ENGINE_TRANSACTION_LOG_POLICY_ID = "digest-bound-wms-engine-transaction-log-v1"
WMS_ENGINE_ADAPTER_PROFILE = "reference-wms-engine-adapter-v1"
WMS_ENGINE_ADAPTER_SIGNATURE_PROFILE = "signed-wms-engine-adapter-log-v1"
WMS_ENGINE_ADAPTER_SIGNATURE_DIGEST_PROFILE = (
    "wms-engine-adapter-signature-digest-v1"
)
WMS_ENGINE_TRANSACTION_ENTRY_DIGEST_PROFILE = "wms-engine-transaction-entry-digest-v1"
WMS_ENGINE_TRANSACTION_LOG_DIGEST_PROFILE = "wms-engine-transaction-log-digest-v1"
WMS_ENGINE_ROUTE_BINDING_POLICY_ID = "distributed-transport-bound-wms-engine-adapter-route-v1"
WMS_ENGINE_ROUTE_BINDING_DIGEST_PROFILE = "wms-engine-route-binding-digest-v1"
WMS_ENGINE_ROUTE_TRACE_PROFILE = "non-loopback-mtls-authority-route-v1"
WMS_ENGINE_ROUTE_SOCKET_PROFILE = "mtls-socket-trace-v1"
WMS_ENGINE_ROUTE_OS_OBSERVER_PROFILE = "os-native-tcp-observer-v1"
WMS_ENGINE_ROUTE_CROSS_HOST_PROFILE = "attested-cross-host-authority-binding-v1"
WMS_ENGINE_ROUTE_TARGET_DISCOVERY_PROFILE = "bounded-authority-route-target-discovery-v1"
WMS_ENGINE_CAPTURE_BINDING_POLICY_ID = "packet-capture-bound-wms-engine-route-v1"
WMS_ENGINE_CAPTURE_BINDING_DIGEST_PROFILE = "wms-engine-capture-binding-digest-v1"
WMS_ENGINE_PACKET_CAPTURE_PROFILE = "trace-bound-pcap-export-v1"
WMS_ENGINE_PACKET_CAPTURE_FORMAT = "pcap"
WMS_ENGINE_PRIVILEGED_CAPTURE_PROFILE = "bounded-live-interface-capture-acquisition-v1"
WMS_ENGINE_PRIVILEGED_CAPTURE_MODE = "delegated-broker"
WMS_ENGINE_TRANSACTION_OPERATIONS = {
    "time_rate_escape_evidence",
    "approval_collection_bound",
    "approval_fanout_bound",
    "physics_rules_apply",
    "physics_rules_revert",
}
WMS_ALLOWED_MODES = {"shared_reality", "private_reality", "mixed"}
WMS_ALLOWED_AUTHORITIES = {"consensus", "local", "broker"}
WMS_PHYSICS_CHANGE_OPERATIONS = {"apply", "revert"}
WMS_PHYSICS_CHANGE_DECISIONS = {"applied", "reverted", "rejected"}


def _dedupe_preserve_order(values: Sequence[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _physics_rules_change_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: deepcopy(value) for key, value in receipt.items() if key != "digest"}


def _approval_transport_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: deepcopy(value) for key, value in receipt.items() if key != "digest"}


def _approval_collection_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: deepcopy(value) for key, value in receipt.items() if key != "digest"}


def _approval_fanout_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: deepcopy(value) for key, value in receipt.items() if key != "digest"}


def _fanout_retry_attempt_digest_payload(attempt: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        key: deepcopy(value)
        for key, value in attempt.items()
        if key != "attempt_digest"
    }


def _remote_authority_route_observation_digest_payload(
    observation: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        key: deepcopy(value)
        for key, value in observation.items()
        if key != "observation_digest"
    }


def _remote_authority_retry_schedule_entry_digest_payload(
    entry: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        key: deepcopy(value)
        for key, value in entry.items()
        if key != "schedule_entry_digest"
    }


def _remote_authority_retry_budget_digest_payload(
    receipt: Mapping[str, Any],
) -> Dict[str, Any]:
    return {key: deepcopy(value) for key, value in receipt.items() if key != "digest"}


def _time_rate_attestation_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: deepcopy(value) for key, value in receipt.items() if key != "digest"}


def _engine_transaction_entry_digest_payload(entry: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: deepcopy(value) for key, value in entry.items() if key != "entry_digest"}


def _engine_transaction_log_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: deepcopy(value) for key, value in receipt.items() if key != "digest"}


def _engine_adapter_signature_digest_payload(
    *,
    engine_adapter_signature_profile: str,
    engine_adapter_key_ref: str,
    engine_adapter_ref: str,
    engine_session_ref: str,
    transaction_log_ref: str,
    required_operations: Sequence[str],
    covered_operations: Sequence[str],
    transaction_set_digest: str,
    source_artifact_digest_set_digest: str,
    engine_state_transition_digest: str,
    current_wms_state_digest: str,
) -> Dict[str, Any]:
    return {
        "engine_adapter_signature_profile": engine_adapter_signature_profile,
        "engine_adapter_key_ref": engine_adapter_key_ref,
        "engine_adapter_ref": engine_adapter_ref,
        "engine_session_ref": engine_session_ref,
        "transaction_log_ref": transaction_log_ref,
        "required_operations": list(required_operations),
        "covered_operations": list(covered_operations),
        "transaction_set_digest": transaction_set_digest,
        "source_artifact_digest_set_digest": source_artifact_digest_set_digest,
        "engine_state_transition_digest": engine_state_transition_digest,
        "current_wms_state_digest": current_wms_state_digest,
    }


def _engine_route_binding_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: deepcopy(value) for key, value in receipt.items() if key != "digest"}


def _engine_capture_binding_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: deepcopy(value) for key, value in receipt.items() if key != "digest"}


def _transport_receipt_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        key: deepcopy(value)
        for key, value in receipt.items()
        if key not in {"kind", "schema_version", "digest"}
    }


def _route_trace_digest_payload(trace: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: deepcopy(value) for key, value in trace.items() if key != "digest"}


class WorldModelSync:
    """Deterministic L6 world-state reconciliation and escape model."""

    def __init__(self) -> None:
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def reference_profile(self) -> Dict[str, Any]:
        return {
            "schema_version": WMS_SCHEMA_VERSION,
            "modes": ["shared_reality", "private_reality", "mixed"],
            "minor_diff_threshold": WMS_MINOR_DIFF_THRESHOLD,
            "default_time_rate": WMS_DEFAULT_TIME_RATE,
            "private_escape_free": True,
            "malicious_inject_action": "guardian-veto",
            "time_rate_policy": {
                "policy_id": WMS_TIME_RATE_POLICY_ID,
                "default_time_rate": WMS_DEFAULT_TIME_RATE,
                "deviation_action": "offer-private-reality",
                "state_mutation_allowed": False,
                "digest_profile": WMS_TIME_RATE_DEVIATION_DIGEST_PROFILE,
                "attestation_policy_id": WMS_TIME_RATE_ATTESTATION_POLICY_ID,
                "attestation_digest_profile": WMS_TIME_RATE_ATTESTATION_DIGEST_PROFILE,
                "attestation_transport_kind": WMS_TIME_RATE_ATTESTATION_KIND,
                "attestation_required_when_deviation": True,
            },
            "physics_rules_change_policy": {
                "policy_id": WMS_PHYSICS_CHANGE_POLICY_ID,
                "required_approval": "unanimous-participant-approval",
                "approval_transport_policy_id": WMS_APPROVAL_TRANSPORT_POLICY_ID,
                "approval_collection_policy_id": WMS_APPROVAL_COLLECTION_POLICY_ID,
                "approval_fanout_policy_id": WMS_APPROVAL_FANOUT_POLICY_ID,
                "approval_fanout_digest_profile": WMS_APPROVAL_FANOUT_DIGEST_PROFILE,
                "approval_fanout_transport_profile": WMS_APPROVAL_FANOUT_TRANSPORT_PROFILE,
                "approval_fanout_retry_policy_id": WMS_APPROVAL_FANOUT_RETRY_POLICY_ID,
                "approval_fanout_retry_digest_profile": WMS_APPROVAL_FANOUT_RETRY_DIGEST_PROFILE,
                "approval_fanout_max_retry_attempts": WMS_APPROVAL_FANOUT_MAX_RETRY_ATTEMPTS,
                "approval_fanout_retry_window_ms": WMS_APPROVAL_FANOUT_RETRY_WINDOW_MS,
                "remote_authority_retry_policy_id": WMS_REMOTE_AUTHORITY_RETRY_POLICY_ID,
                "remote_authority_retry_digest_profile": WMS_REMOTE_AUTHORITY_RETRY_DIGEST_PROFILE,
                "remote_authority_retry_signature_policy_id": WMS_REMOTE_AUTHORITY_RETRY_SIGNATURE_POLICY_ID,
                "remote_authority_jurisdiction_rate_limit_profile": WMS_REMOTE_AUTHORITY_JURISDICTION_RATE_LIMIT_PROFILE,
                "remote_authority_signature_digest_profile": WMS_REMOTE_AUTHORITY_SIGNATURE_DIGEST_PROFILE,
                "remote_authority_retry_schedule_profile": WMS_REMOTE_AUTHORITY_RETRY_SCHEDULE_PROFILE,
                "remote_authority_retry_base_delay_ms": WMS_REMOTE_AUTHORITY_RETRY_BASE_DELAY_MS,
                "remote_authority_retry_multiplier": WMS_REMOTE_AUTHORITY_RETRY_MULTIPLIER,
                "remote_authority_retry_total_budget_ms": WMS_REMOTE_AUTHORITY_RETRY_TOTAL_BUDGET_MS,
                "approval_collection_max_batch_size": WMS_APPROVAL_COLLECTION_MAX_BATCH_SIZE,
                "approval_transport_kind": WMS_APPROVAL_TRANSPORT_KIND,
                "guardian_attestation_required": True,
                "rollback_token_required": True,
                "revert_operation_required": True,
                "engine_transaction_log_policy_id": WMS_ENGINE_TRANSACTION_LOG_POLICY_ID,
                "engine_adapter_profile": WMS_ENGINE_ADAPTER_PROFILE,
                "engine_adapter_signature_profile": WMS_ENGINE_ADAPTER_SIGNATURE_PROFILE,
                "engine_adapter_signature_digest_profile": WMS_ENGINE_ADAPTER_SIGNATURE_DIGEST_PROFILE,
                "engine_transaction_operations": sorted(WMS_ENGINE_TRANSACTION_OPERATIONS),
                "engine_route_binding_policy_id": WMS_ENGINE_ROUTE_BINDING_POLICY_ID,
                "engine_route_binding_digest_profile": WMS_ENGINE_ROUTE_BINDING_DIGEST_PROFILE,
                "engine_route_trace_profile": WMS_ENGINE_ROUTE_TRACE_PROFILE,
                "engine_route_cross_host_profile": WMS_ENGINE_ROUTE_CROSS_HOST_PROFILE,
                "engine_capture_binding_policy_id": WMS_ENGINE_CAPTURE_BINDING_POLICY_ID,
                "engine_capture_binding_digest_profile": WMS_ENGINE_CAPTURE_BINDING_DIGEST_PROFILE,
                "engine_packet_capture_profile": WMS_ENGINE_PACKET_CAPTURE_PROFILE,
                "engine_privileged_capture_profile": WMS_ENGINE_PRIVILEGED_CAPTURE_PROFILE,
            },
            "consensus_policy": {
                "minor_diff": "consensus_round",
                "major_diff": "offer-private-reality",
                "malicious_inject": "guardian-veto",
            },
        }

    def build_time_rate_attestation_subject(
        self,
        session_id: str,
        *,
        proposer_id: str,
        requested_time_rate: float,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        proposer = self._normalize_non_empty_string(proposer_id, "proposer_id")
        requested = self._normalize_time_rate(requested_time_rate)
        baseline = float(session["current_state"]["time_rate"])
        subject = {
            "schema_version": WMS_SCHEMA_VERSION,
            "session_id": session_id,
            "proposer_id": proposer,
            "time_rate_policy_id": WMS_TIME_RATE_POLICY_ID,
            "attestation_policy_id": WMS_TIME_RATE_ATTESTATION_POLICY_ID,
            "baseline_time_rate": baseline,
            "requested_time_rate": requested,
            "time_rate_delta": round(abs(requested - baseline), 3),
            "attestation_decision": WMS_TIME_RATE_ATTESTATION_DECISION,
            "state_mutation_allowed": False,
            "escape_decision": "offer-private-reality",
        }
        subject["digest"] = sha256_text(canonical_json(subject))
        return subject

    def build_time_rate_attestation_receipt(
        self,
        session_id: str,
        *,
        participant_id: str,
        time_rate_attestation_subject_digest: str,
        baseline_time_rate: float,
        requested_time_rate: float,
        imc_session: Mapping[str, Any],
        imc_message: Mapping[str, Any],
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        participant = self._normalize_non_empty_string(participant_id, "participant_id")
        subject_digest = self._normalize_digest(
            time_rate_attestation_subject_digest,
            "time_rate_attestation_subject_digest",
        )
        baseline = self._normalize_time_rate(baseline_time_rate)
        requested = self._normalize_time_rate(requested_time_rate)
        if baseline != float(session["current_state"]["time_rate"]):
            raise ValueError("baseline_time_rate must match the current WMS state")
        if participant not in session["current_state"]["participants"]:
            raise ValueError("participant_id must belong to the WMS session")
        if not isinstance(imc_session, Mapping):
            raise ValueError("imc_session must be a mapping")
        if not isinstance(imc_message, Mapping):
            raise ValueError("imc_message must be a mapping")
        handshake = imc_session.get("handshake")
        if not isinstance(handshake, Mapping):
            raise ValueError("imc_session.handshake must be a mapping")
        delivered_fields = imc_message.get("delivered_fields")
        if not isinstance(delivered_fields, Mapping):
            raise ValueError("imc_message.delivered_fields must be a mapping")
        expected_payload = {
            "time_rate_attestation_subject_digest": subject_digest,
            "participant_id": participant,
            "baseline_time_rate": baseline,
            "requested_time_rate": requested,
            "attestation_decision": WMS_TIME_RATE_ATTESTATION_DECISION,
        }
        expected_payload_digest = sha256_text(canonical_json(expected_payload))
        if delivered_fields != expected_payload:
            raise ValueError("imc_message delivered fields must equal the time-rate attestation payload")
        if imc_message.get("payload_digest") != expected_payload_digest:
            raise ValueError("imc_message payload digest must bind the time-rate attestation payload")
        if imc_message.get("sender_id") != participant:
            raise ValueError("imc_message sender_id must match participant_id")
        if imc_message.get("session_id") != imc_session.get("session_id"):
            raise ValueError("imc_message must belong to imc_session")
        imc_participants = imc_session.get("participants")
        if not isinstance(imc_participants, list) or participant not in imc_participants:
            raise ValueError("imc_session participants must include participant_id")

        receipt = {
            "kind": "wms_time_rate_attestation_receipt",
            "schema_version": WMS_SCHEMA_VERSION,
            "attestation_policy_id": WMS_TIME_RATE_ATTESTATION_POLICY_ID,
            "time_rate_policy_id": WMS_TIME_RATE_POLICY_ID,
            "session_id": session_id,
            "participant_id": participant,
            "time_rate_attestation_subject_digest": subject_digest,
            "baseline_time_rate": baseline,
            "requested_time_rate": requested,
            "time_rate_delta": round(abs(requested - baseline), 3),
            "attestation_decision": WMS_TIME_RATE_ATTESTATION_DECISION,
            "transport_kind": WMS_TIME_RATE_ATTESTATION_KIND,
            "transport_session_id": imc_session["session_id"],
            "transport_handshake_id": handshake["handshake_id"],
            "transport_handshake_digest": sha256_text(canonical_json(handshake)),
            "transport_message_id": imc_message["message_id"],
            "transport_message_summary_digest": sha256_text(str(imc_message["summary"])),
            "attestation_payload_digest": expected_payload_digest,
            "delivered_field_names": sorted(delivered_fields.keys()),
            "redacted_fields": list(imc_message.get("redacted_fields", [])),
            "continuity_event_ref": imc_message["continuity_event_ref"],
            "peer_attested": handshake.get("attestation_status") == "verified",
            "forward_secrecy": handshake.get("forward_secrecy") is True,
            "council_witnessed": handshake.get("council_witnessed") is True,
            "delivery_status": imc_message.get("delivery_status"),
        }
        receipt["digest"] = sha256_text(
            canonical_json(_time_rate_attestation_digest_payload(receipt))
        )
        return receipt

    def build_physics_rules_approval_subject(
        self,
        session_id: str,
        *,
        requested_by: str,
        proposed_physics_rules_ref: str,
        rationale: str,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        requester = self._normalize_non_empty_string(requested_by, "requested_by")
        proposed_ref = self._normalize_non_empty_string(
            proposed_physics_rules_ref,
            "proposed_physics_rules_ref",
        )
        rationale_text = self._normalize_non_empty_string(rationale, "rationale")
        subject = {
            "schema_version": WMS_SCHEMA_VERSION,
            "session_id": session_id,
            "requested_by": requester,
            "previous_physics_rules_ref": session["current_state"]["physics_rules_ref"],
            "proposed_physics_rules_ref": proposed_ref,
            "rationale": rationale_text,
            "approval_policy_id": WMS_PHYSICS_CHANGE_POLICY_ID,
            "approval_transport_policy_id": WMS_APPROVAL_TRANSPORT_POLICY_ID,
        }
        subject["digest"] = sha256_text(canonical_json(subject))
        return subject

    def build_participant_approval_transport_receipt(
        self,
        session_id: str,
        *,
        participant_id: str,
        approval_subject_digest: str,
        imc_session: Mapping[str, Any],
        imc_message: Mapping[str, Any],
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        participant = self._normalize_non_empty_string(participant_id, "participant_id")
        subject_digest = self._normalize_digest(
            approval_subject_digest,
            "approval_subject_digest",
        )
        if participant not in session["current_state"]["participants"]:
            raise ValueError("participant_id must belong to the WMS session")
        if not isinstance(imc_session, Mapping):
            raise ValueError("imc_session must be a mapping")
        if not isinstance(imc_message, Mapping):
            raise ValueError("imc_message must be a mapping")
        handshake = imc_session.get("handshake")
        if not isinstance(handshake, Mapping):
            raise ValueError("imc_session.handshake must be a mapping")
        delivered_fields = imc_message.get("delivered_fields")
        if not isinstance(delivered_fields, Mapping):
            raise ValueError("imc_message.delivered_fields must be a mapping")
        expected_payload = {
            "approval_subject_digest": subject_digest,
            "participant_id": participant,
            "approval_decision": WMS_APPROVAL_DECISION,
        }
        expected_payload_digest = sha256_text(canonical_json(expected_payload))
        if delivered_fields != expected_payload:
            raise ValueError("imc_message delivered fields must equal the approval payload")
        if imc_message.get("payload_digest") != expected_payload_digest:
            raise ValueError("imc_message payload digest must bind the approval payload")
        if imc_message.get("sender_id") != participant:
            raise ValueError("imc_message sender_id must match participant_id")
        if imc_message.get("session_id") != imc_session.get("session_id"):
            raise ValueError("imc_message must belong to imc_session")
        imc_participants = imc_session.get("participants")
        if not isinstance(imc_participants, list) or participant not in imc_participants:
            raise ValueError("imc_session participants must include participant_id")

        receipt = {
            "kind": "wms_participant_approval_transport_receipt",
            "schema_version": WMS_SCHEMA_VERSION,
            "transport_policy_id": WMS_APPROVAL_TRANSPORT_POLICY_ID,
            "session_id": session_id,
            "participant_id": participant,
            "approval_subject_digest": subject_digest,
            "approval_decision": WMS_APPROVAL_DECISION,
            "transport_kind": WMS_APPROVAL_TRANSPORT_KIND,
            "transport_session_id": imc_session["session_id"],
            "transport_handshake_id": handshake["handshake_id"],
            "transport_handshake_digest": sha256_text(canonical_json(handshake)),
            "transport_message_id": imc_message["message_id"],
            "transport_message_summary_digest": sha256_text(str(imc_message["summary"])),
            "approval_payload_digest": expected_payload_digest,
            "delivered_field_names": sorted(delivered_fields.keys()),
            "redacted_fields": list(imc_message.get("redacted_fields", [])),
            "continuity_event_ref": imc_message["continuity_event_ref"],
            "peer_attested": handshake.get("attestation_status") == "verified",
            "forward_secrecy": handshake.get("forward_secrecy") is True,
            "council_witnessed": handshake.get("council_witnessed") is True,
            "delivery_status": imc_message.get("delivery_status"),
        }
        receipt["digest"] = sha256_text(canonical_json(_approval_transport_digest_payload(receipt)))
        return receipt

    def build_approval_collection_receipt(
        self,
        session_id: str,
        *,
        approval_subject_digest: str,
        approval_transport_receipts: Sequence[Mapping[str, Any]],
        max_batch_size: int = WMS_APPROVAL_COLLECTION_MAX_BATCH_SIZE,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        subject_digest = self._normalize_digest(
            approval_subject_digest,
            "approval_subject_digest",
        )
        if not isinstance(max_batch_size, int) or max_batch_size < 1:
            raise ValueError("max_batch_size must be a positive integer")
        required_participants = list(session["current_state"]["participants"])
        receipts = [deepcopy(receipt) for receipt in approval_transport_receipts]
        receipts_by_participant: Dict[str, Mapping[str, Any]] = {}
        duplicate_participants: List[str] = []
        invalid_receipt_count = 0
        for receipt in receipts:
            validation = self.validate_approval_transport_receipt(
                receipt,
                approval_subject_digest=subject_digest,
            )
            participant_id = receipt.get("participant_id")
            if (
                not validation["ok"]
                or not isinstance(participant_id, str)
                or participant_id not in required_participants
            ):
                invalid_receipt_count += 1
                continue
            if participant_id in receipts_by_participant:
                duplicate_participants.append(participant_id)
                continue
            receipts_by_participant[participant_id] = receipt

        covered_participants = [
            participant
            for participant in required_participants
            if participant in receipts_by_participant
        ]
        missing_participants = [
            participant
            for participant in required_participants
            if participant not in receipts_by_participant
        ]
        receipt_digests = [
            receipts_by_participant[participant]["digest"]
            for participant in covered_participants
        ]
        batches = []
        for index in range(0, len(covered_participants), max_batch_size):
            batch_participants = covered_participants[index : index + max_batch_size]
            batch_receipt_digests = [
                receipts_by_participant[participant]["digest"]
                for participant in batch_participants
            ]
            batch = {
                "batch_id": f"wms-approval-batch-{len(batches) + 1:02d}",
                "participant_ids": batch_participants,
                "receipt_digests": batch_receipt_digests,
                "batch_size": len(batch_participants),
                "batch_index": len(batches),
                "within_batch_limit": len(batch_participants) <= max_batch_size,
            }
            batch["batch_digest"] = sha256_text(canonical_json(batch))
            batches.append(batch)

        receipt = {
            "kind": "wms_approval_collection_receipt",
            "schema_version": WMS_SCHEMA_VERSION,
            "collection_policy_id": WMS_APPROVAL_COLLECTION_POLICY_ID,
            "approval_transport_policy_id": WMS_APPROVAL_TRANSPORT_POLICY_ID,
            "session_id": session_id,
            "approval_subject_digest": subject_digest,
            "required_participants": required_participants,
            "participant_count": len(required_participants),
            "covered_participants": covered_participants,
            "missing_participants": missing_participants,
            "duplicate_participants": _dedupe_preserve_order(duplicate_participants),
            "invalid_receipt_count": invalid_receipt_count,
            "receipt_count": len(covered_participants),
            "receipt_digests": receipt_digests,
            "receipt_set_digest": sha256_text(canonical_json(receipt_digests)),
            "max_batch_size": max_batch_size,
            "batch_count": len(batches),
            "batches": batches,
            "collection_status": (
                "complete"
                if not missing_participants
                and invalid_receipt_count == 0
                and not duplicate_participants
                else "incomplete"
            ),
            "approval_quorum_met": not missing_participants,
            "transport_receipt_set_complete": (
                not missing_participants
                and invalid_receipt_count == 0
                and not duplicate_participants
            ),
            "participant_order_bound": covered_participants == required_participants,
            "digest_profile": "participant-ordered-batch-digest-v1",
        }
        receipt["digest"] = sha256_text(canonical_json(_approval_collection_digest_payload(receipt)))
        return receipt

    def build_distributed_approval_result_digest(
        self,
        *,
        approval_subject_digest: str,
        participant_id: str,
        approval_collection_digest: str,
    ) -> str:
        subject_digest = self._normalize_digest(
            approval_subject_digest,
            "approval_subject_digest",
        )
        participant = self._normalize_non_empty_string(participant_id, "participant_id")
        collection_digest = self._normalize_digest(
            approval_collection_digest,
            "approval_collection_digest",
        )
        return sha256_text(
            canonical_json(
                {
                    "approval_subject_digest": subject_digest,
                    "participant_id": participant,
                    "approval_decision": WMS_APPROVAL_DECISION,
                    "approval_collection_digest": collection_digest,
                    "fanout_policy_id": WMS_APPROVAL_FANOUT_POLICY_ID,
                }
            )
        )

    def build_distributed_approval_fanout_receipt(
        self,
        session_id: str,
        *,
        approval_subject_digest: str,
        approval_collection_receipt: Mapping[str, Any],
        participant_fanout_results: Sequence[Mapping[str, Any]],
        fanout_retry_attempts: Sequence[Mapping[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        subject_digest = self._normalize_digest(
            approval_subject_digest,
            "approval_subject_digest",
        )
        if not isinstance(approval_collection_receipt, Mapping):
            raise ValueError("approval_collection_receipt must be a mapping")
        collection_receipt = deepcopy(approval_collection_receipt)
        collection_digest = self._normalize_digest(
            collection_receipt.get("digest"),
            "approval_collection_digest",
        )
        required_participants = list(session["current_state"]["participants"])
        collection_validation = self.validate_approval_collection_receipt(
            collection_receipt,
            required_participants=required_participants,
            approval_subject_digest=subject_digest,
        )

        results_by_participant: Dict[str, Dict[str, Any]] = {}
        duplicate_participants: List[str] = []
        invalid_result_count = 0
        for result in participant_fanout_results:
            if not isinstance(result, Mapping):
                invalid_result_count += 1
                continue
            participant_id = result.get("participant_id")
            if not isinstance(participant_id, str) or not participant_id.strip():
                invalid_result_count += 1
                continue
            participant = participant_id.strip()
            if participant not in required_participants:
                invalid_result_count += 1
                continue
            if participant in results_by_participant:
                duplicate_participants.append(participant)
                continue
            envelope = result.get("transport_envelope")
            transport_receipt = result.get("transport_receipt")
            approval_result_digest = result.get("approval_result_digest")
            if not isinstance(envelope, Mapping) or not isinstance(transport_receipt, Mapping):
                invalid_result_count += 1
                continue
            expected_result_digest = self.build_distributed_approval_result_digest(
                approval_subject_digest=subject_digest,
                participant_id=participant,
                approval_collection_digest=collection_digest,
            )
            authenticity_checks = transport_receipt.get("authenticity_checks")
            if not isinstance(authenticity_checks, Mapping):
                authenticity_checks = {}
            transport_authenticated = (
                envelope.get("kind") == "distributed_transport_envelope"
                and transport_receipt.get("kind") == "distributed_transport_receipt"
                and envelope.get("council_tier") == WMS_APPROVAL_FANOUT_COUNCIL_TIER
                and transport_receipt.get("council_tier") == WMS_APPROVAL_FANOUT_COUNCIL_TIER
                and envelope.get("transport_profile") == WMS_APPROVAL_FANOUT_TRANSPORT_PROFILE
                and transport_receipt.get("transport_profile")
                == WMS_APPROVAL_FANOUT_TRANSPORT_PROFILE
                and transport_receipt.get("envelope_ref") == envelope.get("envelope_id")
                and transport_receipt.get("envelope_digest") == envelope.get("envelope_digest")
                and transport_receipt.get("receipt_status") == "authenticated"
                and authenticity_checks.get("channel_authenticated") is True
                and authenticity_checks.get("required_roles_satisfied") is True
                and authenticity_checks.get("quorum_attested") is True
                and authenticity_checks.get("federated_roots_verified") is True
                and authenticity_checks.get("key_epoch_accepted") is True
                and authenticity_checks.get("replay_guard_status") == "accepted"
                and authenticity_checks.get("multi_hop_replay_status") == "accepted"
            )
            result_digest_bound = (
                isinstance(approval_result_digest, str)
                and approval_result_digest == expected_result_digest
                and transport_receipt.get("result_digest") == expected_result_digest
            )
            if not transport_authenticated or not result_digest_bound:
                invalid_result_count += 1
                continue
            results_by_participant[participant] = {
                "participant_id": participant,
                "approval_result_ref": self._normalize_non_empty_string(
                    str(result.get("approval_result_ref") or transport_receipt.get("result_ref")),
                    "approval_result_ref",
                ),
                "approval_result_digest": expected_result_digest,
                "expected_approval_result_digest": expected_result_digest,
                "transport_envelope": deepcopy(envelope),
                "transport_receipt": deepcopy(transport_receipt),
                "transport_envelope_digest": envelope["envelope_digest"],
                "transport_receipt_digest": transport_receipt["digest"],
                "transport_authenticated": transport_authenticated,
                "result_digest_bound": result_digest_bound,
                "council_tier": WMS_APPROVAL_FANOUT_COUNCIL_TIER,
                "transport_profile": WMS_APPROVAL_FANOUT_TRANSPORT_PROFILE,
            }

        covered_participants = [
            participant
            for participant in required_participants
            if participant in results_by_participant
        ]
        missing_participants = [
            participant
            for participant in required_participants
            if participant not in results_by_participant
        ]
        ordered_results = [
            results_by_participant[participant] for participant in covered_participants
        ]
        participant_result_digests = [
            result["approval_result_digest"] for result in ordered_results
        ]
        transport_envelope_digests = [
            result["transport_envelope_digest"] for result in ordered_results
        ]
        transport_receipt_digests = [
            result["transport_receipt_digest"] for result in ordered_results
        ]
        retry_attempts = self._build_fanout_retry_attempts(
            fanout_retry_attempts or [],
            required_participants=required_participants,
            results_by_participant=results_by_participant,
        )
        retry_attempt_digests = [
            attempt["attempt_digest"] for attempt in retry_attempts
        ]
        outage_participants = _dedupe_preserve_order(
            [attempt["participant_id"] for attempt in retry_attempts]
        )
        retry_recovered_participants = _dedupe_preserve_order(
            [
                attempt["participant_id"]
                for attempt in retry_attempts
                if attempt["recovered"] is True
            ]
        )
        all_retry_attempts_recovered = (
            not retry_attempts
            or outage_participants == retry_recovered_participants
        )
        partial_outage_status = (
            "not-required"
            if not retry_attempts
            else "recovered"
            if all_retry_attempts_recovered
            else "blocked"
        )
        retry_policy_ok = (
            partial_outage_status != "blocked"
            and len(retry_attempts)
            <= WMS_APPROVAL_FANOUT_MAX_RETRY_ATTEMPTS * max(1, len(required_participants))
        )
        complete = (
            collection_validation["ok"]
            and not missing_participants
            and invalid_result_count == 0
            and not duplicate_participants
            and retry_policy_ok
        )
        receipt = {
            "kind": "wms_distributed_approval_fanout_receipt",
            "schema_version": WMS_SCHEMA_VERSION,
            "fanout_policy_id": WMS_APPROVAL_FANOUT_POLICY_ID,
            "digest_profile": WMS_APPROVAL_FANOUT_DIGEST_PROFILE,
            "fanout_retry_policy_id": WMS_APPROVAL_FANOUT_RETRY_POLICY_ID,
            "retry_digest_profile": WMS_APPROVAL_FANOUT_RETRY_DIGEST_PROFILE,
            "max_retry_attempts": WMS_APPROVAL_FANOUT_MAX_RETRY_ATTEMPTS,
            "retry_window_ms": WMS_APPROVAL_FANOUT_RETRY_WINDOW_MS,
            "session_id": session_id,
            "approval_subject_digest": subject_digest,
            "approval_collection_policy_id": WMS_APPROVAL_COLLECTION_POLICY_ID,
            "approval_collection_digest": collection_digest,
            "approval_collection_receipt": collection_receipt,
            "approval_collection_complete": collection_validation["ok"],
            "distributed_transport_profile": WMS_APPROVAL_FANOUT_TRANSPORT_PROFILE,
            "council_tier": WMS_APPROVAL_FANOUT_COUNCIL_TIER,
            "required_participants": required_participants,
            "participant_count": len(required_participants),
            "covered_participants": covered_participants,
            "missing_participants": missing_participants,
            "duplicate_participants": _dedupe_preserve_order(duplicate_participants),
            "invalid_result_count": invalid_result_count,
            "result_count": len(covered_participants),
            "participant_result_digests": participant_result_digests,
            "transport_envelope_digests": transport_envelope_digests,
            "transport_receipt_digests": transport_receipt_digests,
            "transport_receipt_set_digest": sha256_text(
                canonical_json(transport_receipt_digests)
            ),
            "participant_fanout_results": ordered_results,
            "retry_attempts": retry_attempts,
            "retry_attempt_count": len(retry_attempts),
            "retry_attempt_digests": retry_attempt_digests,
            "retry_attempt_set_digest": sha256_text(
                canonical_json(retry_attempt_digests)
            ),
            "outage_participants": outage_participants,
            "retry_recovered_participants": retry_recovered_participants,
            "partial_outage_status": partial_outage_status,
            "all_retry_attempts_recovered": all_retry_attempts_recovered,
            "fanout_status": "complete" if complete else "incomplete",
            "transport_receipt_set_authenticated": complete,
            "participant_order_bound": covered_participants == required_participants,
        }
        receipt["digest"] = sha256_text(canonical_json(_approval_fanout_digest_payload(receipt)))
        return receipt

    def build_remote_authority_retry_budget_receipt(
        self,
        session_id: str,
        *,
        authority_profile_ref: str,
        approval_fanout_receipt: Mapping[str, Any],
        engine_transaction_log_receipt: Mapping[str, Any],
        route_health_observations: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        authority_ref = self._normalize_non_empty_string(
            authority_profile_ref,
            "authority_profile_ref",
        )
        if not isinstance(approval_fanout_receipt, Mapping):
            raise ValueError("approval_fanout_receipt must be a mapping")
        if not isinstance(engine_transaction_log_receipt, Mapping):
            raise ValueError("engine_transaction_log_receipt must be a mapping")
        fanout_receipt = deepcopy(approval_fanout_receipt)
        engine_log = deepcopy(engine_transaction_log_receipt)
        required_participants = list(session["current_state"]["participants"])
        fanout_digest = self._normalize_digest(
            fanout_receipt.get("digest"),
            "approval_fanout_digest",
        )
        engine_log_digest = self._normalize_digest(
            engine_log.get("digest"),
            "engine_transaction_log_digest",
        )
        fanout_validation = self.validate_distributed_approval_fanout_receipt(
            fanout_receipt,
            required_participants=required_participants,
            approval_subject_digest=fanout_receipt.get("approval_subject_digest"),
            approval_collection_digest=fanout_receipt.get("approval_collection_digest"),
        )
        engine_log_validation = self.validate_engine_transaction_log_receipt(engine_log)
        engine_log_fanout_bound = any(
            entry.get("operation") == "approval_fanout_bound"
            and entry.get("source_artifact_digest") == fanout_digest
            for entry in engine_log.get("transaction_entries", [])
            if isinstance(entry, Mapping)
        )
        observations = self._build_remote_authority_route_observations(
            route_health_observations,
            required_participants=required_participants,
        )
        observations_by_key = {
            (observation["participant_id"], observation["outage_kind"]): observation
            for observation in observations
        }
        retry_attempts = [
            deepcopy(attempt)
            for attempt in fanout_receipt.get("retry_attempts", [])
            if isinstance(attempt, Mapping)
        ]
        schedule_entries: List[Dict[str, Any]] = []
        cumulative_delay_ms = 0
        for attempt in retry_attempts:
            participant = str(attempt["participant_id"])
            outage_kind = str(attempt["outage_kind"])
            attempt_index = int(attempt["attempt_index"])
            observation = observations_by_key.get((participant, outage_kind))
            retry_after_ms = int(attempt["retry_after_ms"])
            computed_backoff_ms = min(
                WMS_REMOTE_AUTHORITY_RETRY_BASE_DELAY_MS
                * (WMS_REMOTE_AUTHORITY_RETRY_MULTIPLIER ** (attempt_index - 1)),
                WMS_REMOTE_AUTHORITY_RETRY_TOTAL_BUDGET_MS,
            )
            cumulative_delay_ms += retry_after_ms
            route_health_eligible = (
                observation is not None
                and observation["retry_budget_eligible"] is True
            )
            within_budget = (
                retry_after_ms <= computed_backoff_ms
                and observation is not None
                and retry_after_ms <= observation["jurisdiction_retry_limit_ms"]
                and cumulative_delay_ms <= WMS_REMOTE_AUTHORITY_RETRY_TOTAL_BUDGET_MS
            )
            schedule_entry = {
                "schedule_entry_ref": (
                    "retry-schedule://wms-authority/"
                    f"{sha256_text(participant)[:12]}/{attempt_index}"
                ),
                "retry_attempt_ref": attempt["retry_attempt_ref"],
                "participant_id": participant,
                "attempt_index": attempt_index,
                "outage_kind": outage_kind,
                "retry_after_ms": retry_after_ms,
                "computed_backoff_ms": computed_backoff_ms,
                "remaining_budget_ms": max(
                    0,
                    WMS_REMOTE_AUTHORITY_RETRY_TOTAL_BUDGET_MS - cumulative_delay_ms,
                ),
                "route_health_observation_digest": (
                    observation["observation_digest"] if observation is not None else ""
                ),
                "remote_jurisdiction": (
                    observation["remote_jurisdiction"] if observation is not None else ""
                ),
                "jurisdiction_rate_limit_ref": (
                    observation["jurisdiction_rate_limit_ref"]
                    if observation is not None
                    else ""
                ),
                "jurisdiction_retry_limit_ms": (
                    observation["jurisdiction_retry_limit_ms"]
                    if observation is not None
                    else 0
                ),
                "jurisdiction_rate_limit_digest": (
                    observation["jurisdiction_rate_limit_digest"]
                    if observation is not None
                    else ""
                ),
                "authority_signature_digest": (
                    observation["authority_signature_digest"]
                    if observation is not None
                    else ""
                ),
                "recovery_result_digest": attempt["recovery_result_digest"],
                "recovery_transport_receipt_digest": attempt[
                    "recovery_transport_receipt_digest"
                ],
                "route_health_eligible": route_health_eligible,
                "jurisdiction_rate_limit_ok": (
                    observation is not None
                    and retry_after_ms <= observation["jurisdiction_retry_limit_ms"]
                ),
                "within_budget": within_budget,
                "budget_decision": (
                    "retry" if route_health_eligible and within_budget else "blocked"
                ),
            }
            schedule_entry["schedule_entry_digest"] = sha256_text(
                canonical_json(
                    _remote_authority_retry_schedule_entry_digest_payload(
                        schedule_entry
                    )
                )
            )
            schedule_entries.append(schedule_entry)

        route_observation_digests = [
            observation["observation_digest"] for observation in observations
        ]
        jurisdiction_rate_limit_digests = [
            observation["jurisdiction_rate_limit_digest"]
            for observation in observations
        ]
        authority_signature_digests = [
            observation["authority_signature_digest"] for observation in observations
        ]
        remote_jurisdictions = sorted(
            {observation["remote_jurisdiction"] for observation in observations}
        )
        schedule_entry_digests = [
            entry["schedule_entry_digest"] for entry in schedule_entries
        ]
        outage_participants = list(fanout_receipt.get("outage_participants", []))
        all_outages_budgeted = (
            len(schedule_entries) == len(retry_attempts)
            and all(entry["budget_decision"] == "retry" for entry in schedule_entries)
            and all(
                any(
                    observation["participant_id"] == participant
                    for observation in observations
                )
                for participant in outage_participants
            )
        )
        total_scheduled_delay_ms = sum(
            entry["retry_after_ms"] for entry in schedule_entries
        )
        adaptive_budget_bound = (
            fanout_validation["ok"]
            and engine_log_validation["ok"]
            and engine_log_fanout_bound
            and all_outages_budgeted
            and bool(jurisdiction_rate_limit_digests)
            and bool(authority_signature_digests)
            and total_scheduled_delay_ms <= WMS_REMOTE_AUTHORITY_RETRY_TOTAL_BUDGET_MS
            and fanout_receipt.get("partial_outage_status") in {"not-required", "recovered"}
        )
        receipt = {
            "kind": "wms_remote_authority_retry_budget_receipt",
            "schema_version": WMS_SCHEMA_VERSION,
            "retry_budget_policy_id": WMS_REMOTE_AUTHORITY_RETRY_POLICY_ID,
            "digest_profile": WMS_REMOTE_AUTHORITY_RETRY_DIGEST_PROFILE,
            "signature_policy_id": WMS_REMOTE_AUTHORITY_RETRY_SIGNATURE_POLICY_ID,
            "jurisdiction_rate_limit_profile": WMS_REMOTE_AUTHORITY_JURISDICTION_RATE_LIMIT_PROFILE,
            "signature_digest_profile": WMS_REMOTE_AUTHORITY_SIGNATURE_DIGEST_PROFILE,
            "schedule_profile": WMS_REMOTE_AUTHORITY_RETRY_SCHEDULE_PROFILE,
            "session_id": session_id,
            "authority_profile_ref": authority_ref,
            "approval_fanout_policy_id": WMS_APPROVAL_FANOUT_POLICY_ID,
            "approval_fanout_digest": fanout_digest,
            "fanout_retry_policy_id": WMS_APPROVAL_FANOUT_RETRY_POLICY_ID,
            "fanout_retry_attempt_count": len(retry_attempts),
            "fanout_retry_attempt_digests": [
                attempt["attempt_digest"] for attempt in retry_attempts
            ],
            "fanout_partial_outage_status": fanout_receipt.get(
                "partial_outage_status"
            ),
            "engine_transaction_log_policy_id": WMS_ENGINE_TRANSACTION_LOG_POLICY_ID,
            "engine_transaction_log_digest": engine_log_digest,
            "engine_log_fanout_bound": engine_log_fanout_bound,
            "route_health_observations": observations,
            "route_health_observation_digests": route_observation_digests,
            "route_health_set_digest": sha256_text(
                canonical_json(route_observation_digests)
            ),
            "remote_jurisdictions": remote_jurisdictions,
            "jurisdiction_rate_limit_digests": jurisdiction_rate_limit_digests,
            "jurisdiction_rate_limit_set_digest": sha256_text(
                canonical_json(jurisdiction_rate_limit_digests)
            ),
            "authority_signature_digests": authority_signature_digests,
            "authority_signature_set_digest": sha256_text(
                canonical_json(authority_signature_digests)
            ),
            "outage_participants": outage_participants,
            "schedule_entries": schedule_entries,
            "schedule_entry_digests": schedule_entry_digests,
            "schedule_set_digest": sha256_text(
                canonical_json(schedule_entry_digests)
            ),
            "base_retry_after_ms": WMS_REMOTE_AUTHORITY_RETRY_BASE_DELAY_MS,
            "exponential_multiplier": WMS_REMOTE_AUTHORITY_RETRY_MULTIPLIER,
            "max_retry_attempts": WMS_APPROVAL_FANOUT_MAX_RETRY_ATTEMPTS,
            "total_retry_budget_ms": WMS_REMOTE_AUTHORITY_RETRY_TOTAL_BUDGET_MS,
            "total_scheduled_delay_ms": total_scheduled_delay_ms,
            "max_scheduled_delay_ms": max(
                [entry["retry_after_ms"] for entry in schedule_entries] or [0]
            ),
            "all_outages_budgeted": all_outages_budgeted,
            "adaptive_retry_budget_bound": adaptive_budget_bound,
            "jurisdiction_rate_limit_bound": bool(jurisdiction_rate_limit_digests),
            "authority_signature_bound": bool(authority_signature_digests),
            "signed_jurisdiction_retry_budget_bound": adaptive_budget_bound,
            "budget_status": "complete" if adaptive_budget_bound else "incomplete",
            "raw_remote_transcript_stored": False,
        }
        receipt["digest"] = sha256_text(
            canonical_json(_remote_authority_retry_budget_digest_payload(receipt))
        )
        return receipt

    def build_engine_transaction_entry(
        self,
        *,
        transaction_id: str,
        transaction_index: int,
        operation: str,
        source_artifact_kind: str,
        source_artifact_ref: str,
        source_artifact_digest: str,
        engine_session_ref: str,
        engine_state_before_digest: str,
        engine_state_after_digest: str,
        participant_ids: Sequence[str],
        committed_at: str | None = None,
    ) -> Dict[str, Any]:
        normalized_operation = self._normalize_non_empty_string(operation, "operation")
        if normalized_operation not in WMS_ENGINE_TRANSACTION_OPERATIONS:
            raise ValueError("operation is not allowed")
        if not isinstance(transaction_index, int) or transaction_index < 1:
            raise ValueError("transaction_index must be a positive integer")
        entry = {
            "kind": "wms_engine_transaction_entry",
            "schema_version": WMS_SCHEMA_VERSION,
            "entry_digest_profile": WMS_ENGINE_TRANSACTION_ENTRY_DIGEST_PROFILE,
            "transaction_id": self._normalize_non_empty_string(
                transaction_id,
                "transaction_id",
            ),
            "transaction_index": transaction_index,
            "operation": normalized_operation,
            "source_artifact_kind": self._normalize_non_empty_string(
                source_artifact_kind,
                "source_artifact_kind",
            ),
            "source_artifact_ref": self._normalize_non_empty_string(
                source_artifact_ref,
                "source_artifact_ref",
            ),
            "source_artifact_digest": self._normalize_digest(
                source_artifact_digest,
                "source_artifact_digest",
            ),
            "engine_session_ref": self._normalize_non_empty_string(
                engine_session_ref,
                "engine_session_ref",
            ),
            "engine_state_before_digest": self._normalize_digest(
                engine_state_before_digest,
                "engine_state_before_digest",
            ),
            "engine_state_after_digest": self._normalize_digest(
                engine_state_after_digest,
                "engine_state_after_digest",
            ),
            "participant_ids": self._normalize_string_list(
                participant_ids,
                "participant_ids",
            ),
            "payload_redacted": True,
            "raw_payload_stored": False,
            "transaction_status": "committed",
            "committed_at": committed_at or utc_now_iso(),
        }
        entry["entry_digest"] = sha256_text(
            canonical_json(_engine_transaction_entry_digest_payload(entry))
        )
        return entry

    def build_engine_transaction_log_receipt(
        self,
        session_id: str,
        *,
        engine_adapter_ref: str,
        engine_session_ref: str,
        transaction_log_ref: str,
        transaction_entries: Sequence[Mapping[str, Any]],
        engine_adapter_key_ref: str | None = None,
        required_operations: Sequence[str] | None = None,
        source_artifact_digests: Mapping[str, str] | None = None,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        adapter_ref = self._normalize_non_empty_string(
            engine_adapter_ref,
            "engine_adapter_ref",
        )
        adapter_key_ref = self._normalize_non_empty_string(
            engine_adapter_key_ref
            or f"engine-key://reference-wms/{sha256_text(adapter_ref)[:16]}",
            "engine_adapter_key_ref",
        )
        engine_session = self._normalize_non_empty_string(
            engine_session_ref,
            "engine_session_ref",
        )
        log_ref = self._normalize_non_empty_string(transaction_log_ref, "transaction_log_ref")
        required = self._normalize_engine_required_operations(required_operations)
        expected_digests = {
            operation: self._normalize_digest(digest, f"source_artifact_digests.{operation}")
            for operation, digest in (source_artifact_digests or {}).items()
        }

        normalized_entries: List[Dict[str, Any]] = []
        invalid_transaction_count = 0
        duplicate_transaction_ids: List[str] = []
        seen_transaction_ids: set[str] = set()
        for raw_entry in transaction_entries:
            if not isinstance(raw_entry, Mapping):
                invalid_transaction_count += 1
                continue
            entry = deepcopy(raw_entry)
            if entry.get("transaction_id") in seen_transaction_ids:
                duplicate_transaction_ids.append(str(entry.get("transaction_id")))
                continue
            try:
                self._validate_engine_transaction_entry(
                    entry,
                    expected_index=len(normalized_entries) + 1,
                    engine_session_ref=engine_session,
                    source_artifact_digests=expected_digests,
                )
            except ValueError:
                invalid_transaction_count += 1
                continue
            seen_transaction_ids.add(str(entry["transaction_id"]))
            normalized_entries.append(entry)

        covered_operations = [
            entry["operation"]
            for entry in normalized_entries
            if entry["operation"] in required
        ]
        missing_operations = [
            operation for operation in required if operation not in covered_operations
        ]
        ordered_entry_digests = [entry["entry_digest"] for entry in normalized_entries]
        source_artifact_digests_ordered = [
            entry["source_artifact_digest"] for entry in normalized_entries
        ]
        state_transition_pairs = [
            {
                "transaction_id": entry["transaction_id"],
                "operation": entry["operation"],
                "engine_state_before_digest": entry["engine_state_before_digest"],
                "engine_state_after_digest": entry["engine_state_after_digest"],
            }
            for entry in normalized_entries
        ]
        entry_order_bound = [
            entry["transaction_index"] for entry in normalized_entries
        ] == list(range(1, len(normalized_entries) + 1))
        redaction_complete = all(
            entry.get("payload_redacted") is True
            and entry.get("raw_payload_stored") is False
            for entry in normalized_entries
        )
        source_artifacts_bound = not missing_operations and all(
            not expected_digests
            or entry["operation"] not in expected_digests
            or entry["source_artifact_digest"] == expected_digests[entry["operation"]]
            for entry in normalized_entries
        )
        transaction_set_digest = sha256_text(canonical_json(ordered_entry_digests))
        source_artifact_digest_set_digest = sha256_text(
            canonical_json(source_artifact_digests_ordered)
        )
        engine_state_transition_digest = sha256_text(
            canonical_json(state_transition_pairs)
        )
        current_wms_state_digest = sha256_text(canonical_json(session["current_state"]))
        complete_without_signature = (
            bool(normalized_entries)
            and not missing_operations
            and invalid_transaction_count == 0
            and not duplicate_transaction_ids
            and entry_order_bound
            and redaction_complete
            and source_artifacts_bound
        )
        engine_adapter_signature_digest = sha256_text(
            canonical_json(
                _engine_adapter_signature_digest_payload(
                    engine_adapter_signature_profile=WMS_ENGINE_ADAPTER_SIGNATURE_PROFILE,
                    engine_adapter_key_ref=adapter_key_ref,
                    engine_adapter_ref=adapter_ref,
                    engine_session_ref=engine_session,
                    transaction_log_ref=log_ref,
                    required_operations=required,
                    covered_operations=covered_operations,
                    transaction_set_digest=transaction_set_digest,
                    source_artifact_digest_set_digest=source_artifact_digest_set_digest,
                    engine_state_transition_digest=engine_state_transition_digest,
                    current_wms_state_digest=current_wms_state_digest,
                )
            )
        )
        engine_adapter_signature_bound = complete_without_signature
        receipt = {
            "kind": "wms_engine_transaction_log",
            "schema_version": WMS_SCHEMA_VERSION,
            "transaction_log_policy_id": WMS_ENGINE_TRANSACTION_LOG_POLICY_ID,
            "engine_adapter_profile": WMS_ENGINE_ADAPTER_PROFILE,
            "engine_adapter_signature_profile": WMS_ENGINE_ADAPTER_SIGNATURE_PROFILE,
            "engine_adapter_signature_digest_profile": WMS_ENGINE_ADAPTER_SIGNATURE_DIGEST_PROFILE,
            "engine_adapter_key_ref": adapter_key_ref,
            "entry_digest_profile": WMS_ENGINE_TRANSACTION_ENTRY_DIGEST_PROFILE,
            "digest_profile": WMS_ENGINE_TRANSACTION_LOG_DIGEST_PROFILE,
            "session_id": session_id,
            "engine_adapter_ref": adapter_ref,
            "engine_session_ref": engine_session,
            "transaction_log_ref": log_ref,
            "required_operations": required,
            "covered_operations": covered_operations,
            "missing_operations": missing_operations,
            "duplicate_transaction_ids": _dedupe_preserve_order(duplicate_transaction_ids),
            "invalid_transaction_count": invalid_transaction_count,
            "transaction_entry_count": len(normalized_entries),
            "transaction_entries": normalized_entries,
            "ordered_transaction_ids": [
                entry["transaction_id"] for entry in normalized_entries
            ],
            "ordered_entry_digests": ordered_entry_digests,
            "transaction_set_digest": transaction_set_digest,
            "source_artifact_digest_set_digest": source_artifact_digest_set_digest,
            "engine_state_transition_digest": engine_state_transition_digest,
            "current_wms_state_digest": current_wms_state_digest,
            "engine_adapter_signature_digest": engine_adapter_signature_digest,
            "entry_order_bound": entry_order_bound,
            "source_artifacts_bound": source_artifacts_bound,
            "redaction_complete": redaction_complete,
            "state_transition_bound": bool(normalized_entries),
            "engine_adapter_signature_bound": engine_adapter_signature_bound,
            "raw_adapter_signature_stored": False,
            "engine_binding_status": (
                "complete" if engine_adapter_signature_bound else "incomplete"
            ),
        }
        receipt["digest"] = sha256_text(
            canonical_json(_engine_transaction_log_digest_payload(receipt))
        )
        return receipt

    def build_engine_route_binding_receipt(
        self,
        session_id: str,
        *,
        engine_transaction_log_receipt: Mapping[str, Any],
        authority_route_trace: Mapping[str, Any],
    ) -> Dict[str, Any]:
        self._require_session(session_id)
        if not isinstance(engine_transaction_log_receipt, Mapping):
            raise ValueError("engine_transaction_log_receipt must be a mapping")
        if not isinstance(authority_route_trace, Mapping):
            raise ValueError("authority_route_trace must be a mapping")
        engine_log = deepcopy(engine_transaction_log_receipt)
        route_trace = deepcopy(authority_route_trace)
        engine_log_digest = self._normalize_digest(
            engine_log.get("digest"),
            "engine_transaction_log_digest",
        )
        route_trace_digest = self._normalize_digest(
            route_trace.get("digest"),
            "authority_route_trace_digest",
        )
        engine_log_validation = self.validate_engine_transaction_log_receipt(engine_log)
        route_trace_validation = self._validate_engine_authority_route_trace(route_trace)

        transaction_ids = [
            str(transaction_id)
            for transaction_id in engine_log.get("ordered_transaction_ids", [])
            if isinstance(transaction_id, str)
        ]
        transaction_entry_digests = [
            str(entry_digest)
            for entry_digest in engine_log.get("ordered_entry_digests", [])
            if isinstance(entry_digest, str)
        ]
        route_binding_refs = route_trace_validation["route_binding_refs"]
        remote_host_refs = route_trace_validation["remote_host_refs"]
        remote_host_attestation_refs = route_trace_validation[
            "remote_host_attestation_refs"
        ]
        os_observer_tuple_digests = route_trace_validation["os_observer_tuple_digests"]
        os_observer_host_binding_digests = route_trace_validation[
            "os_observer_host_binding_digests"
        ]
        route_binding_digest_set_digest = sha256_text(canonical_json(route_binding_refs))
        transaction_digest_set_digest = sha256_text(canonical_json(transaction_entry_digests))
        engine_log_bound = (
            engine_log_validation["ok"]
            and engine_log.get("engine_binding_status") == "complete"
            and engine_log.get("digest") == engine_log_digest
        )
        authority_route_trace_bound = route_trace_validation["ok"]
        cross_host_route_bound = route_trace_validation["cross_host_route_bound"]
        redaction_complete = (
            engine_log.get("redaction_complete") is True
            and all(
                entry.get("payload_redacted") is True
                and entry.get("raw_payload_stored") is False
                for entry in engine_log.get("transaction_entries", [])
                if isinstance(entry, Mapping)
            )
        )
        complete = (
            engine_log_bound
            and authority_route_trace_bound
            and cross_host_route_bound
            and redaction_complete
        )
        receipt = {
            "kind": "wms_engine_route_binding_receipt",
            "schema_version": WMS_SCHEMA_VERSION,
            "binding_policy_id": WMS_ENGINE_ROUTE_BINDING_POLICY_ID,
            "digest_profile": WMS_ENGINE_ROUTE_BINDING_DIGEST_PROFILE,
            "session_id": session_id,
            "engine_transaction_log_policy_id": WMS_ENGINE_TRANSACTION_LOG_POLICY_ID,
            "engine_transaction_log_digest": engine_log_digest,
            "engine_adapter_ref": engine_log["engine_adapter_ref"],
            "engine_session_ref": engine_log["engine_session_ref"],
            "transaction_log_ref": engine_log["transaction_log_ref"],
            "engine_transaction_ids": transaction_ids,
            "engine_transaction_entry_digests": transaction_entry_digests,
            "engine_transaction_digest_set_digest": transaction_digest_set_digest,
            "transaction_entry_count": len(transaction_entry_digests),
            "authority_route_trace_ref": route_trace["trace_ref"],
            "authority_route_trace_digest": route_trace_digest,
            "authority_plane_ref": route_trace["authority_plane_ref"],
            "authority_plane_digest": route_trace["authority_plane_digest"],
            "route_target_discovery_ref": route_trace["route_target_discovery_ref"],
            "route_target_discovery_digest": route_trace[
                "route_target_discovery_digest"
            ],
            "council_tier": route_trace["council_tier"],
            "transport_profile": route_trace["transport_profile"],
            "trace_profile": route_trace["trace_profile"],
            "socket_trace_profile": route_trace["socket_trace_profile"],
            "os_observer_profile": route_trace["os_observer_profile"],
            "cross_host_binding_profile": route_trace["cross_host_binding_profile"],
            "route_target_discovery_profile": route_trace[
                "route_target_discovery_profile"
            ],
            "route_count": int(route_trace["route_count"]),
            "mtls_authenticated_count": int(route_trace["mtls_authenticated_count"]),
            "distinct_remote_host_count": int(route_trace["distinct_remote_host_count"]),
            "route_binding_refs": route_binding_refs,
            "route_binding_digest_set_digest": route_binding_digest_set_digest,
            "remote_host_refs": remote_host_refs,
            "remote_host_attestation_refs": remote_host_attestation_refs,
            "os_observer_tuple_digests": os_observer_tuple_digests,
            "os_observer_host_binding_digests": os_observer_host_binding_digests,
            "engine_log_bound": engine_log_bound,
            "authority_route_trace_bound": authority_route_trace_bound,
            "cross_host_route_bound": cross_host_route_bound,
            "redaction_complete": redaction_complete,
            "raw_engine_payload_stored": False,
            "raw_route_payload_stored": False,
            "engine_route_binding_status": "complete" if complete else "incomplete",
        }
        receipt["digest"] = sha256_text(
            canonical_json(_engine_route_binding_digest_payload(receipt))
        )
        return receipt

    def build_engine_capture_binding_receipt(
        self,
        session_id: str,
        *,
        engine_route_binding_receipt: Mapping[str, Any],
        packet_capture_export: Mapping[str, Any],
        privileged_capture_acquisition: Mapping[str, Any],
    ) -> Dict[str, Any]:
        self._require_session(session_id)
        if not isinstance(engine_route_binding_receipt, Mapping):
            raise ValueError("engine_route_binding_receipt must be a mapping")
        if not isinstance(packet_capture_export, Mapping):
            raise ValueError("packet_capture_export must be a mapping")
        if not isinstance(privileged_capture_acquisition, Mapping):
            raise ValueError("privileged_capture_acquisition must be a mapping")
        route_binding = deepcopy(engine_route_binding_receipt)
        capture = deepcopy(packet_capture_export)
        acquisition = deepcopy(privileged_capture_acquisition)
        route_binding_digest = self._normalize_digest(
            route_binding.get("digest"),
            "engine_route_binding_digest",
        )
        packet_capture_digest = self._normalize_digest(
            capture.get("digest"),
            "packet_capture_digest",
        )
        privileged_capture_digest = self._normalize_digest(
            acquisition.get("digest"),
            "privileged_capture_digest",
        )
        route_validation = self.validate_engine_route_binding_receipt(route_binding)
        capture_validation = self._validate_engine_packet_capture_export(
            capture,
            engine_route_binding_receipt=route_binding,
        )
        acquisition_validation = self._validate_engine_privileged_capture_acquisition(
            acquisition,
            engine_route_binding_receipt=route_binding,
            packet_capture_export=capture,
        )
        route_binding_refs = [
            str(route_ref)
            for route_ref in route_binding.get("route_binding_refs", [])
            if isinstance(route_ref, str)
        ]
        route_binding_set_digest = sha256_text(canonical_json(route_binding_refs))
        capture_route_binding_refs = [
            str(route_export.get("route_binding_ref"))
            for route_export in capture.get("route_exports", [])
            if isinstance(route_export, Mapping)
            and isinstance(route_export.get("route_binding_ref"), str)
        ]
        capture_route_binding_set_digest = sha256_text(
            canonical_json(capture_route_binding_refs)
        )
        acquisition_route_binding_refs = [
            str(route_ref)
            for route_ref in acquisition.get("route_binding_refs", [])
            if isinstance(route_ref, str)
        ]
        acquisition_route_binding_set_digest = sha256_text(
            canonical_json(sorted(acquisition_route_binding_refs))
        )
        route_binding_set_bound = (
            route_binding_set_digest == capture_route_binding_set_digest
            and sorted(route_binding_refs) == sorted(acquisition_route_binding_refs)
        )
        raw_payloads_redacted = (
            route_binding.get("raw_engine_payload_stored") is False
            and route_binding.get("raw_route_payload_stored") is False
            and capture.get("artifact_format") == WMS_ENGINE_PACKET_CAPTURE_FORMAT
        )
        complete = (
            route_validation["ok"]
            and capture_validation["ok"]
            and acquisition_validation["ok"]
            and route_binding_set_bound
            and raw_payloads_redacted
        )
        receipt = {
            "kind": "wms_engine_capture_binding_receipt",
            "schema_version": WMS_SCHEMA_VERSION,
            "capture_binding_policy_id": WMS_ENGINE_CAPTURE_BINDING_POLICY_ID,
            "digest_profile": WMS_ENGINE_CAPTURE_BINDING_DIGEST_PROFILE,
            "session_id": session_id,
            "engine_route_binding_policy_id": WMS_ENGINE_ROUTE_BINDING_POLICY_ID,
            "engine_route_binding_digest": route_binding_digest,
            "engine_transaction_log_digest": route_binding["engine_transaction_log_digest"],
            "authority_route_trace_ref": route_binding["authority_route_trace_ref"],
            "authority_route_trace_digest": route_binding["authority_route_trace_digest"],
            "authority_plane_ref": route_binding["authority_plane_ref"],
            "authority_plane_digest": route_binding["authority_plane_digest"],
            "council_tier": route_binding["council_tier"],
            "transport_profile": route_binding["transport_profile"],
            "route_count": int(route_binding["route_count"]),
            "route_binding_refs": route_binding_refs,
            "route_binding_digest_set_digest": route_binding_set_digest,
            "packet_capture_ref": capture["capture_ref"],
            "packet_capture_digest": packet_capture_digest,
            "packet_capture_profile": capture["capture_profile"],
            "packet_capture_artifact_format": capture["artifact_format"],
            "packet_capture_artifact_digest": capture["artifact_digest"],
            "packet_capture_readback_digest": capture["readback_digest"],
            "packet_count": int(capture["packet_count"]),
            "packet_capture_export_status": capture["export_status"],
            "packet_capture_route_binding_refs": capture_route_binding_refs,
            "packet_capture_route_binding_set_digest": capture_route_binding_set_digest,
            "os_native_readback_available": bool(capture["os_native_readback_available"]),
            "os_native_readback_ok": bool(capture["os_native_readback_ok"]),
            "privileged_capture_ref": acquisition["acquisition_ref"],
            "privileged_capture_digest": privileged_capture_digest,
            "privileged_capture_profile": acquisition["acquisition_profile"],
            "privilege_mode": acquisition["privilege_mode"],
            "broker_profile": acquisition["broker_profile"],
            "broker_attestation_ref": acquisition["broker_attestation_ref"],
            "lease_ref": acquisition["lease_ref"],
            "interface_name": acquisition["interface_name"],
            "local_ips": list(acquisition["local_ips"]),
            "capture_filter_digest": acquisition["filter_digest"],
            "capture_command_digest": sha256_text(
                canonical_json(acquisition["capture_command"])
            ),
            "acquisition_route_binding_refs": acquisition_route_binding_refs,
            "acquisition_route_binding_set_digest": acquisition_route_binding_set_digest,
            "engine_route_binding_bound": route_validation["ok"],
            "packet_capture_bound": capture_validation["ok"],
            "privileged_capture_bound": acquisition_validation["ok"],
            "route_binding_set_bound": route_binding_set_bound,
            "raw_engine_payload_stored": False,
            "raw_route_payload_stored": False,
            "raw_packet_body_stored": False,
            "engine_capture_binding_status": "complete" if complete else "incomplete",
        }
        receipt["digest"] = sha256_text(
            canonical_json(_engine_capture_binding_digest_payload(receipt))
        )
        return receipt

    def collect_approval_transport_receipts(
        self,
        session_id: str,
        *,
        approval_subject_digest: str,
        approval_transport_receipts: Sequence[Mapping[str, Any]],
        max_batch_size: int = WMS_APPROVAL_COLLECTION_MAX_BATCH_SIZE,
    ) -> Dict[str, Any]:
        return self.build_approval_collection_receipt(
            session_id,
            approval_subject_digest=approval_subject_digest,
            approval_transport_receipts=approval_transport_receipts,
            max_batch_size=max_batch_size,
        )

    def create_session(
        self,
        participants: Sequence[str],
        *,
        mode: str = "shared_reality",
        objects: Sequence[str],
        authority: str = "consensus",
        physics_rules_ref: str = WMS_DEFAULT_PHYSICS_RULES_REF,
        time_rate: float = WMS_DEFAULT_TIME_RATE,
    ) -> Dict[str, Any]:
        normalized_participants = self._normalize_string_list(participants, "participants")
        normalized_objects = self._normalize_string_list(objects, "objects")
        normalized_mode = self._normalize_mode(mode)
        normalized_authority = self._normalize_authority(authority)
        normalized_physics_rules = self._normalize_non_empty_string(
            physics_rules_ref,
            "physics_rules_ref",
        )
        normalized_time_rate = self._normalize_time_rate(time_rate)

        session_id = new_id("wms")
        recorded_at = utc_now_iso()
        state = {
            "schema_version": WMS_SCHEMA_VERSION,
            "state_id": new_id("world-state"),
            "participants": normalized_participants,
            "spatial_layout": self._layout_ref(normalized_mode, normalized_objects),
            "objects": normalized_objects,
            "physics_rules_ref": normalized_physics_rules,
            "time_rate": normalized_time_rate,
            "authority": normalized_authority,
            "recorded_at": recorded_at,
        }
        session = {
            "schema_version": WMS_SCHEMA_VERSION,
            "session_id": session_id,
            "mode": normalized_mode,
            "authority": normalized_authority,
            "baseline_state": deepcopy(state),
            "current_state": deepcopy(state),
            "consensus_rounds": 0,
            "last_reconcile": None,
            "last_violation": None,
            "physics_change_log": [],
        }
        self.sessions[session_id] = session
        return deepcopy(session)

    def snapshot(self, session_id: str) -> Dict[str, Any]:
        session = self._require_session(session_id)
        return deepcopy(session["current_state"])

    def propose_diff(
        self,
        session_id: str,
        *,
        proposer_id: str,
        candidate_objects: Sequence[str],
        affected_object_ratio: float,
        attested: bool,
        requested_time_rate: float = WMS_DEFAULT_TIME_RATE,
        time_rate_attestation_receipts: Sequence[Mapping[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        proposer = self._normalize_non_empty_string(proposer_id, "proposer_id")
        objects = self._normalize_string_list(candidate_objects, "candidate_objects")
        ratio = self._normalize_ratio(affected_object_ratio, "affected_object_ratio")
        time_rate = self._normalize_time_rate(requested_time_rate)

        classification = self._classify_diff(
            session,
            proposer_id=proposer,
            affected_object_ratio=ratio,
            attested=attested,
            requested_time_rate=time_rate,
        )
        time_rate_fields = self._time_rate_deviation_fields(
            session,
            proposer_id=proposer,
            requested_time_rate=time_rate,
            classification=classification,
            time_rate_attestation_receipts=time_rate_attestation_receipts,
        )
        reconcile_id = new_id("wms-reconcile")
        recorded_at = utc_now_iso()
        audit_event_ref = f"ledger://wms-reconcile/{reconcile_id}"

        if classification == "malicious_inject":
            violation = self._build_violation(
                session,
                classification=classification,
                proposer_id=proposer,
                affected_object_ratio=ratio,
                attested=attested,
                requested_time_rate=time_rate,
                audit_event_ref=audit_event_ref,
            )
            session["last_violation"] = violation
            result = {
                "schema_version": WMS_SCHEMA_VERSION,
                "reconcile_id": reconcile_id,
                "session_id": session_id,
                "recorded_at": recorded_at,
                "classification": classification,
                "decision": "guardian-veto",
                "consensus_required": False,
                "guardian_action": "isolate-session",
                "council_notification": "async-audit-only",
                "escape_offered": True,
                "resulting_mode": session["mode"],
                "resulting_state_id": session["current_state"]["state_id"],
                "affected_object_ratio": ratio,
                "requested_time_rate": time_rate,
                **time_rate_fields,
                "audit_event_ref": audit_event_ref,
            }
            session["last_reconcile"] = result
            return deepcopy(result)

        candidate_state = {
            "schema_version": WMS_SCHEMA_VERSION,
            "state_id": new_id("world-state"),
            "participants": list(session["current_state"]["participants"]),
            "spatial_layout": self._layout_ref(session["mode"], objects),
            "objects": objects,
            "physics_rules_ref": session["current_state"]["physics_rules_ref"],
            "time_rate": session["current_state"]["time_rate"],
            "authority": session["current_state"]["authority"],
            "recorded_at": recorded_at,
        }

        if classification == "minor_diff":
            session["consensus_rounds"] += 1
            session["current_state"] = candidate_state
            decision = "consensus-round"
            guardian_action = "continue-shared-sync"
            council_notification = "not-required"
            escape_offered = False
        else:
            decision = "offer-private-reality"
            guardian_action = "await-human-choice"
            council_notification = "required"
            escape_offered = True

        result = {
            "schema_version": WMS_SCHEMA_VERSION,
            "reconcile_id": reconcile_id,
            "session_id": session_id,
            "recorded_at": recorded_at,
            "classification": classification,
            "decision": decision,
            "consensus_required": classification == "minor_diff",
            "guardian_action": guardian_action,
            "council_notification": council_notification,
            "escape_offered": escape_offered,
            "resulting_mode": session["mode"],
            "resulting_state_id": (
                candidate_state["state_id"]
                if classification == "minor_diff"
                else session["current_state"]["state_id"]
            ),
            "affected_object_ratio": ratio,
            "requested_time_rate": time_rate,
            **time_rate_fields,
            "audit_event_ref": audit_event_ref,
        }
        session["last_reconcile"] = result
        return deepcopy(result)

    def switch_mode(
        self,
        session_id: str,
        *,
        mode: str,
        requested_by: str,
        reason: str,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        target_mode = self._normalize_mode(mode)
        requester = self._normalize_non_empty_string(requested_by, "requested_by")
        reason_text = self._normalize_non_empty_string(reason, "reason")

        previous_mode = session["mode"]
        session["mode"] = target_mode
        session["current_state"]["authority"] = "local" if target_mode == "private_reality" else "consensus"
        session["current_state"]["spatial_layout"] = self._layout_ref(
            target_mode,
            session["current_state"]["objects"],
        )
        session["current_state"]["recorded_at"] = utc_now_iso()

        return {
            "session_id": session_id,
            "recorded_at": session["current_state"]["recorded_at"],
            "old_mode": previous_mode,
            "new_mode": target_mode,
            "requested_by": requester,
            "reason": reason_text,
            "authority": session["current_state"]["authority"],
            "private_escape_honored": previous_mode == "shared_reality"
            and target_mode == "private_reality",
            "resulting_state_id": session["current_state"]["state_id"],
            "audit_event_ref": f"ledger://wms-mode/{new_id('wms-mode')}",
        }

    def propose_physics_rules_change(
        self,
        session_id: str,
        *,
        requested_by: str,
        proposed_physics_rules_ref: str,
        rationale: str,
        participant_approvals: Sequence[str],
        guardian_attested: bool,
        reversible: bool = True,
        rollback_physics_rules_ref: str | None = None,
        approval_transport_receipts: Sequence[Mapping[str, Any]] | None = None,
        approval_collection_receipt: Mapping[str, Any] | None = None,
        approval_fanout_receipt: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        requester = self._normalize_non_empty_string(requested_by, "requested_by")
        proposed_ref = self._normalize_non_empty_string(
            proposed_physics_rules_ref,
            "proposed_physics_rules_ref",
        )
        rationale_text = self._normalize_non_empty_string(rationale, "rationale")
        approvals = self._normalize_string_list(
            participant_approvals,
            "participant_approvals",
        )
        previous_ref = session["current_state"]["physics_rules_ref"]
        rollback_ref = (
            self._normalize_non_empty_string(
                rollback_physics_rules_ref,
                "rollback_physics_rules_ref",
            )
            if rollback_physics_rules_ref is not None
            else previous_ref
        )
        required_approvals = list(session["current_state"]["participants"])
        approval_quorum_met = set(required_approvals).issubset(set(approvals))
        approval_subject = self.build_physics_rules_approval_subject(
            session_id,
            requested_by=requester,
            proposed_physics_rules_ref=proposed_ref,
            rationale=rationale_text,
        )
        transport_receipts = [deepcopy(receipt) for receipt in (approval_transport_receipts or [])]
        approval_transport_quorum_met = self._approval_transport_quorum_met(
            transport_receipts,
            required_approvals=required_approvals,
            approval_subject_digest=approval_subject["digest"],
        )
        collection_receipt = (
            deepcopy(approval_collection_receipt)
            if approval_collection_receipt is not None
            else self.build_approval_collection_receipt(
                session_id,
                approval_subject_digest=approval_subject["digest"],
                approval_transport_receipts=transport_receipts,
            )
        )
        collection_validation = self.validate_approval_collection_receipt(
            collection_receipt,
            required_participants=required_approvals,
            approval_subject_digest=approval_subject["digest"],
            approval_transport_receipts=transport_receipts,
        )
        approval_collection_complete = collection_validation["ok"]
        fanout_receipt = deepcopy(approval_fanout_receipt) if approval_fanout_receipt is not None else None
        fanout_validation = (
            self.validate_distributed_approval_fanout_receipt(
                fanout_receipt,
                required_participants=required_approvals,
                approval_subject_digest=approval_subject["digest"],
                approval_collection_digest=collection_receipt["digest"],
            )
            if isinstance(fanout_receipt, Mapping)
            else {"ok": False, "digest_bound": False}
        )
        requester_allowed = requester in required_approvals
        reversible_ok = bool(reversible) and rollback_ref == previous_ref
        guardian_ok = bool(guardian_attested)
        can_apply = (
            requester_allowed
            and approval_quorum_met
            and approval_transport_quorum_met
            and approval_collection_complete
            and (
                fanout_receipt is None
                or fanout_validation["ok"]
            )
            and guardian_ok
            and reversible_ok
            and proposed_ref != previous_ref
        )
        change_id = new_id("wms-physics-change")
        recorded_at = utc_now_iso()
        resulting_ref = proposed_ref if can_apply else previous_ref
        if can_apply:
            session["current_state"]["physics_rules_ref"] = proposed_ref
            session["current_state"]["state_id"] = new_id("world-state")
            session["current_state"]["recorded_at"] = recorded_at

        receipt = {
            "kind": "wms_physics_rules_change_receipt",
            "schema_version": WMS_SCHEMA_VERSION,
            "operation": "apply",
            "change_id": change_id,
            "session_id": session_id,
            "requested_by": requester,
            "recorded_at": recorded_at,
            "rationale": rationale_text,
            "previous_physics_rules_ref": previous_ref,
            "proposed_physics_rules_ref": proposed_ref,
            "resulting_physics_rules_ref": resulting_ref,
            "approval_policy_id": WMS_PHYSICS_CHANGE_POLICY_ID,
            "required_approvals": required_approvals,
            "participant_approvals": approvals,
            "approval_quorum_met": approval_quorum_met,
            "approval_subject_digest": approval_subject["digest"],
            "approval_transport_policy_id": WMS_APPROVAL_TRANSPORT_POLICY_ID,
            "approval_transport_receipts": transport_receipts,
            "approval_transport_quorum_met": approval_transport_quorum_met,
            "approval_transport_digest": sha256_text(canonical_json(transport_receipts)),
            "approval_collection_policy_id": WMS_APPROVAL_COLLECTION_POLICY_ID,
            "approval_collection_receipt": collection_receipt,
            "approval_collection_digest": collection_receipt["digest"],
            "approval_collection_complete": approval_collection_complete,
            "guardian_attested": guardian_ok,
            "reversible": bool(reversible),
            "rollback_physics_rules_ref": rollback_ref,
            "rollback_token_ref": f"rollback://wms-physics/{change_id}",
            "decision": "applied" if can_apply else "rejected",
            "revert_of_change_id": "",
            "reverted": False,
            "resulting_state_id": session["current_state"]["state_id"],
            "audit_event_ref": f"ledger://wms-physics/{change_id}",
        }
        if fanout_receipt is not None:
            receipt.update(
                {
                    "approval_fanout_policy_id": WMS_APPROVAL_FANOUT_POLICY_ID,
                    "approval_fanout_receipt": fanout_receipt,
                    "approval_fanout_digest": fanout_receipt["digest"],
                    "approval_fanout_complete": fanout_validation["ok"],
                }
            )
        receipt["digest"] = sha256_text(canonical_json(_physics_rules_change_digest_payload(receipt)))
        session["physics_change_log"].append(deepcopy(receipt))
        return deepcopy(receipt)

    def revert_physics_rules_change(
        self,
        session_id: str,
        *,
        change_id: str,
        requested_by: str,
        reason: str,
        guardian_attested: bool,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        target_change_id = self._normalize_non_empty_string(change_id, "change_id")
        requester = self._normalize_non_empty_string(requested_by, "requested_by")
        reason_text = self._normalize_non_empty_string(reason, "reason")
        participants = list(session["current_state"]["participants"])
        if requester not in participants:
            raise ValueError("requested_by must be a session participant")
        if not guardian_attested:
            raise ValueError("guardian_attested must be true for physics rules revert")
        target_receipt = None
        for receipt in session["physics_change_log"]:
            if receipt.get("change_id") == target_change_id and receipt.get("operation") == "apply":
                target_receipt = receipt
                break
        if target_receipt is None or target_receipt.get("decision") != "applied":
            raise ValueError("change_id must refer to an applied physics rules change")
        if any(
            receipt.get("operation") == "revert"
            and receipt.get("revert_of_change_id") == target_change_id
            for receipt in session["physics_change_log"]
        ):
            raise ValueError("physics rules change has already been reverted")

        revert_id = new_id("wms-physics-revert")
        recorded_at = utc_now_iso()
        previous_ref = session["current_state"]["physics_rules_ref"]
        rollback_ref = target_receipt["rollback_physics_rules_ref"]
        session["current_state"]["physics_rules_ref"] = rollback_ref
        session["current_state"]["state_id"] = new_id("world-state")
        session["current_state"]["recorded_at"] = recorded_at

        receipt = {
            "kind": "wms_physics_rules_change_receipt",
            "schema_version": WMS_SCHEMA_VERSION,
            "operation": "revert",
            "change_id": revert_id,
            "session_id": session_id,
            "requested_by": requester,
            "recorded_at": recorded_at,
            "rationale": reason_text,
            "previous_physics_rules_ref": previous_ref,
            "proposed_physics_rules_ref": target_receipt["proposed_physics_rules_ref"],
            "resulting_physics_rules_ref": rollback_ref,
            "approval_policy_id": WMS_PHYSICS_CHANGE_POLICY_ID,
            "required_approvals": participants,
            "participant_approvals": participants,
            "approval_quorum_met": True,
            "approval_subject_digest": target_receipt["approval_subject_digest"],
            "approval_transport_policy_id": target_receipt["approval_transport_policy_id"],
            "approval_transport_receipts": deepcopy(target_receipt["approval_transport_receipts"]),
            "approval_transport_quorum_met": target_receipt["approval_transport_quorum_met"],
            "approval_transport_digest": target_receipt["approval_transport_digest"],
            "approval_collection_policy_id": target_receipt["approval_collection_policy_id"],
            "approval_collection_receipt": deepcopy(target_receipt["approval_collection_receipt"]),
            "approval_collection_digest": target_receipt["approval_collection_digest"],
            "approval_collection_complete": target_receipt["approval_collection_complete"],
            "guardian_attested": True,
            "reversible": True,
            "rollback_physics_rules_ref": rollback_ref,
            "rollback_token_ref": target_receipt["rollback_token_ref"],
            "decision": "reverted",
            "revert_of_change_id": target_change_id,
            "reverted": True,
            "resulting_state_id": session["current_state"]["state_id"],
            "audit_event_ref": f"ledger://wms-physics-revert/{revert_id}",
        }
        if "approval_fanout_receipt" in target_receipt:
            receipt.update(
                {
                    "approval_fanout_policy_id": target_receipt["approval_fanout_policy_id"],
                    "approval_fanout_receipt": deepcopy(target_receipt["approval_fanout_receipt"]),
                    "approval_fanout_digest": target_receipt["approval_fanout_digest"],
                    "approval_fanout_complete": target_receipt["approval_fanout_complete"],
                }
            )
        receipt["digest"] = sha256_text(canonical_json(_physics_rules_change_digest_payload(receipt)))
        session["physics_change_log"].append(deepcopy(receipt))
        return deepcopy(receipt)

    def observe_violation(self, session_id: str) -> Dict[str, Any]:
        session = self._require_session(session_id)
        if session["last_violation"] is None:
            return {
                "session_id": session_id,
                "observed_at": utc_now_iso(),
                "violation_detected": False,
                "classification": "none",
                "guardian_action": "continue-shared-sync",
                "requires_council_review": False,
                "audit_event_ref": "",
            }
        return deepcopy(session["last_violation"])

    def validate_time_rate_attestation_receipt(
        self,
        receipt: Mapping[str, Any],
        *,
        time_rate_attestation_subject_digest: str | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")
        if receipt.get("kind") != "wms_time_rate_attestation_receipt":
            errors.append("kind must equal wms_time_rate_attestation_receipt")
        if receipt.get("schema_version") != WMS_SCHEMA_VERSION:
            errors.append(f"schema_version must be {WMS_SCHEMA_VERSION}")
        if receipt.get("attestation_policy_id") != WMS_TIME_RATE_ATTESTATION_POLICY_ID:
            errors.append("attestation_policy_id mismatch")
        if receipt.get("time_rate_policy_id") != WMS_TIME_RATE_POLICY_ID:
            errors.append("time_rate_policy_id mismatch")
        if receipt.get("transport_kind") != WMS_TIME_RATE_ATTESTATION_KIND:
            errors.append("transport_kind must be imc")
        if receipt.get("attestation_decision") != WMS_TIME_RATE_ATTESTATION_DECISION:
            errors.append("attestation_decision must be attest")
        for field_name in (
            "session_id",
            "participant_id",
            "transport_session_id",
            "transport_handshake_id",
            "transport_message_id",
            "continuity_event_ref",
            "delivery_status",
        ):
            self._check_non_empty_string(receipt.get(field_name), field_name, errors)

        expected_subject = time_rate_attestation_subject_digest
        if expected_subject is not None:
            try:
                expected_subject = self._normalize_digest(
                    expected_subject,
                    "time_rate_attestation_subject_digest",
                )
            except ValueError as exc:
                errors.append(str(exc))
        subject_digest = receipt.get("time_rate_attestation_subject_digest")
        if not isinstance(subject_digest, str) or len(subject_digest) != 64:
            errors.append("time_rate_attestation_subject_digest must be a sha256 hex digest")
        elif expected_subject is not None and subject_digest != expected_subject:
            errors.append("time_rate_attestation_subject_digest must match expected subject")

        baseline = receipt.get("baseline_time_rate")
        requested = receipt.get("requested_time_rate")
        if not isinstance(baseline, (int, float)) or float(baseline) <= 0:
            errors.append("baseline_time_rate must be a positive number")
            baseline = 0.0
        if not isinstance(requested, (int, float)) or float(requested) <= 0:
            errors.append("requested_time_rate must be a positive number")
            requested = 0.0
        expected_delta = round(abs(float(requested) - float(baseline)), 3)
        if receipt.get("time_rate_delta") != expected_delta:
            errors.append("time_rate_delta must match requested-baseline absolute delta")

        for digest_field in (
            "transport_handshake_digest",
            "transport_message_summary_digest",
            "attestation_payload_digest",
            "digest",
        ):
            digest_value = receipt.get(digest_field)
            if not isinstance(digest_value, str) or len(digest_value) != 64:
                errors.append(f"{digest_field} must be a sha256 hex digest")
        delivered_field_names = receipt.get("delivered_field_names")
        required_fields = {
            "time_rate_attestation_subject_digest",
            "participant_id",
            "baseline_time_rate",
            "requested_time_rate",
            "attestation_decision",
        }
        delivered_fields_bound = (
            isinstance(delivered_field_names, list)
            and set(delivered_field_names) == required_fields
        )
        if not delivered_fields_bound:
            errors.append("delivered_field_names must bind exactly the time-rate attestation payload fields")
        redacted_fields = receipt.get("redacted_fields")
        redactions_empty = isinstance(redacted_fields, list) and not redacted_fields
        if not redactions_empty:
            errors.append("redacted_fields must be empty for time-rate attestation payloads")
        peer_attested = receipt.get("peer_attested") is True
        forward_secrecy = receipt.get("forward_secrecy") is True
        if not peer_attested:
            errors.append("peer_attested must be true")
        if not forward_secrecy:
            errors.append("forward_secrecy must be true")
        if receipt.get("delivery_status") not in {"delivered", "delivered-with-redactions"}:
            errors.append("delivery_status must be delivered or delivered-with-redactions")
        expected_digest = sha256_text(
            canonical_json(_time_rate_attestation_digest_payload(receipt))
        )
        digest_bound = receipt.get("digest") == expected_digest
        if not digest_bound:
            errors.append("digest must match time-rate attestation receipt payload")
        return {
            "ok": not errors,
            "errors": errors,
            "delivered_fields_bound": delivered_fields_bound,
            "redactions_empty": redactions_empty,
            "peer_attested": peer_attested,
            "forward_secrecy": forward_secrecy,
            "digest_bound": digest_bound,
        }

    def validate_approval_transport_receipt(
        self,
        receipt: Mapping[str, Any],
        *,
        approval_subject_digest: str | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")
        if receipt.get("kind") != "wms_participant_approval_transport_receipt":
            errors.append("kind must equal wms_participant_approval_transport_receipt")
        if receipt.get("schema_version") != WMS_SCHEMA_VERSION:
            errors.append(f"schema_version must be {WMS_SCHEMA_VERSION}")
        if receipt.get("transport_policy_id") != WMS_APPROVAL_TRANSPORT_POLICY_ID:
            errors.append("transport_policy_id mismatch")
        if receipt.get("transport_kind") != WMS_APPROVAL_TRANSPORT_KIND:
            errors.append("transport_kind must be imc")
        if receipt.get("approval_decision") != WMS_APPROVAL_DECISION:
            errors.append("approval_decision must be approve")
        for field_name in (
            "session_id",
            "participant_id",
            "transport_session_id",
            "transport_handshake_id",
            "transport_message_id",
            "continuity_event_ref",
            "delivery_status",
        ):
            self._check_non_empty_string(receipt.get(field_name), field_name, errors)
        expected_subject = approval_subject_digest
        if expected_subject is not None:
            try:
                expected_subject = self._normalize_digest(
                    expected_subject,
                    "approval_subject_digest",
                )
            except ValueError as exc:
                errors.append(str(exc))
        subject_digest = receipt.get("approval_subject_digest")
        if not isinstance(subject_digest, str) or len(subject_digest) != 64:
            errors.append("approval_subject_digest must be a sha256 hex digest")
        elif expected_subject is not None and subject_digest != expected_subject:
            errors.append("approval_subject_digest must match the physics change subject")
        for digest_field in (
            "transport_handshake_digest",
            "transport_message_summary_digest",
            "approval_payload_digest",
            "digest",
        ):
            digest_value = receipt.get(digest_field)
            if not isinstance(digest_value, str) or len(digest_value) != 64:
                errors.append(f"{digest_field} must be a sha256 hex digest")
        delivered_field_names = receipt.get("delivered_field_names")
        required_fields = {
            "approval_subject_digest",
            "participant_id",
            "approval_decision",
        }
        delivered_fields_bound = (
            isinstance(delivered_field_names, list)
            and set(delivered_field_names) == required_fields
        )
        if not delivered_fields_bound:
            errors.append("delivered_field_names must bind exactly the approval payload fields")
        redacted_fields = receipt.get("redacted_fields")
        redactions_empty = isinstance(redacted_fields, list) and not redacted_fields
        if not redactions_empty:
            errors.append("redacted_fields must be empty for approval payloads")
        peer_attested = receipt.get("peer_attested") is True
        forward_secrecy = receipt.get("forward_secrecy") is True
        if not peer_attested:
            errors.append("peer_attested must be true")
        if not forward_secrecy:
            errors.append("forward_secrecy must be true")
        if receipt.get("delivery_status") not in {"delivered", "delivered-with-redactions"}:
            errors.append("delivery_status must be delivered or delivered-with-redactions")
        expected_digest = sha256_text(canonical_json(_approval_transport_digest_payload(receipt)))
        digest_bound = receipt.get("digest") == expected_digest
        if not digest_bound:
            errors.append("digest must match approval transport receipt payload")
        return {
            "ok": not errors,
            "errors": errors,
            "delivered_fields_bound": delivered_fields_bound,
            "redactions_empty": redactions_empty,
            "peer_attested": peer_attested,
            "forward_secrecy": forward_secrecy,
            "digest_bound": digest_bound,
        }

    def validate_approval_collection_receipt(
        self,
        receipt: Mapping[str, Any],
        *,
        required_participants: Sequence[str] | None = None,
        approval_subject_digest: str | None = None,
        approval_transport_receipts: Sequence[Mapping[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")
        if receipt.get("kind") != "wms_approval_collection_receipt":
            errors.append("kind must equal wms_approval_collection_receipt")
        if receipt.get("schema_version") != WMS_SCHEMA_VERSION:
            errors.append(f"schema_version must be {WMS_SCHEMA_VERSION}")
        if receipt.get("collection_policy_id") != WMS_APPROVAL_COLLECTION_POLICY_ID:
            errors.append("collection_policy_id mismatch")
        if receipt.get("approval_transport_policy_id") != WMS_APPROVAL_TRANSPORT_POLICY_ID:
            errors.append("approval_transport_policy_id mismatch")

        expected_subject = approval_subject_digest
        if expected_subject is not None:
            try:
                expected_subject = self._normalize_digest(
                    expected_subject,
                    "approval_subject_digest",
                )
            except ValueError as exc:
                errors.append(str(exc))
        subject_digest = receipt.get("approval_subject_digest")
        if not isinstance(subject_digest, str) or len(subject_digest) != 64:
            errors.append("approval_subject_digest must be a sha256 hex digest")
        elif expected_subject is not None and subject_digest != expected_subject:
            errors.append("approval_subject_digest must match expected subject")

        expected_required = list(required_participants or receipt.get("required_participants", []))
        required = receipt.get("required_participants")
        covered = receipt.get("covered_participants")
        missing = receipt.get("missing_participants")
        digest_list = receipt.get("receipt_digests")
        batches = receipt.get("batches")
        max_batch_size = receipt.get("max_batch_size")
        if not isinstance(required, list) or not required:
            errors.append("required_participants must be a non-empty list")
            required = []
        if expected_required and required != expected_required:
            errors.append("required_participants must preserve WMS session participant order")
        if not isinstance(covered, list):
            errors.append("covered_participants must be a list")
            covered = []
        if not isinstance(missing, list):
            errors.append("missing_participants must be a list")
            missing = []
        duplicate_participants = receipt.get("duplicate_participants")
        if not isinstance(duplicate_participants, list):
            errors.append("duplicate_participants must be a list")
            duplicate_participants = []
        invalid_receipt_count = receipt.get("invalid_receipt_count")
        if not isinstance(invalid_receipt_count, int) or invalid_receipt_count < 0:
            errors.append("invalid_receipt_count must be a non-negative integer")
            invalid_receipt_count = 0
        if not isinstance(digest_list, list):
            errors.append("receipt_digests must be a list")
            digest_list = []
        if not isinstance(batches, list):
            errors.append("batches must be a list")
            batches = []
        if not isinstance(max_batch_size, int) or max_batch_size < 1:
            errors.append("max_batch_size must be a positive integer")
            max_batch_size = 0

        participant_order_bound = covered == required[: len(covered)]
        if receipt.get("participant_order_bound") is not participant_order_bound:
            errors.append("participant_order_bound must reflect covered participant ordering")
        missing_expected = [participant for participant in required if participant not in covered]
        if missing != missing_expected:
            errors.append("missing_participants must reflect required minus covered participants")
        coverage_complete = not missing_expected and bool(required)
        collection_complete = (
            coverage_complete
            and invalid_receipt_count == 0
            and not duplicate_participants
        )
        if receipt.get("approval_quorum_met") is not coverage_complete:
            errors.append("approval_quorum_met must reflect missing participant coverage")
        if receipt.get("transport_receipt_set_complete") is not collection_complete:
            errors.append("transport_receipt_set_complete must reflect complete valid receipt coverage")
        if receipt.get("collection_status") not in {"complete", "incomplete"}:
            errors.append("collection_status must be complete or incomplete")
        elif receipt.get("collection_status") == "complete" and not collection_complete:
            errors.append("complete collection cannot have missing participants")

        expected_receipt_digests: List[str] | None = None
        if approval_transport_receipts is not None:
            receipt_by_participant = {
                item.get("participant_id"): item
                for item in approval_transport_receipts
                if isinstance(item, Mapping)
            }
            expected_receipt_digests = [
                receipt_by_participant[participant]["digest"]
                for participant in covered
                if participant in receipt_by_participant
            ]
            if digest_list != expected_receipt_digests:
                errors.append("receipt_digests must follow covered participant order")

        receipt_set_digest_bound = receipt.get("receipt_set_digest") == sha256_text(
            canonical_json(digest_list)
        )
        if not receipt_set_digest_bound:
            errors.append("receipt_set_digest must match receipt_digests")
        batches_within_limit = True
        batch_digest_bound = True
        flattened_batch_participants: List[str] = []
        flattened_batch_digests: List[str] = []
        for batch in batches:
            if not isinstance(batch, Mapping):
                errors.append("batches must contain objects")
                batches_within_limit = False
                batch_digest_bound = False
                continue
            batch_participants = batch.get("participant_ids")
            batch_digests = batch.get("receipt_digests")
            if not isinstance(batch_participants, list) or not isinstance(batch_digests, list):
                errors.append("batch participants and receipt_digests must be lists")
                batches_within_limit = False
                batch_digest_bound = False
                continue
            flattened_batch_participants.extend(batch_participants)
            flattened_batch_digests.extend(batch_digests)
            if len(batch_participants) > max_batch_size or batch.get("within_batch_limit") is not True:
                batches_within_limit = False
                errors.append("batch exceeds max_batch_size")
            expected_batch = {
                key: deepcopy(value)
                for key, value in batch.items()
                if key != "batch_digest"
            }
            if batch.get("batch_digest") != sha256_text(canonical_json(expected_batch)):
                batch_digest_bound = False
                errors.append("batch_digest must bind batch payload")
        if flattened_batch_participants != covered:
            errors.append("batches must cover participants in collection order")
        if flattened_batch_digests != digest_list:
            errors.append("batches must cover receipt digests in collection order")
        if receipt.get("batch_count") != len(batches):
            errors.append("batch_count must equal batches length")
        if receipt.get("receipt_count") != len(covered):
            errors.append("receipt_count must equal covered participant count")
        expected_digest = sha256_text(canonical_json(_approval_collection_digest_payload(receipt)))
        digest_bound = receipt.get("digest") == expected_digest
        if not digest_bound:
            errors.append("digest must match approval collection receipt payload")
        return {
            "ok": not errors,
            "errors": errors,
            "collection_complete": collection_complete,
            "participant_order_bound": participant_order_bound,
            "receipt_set_digest_bound": receipt_set_digest_bound,
            "batches_within_limit": batches_within_limit,
            "batch_digest_bound": batch_digest_bound,
            "digest_bound": digest_bound,
        }

    def validate_distributed_approval_fanout_receipt(
        self,
        receipt: Mapping[str, Any],
        *,
        required_participants: Sequence[str] | None = None,
        approval_subject_digest: str | None = None,
        approval_collection_digest: str | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")
        if receipt.get("kind") != "wms_distributed_approval_fanout_receipt":
            errors.append("kind must equal wms_distributed_approval_fanout_receipt")
        if receipt.get("schema_version") != WMS_SCHEMA_VERSION:
            errors.append(f"schema_version must be {WMS_SCHEMA_VERSION}")
        if receipt.get("fanout_policy_id") != WMS_APPROVAL_FANOUT_POLICY_ID:
            errors.append("fanout_policy_id mismatch")
        if receipt.get("digest_profile") != WMS_APPROVAL_FANOUT_DIGEST_PROFILE:
            errors.append("digest_profile mismatch")
        if receipt.get("fanout_retry_policy_id") != WMS_APPROVAL_FANOUT_RETRY_POLICY_ID:
            errors.append("fanout_retry_policy_id mismatch")
        if receipt.get("retry_digest_profile") != WMS_APPROVAL_FANOUT_RETRY_DIGEST_PROFILE:
            errors.append("retry_digest_profile mismatch")
        if receipt.get("max_retry_attempts") != WMS_APPROVAL_FANOUT_MAX_RETRY_ATTEMPTS:
            errors.append("max_retry_attempts mismatch")
        if receipt.get("retry_window_ms") != WMS_APPROVAL_FANOUT_RETRY_WINDOW_MS:
            errors.append("retry_window_ms mismatch")
        if receipt.get("distributed_transport_profile") != WMS_APPROVAL_FANOUT_TRANSPORT_PROFILE:
            errors.append("distributed_transport_profile mismatch")
        if receipt.get("council_tier") != WMS_APPROVAL_FANOUT_COUNCIL_TIER:
            errors.append("council_tier must be federation")

        expected_subject = approval_subject_digest
        if expected_subject is not None:
            try:
                expected_subject = self._normalize_digest(
                    expected_subject,
                    "approval_subject_digest",
                )
            except ValueError as exc:
                errors.append(str(exc))
        subject_digest = receipt.get("approval_subject_digest")
        if not isinstance(subject_digest, str) or len(subject_digest) != 64:
            errors.append("approval_subject_digest must be a sha256 hex digest")
            subject_digest = None
        elif expected_subject is not None and subject_digest != expected_subject:
            errors.append("approval_subject_digest must match expected subject")

        collection_digest = receipt.get("approval_collection_digest")
        if not isinstance(collection_digest, str) or len(collection_digest) != 64:
            errors.append("approval_collection_digest must be a sha256 hex digest")
            collection_digest = None
        elif approval_collection_digest is not None:
            try:
                expected_collection_digest = self._normalize_digest(
                    approval_collection_digest,
                    "approval_collection_digest",
                )
                if collection_digest != expected_collection_digest:
                    errors.append("approval_collection_digest must match expected collection")
            except ValueError as exc:
                errors.append(str(exc))

        collection_receipt = receipt.get("approval_collection_receipt")
        collection_validation = {"ok": False}
        if not isinstance(collection_receipt, Mapping):
            errors.append("approval_collection_receipt must be an object")
        else:
            if collection_digest is not None and collection_receipt.get("digest") != collection_digest:
                errors.append("approval_collection_digest must match collection receipt digest")
            collection_validation = self.validate_approval_collection_receipt(
                collection_receipt,
                required_participants=required_participants,
                approval_subject_digest=subject_digest,
            )
            errors.extend(
                f"approval_collection_receipt.{error}"
                for error in collection_validation["errors"]
            )
        if receipt.get("approval_collection_complete") is not collection_validation["ok"]:
            errors.append("approval_collection_complete must reflect collection validation")

        expected_required = list(required_participants or receipt.get("required_participants", []))
        required = receipt.get("required_participants")
        covered = receipt.get("covered_participants")
        missing = receipt.get("missing_participants")
        fanout_results = receipt.get("participant_fanout_results")
        if not isinstance(required, list) or not required:
            errors.append("required_participants must be a non-empty list")
            required = []
        if expected_required and required != expected_required:
            errors.append("required_participants must preserve WMS session order")
        if not isinstance(covered, list):
            errors.append("covered_participants must be a list")
            covered = []
        if not isinstance(missing, list):
            errors.append("missing_participants must be a list")
            missing = []
        if not isinstance(fanout_results, list):
            errors.append("participant_fanout_results must be a list")
            fanout_results = []
        retry_attempts = receipt.get("retry_attempts")
        if not isinstance(retry_attempts, list):
            errors.append("retry_attempts must be a list")
            retry_attempts = []
        duplicate_participants = receipt.get("duplicate_participants")
        if not isinstance(duplicate_participants, list):
            errors.append("duplicate_participants must be a list")
            duplicate_participants = []
        invalid_result_count = receipt.get("invalid_result_count")
        if not isinstance(invalid_result_count, int) or invalid_result_count < 0:
            errors.append("invalid_result_count must be a non-negative integer")
            invalid_result_count = 0

        participant_order_bound = covered == required[: len(covered)]
        if receipt.get("participant_order_bound") is not participant_order_bound:
            errors.append("participant_order_bound must reflect covered participant ordering")
        expected_missing = [participant for participant in required if participant not in covered]
        if missing != expected_missing:
            errors.append("missing_participants must reflect required minus covered participants")
        if receipt.get("participant_count") != len(required):
            errors.append("participant_count must equal required_participants length")
        if receipt.get("result_count") != len(covered):
            errors.append("result_count must equal covered_participants length")

        expected_result_digests: List[str] = []
        expected_envelope_digests: List[str] = []
        expected_receipt_digests: List[str] = []
        all_transport_authenticated = True
        all_result_digest_bound = True
        result_by_participant: Dict[str, Mapping[str, Any]] = {}
        for participant, result in zip(covered, fanout_results):
            if not isinstance(result, Mapping):
                errors.append("participant_fanout_results must contain objects")
                all_transport_authenticated = False
                all_result_digest_bound = False
                continue
            if result.get("participant_id") != participant:
                errors.append("participant_fanout_results must follow covered participant order")
            if result.get("council_tier") != WMS_APPROVAL_FANOUT_COUNCIL_TIER:
                errors.append("fanout result council_tier mismatch")
            if result.get("transport_profile") != WMS_APPROVAL_FANOUT_TRANSPORT_PROFILE:
                errors.append("fanout result transport_profile mismatch")
            envelope = result.get("transport_envelope")
            transport_receipt = result.get("transport_receipt")
            if not isinstance(envelope, Mapping) or not isinstance(transport_receipt, Mapping):
                errors.append("fanout result must carry transport_envelope and transport_receipt")
                all_transport_authenticated = False
                all_result_digest_bound = False
                continue
            expected_digest = (
                self.build_distributed_approval_result_digest(
                    approval_subject_digest=subject_digest,
                    participant_id=participant,
                    approval_collection_digest=collection_digest,
                )
                if isinstance(subject_digest, str) and isinstance(collection_digest, str)
                else ""
            )
            expected_result_digests.append(expected_digest)
            expected_envelope_digests.append(str(envelope.get("envelope_digest")))
            expected_receipt_digests.append(str(transport_receipt.get("digest")))
            if result.get("approval_result_digest") != expected_digest:
                all_result_digest_bound = False
                errors.append("approval_result_digest must bind participant, subject, and collection")
            if result.get("expected_approval_result_digest") != expected_digest:
                all_result_digest_bound = False
                errors.append("expected_approval_result_digest must match computed digest")
            if transport_receipt.get("result_digest") != expected_digest:
                all_result_digest_bound = False
                errors.append("transport receipt result_digest must match approval result digest")
            authenticity_checks = transport_receipt.get("authenticity_checks")
            if not isinstance(authenticity_checks, Mapping):
                authenticity_checks = {}
            authenticated = (
                envelope.get("kind") == "distributed_transport_envelope"
                and transport_receipt.get("kind") == "distributed_transport_receipt"
                and transport_receipt.get("receipt_status") == "authenticated"
                and transport_receipt.get("envelope_ref") == envelope.get("envelope_id")
                and transport_receipt.get("envelope_digest") == envelope.get("envelope_digest")
                and authenticity_checks.get("channel_authenticated") is True
                and authenticity_checks.get("required_roles_satisfied") is True
                and authenticity_checks.get("quorum_attested") is True
                and authenticity_checks.get("federated_roots_verified") is True
                and authenticity_checks.get("key_epoch_accepted") is True
                and authenticity_checks.get("replay_guard_status") == "accepted"
                and authenticity_checks.get("multi_hop_replay_status") == "accepted"
            )
            if result.get("transport_authenticated") is not authenticated or not authenticated:
                all_transport_authenticated = False
                errors.append("fanout transport receipt must be authenticated and bound")
            if result.get("result_digest_bound") is not (transport_receipt.get("result_digest") == expected_digest):
                all_result_digest_bound = False
                errors.append("result_digest_bound must reflect transport receipt result digest")
            if result.get("transport_envelope_digest") != envelope.get("envelope_digest"):
                errors.append("transport_envelope_digest must match envelope")
            if result.get("transport_receipt_digest") != transport_receipt.get("digest"):
                errors.append("transport_receipt_digest must match receipt")
            if isinstance(result.get("participant_id"), str):
                result_by_participant[str(result["participant_id"])] = result

        if len(fanout_results) != len(covered):
            errors.append("participant_fanout_results length must equal covered_participants length")
        if receipt.get("participant_result_digests") != expected_result_digests:
            errors.append("participant_result_digests must follow covered participant order")
        if receipt.get("transport_envelope_digests") != expected_envelope_digests:
            errors.append("transport_envelope_digests must follow covered participant order")
        if receipt.get("transport_receipt_digests") != expected_receipt_digests:
            errors.append("transport_receipt_digests must follow covered participant order")
        receipt_set_digest_bound = receipt.get("transport_receipt_set_digest") == sha256_text(
            canonical_json(receipt.get("transport_receipt_digests", []))
        )
        if not receipt_set_digest_bound:
            errors.append("transport_receipt_set_digest must bind transport_receipt_digests")
        retry_policy_bound = self._validate_fanout_retry_policy(
            retry_attempts,
            receipt=receipt,
            required_participants=required,
            covered_participants=covered,
            result_by_participant=result_by_participant,
            errors=errors,
        )
        complete = (
            collection_validation["ok"]
            and not expected_missing
            and invalid_result_count == 0
            and not duplicate_participants
            and all_transport_authenticated
            and all_result_digest_bound
            and retry_policy_bound
        )
        if receipt.get("fanout_status") not in {"complete", "incomplete"}:
            errors.append("fanout_status must be complete or incomplete")
        elif receipt.get("fanout_status") == "complete" and not complete:
            errors.append("complete fanout requires all participant transport results")
        if receipt.get("transport_receipt_set_authenticated") is not complete:
            errors.append("transport_receipt_set_authenticated must reflect complete transport fanout")
        expected_digest = sha256_text(canonical_json(_approval_fanout_digest_payload(receipt)))
        digest_bound = receipt.get("digest") == expected_digest
        if not digest_bound:
            errors.append("digest must match approval fanout receipt payload")
        return {
            "ok": not errors,
            "errors": errors,
            "approval_collection_complete": collection_validation["ok"],
            "fanout_complete": complete,
            "transport_receipt_set_authenticated": complete,
            "result_digest_bound": all_result_digest_bound,
            "participant_order_bound": participant_order_bound,
            "retry_policy_bound": retry_policy_bound,
            "partial_outage_recovered": receipt.get("partial_outage_status")
            in {"not-required", "recovered"},
            "collection_digest_bound": (
                isinstance(collection_receipt, Mapping)
                and receipt.get("approval_collection_digest") == collection_receipt.get("digest")
            ),
            "receipt_set_digest_bound": receipt_set_digest_bound,
            "digest_bound": digest_bound,
        }

    def _build_fanout_retry_attempts(
        self,
        retry_attempts: Sequence[Mapping[str, Any]],
        *,
        required_participants: Sequence[str],
        results_by_participant: Mapping[str, Mapping[str, Any]],
    ) -> List[Dict[str, Any]]:
        normalized_attempts: List[Dict[str, Any]] = []
        seen_attempts: set[tuple[str, int]] = set()
        for raw_attempt in retry_attempts:
            if not isinstance(raw_attempt, Mapping):
                raise ValueError("fanout_retry_attempts must contain mappings")
            participant = self._normalize_non_empty_string(
                str(raw_attempt.get("participant_id") or ""),
                "participant_id",
            )
            if participant not in required_participants:
                raise ValueError("retry participant_id must belong to the WMS session")
            if participant not in results_by_participant:
                raise ValueError("retry participant must have a recovered fanout result")
            attempt_index = raw_attempt.get("attempt_index")
            if (
                not isinstance(attempt_index, int)
                or attempt_index < 1
                or attempt_index > WMS_APPROVAL_FANOUT_MAX_RETRY_ATTEMPTS
            ):
                raise ValueError("attempt_index must be within bounded retry attempts")
            attempt_key = (participant, attempt_index)
            if attempt_key in seen_attempts:
                raise ValueError("retry attempts must be unique per participant and index")
            seen_attempts.add(attempt_key)
            outage_kind = self._normalize_non_empty_string(
                str(raw_attempt.get("outage_kind") or ""),
                "outage_kind",
            )
            if outage_kind not in WMS_APPROVAL_FANOUT_OUTAGE_KINDS:
                raise ValueError("outage_kind is not allowed")
            retry_after_ms = raw_attempt.get("retry_after_ms")
            if (
                not isinstance(retry_after_ms, int)
                or retry_after_ms < 0
                or retry_after_ms > WMS_APPROVAL_FANOUT_RETRY_WINDOW_MS
            ):
                raise ValueError("retry_after_ms must fit the retry window")
            retry_decision = raw_attempt.get("retry_decision", "retry")
            if retry_decision != "retry":
                raise ValueError("retry_decision must be retry")

            result = results_by_participant[participant]
            recovery_result_digest = self._normalize_digest(
                raw_attempt.get("recovery_result_digest")
                or result["approval_result_digest"],
                "recovery_result_digest",
            )
            recovery_transport_receipt_digest = self._normalize_digest(
                raw_attempt.get("recovery_transport_receipt_digest")
                or result["transport_receipt_digest"],
                "recovery_transport_receipt_digest",
            )
            if recovery_result_digest != result["approval_result_digest"]:
                raise ValueError("recovery_result_digest must match recovered fanout result")
            if recovery_transport_receipt_digest != result["transport_receipt_digest"]:
                raise ValueError(
                    "recovery_transport_receipt_digest must match recovered transport receipt"
                )

            retry_attempt_ref = raw_attempt.get("retry_attempt_ref")
            if retry_attempt_ref is None:
                participant_digest = sha256_text(participant)[:12]
                retry_attempt_ref = (
                    f"retry://wms-approval-fanout/{participant_digest}/{attempt_index}"
                )
            retry_attempt_ref = self._normalize_non_empty_string(
                str(retry_attempt_ref),
                "retry_attempt_ref",
            )
            outage_observation_digest = raw_attempt.get("outage_observation_digest")
            if outage_observation_digest is None:
                outage_observation_digest = sha256_text(
                    canonical_json(
                        {
                            "participant_id": participant,
                            "attempt_index": attempt_index,
                            "outage_kind": outage_kind,
                            "retry_after_ms": retry_after_ms,
                            "retry_policy_id": WMS_APPROVAL_FANOUT_RETRY_POLICY_ID,
                        }
                    )
                )
            outage_observation_digest = self._normalize_digest(
                outage_observation_digest,
                "outage_observation_digest",
            )
            attempt = {
                "retry_attempt_ref": retry_attempt_ref,
                "participant_id": participant,
                "attempt_index": attempt_index,
                "outage_kind": outage_kind,
                "outage_observation_digest": outage_observation_digest,
                "retry_after_ms": retry_after_ms,
                "retry_window_ms": WMS_APPROVAL_FANOUT_RETRY_WINDOW_MS,
                "retry_decision": "retry",
                "recovery_result_digest": recovery_result_digest,
                "recovery_transport_receipt_digest": recovery_transport_receipt_digest,
                "recovered": True,
            }
            attempt["attempt_digest"] = sha256_text(
                canonical_json(_fanout_retry_attempt_digest_payload(attempt))
            )
            normalized_attempts.append(attempt)
        participant_rank = {
            participant: index for index, participant in enumerate(required_participants)
        }
        normalized_attempts.sort(
            key=lambda attempt: (
                participant_rank.get(attempt["participant_id"], len(participant_rank)),
                attempt["attempt_index"],
            )
        )
        return normalized_attempts

    def _validate_fanout_retry_policy(
        self,
        retry_attempts: Sequence[Mapping[str, Any]],
        *,
        receipt: Mapping[str, Any],
        required_participants: Sequence[str],
        covered_participants: Sequence[str],
        result_by_participant: Mapping[str, Mapping[str, Any]],
        errors: List[str],
    ) -> bool:
        retry_attempt_digests: List[str] = []
        outage_participants: List[str] = []
        recovered_participants: List[str] = []
        retry_policy_bound = True
        seen_attempts: set[tuple[str, int]] = set()
        for attempt in retry_attempts:
            if not isinstance(attempt, Mapping):
                errors.append("retry_attempts must contain objects")
                retry_policy_bound = False
                continue
            participant = attempt.get("participant_id")
            attempt_index = attempt.get("attempt_index")
            if participant not in required_participants:
                errors.append("retry participant_id must belong to required_participants")
                retry_policy_bound = False
            if participant not in covered_participants:
                errors.append("retry participant must have a recovered fanout result")
                retry_policy_bound = False
            if (
                not isinstance(attempt_index, int)
                or attempt_index < 1
                or attempt_index > WMS_APPROVAL_FANOUT_MAX_RETRY_ATTEMPTS
            ):
                errors.append("retry attempt_index must fit max_retry_attempts")
                retry_policy_bound = False
                attempt_index = -1
            attempt_key = (str(participant), int(attempt_index))
            if attempt_key in seen_attempts:
                errors.append("retry attempts must be unique per participant and index")
                retry_policy_bound = False
            seen_attempts.add(attempt_key)
            if attempt.get("outage_kind") not in WMS_APPROVAL_FANOUT_OUTAGE_KINDS:
                errors.append("retry outage_kind is not allowed")
                retry_policy_bound = False
            retry_after_ms = attempt.get("retry_after_ms")
            if (
                not isinstance(retry_after_ms, int)
                or retry_after_ms < 0
                or retry_after_ms > WMS_APPROVAL_FANOUT_RETRY_WINDOW_MS
            ):
                errors.append("retry_after_ms must fit retry_window_ms")
                retry_policy_bound = False
            if attempt.get("retry_window_ms") != WMS_APPROVAL_FANOUT_RETRY_WINDOW_MS:
                errors.append("retry attempt retry_window_ms mismatch")
                retry_policy_bound = False
            if attempt.get("retry_decision") != "retry":
                errors.append("retry_decision must be retry")
                retry_policy_bound = False
            for field_name in (
                "retry_attempt_ref",
                "outage_observation_digest",
                "recovery_result_digest",
                "recovery_transport_receipt_digest",
                "attempt_digest",
            ):
                value = attempt.get(field_name)
                if field_name == "retry_attempt_ref":
                    self._check_non_empty_string(value, field_name, errors)
                    if not isinstance(value, str) or not value.strip():
                        retry_policy_bound = False
                elif not isinstance(value, str) or len(value) != 64:
                    errors.append(f"{field_name} must be a sha256 hex digest")
                    retry_policy_bound = False
            result = (
                result_by_participant.get(str(participant))
                if isinstance(participant, str)
                else None
            )
            if result is not None:
                if attempt.get("recovery_result_digest") != result.get("approval_result_digest"):
                    errors.append("retry recovery_result_digest must match final fanout result")
                    retry_policy_bound = False
                if attempt.get("recovery_transport_receipt_digest") != result.get(
                    "transport_receipt_digest"
                ):
                    errors.append(
                        "retry recovery_transport_receipt_digest must match final transport receipt"
                    )
                    retry_policy_bound = False
            expected_attempt_digest = sha256_text(
                canonical_json(_fanout_retry_attempt_digest_payload(attempt))
            )
            if attempt.get("attempt_digest") != expected_attempt_digest:
                errors.append("retry attempt_digest must bind retry payload")
                retry_policy_bound = False
            if isinstance(attempt.get("attempt_digest"), str):
                retry_attempt_digests.append(str(attempt["attempt_digest"]))
            if isinstance(participant, str):
                outage_participants.append(participant)
                if attempt.get("recovered") is True:
                    recovered_participants.append(participant)
                else:
                    retry_policy_bound = False
                    errors.append("retry attempt must be recovered before fanout completes")

        expected_outage_participants = _dedupe_preserve_order(outage_participants)
        expected_recovered_participants = _dedupe_preserve_order(recovered_participants)
        if receipt.get("retry_attempt_count") != len(retry_attempts):
            errors.append("retry_attempt_count must equal retry_attempts length")
            retry_policy_bound = False
        if receipt.get("retry_attempt_digests") != retry_attempt_digests:
            errors.append("retry_attempt_digests must follow retry attempt order")
            retry_policy_bound = False
        if receipt.get("retry_attempt_set_digest") != sha256_text(
            canonical_json(retry_attempt_digests)
        ):
            errors.append("retry_attempt_set_digest must bind retry_attempt_digests")
            retry_policy_bound = False
        if receipt.get("outage_participants") != expected_outage_participants:
            errors.append("outage_participants must reflect retry attempts")
            retry_policy_bound = False
        if receipt.get("retry_recovered_participants") != expected_recovered_participants:
            errors.append("retry_recovered_participants must reflect recovered attempts")
            retry_policy_bound = False
        expected_status = (
            "not-required"
            if not retry_attempts
            else "recovered"
            if expected_outage_participants == expected_recovered_participants
            else "blocked"
        )
        if receipt.get("partial_outage_status") != expected_status:
            errors.append("partial_outage_status must reflect retry recovery")
            retry_policy_bound = False
        if receipt.get("all_retry_attempts_recovered") is not (
            expected_status in {"not-required", "recovered"}
        ):
            errors.append("all_retry_attempts_recovered must reflect retry status")
            retry_policy_bound = False
        if len(retry_attempts) > WMS_APPROVAL_FANOUT_MAX_RETRY_ATTEMPTS * max(
            1, len(required_participants)
        ):
            errors.append("retry attempts exceed bounded retry policy")
            retry_policy_bound = False
        return retry_policy_bound

    def _build_remote_authority_route_observations(
        self,
        route_health_observations: Sequence[Mapping[str, Any]],
        *,
        required_participants: Sequence[str],
    ) -> List[Dict[str, Any]]:
        observations: List[Dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for index, raw_observation in enumerate(route_health_observations, start=1):
            if not isinstance(raw_observation, Mapping):
                raise ValueError("route_health_observations must contain mappings")
            participant = self._normalize_non_empty_string(
                str(raw_observation.get("participant_id") or ""),
                "participant_id",
            )
            if participant not in required_participants:
                raise ValueError("route health participant_id must belong to the WMS session")
            outage_kind = self._normalize_non_empty_string(
                str(raw_observation.get("outage_kind") or ""),
                "outage_kind",
            )
            if outage_kind not in WMS_APPROVAL_FANOUT_OUTAGE_KINDS:
                raise ValueError("route health outage_kind is not allowed")
            authority_ref = self._normalize_non_empty_string(
                str(raw_observation.get("authority_ref") or ""),
                "authority_ref",
            )
            route_ref = self._normalize_non_empty_string(
                str(raw_observation.get("route_ref") or ""),
                "route_ref",
            )
            remote_jurisdiction = self._normalize_non_empty_string(
                str(raw_observation.get("remote_jurisdiction") or ""),
                "remote_jurisdiction",
            )
            jurisdiction_rate_limit_ref = self._normalize_non_empty_string(
                str(raw_observation.get("jurisdiction_rate_limit_ref") or ""),
                "jurisdiction_rate_limit_ref",
            )
            signer_key_ref = self._normalize_non_empty_string(
                str(raw_observation.get("signer_key_ref") or ""),
                "signer_key_ref",
            )
            jurisdiction_retry_limit_ms = raw_observation.get(
                "jurisdiction_retry_limit_ms"
            )
            if (
                not isinstance(jurisdiction_retry_limit_ms, int)
                or jurisdiction_retry_limit_ms < 1
                or jurisdiction_retry_limit_ms > WMS_REMOTE_AUTHORITY_RETRY_TOTAL_BUDGET_MS
            ):
                raise ValueError(
                    "jurisdiction_retry_limit_ms must be a positive integer within total retry budget"
                )
            key = (participant, outage_kind, route_ref)
            if key in seen:
                raise ValueError("route health observations must be unique per route")
            seen.add(key)
            route_status = self._normalize_non_empty_string(
                str(raw_observation.get("route_status") or ""),
                "route_status",
            )
            if route_status not in WMS_REMOTE_AUTHORITY_ROUTE_STATUSES:
                raise ValueError("route_status is not allowed")
            observed_latency_ms = raw_observation.get("observed_latency_ms")
            if not isinstance(observed_latency_ms, int) or observed_latency_ms < 0:
                raise ValueError("observed_latency_ms must be a non-negative integer")
            success_ratio = raw_observation.get("success_ratio")
            if not isinstance(success_ratio, (int, float)):
                raise ValueError("success_ratio must be a number")
            success_ratio = round(float(success_ratio), 3)
            if success_ratio < 0.0 or success_ratio > 1.0:
                raise ValueError("success_ratio must be between 0 and 1")
            consecutive_failures = raw_observation.get("consecutive_failures", 0)
            if not isinstance(consecutive_failures, int) or consecutive_failures < 0:
                raise ValueError("consecutive_failures must be a non-negative integer")
            retry_budget_eligible = (
                route_status in {"healthy", "degraded", "partial-outage", "recovered"}
                and success_ratio >= 0.5
                and consecutive_failures <= WMS_APPROVAL_FANOUT_MAX_RETRY_ATTEMPTS
            )
            jurisdiction_rate_limit_payload = {
                "authority_ref": authority_ref,
                "route_ref": route_ref,
                "remote_jurisdiction": remote_jurisdiction,
                "jurisdiction_rate_limit_ref": jurisdiction_rate_limit_ref,
                "jurisdiction_retry_limit_ms": jurisdiction_retry_limit_ms,
                "outage_kind": outage_kind,
                "signer_key_ref": signer_key_ref,
            }
            jurisdiction_rate_limit_digest = sha256_text(
                canonical_json(jurisdiction_rate_limit_payload)
            )
            authority_signature_digest = sha256_text(
                canonical_json(
                    {
                        "signature_policy_id": WMS_REMOTE_AUTHORITY_RETRY_SIGNATURE_POLICY_ID,
                        "authority_ref": authority_ref,
                        "route_ref": route_ref,
                        "participant_id": participant,
                        "outage_kind": outage_kind,
                        "remote_jurisdiction": remote_jurisdiction,
                        "jurisdiction_rate_limit_digest": jurisdiction_rate_limit_digest,
                        "signer_key_ref": signer_key_ref,
                    }
                )
            )
            observation = {
                "observation_ref": self._normalize_non_empty_string(
                    str(
                        raw_observation.get("observation_ref")
                        or f"route-health://wms-authority/{index:02d}"
                    ),
                    "observation_ref",
                ),
                "authority_ref": authority_ref,
                "route_ref": route_ref,
                "participant_id": participant,
                "outage_kind": outage_kind,
                "route_status": route_status,
                "remote_jurisdiction": remote_jurisdiction,
                "jurisdiction_rate_limit_ref": jurisdiction_rate_limit_ref,
                "jurisdiction_retry_limit_ms": jurisdiction_retry_limit_ms,
                "jurisdiction_rate_limit_digest": jurisdiction_rate_limit_digest,
                "signer_key_ref": signer_key_ref,
                "authority_signature_digest": authority_signature_digest,
                "observed_latency_ms": observed_latency_ms,
                "success_ratio": success_ratio,
                "consecutive_failures": consecutive_failures,
                "retry_budget_eligible": retry_budget_eligible,
            }
            observation["observation_digest"] = sha256_text(
                canonical_json(
                    _remote_authority_route_observation_digest_payload(observation)
                )
            )
            observations.append(observation)
        participant_rank = {
            participant: index for index, participant in enumerate(required_participants)
        }
        observations.sort(
            key=lambda observation: (
                participant_rank.get(observation["participant_id"], len(participant_rank)),
                observation["outage_kind"],
                observation["route_ref"],
            )
        )
        return observations

    def validate_remote_authority_retry_budget_receipt(
        self,
        receipt: Mapping[str, Any],
        *,
        approval_fanout_receipt: Mapping[str, Any] | None = None,
        engine_transaction_log_receipt: Mapping[str, Any] | None = None,
        required_participants: Sequence[str] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")
        if receipt.get("kind") != "wms_remote_authority_retry_budget_receipt":
            errors.append("kind must equal wms_remote_authority_retry_budget_receipt")
        if receipt.get("schema_version") != WMS_SCHEMA_VERSION:
            errors.append(f"schema_version must be {WMS_SCHEMA_VERSION}")
        if receipt.get("retry_budget_policy_id") != WMS_REMOTE_AUTHORITY_RETRY_POLICY_ID:
            errors.append("retry_budget_policy_id mismatch")
        if receipt.get("digest_profile") != WMS_REMOTE_AUTHORITY_RETRY_DIGEST_PROFILE:
            errors.append("digest_profile mismatch")
        if receipt.get("signature_policy_id") != WMS_REMOTE_AUTHORITY_RETRY_SIGNATURE_POLICY_ID:
            errors.append("signature_policy_id mismatch")
        if (
            receipt.get("jurisdiction_rate_limit_profile")
            != WMS_REMOTE_AUTHORITY_JURISDICTION_RATE_LIMIT_PROFILE
        ):
            errors.append("jurisdiction_rate_limit_profile mismatch")
        if receipt.get("signature_digest_profile") != WMS_REMOTE_AUTHORITY_SIGNATURE_DIGEST_PROFILE:
            errors.append("signature_digest_profile mismatch")
        if receipt.get("schedule_profile") != WMS_REMOTE_AUTHORITY_RETRY_SCHEDULE_PROFILE:
            errors.append("schedule_profile mismatch")
        if receipt.get("approval_fanout_policy_id") != WMS_APPROVAL_FANOUT_POLICY_ID:
            errors.append("approval_fanout_policy_id mismatch")
        if receipt.get("fanout_retry_policy_id") != WMS_APPROVAL_FANOUT_RETRY_POLICY_ID:
            errors.append("fanout_retry_policy_id mismatch")
        if receipt.get("engine_transaction_log_policy_id") != WMS_ENGINE_TRANSACTION_LOG_POLICY_ID:
            errors.append("engine_transaction_log_policy_id mismatch")
        if receipt.get("base_retry_after_ms") != WMS_REMOTE_AUTHORITY_RETRY_BASE_DELAY_MS:
            errors.append("base_retry_after_ms mismatch")
        if receipt.get("exponential_multiplier") != WMS_REMOTE_AUTHORITY_RETRY_MULTIPLIER:
            errors.append("exponential_multiplier mismatch")
        if receipt.get("max_retry_attempts") != WMS_APPROVAL_FANOUT_MAX_RETRY_ATTEMPTS:
            errors.append("max_retry_attempts mismatch")
        if receipt.get("total_retry_budget_ms") != WMS_REMOTE_AUTHORITY_RETRY_TOTAL_BUDGET_MS:
            errors.append("total_retry_budget_ms mismatch")
        for field_name in ("session_id", "authority_profile_ref"):
            self._check_non_empty_string(receipt.get(field_name), field_name, errors)

        fanout_digest = receipt.get("approval_fanout_digest")
        if not isinstance(fanout_digest, str) or len(fanout_digest) != 64:
            errors.append("approval_fanout_digest must be a sha256 hex digest")
            fanout_digest = ""
        engine_log_digest = receipt.get("engine_transaction_log_digest")
        if not isinstance(engine_log_digest, str) or len(engine_log_digest) != 64:
            errors.append("engine_transaction_log_digest must be a sha256 hex digest")
            engine_log_digest = ""

        expected_participants = list(required_participants or [])
        fanout_validation = {"ok": False}
        fanout_retry_attempts: List[Mapping[str, Any]] = []
        engine_log_fanout_bound = receipt.get("engine_log_fanout_bound") is True
        if approval_fanout_receipt is not None:
            if approval_fanout_receipt.get("digest") != fanout_digest:
                errors.append("approval_fanout_digest must match approval_fanout_receipt")
            expected_participants = expected_participants or list(
                approval_fanout_receipt.get("required_participants", [])
            )
            fanout_validation = self.validate_distributed_approval_fanout_receipt(
                approval_fanout_receipt,
                required_participants=expected_participants,
                approval_subject_digest=approval_fanout_receipt.get(
                    "approval_subject_digest"
                ),
                approval_collection_digest=approval_fanout_receipt.get(
                    "approval_collection_digest"
                ),
            )
            errors.extend(
                f"approval_fanout_receipt.{error}"
                for error in fanout_validation["errors"]
            )
            raw_attempts = approval_fanout_receipt.get("retry_attempts", [])
            if isinstance(raw_attempts, list):
                fanout_retry_attempts = [
                    attempt for attempt in raw_attempts if isinstance(attempt, Mapping)
                ]
        if engine_transaction_log_receipt is not None:
            if engine_transaction_log_receipt.get("digest") != engine_log_digest:
                errors.append("engine_transaction_log_digest must match engine log receipt")
            engine_validation = self.validate_engine_transaction_log_receipt(
                engine_transaction_log_receipt
            )
            errors.extend(
                f"engine_transaction_log_receipt.{error}"
                for error in engine_validation["errors"]
            )
            engine_log_fanout_bound = any(
                entry.get("operation") == "approval_fanout_bound"
                and entry.get("source_artifact_digest") == fanout_digest
                for entry in engine_transaction_log_receipt.get("transaction_entries", [])
                if isinstance(entry, Mapping)
            )
        if receipt.get("engine_log_fanout_bound") is not engine_log_fanout_bound:
            errors.append("engine_log_fanout_bound must reflect engine log source artifact binding")

        observations = receipt.get("route_health_observations")
        if not isinstance(observations, list):
            errors.append("route_health_observations must be a list")
            observations = []
        expected_observation_digests: List[str] = []
        expected_rate_limit_digests: List[str] = []
        expected_signature_digests: List[str] = []
        observation_by_key: Dict[tuple[str, str], Mapping[str, Any]] = {}
        route_health_bound = True
        for observation in observations:
            if not isinstance(observation, Mapping):
                errors.append("route_health_observations must contain objects")
                route_health_bound = False
                continue
            for field_name in (
                "observation_ref",
                "authority_ref",
                "route_ref",
                "participant_id",
                "outage_kind",
                "route_status",
                "remote_jurisdiction",
                "jurisdiction_rate_limit_ref",
                "signer_key_ref",
            ):
                self._check_non_empty_string(observation.get(field_name), field_name, errors)
            if observation.get("participant_id") not in expected_participants:
                errors.append("route health participant_id must belong to required participants")
                route_health_bound = False
            if observation.get("outage_kind") not in WMS_APPROVAL_FANOUT_OUTAGE_KINDS:
                errors.append("route health outage_kind is not allowed")
                route_health_bound = False
            if observation.get("route_status") not in WMS_REMOTE_AUTHORITY_ROUTE_STATUSES:
                errors.append("route_status is not allowed")
                route_health_bound = False
            if observation.get("retry_budget_eligible") is not True:
                errors.append("route health observation must be retry-budget eligible")
                route_health_bound = False
            observed_latency_ms = observation.get("observed_latency_ms")
            if not isinstance(observed_latency_ms, int) or observed_latency_ms < 0:
                errors.append("observed_latency_ms must be a non-negative integer")
                route_health_bound = False
            success_ratio = observation.get("success_ratio")
            if not isinstance(success_ratio, (int, float)) or not 0.0 <= float(success_ratio) <= 1.0:
                errors.append("success_ratio must be between 0 and 1")
                route_health_bound = False
            consecutive_failures = observation.get("consecutive_failures")
            if not isinstance(consecutive_failures, int) or consecutive_failures < 0:
                errors.append("consecutive_failures must be a non-negative integer")
                route_health_bound = False
            jurisdiction_retry_limit_ms = observation.get("jurisdiction_retry_limit_ms")
            if (
                not isinstance(jurisdiction_retry_limit_ms, int)
                or jurisdiction_retry_limit_ms < 1
                or jurisdiction_retry_limit_ms > WMS_REMOTE_AUTHORITY_RETRY_TOTAL_BUDGET_MS
            ):
                errors.append("jurisdiction_retry_limit_ms must fit total retry budget")
                route_health_bound = False
                jurisdiction_retry_limit_ms = 0
            rate_limit_payload = {
                "authority_ref": observation.get("authority_ref"),
                "route_ref": observation.get("route_ref"),
                "remote_jurisdiction": observation.get("remote_jurisdiction"),
                "jurisdiction_rate_limit_ref": observation.get(
                    "jurisdiction_rate_limit_ref"
                ),
                "jurisdiction_retry_limit_ms": jurisdiction_retry_limit_ms,
                "outage_kind": observation.get("outage_kind"),
                "signer_key_ref": observation.get("signer_key_ref"),
            }
            expected_rate_limit_digest = sha256_text(
                canonical_json(rate_limit_payload)
            )
            if observation.get("jurisdiction_rate_limit_digest") != expected_rate_limit_digest:
                errors.append("jurisdiction_rate_limit_digest must bind signed rate limit payload")
                route_health_bound = False
            expected_signature_digest = sha256_text(
                canonical_json(
                    {
                        "signature_policy_id": WMS_REMOTE_AUTHORITY_RETRY_SIGNATURE_POLICY_ID,
                        "authority_ref": observation.get("authority_ref"),
                        "route_ref": observation.get("route_ref"),
                        "participant_id": observation.get("participant_id"),
                        "outage_kind": observation.get("outage_kind"),
                        "remote_jurisdiction": observation.get("remote_jurisdiction"),
                        "jurisdiction_rate_limit_digest": expected_rate_limit_digest,
                        "signer_key_ref": observation.get("signer_key_ref"),
                    }
                )
            )
            if observation.get("authority_signature_digest") != expected_signature_digest:
                errors.append("authority_signature_digest must bind jurisdiction rate limit digest")
                route_health_bound = False
            expected_digest = sha256_text(
                canonical_json(
                    _remote_authority_route_observation_digest_payload(observation)
                )
            )
            if observation.get("observation_digest") != expected_digest:
                errors.append("observation_digest must bind route health payload")
                route_health_bound = False
            if isinstance(observation.get("observation_digest"), str):
                expected_observation_digests.append(str(observation["observation_digest"]))
            if isinstance(observation.get("jurisdiction_rate_limit_digest"), str):
                expected_rate_limit_digests.append(
                    str(observation["jurisdiction_rate_limit_digest"])
                )
            if isinstance(observation.get("authority_signature_digest"), str):
                expected_signature_digests.append(
                    str(observation["authority_signature_digest"])
                )
            if isinstance(observation.get("participant_id"), str) and isinstance(
                observation.get("outage_kind"),
                str,
            ):
                observation_by_key[
                    (str(observation["participant_id"]), str(observation["outage_kind"]))
                ] = observation
        if receipt.get("route_health_observation_digests") != expected_observation_digests:
            errors.append("route_health_observation_digests must follow observation order")
            route_health_bound = False
        if receipt.get("route_health_set_digest") != sha256_text(
            canonical_json(expected_observation_digests)
        ):
            errors.append("route_health_set_digest must bind observation digests")
            route_health_bound = False

        remote_jurisdictions = receipt.get("remote_jurisdictions")
        expected_remote_jurisdictions = sorted(
            {
                str(observation.get("remote_jurisdiction"))
                for observation in observations
                if isinstance(observation, Mapping)
                and isinstance(observation.get("remote_jurisdiction"), str)
            }
        )
        jurisdiction_rate_limit_bound = route_health_bound and bool(
            expected_rate_limit_digests
        )
        authority_signature_bound = route_health_bound and bool(
            expected_signature_digests
        )
        if remote_jurisdictions != expected_remote_jurisdictions:
            errors.append("remote_jurisdictions must reflect observed jurisdictions")
            jurisdiction_rate_limit_bound = False
        if receipt.get("jurisdiction_rate_limit_digests") != expected_rate_limit_digests:
            errors.append("jurisdiction_rate_limit_digests must follow observation order")
            jurisdiction_rate_limit_bound = False
        if receipt.get("jurisdiction_rate_limit_set_digest") != sha256_text(
            canonical_json(expected_rate_limit_digests)
        ):
            errors.append("jurisdiction_rate_limit_set_digest must bind rate limit digests")
            jurisdiction_rate_limit_bound = False
        if receipt.get("authority_signature_digests") != expected_signature_digests:
            errors.append("authority_signature_digests must follow observation order")
            authority_signature_bound = False
        if receipt.get("authority_signature_set_digest") != sha256_text(
            canonical_json(expected_signature_digests)
        ):
            errors.append("authority_signature_set_digest must bind signature digests")
            authority_signature_bound = False

        schedule_entries = receipt.get("schedule_entries")
        if not isinstance(schedule_entries, list):
            errors.append("schedule_entries must be a list")
            schedule_entries = []
        expected_schedule_digests: List[str] = []
        schedule_bound = True
        total_scheduled_delay_ms = 0
        attempt_by_key = {
            (str(attempt.get("participant_id")), int(attempt.get("attempt_index", -1))): attempt
            for attempt in fanout_retry_attempts
        }
        for entry in schedule_entries:
            if not isinstance(entry, Mapping):
                errors.append("schedule_entries must contain objects")
                schedule_bound = False
                continue
            for field_name in (
                "schedule_entry_ref",
                "retry_attempt_ref",
                "participant_id",
                "outage_kind",
                "remote_jurisdiction",
                "jurisdiction_rate_limit_ref",
            ):
                self._check_non_empty_string(entry.get(field_name), field_name, errors)
            attempt_index = entry.get("attempt_index")
            if (
                not isinstance(attempt_index, int)
                or attempt_index < 1
                or attempt_index > WMS_APPROVAL_FANOUT_MAX_RETRY_ATTEMPTS
            ):
                errors.append("schedule attempt_index must fit max_retry_attempts")
                schedule_bound = False
                attempt_index = -1
            retry_after_ms = entry.get("retry_after_ms")
            if not isinstance(retry_after_ms, int) or retry_after_ms < 0:
                errors.append("schedule retry_after_ms must be non-negative")
                schedule_bound = False
                retry_after_ms = 0
            computed_backoff_ms = min(
                WMS_REMOTE_AUTHORITY_RETRY_BASE_DELAY_MS
                * (WMS_REMOTE_AUTHORITY_RETRY_MULTIPLIER ** (attempt_index - 1)),
                WMS_REMOTE_AUTHORITY_RETRY_TOTAL_BUDGET_MS,
            )
            if entry.get("computed_backoff_ms") != computed_backoff_ms:
                errors.append("computed_backoff_ms must follow fixed exponential backoff")
                schedule_bound = False
            total_scheduled_delay_ms += retry_after_ms
            observation = observation_by_key.get(
                (str(entry.get("participant_id")), str(entry.get("outage_kind")))
            )
            jurisdiction_retry_limit_ms = entry.get("jurisdiction_retry_limit_ms")
            if not isinstance(jurisdiction_retry_limit_ms, int) or jurisdiction_retry_limit_ms < 1:
                errors.append("schedule jurisdiction_retry_limit_ms must be positive")
                schedule_bound = False
                jurisdiction_retry_limit_ms = 0
            if observation is None:
                errors.append("schedule entry must bind a route health observation")
                schedule_bound = False
            elif entry.get("route_health_observation_digest") != observation.get(
                "observation_digest"
            ):
                errors.append("route_health_observation_digest must match observation")
                schedule_bound = False
            elif (
                entry.get("remote_jurisdiction") != observation.get("remote_jurisdiction")
                or entry.get("jurisdiction_rate_limit_ref")
                != observation.get("jurisdiction_rate_limit_ref")
                or entry.get("jurisdiction_retry_limit_ms")
                != observation.get("jurisdiction_retry_limit_ms")
                or entry.get("jurisdiction_rate_limit_digest")
                != observation.get("jurisdiction_rate_limit_digest")
                or entry.get("authority_signature_digest")
                != observation.get("authority_signature_digest")
            ):
                errors.append("schedule entry must copy jurisdiction rate limit and signature evidence")
                schedule_bound = False
            attempt = attempt_by_key.get((str(entry.get("participant_id")), attempt_index))
            if attempt is not None:
                if entry.get("retry_attempt_ref") != attempt.get("retry_attempt_ref"):
                    errors.append("schedule retry_attempt_ref must match fanout retry attempt")
                    schedule_bound = False
                if entry.get("recovery_result_digest") != attempt.get("recovery_result_digest"):
                    errors.append("schedule recovery_result_digest must match retry attempt")
                    schedule_bound = False
                if entry.get("recovery_transport_receipt_digest") != attempt.get(
                    "recovery_transport_receipt_digest"
                ):
                    errors.append("schedule recovery transport digest must match retry attempt")
                    schedule_bound = False
            if entry.get("route_health_eligible") is not True:
                errors.append("route_health_eligible must be true")
                schedule_bound = False
            jurisdiction_rate_limit_ok = (
                jurisdiction_retry_limit_ms > 0
                and retry_after_ms <= jurisdiction_retry_limit_ms
            )
            if entry.get("jurisdiction_rate_limit_ok") is not jurisdiction_rate_limit_ok:
                errors.append("jurisdiction_rate_limit_ok must reflect signed jurisdiction limit")
                schedule_bound = False
            if entry.get("within_budget") is not (
                retry_after_ms <= computed_backoff_ms
                and jurisdiction_rate_limit_ok
            ):
                errors.append("within_budget must reflect retry_after_ms, backoff, and jurisdiction limit")
                schedule_bound = False
            if entry.get("budget_decision") != "retry":
                errors.append("budget_decision must be retry")
                schedule_bound = False
            expected_entry_digest = sha256_text(
                canonical_json(
                    _remote_authority_retry_schedule_entry_digest_payload(entry)
                )
            )
            if entry.get("schedule_entry_digest") != expected_entry_digest:
                errors.append("schedule_entry_digest must bind schedule payload")
                schedule_bound = False
            if isinstance(entry.get("schedule_entry_digest"), str):
                expected_schedule_digests.append(str(entry["schedule_entry_digest"]))
        if receipt.get("schedule_entry_digests") != expected_schedule_digests:
            errors.append("schedule_entry_digests must follow schedule entry order")
            schedule_bound = False
        if receipt.get("schedule_set_digest") != sha256_text(
            canonical_json(expected_schedule_digests)
        ):
            errors.append("schedule_set_digest must bind schedule entry digests")
            schedule_bound = False
        if receipt.get("total_scheduled_delay_ms") != total_scheduled_delay_ms:
            errors.append("total_scheduled_delay_ms must equal schedule delay sum")
            schedule_bound = False
        if total_scheduled_delay_ms > WMS_REMOTE_AUTHORITY_RETRY_TOTAL_BUDGET_MS:
            errors.append("total_scheduled_delay_ms exceeds total retry budget")
            schedule_bound = False
        if receipt.get("max_scheduled_delay_ms") != max(
            [entry.get("retry_after_ms", 0) for entry in schedule_entries if isinstance(entry, Mapping)]
            or [0]
        ):
            errors.append("max_scheduled_delay_ms must reflect schedule entries")
            schedule_bound = False

        outage_participants = receipt.get("outage_participants")
        if not isinstance(outage_participants, list):
            errors.append("outage_participants must be a list")
            outage_participants = []
        all_outages_budgeted = (
            schedule_bound
            and route_health_bound
            and all(
                any(
                    entry.get("participant_id") == participant
                    for entry in schedule_entries
                    if isinstance(entry, Mapping)
                )
                for participant in outage_participants
            )
        )
        if receipt.get("all_outages_budgeted") is not all_outages_budgeted:
            errors.append("all_outages_budgeted must reflect schedule coverage")
        adaptive_retry_budget_bound = (
            (fanout_validation["ok"] if approval_fanout_receipt is not None else True)
            and engine_log_fanout_bound
            and route_health_bound
            and jurisdiction_rate_limit_bound
            and authority_signature_bound
            and schedule_bound
            and all_outages_budgeted
            and total_scheduled_delay_ms <= WMS_REMOTE_AUTHORITY_RETRY_TOTAL_BUDGET_MS
            and receipt.get("raw_remote_transcript_stored") is False
        )
        if receipt.get("jurisdiction_rate_limit_bound") is not jurisdiction_rate_limit_bound:
            errors.append("jurisdiction_rate_limit_bound must reflect signed rate limit digest binding")
        if receipt.get("authority_signature_bound") is not authority_signature_bound:
            errors.append("authority_signature_bound must reflect signature digest binding")
        if (
            receipt.get("signed_jurisdiction_retry_budget_bound")
            is not adaptive_retry_budget_bound
        ):
            errors.append("signed_jurisdiction_retry_budget_bound must reflect complete signed budget binding")
        if receipt.get("adaptive_retry_budget_bound") is not adaptive_retry_budget_bound:
            errors.append("adaptive_retry_budget_bound must reflect fanout, engine, route, and schedule binding")
        if receipt.get("budget_status") not in {"complete", "incomplete"}:
            errors.append("budget_status must be complete or incomplete")
        elif receipt.get("budget_status") == "complete" and not adaptive_retry_budget_bound:
            errors.append("complete budget_status requires adaptive_retry_budget_bound")
        if receipt.get("raw_remote_transcript_stored") is not False:
            errors.append("raw_remote_transcript_stored must be false")
        expected_digest = sha256_text(
            canonical_json(_remote_authority_retry_budget_digest_payload(receipt))
        )
        digest_bound = receipt.get("digest") == expected_digest
        if not digest_bound:
            errors.append("digest must match remote authority retry budget receipt payload")
        return {
            "ok": not errors,
            "errors": errors,
            "adaptive_retry_budget_bound": adaptive_retry_budget_bound,
            "budget_complete": receipt.get("budget_status") == "complete"
            and adaptive_retry_budget_bound,
            "engine_log_fanout_bound": engine_log_fanout_bound,
            "route_health_bound": route_health_bound,
            "schedule_bound": schedule_bound,
            "all_outages_budgeted": all_outages_budgeted,
            "digest_bound": digest_bound,
            "jurisdiction_rate_limit_bound": jurisdiction_rate_limit_bound,
            "authority_signature_bound": authority_signature_bound,
            "signed_jurisdiction_retry_budget_bound": adaptive_retry_budget_bound,
        }

    def validate_engine_transaction_log_receipt(
        self,
        receipt: Mapping[str, Any],
        *,
        required_operations: Sequence[str] | None = None,
        source_artifact_digests: Mapping[str, str] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")
        if receipt.get("kind") != "wms_engine_transaction_log":
            errors.append("kind must equal wms_engine_transaction_log")
        if receipt.get("schema_version") != WMS_SCHEMA_VERSION:
            errors.append(f"schema_version must be {WMS_SCHEMA_VERSION}")
        if receipt.get("transaction_log_policy_id") != WMS_ENGINE_TRANSACTION_LOG_POLICY_ID:
            errors.append("transaction_log_policy_id mismatch")
        if receipt.get("engine_adapter_profile") != WMS_ENGINE_ADAPTER_PROFILE:
            errors.append("engine_adapter_profile mismatch")
        if receipt.get("engine_adapter_signature_profile") != WMS_ENGINE_ADAPTER_SIGNATURE_PROFILE:
            errors.append("engine_adapter_signature_profile mismatch")
        if (
            receipt.get("engine_adapter_signature_digest_profile")
            != WMS_ENGINE_ADAPTER_SIGNATURE_DIGEST_PROFILE
        ):
            errors.append("engine_adapter_signature_digest_profile mismatch")
        if receipt.get("entry_digest_profile") != WMS_ENGINE_TRANSACTION_ENTRY_DIGEST_PROFILE:
            errors.append("entry_digest_profile mismatch")
        if receipt.get("digest_profile") != WMS_ENGINE_TRANSACTION_LOG_DIGEST_PROFILE:
            errors.append("digest_profile mismatch")
        for field_name in (
            "session_id",
            "engine_adapter_ref",
            "engine_adapter_key_ref",
            "engine_session_ref",
            "transaction_log_ref",
        ):
            self._check_non_empty_string(receipt.get(field_name), field_name, errors)
        self._check_digest(
            receipt.get("engine_adapter_signature_digest"),
            "engine_adapter_signature_digest",
            errors,
        )

        required = self._normalize_engine_required_operations(
            required_operations or receipt.get("required_operations")
        )
        if receipt.get("required_operations") != required:
            errors.append("required_operations must match the bounded operation set")
        expected_digests = {
            operation: self._normalize_digest(digest, f"source_artifact_digests.{operation}")
            for operation, digest in (source_artifact_digests or {}).items()
        }
        entries = receipt.get("transaction_entries")
        if not isinstance(entries, list) or not entries:
            errors.append("transaction_entries must be a non-empty list")
            entries = []

        entry_errors: List[str] = []
        normalized_entry_digests: List[str] = []
        ordered_transaction_ids: List[str] = []
        source_artifact_digests_ordered: List[str] = []
        state_transition_pairs: List[Dict[str, Any]] = []
        covered_operations: List[str] = []
        duplicate_transaction_ids: List[str] = []
        seen_transaction_ids: set[str] = set()
        invalid_transaction_count = 0
        engine_session_ref = (
            str(receipt.get("engine_session_ref"))
            if isinstance(receipt.get("engine_session_ref"), str)
            else ""
        )
        for index, entry in enumerate(entries, start=1):
            if not isinstance(entry, Mapping):
                entry_errors.append("transaction_entries must contain objects")
                invalid_transaction_count += 1
                continue
            transaction_id = entry.get("transaction_id")
            if isinstance(transaction_id, str):
                if transaction_id in seen_transaction_ids:
                    duplicate_transaction_ids.append(transaction_id)
                seen_transaction_ids.add(transaction_id)
                ordered_transaction_ids.append(transaction_id)
            try:
                self._validate_engine_transaction_entry(
                    entry,
                    expected_index=index,
                    engine_session_ref=engine_session_ref,
                    source_artifact_digests=expected_digests,
                )
            except ValueError as exc:
                entry_errors.append(str(exc))
                invalid_transaction_count += 1
                continue
            normalized_entry_digests.append(str(entry["entry_digest"]))
            source_artifact_digests_ordered.append(str(entry["source_artifact_digest"]))
            state_transition_pairs.append(
                {
                    "transaction_id": entry["transaction_id"],
                    "operation": entry["operation"],
                    "engine_state_before_digest": entry["engine_state_before_digest"],
                    "engine_state_after_digest": entry["engine_state_after_digest"],
                }
            )
            if entry["operation"] in required:
                covered_operations.append(str(entry["operation"]))

        errors.extend(f"transaction_entries.{error}" for error in entry_errors)
        missing_operations = [
            operation for operation in required if operation not in covered_operations
        ]
        entry_order_bound = [
            entry.get("transaction_index")
            for entry in entries
            if isinstance(entry, Mapping)
        ] == list(range(1, len(entries) + 1))
        redaction_complete = all(
            isinstance(entry, Mapping)
            and entry.get("payload_redacted") is True
            and entry.get("raw_payload_stored") is False
            for entry in entries
        )
        source_artifacts_bound = (
            not missing_operations
            and not entry_errors
            and all(
                not expected_digests
                or not isinstance(entry, Mapping)
                or entry.get("operation") not in expected_digests
                or entry.get("source_artifact_digest")
                == expected_digests[str(entry.get("operation"))]
                for entry in entries
            )
        )
        if receipt.get("covered_operations") != covered_operations:
            errors.append("covered_operations must follow transaction entry order")
        if receipt.get("missing_operations") != missing_operations:
            errors.append("missing_operations must reflect required minus covered operations")
        if receipt.get("duplicate_transaction_ids") != _dedupe_preserve_order(duplicate_transaction_ids):
            errors.append("duplicate_transaction_ids must reflect duplicate entry ids")
        if receipt.get("invalid_transaction_count") != invalid_transaction_count:
            errors.append("invalid_transaction_count must reflect invalid entries")
        if receipt.get("transaction_entry_count") != len(entries):
            errors.append("transaction_entry_count must equal transaction_entries length")
        if receipt.get("ordered_transaction_ids") != ordered_transaction_ids:
            errors.append("ordered_transaction_ids must follow transaction order")
        transaction_set_digest = sha256_text(canonical_json(normalized_entry_digests))
        source_artifact_digest_set_digest = sha256_text(
            canonical_json(source_artifact_digests_ordered)
        )
        engine_state_transition_digest = sha256_text(canonical_json(state_transition_pairs))
        if receipt.get("ordered_entry_digests") != normalized_entry_digests:
            errors.append("ordered_entry_digests must follow transaction order")
        if receipt.get("transaction_set_digest") != transaction_set_digest:
            errors.append("transaction_set_digest must bind ordered_entry_digests")
        if receipt.get("source_artifact_digest_set_digest") != source_artifact_digest_set_digest:
            errors.append("source_artifact_digest_set_digest must bind source artifacts")
        if receipt.get("engine_state_transition_digest") != engine_state_transition_digest:
            errors.append("engine_state_transition_digest must bind state transition pairs")
        if receipt.get("entry_order_bound") is not entry_order_bound:
            errors.append("entry_order_bound must reflect transaction indices")
        if receipt.get("source_artifacts_bound") is not source_artifacts_bound:
            errors.append("source_artifacts_bound must reflect source digest checks")
        if receipt.get("redaction_complete") is not redaction_complete:
            errors.append("redaction_complete must reflect transaction redaction flags")
        if receipt.get("state_transition_bound") is not bool(entries):
            errors.append("state_transition_bound must reflect transaction presence")
        complete_without_signature = (
            bool(entries)
            and not missing_operations
            and invalid_transaction_count == 0
            and not duplicate_transaction_ids
            and entry_order_bound
            and source_artifacts_bound
            and redaction_complete
        )
        current_wms_state_digest = receipt.get("current_wms_state_digest")
        if not isinstance(current_wms_state_digest, str) or len(current_wms_state_digest) != 64:
            errors.append("current_wms_state_digest must be a sha256 hex digest")
            current_wms_state_digest = ""
        expected_signature_digest = sha256_text(
            canonical_json(
                _engine_adapter_signature_digest_payload(
                    engine_adapter_signature_profile=WMS_ENGINE_ADAPTER_SIGNATURE_PROFILE,
                    engine_adapter_key_ref=str(receipt.get("engine_adapter_key_ref") or ""),
                    engine_adapter_ref=str(receipt.get("engine_adapter_ref") or ""),
                    engine_session_ref=str(receipt.get("engine_session_ref") or ""),
                    transaction_log_ref=str(receipt.get("transaction_log_ref") or ""),
                    required_operations=required,
                    covered_operations=covered_operations,
                    transaction_set_digest=transaction_set_digest,
                    source_artifact_digest_set_digest=source_artifact_digest_set_digest,
                    engine_state_transition_digest=engine_state_transition_digest,
                    current_wms_state_digest=current_wms_state_digest,
                )
            )
        )
        signature_digest_bound = (
            receipt.get("engine_adapter_signature_digest") == expected_signature_digest
        )
        raw_adapter_signature_excluded = receipt.get("raw_adapter_signature_stored") is False
        engine_adapter_signature_bound = (
            complete_without_signature
            and signature_digest_bound
            and raw_adapter_signature_excluded
        )
        if not signature_digest_bound:
            errors.append("engine_adapter_signature_digest must bind adapter key and log digest set")
        if receipt.get("engine_adapter_signature_bound") is not engine_adapter_signature_bound:
            errors.append("engine_adapter_signature_bound must reflect adapter signature digest binding")
        if not raw_adapter_signature_excluded:
            errors.append("raw_adapter_signature_stored must be false")
        complete = complete_without_signature and engine_adapter_signature_bound
        expected_status = "complete" if complete else "incomplete"
        if receipt.get("engine_binding_status") != expected_status:
            errors.append("engine_binding_status must reflect transaction completeness")
        expected_digest = sha256_text(canonical_json(_engine_transaction_log_digest_payload(receipt)))
        digest_bound = receipt.get("digest") == expected_digest
        if not digest_bound:
            errors.append("digest must match engine transaction log payload")
        return {
            "ok": not errors,
            "errors": errors,
            "engine_binding_complete": complete,
            "entry_order_bound": entry_order_bound,
            "source_artifacts_bound": source_artifacts_bound,
            "redaction_complete": redaction_complete,
            "state_transition_bound": bool(entries),
            "engine_adapter_signature_bound": engine_adapter_signature_bound,
            "signature_digest_bound": signature_digest_bound,
            "raw_adapter_signature_excluded": raw_adapter_signature_excluded,
            "digest_bound": digest_bound,
            "missing_operations": missing_operations,
        }

    def validate_engine_route_binding_receipt(
        self,
        receipt: Mapping[str, Any],
        *,
        engine_transaction_log_receipt: Mapping[str, Any] | None = None,
        authority_route_trace: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")
        if receipt.get("kind") != "wms_engine_route_binding_receipt":
            errors.append("kind must equal wms_engine_route_binding_receipt")
        if receipt.get("schema_version") != WMS_SCHEMA_VERSION:
            errors.append(f"schema_version must be {WMS_SCHEMA_VERSION}")
        if receipt.get("binding_policy_id") != WMS_ENGINE_ROUTE_BINDING_POLICY_ID:
            errors.append("binding_policy_id mismatch")
        if receipt.get("digest_profile") != WMS_ENGINE_ROUTE_BINDING_DIGEST_PROFILE:
            errors.append("digest_profile mismatch")
        if receipt.get("engine_transaction_log_policy_id") != WMS_ENGINE_TRANSACTION_LOG_POLICY_ID:
            errors.append("engine_transaction_log_policy_id mismatch")
        for field_name in (
            "session_id",
            "engine_adapter_ref",
            "engine_session_ref",
            "transaction_log_ref",
            "authority_route_trace_ref",
            "authority_plane_ref",
            "route_target_discovery_ref",
            "council_tier",
            "transport_profile",
            "trace_profile",
            "socket_trace_profile",
            "os_observer_profile",
            "cross_host_binding_profile",
            "route_target_discovery_profile",
        ):
            self._check_non_empty_string(receipt.get(field_name), field_name, errors)
        for field_name in (
            "engine_transaction_log_digest",
            "engine_transaction_digest_set_digest",
            "authority_route_trace_digest",
            "authority_plane_digest",
            "route_target_discovery_digest",
            "route_binding_digest_set_digest",
        ):
            self._check_digest(receipt.get(field_name), field_name, errors)
        if receipt.get("trace_profile") != WMS_ENGINE_ROUTE_TRACE_PROFILE:
            errors.append("trace_profile mismatch")
        if receipt.get("socket_trace_profile") != WMS_ENGINE_ROUTE_SOCKET_PROFILE:
            errors.append("socket_trace_profile mismatch")
        if receipt.get("os_observer_profile") != WMS_ENGINE_ROUTE_OS_OBSERVER_PROFILE:
            errors.append("os_observer_profile mismatch")
        if receipt.get("cross_host_binding_profile") != WMS_ENGINE_ROUTE_CROSS_HOST_PROFILE:
            errors.append("cross_host_binding_profile mismatch")
        if (
            receipt.get("route_target_discovery_profile")
            != WMS_ENGINE_ROUTE_TARGET_DISCOVERY_PROFILE
        ):
            errors.append("route_target_discovery_profile mismatch")

        engine_transaction_ids = receipt.get("engine_transaction_ids")
        if not isinstance(engine_transaction_ids, list) or not engine_transaction_ids:
            errors.append("engine_transaction_ids must be a non-empty list")
            engine_transaction_ids = []
        engine_transaction_entry_digests = receipt.get("engine_transaction_entry_digests")
        if (
            not isinstance(engine_transaction_entry_digests, list)
            or not engine_transaction_entry_digests
        ):
            errors.append("engine_transaction_entry_digests must be a non-empty list")
            engine_transaction_entry_digests = []
        else:
            for entry_digest in engine_transaction_entry_digests:
                self._check_digest(entry_digest, "engine_transaction_entry_digest", errors)
        if receipt.get("transaction_entry_count") != len(engine_transaction_entry_digests):
            errors.append("transaction_entry_count must equal engine transaction digest count")
        if receipt.get("engine_transaction_digest_set_digest") != sha256_text(
            canonical_json(engine_transaction_entry_digests)
        ):
            errors.append("engine_transaction_digest_set_digest must bind entry digests")

        route_binding_refs = receipt.get("route_binding_refs")
        if not isinstance(route_binding_refs, list) or not route_binding_refs:
            errors.append("route_binding_refs must be a non-empty list")
            route_binding_refs = []
        else:
            for route_ref in route_binding_refs:
                self._check_non_empty_string(route_ref, "route_binding_ref", errors)
        if receipt.get("route_binding_digest_set_digest") != sha256_text(
            canonical_json(route_binding_refs)
        ):
            errors.append("route_binding_digest_set_digest must bind route refs")
        for list_field in (
            "remote_host_refs",
            "remote_host_attestation_refs",
            "os_observer_tuple_digests",
            "os_observer_host_binding_digests",
        ):
            value = receipt.get(list_field)
            if not isinstance(value, list) or len(value) != len(route_binding_refs):
                errors.append(f"{list_field} must align with route_binding_refs")
            elif list_field.endswith("digests"):
                for digest in value:
                    self._check_digest(digest, list_field[:-1], errors)
            else:
                for item in value:
                    self._check_non_empty_string(item, list_field[:-1], errors)

        engine_log_bound = receipt.get("engine_log_bound") is True
        if engine_transaction_log_receipt is not None:
            if not isinstance(engine_transaction_log_receipt, Mapping):
                raise ValueError("engine_transaction_log_receipt must be a mapping")
            engine_validation = self.validate_engine_transaction_log_receipt(
                engine_transaction_log_receipt
            )
            expected_engine_entry_digests = list(
                engine_transaction_log_receipt.get("ordered_entry_digests", [])
            )
            expected_engine_transaction_ids = list(
                engine_transaction_log_receipt.get("ordered_transaction_ids", [])
            )
            engine_log_bound = (
                engine_validation["ok"]
                and receipt.get("engine_transaction_log_digest")
                == engine_transaction_log_receipt.get("digest")
                and receipt.get("engine_adapter_ref")
                == engine_transaction_log_receipt.get("engine_adapter_ref")
                and receipt.get("engine_session_ref")
                == engine_transaction_log_receipt.get("engine_session_ref")
                and receipt.get("transaction_log_ref")
                == engine_transaction_log_receipt.get("transaction_log_ref")
                and engine_transaction_entry_digests == expected_engine_entry_digests
                and engine_transaction_ids == expected_engine_transaction_ids
                and receipt.get("transaction_entry_count")
                == engine_transaction_log_receipt.get("transaction_entry_count")
            )
            if not engine_log_bound:
                errors.append("engine log fields must bind the supplied transaction log")
        if receipt.get("engine_log_bound") is not engine_log_bound:
            errors.append("engine_log_bound must reflect engine transaction log binding")

        authority_route_trace_bound = receipt.get("authority_route_trace_bound") is True
        cross_host_route_bound = receipt.get("cross_host_route_bound") is True
        if authority_route_trace is not None:
            if not isinstance(authority_route_trace, Mapping):
                raise ValueError("authority_route_trace must be a mapping")
            trace_validation = self._validate_engine_authority_route_trace(
                authority_route_trace
            )
            authority_route_trace_bound = (
                trace_validation["ok"]
                and receipt.get("authority_route_trace_ref")
                == authority_route_trace.get("trace_ref")
                and receipt.get("authority_route_trace_digest")
                == authority_route_trace.get("digest")
                and receipt.get("authority_plane_ref")
                == authority_route_trace.get("authority_plane_ref")
                and receipt.get("authority_plane_digest")
                == authority_route_trace.get("authority_plane_digest")
                and receipt.get("route_target_discovery_ref")
                == authority_route_trace.get("route_target_discovery_ref")
                and receipt.get("route_target_discovery_digest")
                == authority_route_trace.get("route_target_discovery_digest")
                and receipt.get("council_tier") == authority_route_trace.get("council_tier")
                and receipt.get("transport_profile")
                == authority_route_trace.get("transport_profile")
                and route_binding_refs == trace_validation["route_binding_refs"]
                and receipt.get("remote_host_refs") == trace_validation["remote_host_refs"]
                and receipt.get("remote_host_attestation_refs")
                == trace_validation["remote_host_attestation_refs"]
                and receipt.get("os_observer_tuple_digests")
                == trace_validation["os_observer_tuple_digests"]
                and receipt.get("os_observer_host_binding_digests")
                == trace_validation["os_observer_host_binding_digests"]
            )
            cross_host_route_bound = trace_validation["cross_host_route_bound"]
            if not authority_route_trace_bound:
                errors.append("authority route fields must bind the supplied route trace")
        if receipt.get("authority_route_trace_bound") is not authority_route_trace_bound:
            errors.append("authority_route_trace_bound must reflect route trace binding")
        if receipt.get("cross_host_route_bound") is not cross_host_route_bound:
            errors.append("cross_host_route_bound must reflect route trace cross-host checks")

        route_count = receipt.get("route_count")
        mtls_authenticated_count = receipt.get("mtls_authenticated_count")
        distinct_remote_host_count = receipt.get("distinct_remote_host_count")
        if not isinstance(route_count, int) or route_count < 1:
            errors.append("route_count must be a positive integer")
            route_count = 0
        if not isinstance(mtls_authenticated_count, int) or mtls_authenticated_count < 0:
            errors.append("mtls_authenticated_count must be a non-negative integer")
            mtls_authenticated_count = -1
        if not isinstance(distinct_remote_host_count, int) or distinct_remote_host_count < 1:
            errors.append("distinct_remote_host_count must be a positive integer")
            distinct_remote_host_count = 0
        if route_count != len(route_binding_refs):
            errors.append("route_count must equal route_binding_refs length")
        raw_flags_clear = (
            receipt.get("raw_engine_payload_stored") is False
            and receipt.get("raw_route_payload_stored") is False
        )
        if receipt.get("redaction_complete") is not raw_flags_clear:
            errors.append("redaction_complete must reflect raw payload flags")
        if not raw_flags_clear:
            errors.append("raw payload flags must be false")
        complete = (
            engine_log_bound
            and authority_route_trace_bound
            and cross_host_route_bound
            and raw_flags_clear
            and mtls_authenticated_count == route_count
            and distinct_remote_host_count == route_count
            and route_count >= 2
        )
        expected_status = "complete" if complete else "incomplete"
        if receipt.get("engine_route_binding_status") != expected_status:
            errors.append("engine_route_binding_status must reflect binding completeness")
        expected_digest = sha256_text(
            canonical_json(_engine_route_binding_digest_payload(receipt))
        )
        digest_bound = receipt.get("digest") == expected_digest
        if not digest_bound:
            errors.append("digest must match engine route binding receipt payload")
        return {
            "ok": not errors,
            "errors": errors,
            "engine_log_bound": engine_log_bound,
            "authority_route_trace_bound": authority_route_trace_bound,
            "cross_host_route_bound": cross_host_route_bound,
            "redaction_complete": raw_flags_clear,
            "engine_route_binding_complete": complete,
            "digest_bound": digest_bound,
        }

    def validate_engine_capture_binding_receipt(
        self,
        receipt: Mapping[str, Any],
        *,
        engine_route_binding_receipt: Mapping[str, Any] | None = None,
        packet_capture_export: Mapping[str, Any] | None = None,
        privileged_capture_acquisition: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")
        if receipt.get("kind") != "wms_engine_capture_binding_receipt":
            errors.append("kind must equal wms_engine_capture_binding_receipt")
        if receipt.get("schema_version") != WMS_SCHEMA_VERSION:
            errors.append(f"schema_version must be {WMS_SCHEMA_VERSION}")
        if receipt.get("capture_binding_policy_id") != WMS_ENGINE_CAPTURE_BINDING_POLICY_ID:
            errors.append("capture_binding_policy_id mismatch")
        if receipt.get("digest_profile") != WMS_ENGINE_CAPTURE_BINDING_DIGEST_PROFILE:
            errors.append("digest_profile mismatch")
        if receipt.get("engine_route_binding_policy_id") != WMS_ENGINE_ROUTE_BINDING_POLICY_ID:
            errors.append("engine_route_binding_policy_id mismatch")
        for field_name in (
            "session_id",
            "authority_route_trace_ref",
            "authority_plane_ref",
            "council_tier",
            "transport_profile",
            "packet_capture_ref",
            "packet_capture_profile",
            "packet_capture_artifact_format",
            "packet_capture_export_status",
            "privileged_capture_ref",
            "privileged_capture_profile",
            "privilege_mode",
            "broker_profile",
            "broker_attestation_ref",
            "lease_ref",
            "interface_name",
        ):
            self._check_non_empty_string(receipt.get(field_name), field_name, errors)
        for field_name in (
            "engine_route_binding_digest",
            "engine_transaction_log_digest",
            "authority_route_trace_digest",
            "authority_plane_digest",
            "route_binding_digest_set_digest",
            "packet_capture_digest",
            "packet_capture_artifact_digest",
            "packet_capture_readback_digest",
            "packet_capture_route_binding_set_digest",
            "privileged_capture_digest",
            "capture_filter_digest",
            "capture_command_digest",
            "acquisition_route_binding_set_digest",
        ):
            self._check_digest(receipt.get(field_name), field_name, errors)
        if receipt.get("packet_capture_profile") != WMS_ENGINE_PACKET_CAPTURE_PROFILE:
            errors.append("packet_capture_profile mismatch")
        if receipt.get("packet_capture_artifact_format") != WMS_ENGINE_PACKET_CAPTURE_FORMAT:
            errors.append("packet_capture_artifact_format mismatch")
        if receipt.get("privileged_capture_profile") != WMS_ENGINE_PRIVILEGED_CAPTURE_PROFILE:
            errors.append("privileged_capture_profile mismatch")
        if receipt.get("privilege_mode") != WMS_ENGINE_PRIVILEGED_CAPTURE_MODE:
            errors.append("privilege_mode mismatch")

        route_binding_refs = receipt.get("route_binding_refs")
        if not isinstance(route_binding_refs, list) or not route_binding_refs:
            errors.append("route_binding_refs must be a non-empty list")
            route_binding_refs = []
        else:
            for route_ref in route_binding_refs:
                self._check_non_empty_string(route_ref, "route_binding_ref", errors)
        if receipt.get("route_binding_digest_set_digest") != sha256_text(
            canonical_json(route_binding_refs)
        ):
            errors.append("route_binding_digest_set_digest must bind route refs")
        for list_field in (
            "packet_capture_route_binding_refs",
            "acquisition_route_binding_refs",
        ):
            value = receipt.get(list_field)
            if not isinstance(value, list) or not value:
                errors.append(f"{list_field} must be a non-empty list")
            else:
                for route_ref in value:
                    self._check_non_empty_string(route_ref, list_field[:-1], errors)
        local_ips = receipt.get("local_ips")
        if not isinstance(local_ips, list) or not local_ips:
            errors.append("local_ips must be a non-empty list")
        else:
            for local_ip in local_ips:
                self._check_non_empty_string(local_ip, "local_ip", errors)

        route_validation = {"ok": receipt.get("engine_route_binding_bound") is True}
        if engine_route_binding_receipt is not None:
            route_validation = self.validate_engine_route_binding_receipt(
                engine_route_binding_receipt
            )
            route_bound = (
                route_validation["ok"]
                and receipt.get("engine_route_binding_digest")
                == engine_route_binding_receipt.get("digest")
                and receipt.get("engine_transaction_log_digest")
                == engine_route_binding_receipt.get("engine_transaction_log_digest")
                and receipt.get("authority_route_trace_ref")
                == engine_route_binding_receipt.get("authority_route_trace_ref")
                and receipt.get("authority_route_trace_digest")
                == engine_route_binding_receipt.get("authority_route_trace_digest")
                and receipt.get("authority_plane_ref")
                == engine_route_binding_receipt.get("authority_plane_ref")
                and receipt.get("authority_plane_digest")
                == engine_route_binding_receipt.get("authority_plane_digest")
                and receipt.get("council_tier") == engine_route_binding_receipt.get("council_tier")
                and receipt.get("transport_profile")
                == engine_route_binding_receipt.get("transport_profile")
                and route_binding_refs
                == list(engine_route_binding_receipt.get("route_binding_refs", []))
                and receipt.get("route_count")
                == engine_route_binding_receipt.get("route_count")
            )
            route_validation = {**route_validation, "route_bound": route_bound}
            if not route_bound:
                errors.append("engine capture binding must bind the supplied route binding receipt")
        if receipt.get("engine_route_binding_bound") is not route_validation.get("ok", False):
            errors.append("engine_route_binding_bound must reflect route binding validity")

        capture_validation = {"ok": receipt.get("packet_capture_bound") is True}
        if packet_capture_export is not None:
            capture_validation = self._validate_engine_packet_capture_export(
                packet_capture_export,
                engine_route_binding_receipt=engine_route_binding_receipt,
            )
            capture_bound = (
                capture_validation["ok"]
                and receipt.get("packet_capture_ref") == packet_capture_export.get("capture_ref")
                and receipt.get("packet_capture_digest") == packet_capture_export.get("digest")
                and receipt.get("packet_capture_artifact_digest")
                == packet_capture_export.get("artifact_digest")
                and receipt.get("packet_capture_readback_digest")
                == packet_capture_export.get("readback_digest")
                and receipt.get("packet_count") == packet_capture_export.get("packet_count")
                and receipt.get("packet_capture_export_status")
                == packet_capture_export.get("export_status")
            )
            capture_validation = {**capture_validation, "capture_bound": capture_bound}
            if not capture_bound:
                errors.append("engine capture binding must bind the supplied packet capture export")
        if receipt.get("packet_capture_bound") is not capture_validation.get("ok", False):
            errors.append("packet_capture_bound must reflect packet capture export validity")

        acquisition_validation = {"ok": receipt.get("privileged_capture_bound") is True}
        if privileged_capture_acquisition is not None:
            acquisition_validation = self._validate_engine_privileged_capture_acquisition(
                privileged_capture_acquisition,
                engine_route_binding_receipt=engine_route_binding_receipt,
                packet_capture_export=packet_capture_export,
            )
            acquisition_bound = (
                acquisition_validation["ok"]
                and receipt.get("privileged_capture_ref")
                == privileged_capture_acquisition.get("acquisition_ref")
                and receipt.get("privileged_capture_digest")
                == privileged_capture_acquisition.get("digest")
                and receipt.get("broker_attestation_ref")
                == privileged_capture_acquisition.get("broker_attestation_ref")
                and receipt.get("lease_ref") == privileged_capture_acquisition.get("lease_ref")
                and receipt.get("capture_filter_digest")
                == privileged_capture_acquisition.get("filter_digest")
                and receipt.get("capture_command_digest")
                == sha256_text(
                    canonical_json(
                        privileged_capture_acquisition.get("capture_command", [])
                    )
                )
            )
            acquisition_validation = {
                **acquisition_validation,
                "acquisition_bound": acquisition_bound,
            }
            if not acquisition_bound:
                errors.append("engine capture binding must bind the supplied privileged capture acquisition")
        if receipt.get("privileged_capture_bound") is not acquisition_validation.get("ok", False):
            errors.append("privileged_capture_bound must reflect capture acquisition validity")

        route_binding_set_bound = (
            receipt.get("route_binding_set_bound") is True
            and receipt.get("packet_capture_route_binding_set_digest")
            == sha256_text(canonical_json(receipt.get("packet_capture_route_binding_refs", [])))
            and receipt.get("acquisition_route_binding_set_digest")
            == sha256_text(
                canonical_json(sorted(receipt.get("acquisition_route_binding_refs", [])))
            )
            and receipt.get("route_binding_digest_set_digest")
            == receipt.get("packet_capture_route_binding_set_digest")
            and sorted(route_binding_refs)
            == sorted(receipt.get("packet_capture_route_binding_refs", []))
            == sorted(receipt.get("acquisition_route_binding_refs", []))
        )
        if receipt.get("route_binding_set_bound") is not route_binding_set_bound:
            errors.append("route_binding_set_bound must reflect capture/acquisition route refs")
        raw_flags_clear = (
            receipt.get("raw_engine_payload_stored") is False
            and receipt.get("raw_route_payload_stored") is False
            and receipt.get("raw_packet_body_stored") is False
        )
        if not raw_flags_clear:
            errors.append("raw payload flags must be false")
        complete = (
            route_validation.get("ok", False)
            and capture_validation.get("ok", False)
            and acquisition_validation.get("ok", False)
            and route_binding_set_bound
            and raw_flags_clear
        )
        expected_status = "complete" if complete else "incomplete"
        if receipt.get("engine_capture_binding_status") != expected_status:
            errors.append("engine_capture_binding_status must reflect binding completeness")
        expected_digest = sha256_text(
            canonical_json(_engine_capture_binding_digest_payload(receipt))
        )
        digest_bound = receipt.get("digest") == expected_digest
        if not digest_bound:
            errors.append("digest must match engine capture binding receipt payload")
        return {
            "ok": not errors,
            "errors": errors,
            "engine_route_binding_bound": route_validation.get("ok", False),
            "packet_capture_bound": capture_validation.get("ok", False),
            "privileged_capture_bound": acquisition_validation.get("ok", False),
            "route_binding_set_bound": route_binding_set_bound,
            "raw_payloads_redacted": raw_flags_clear,
            "engine_capture_binding_complete": complete,
            "digest_bound": digest_bound,
        }

    def _validate_engine_packet_capture_export(
        self,
        packet_capture_export: Mapping[str, Any],
        *,
        engine_route_binding_receipt: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(packet_capture_export, Mapping):
            raise ValueError("packet_capture_export must be a mapping")
        if packet_capture_export.get("kind") != "distributed_transport_packet_capture_export":
            errors.append("packet capture export kind mismatch")
        if packet_capture_export.get("schema_version") != "1.0.0":
            errors.append("packet capture export schema_version mismatch")
        for field_name in (
            "capture_ref",
            "trace_ref",
            "authority_plane_ref",
            "envelope_ref",
            "council_tier",
            "transport_profile",
            "capture_profile",
            "artifact_format",
            "readback_profile",
            "os_native_readback_profile",
            "export_status",
        ):
            self._check_non_empty_string(packet_capture_export.get(field_name), field_name, errors)
        for field_name in (
            "trace_digest",
            "authority_plane_digest",
            "envelope_digest",
            "artifact_digest",
            "readback_digest",
            "digest",
        ):
            self._check_digest(packet_capture_export.get(field_name), field_name, errors)
        if packet_capture_export.get("capture_profile") != WMS_ENGINE_PACKET_CAPTURE_PROFILE:
            errors.append("packet capture profile mismatch")
        if packet_capture_export.get("artifact_format") != WMS_ENGINE_PACKET_CAPTURE_FORMAT:
            errors.append("packet capture artifact format mismatch")
        if packet_capture_export.get("export_status") != "verified":
            errors.append("packet capture export_status must be verified")
        route_exports = packet_capture_export.get("route_exports")
        if not isinstance(route_exports, list) or not route_exports:
            errors.append("route_exports must be a non-empty list")
            route_exports = []
        route_binding_refs: List[str] = []
        route_export_errors = 0
        for route_export in route_exports:
            if not isinstance(route_export, Mapping):
                errors.append("route_exports must contain objects")
                route_export_errors += 1
                continue
            for field_name in (
                "route_binding_ref",
                "local_ip",
                "remote_ip",
                "outbound_tuple_digest",
                "inbound_tuple_digest",
                "outbound_payload_digest",
                "inbound_payload_digest",
            ):
                value = route_export.get(field_name)
                if field_name.endswith("digest"):
                    self._check_digest(value, field_name, errors)
                else:
                    self._check_non_empty_string(value, field_name, errors)
            route_binding_ref = route_export.get("route_binding_ref")
            if isinstance(route_binding_ref, str):
                route_binding_refs.append(route_binding_ref)
            if route_export.get("readback_verified") is not True:
                errors.append("packet capture route export must be readback_verified")
                route_export_errors += 1
            if route_export.get("readback_packet_count") != 2:
                errors.append("packet capture route export must have two readback packets")
                route_export_errors += 1
            if (
                packet_capture_export.get("os_native_readback_available") is True
                and route_export.get("os_native_readback_verified") is not True
            ):
                errors.append("os native readback must verify each route export when available")
                route_export_errors += 1
        route_count = packet_capture_export.get("route_count")
        packet_count = packet_capture_export.get("packet_count")
        if not isinstance(route_count, int) or route_count != len(route_exports):
            errors.append("packet capture route_count must equal route_exports length")
            route_count = len(route_exports)
        if not isinstance(packet_count, int) or packet_count != route_count * 2:
            errors.append("packet capture packet_count must equal two packets per route")
        if (
            packet_capture_export.get("os_native_readback_available") is True
            and packet_capture_export.get("os_native_readback_ok") is not True
        ):
            errors.append("os native readback must be ok when available")
        if engine_route_binding_receipt is not None:
            expected_route_refs = list(engine_route_binding_receipt.get("route_binding_refs", []))
            if packet_capture_export.get("trace_ref") != engine_route_binding_receipt.get(
                "authority_route_trace_ref"
            ):
                errors.append("packet capture trace_ref must match engine route binding")
            if packet_capture_export.get("trace_digest") != engine_route_binding_receipt.get(
                "authority_route_trace_digest"
            ):
                errors.append("packet capture trace_digest must match engine route binding")
            if route_binding_refs != expected_route_refs:
                errors.append("packet capture route refs must match engine route binding")
            if route_count != engine_route_binding_receipt.get("route_count"):
                errors.append("packet capture route_count must match engine route binding")
        expected_digest = sha256_text(
            canonical_json(_transport_receipt_digest_payload(packet_capture_export))
        )
        digest_bound = packet_capture_export.get("digest") == expected_digest
        if not digest_bound:
            errors.append("packet capture digest must bind payload")
        return {
            "ok": not errors,
            "errors": errors,
            "digest_bound": digest_bound,
            "route_binding_refs": route_binding_refs,
            "packet_capture_complete": route_export_errors == 0 and not errors,
        }

    def _validate_engine_privileged_capture_acquisition(
        self,
        privileged_capture_acquisition: Mapping[str, Any],
        *,
        engine_route_binding_receipt: Mapping[str, Any] | None = None,
        packet_capture_export: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(privileged_capture_acquisition, Mapping):
            raise ValueError("privileged_capture_acquisition must be a mapping")
        if (
            privileged_capture_acquisition.get("kind")
            != "distributed_transport_privileged_capture_acquisition"
        ):
            errors.append("privileged capture acquisition kind mismatch")
        if privileged_capture_acquisition.get("schema_version") != "1.0.0":
            errors.append("privileged capture acquisition schema_version mismatch")
        for field_name in (
            "acquisition_ref",
            "trace_ref",
            "capture_ref",
            "authority_plane_ref",
            "envelope_ref",
            "council_tier",
            "transport_profile",
            "acquisition_profile",
            "broker_profile",
            "privilege_mode",
            "lease_ref",
            "broker_attestation_ref",
            "interface_name",
            "capture_filter",
            "grant_status",
        ):
            self._check_non_empty_string(
                privileged_capture_acquisition.get(field_name),
                field_name,
                errors,
            )
        for field_name in (
            "trace_digest",
            "capture_digest",
            "authority_plane_digest",
            "envelope_digest",
            "filter_digest",
            "digest",
        ):
            self._check_digest(privileged_capture_acquisition.get(field_name), field_name, errors)
        if (
            privileged_capture_acquisition.get("acquisition_profile")
            != WMS_ENGINE_PRIVILEGED_CAPTURE_PROFILE
        ):
            errors.append("privileged capture acquisition profile mismatch")
        if privileged_capture_acquisition.get("privilege_mode") != WMS_ENGINE_PRIVILEGED_CAPTURE_MODE:
            errors.append("privileged capture mode mismatch")
        if privileged_capture_acquisition.get("grant_status") != "granted":
            errors.append("privileged capture grant_status must be granted")
        local_ips = privileged_capture_acquisition.get("local_ips")
        if not isinstance(local_ips, list) or not local_ips:
            errors.append("privileged capture local_ips must be non-empty")
        route_binding_refs = privileged_capture_acquisition.get("route_binding_refs")
        if not isinstance(route_binding_refs, list) or not route_binding_refs:
            errors.append("privileged capture route_binding_refs must be non-empty")
            route_binding_refs = []
        else:
            for route_ref in route_binding_refs:
                self._check_non_empty_string(route_ref, "route_binding_ref", errors)
        capture_command = privileged_capture_acquisition.get("capture_command")
        if not isinstance(capture_command, list) or not capture_command:
            errors.append("capture_command must be a non-empty list")
            capture_command = []
        else:
            for command_part in capture_command:
                self._check_non_empty_string(command_part, "capture_command", errors)
            if not str(capture_command[0]).endswith("tcpdump"):
                errors.append("capture_command must start with tcpdump")
            if privileged_capture_acquisition.get("interface_name") not in capture_command:
                errors.append("capture_command must bind interface_name")
            if privileged_capture_acquisition.get("capture_filter") not in capture_command:
                errors.append("capture_command must bind capture_filter")
        expected_filter_digest = sha256_text(
            str(privileged_capture_acquisition.get("capture_filter", ""))
        )
        if privileged_capture_acquisition.get("filter_digest") != expected_filter_digest:
            errors.append("filter_digest must bind capture_filter")
        if engine_route_binding_receipt is not None:
            if privileged_capture_acquisition.get("trace_ref") != engine_route_binding_receipt.get(
                "authority_route_trace_ref"
            ):
                errors.append("privileged capture trace_ref must match route binding")
            if privileged_capture_acquisition.get("trace_digest") != engine_route_binding_receipt.get(
                "authority_route_trace_digest"
            ):
                errors.append("privileged capture trace_digest must match route binding")
            if sorted(route_binding_refs) != sorted(
                engine_route_binding_receipt.get("route_binding_refs", [])
            ):
                errors.append("privileged capture route refs must match route binding")
        if packet_capture_export is not None:
            if privileged_capture_acquisition.get("capture_ref") != packet_capture_export.get(
                "capture_ref"
            ):
                errors.append("privileged capture capture_ref must match packet capture")
            if privileged_capture_acquisition.get("capture_digest") != packet_capture_export.get(
                "digest"
            ):
                errors.append("privileged capture capture_digest must match packet capture")
        expected_digest = sha256_text(
            canonical_json(_transport_receipt_digest_payload(privileged_capture_acquisition))
        )
        digest_bound = privileged_capture_acquisition.get("digest") == expected_digest
        if not digest_bound:
            errors.append("privileged capture digest must bind payload")
        return {
            "ok": not errors,
            "errors": errors,
            "digest_bound": digest_bound,
        }

    def _validate_engine_authority_route_trace(
        self,
        trace: Mapping[str, Any],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(trace, Mapping):
            raise ValueError("authority_route_trace must be a mapping")
        if trace.get("kind") != "distributed_transport_authority_route_trace":
            errors.append("route trace kind mismatch")
        if trace.get("schema_version") != "1.0.0":
            errors.append("route trace schema_version mismatch")
        for field_name in (
            "trace_ref",
            "authority_plane_ref",
            "route_target_discovery_ref",
            "envelope_ref",
            "council_tier",
            "transport_profile",
            "trace_profile",
            "socket_trace_profile",
            "os_observer_profile",
            "cross_host_binding_profile",
            "route_target_discovery_profile",
            "authority_cluster_ref",
            "trace_status",
        ):
            self._check_non_empty_string(trace.get(field_name), field_name, errors)
        for field_name in (
            "digest",
            "authority_plane_digest",
            "route_target_discovery_digest",
            "envelope_digest",
        ):
            self._check_digest(trace.get(field_name), field_name, errors)
        expected_trace_digest = sha256_text(canonical_json(_route_trace_digest_payload(trace)))
        digest_bound = trace.get("digest") == expected_trace_digest
        if not digest_bound:
            errors.append("route trace digest must bind trace payload")
        if trace.get("trace_profile") != WMS_ENGINE_ROUTE_TRACE_PROFILE:
            errors.append("route trace profile mismatch")
        if trace.get("socket_trace_profile") != WMS_ENGINE_ROUTE_SOCKET_PROFILE:
            errors.append("route socket trace profile mismatch")
        if trace.get("os_observer_profile") != WMS_ENGINE_ROUTE_OS_OBSERVER_PROFILE:
            errors.append("route os observer profile mismatch")
        if trace.get("cross_host_binding_profile") != WMS_ENGINE_ROUTE_CROSS_HOST_PROFILE:
            errors.append("route cross-host profile mismatch")
        if (
            trace.get("route_target_discovery_profile")
            != WMS_ENGINE_ROUTE_TARGET_DISCOVERY_PROFILE
        ):
            errors.append("route target discovery profile mismatch")

        route_bindings = trace.get("route_bindings")
        if not isinstance(route_bindings, list) or not route_bindings:
            errors.append("route_bindings must be a non-empty list")
            route_bindings = []
        route_binding_refs: List[str] = []
        remote_host_refs: List[str] = []
        remote_host_attestation_refs: List[str] = []
        os_observer_tuple_digests: List[str] = []
        os_observer_host_binding_digests: List[str] = []
        route_binding_errors = 0
        for binding in route_bindings:
            if not isinstance(binding, Mapping):
                errors.append("route_bindings must contain objects")
                route_binding_errors += 1
                continue
            for field_name in (
                "route_binding_ref",
                "remote_host_ref",
                "remote_host_attestation_ref",
                "authority_cluster_ref",
                "mtls_status",
            ):
                self._check_non_empty_string(binding.get(field_name), field_name, errors)
            if binding.get("mtls_status") != "authenticated":
                errors.append("route binding mtls_status must be authenticated")
                route_binding_errors += 1
            if binding.get("response_digest_bound") is not True:
                errors.append("route binding response_digest_bound must be true")
                route_binding_errors += 1
            route_binding_refs.append(str(binding.get("route_binding_ref")))
            remote_host_refs.append(str(binding.get("remote_host_ref")))
            remote_host_attestation_refs.append(
                str(binding.get("remote_host_attestation_ref"))
            )
            os_observer_receipt = binding.get("os_observer_receipt")
            if not isinstance(os_observer_receipt, Mapping):
                errors.append("route binding os_observer_receipt must be an object")
                route_binding_errors += 1
            else:
                if os_observer_receipt.get("observer_profile") != WMS_ENGINE_ROUTE_OS_OBSERVER_PROFILE:
                    errors.append("os observer profile mismatch")
                    route_binding_errors += 1
                if os_observer_receipt.get("receipt_status") != "observed":
                    errors.append("os observer receipt_status must be observed")
                    route_binding_errors += 1
                for field_name in ("tuple_digest", "host_binding_digest"):
                    self._check_digest(os_observer_receipt.get(field_name), field_name, errors)
                if isinstance(os_observer_receipt.get("tuple_digest"), str):
                    os_observer_tuple_digests.append(str(os_observer_receipt["tuple_digest"]))
                if isinstance(os_observer_receipt.get("host_binding_digest"), str):
                    os_observer_host_binding_digests.append(
                        str(os_observer_receipt["host_binding_digest"])
                    )
            socket_trace = binding.get("socket_trace")
            if not isinstance(socket_trace, Mapping):
                errors.append("route binding socket_trace must be an object")
                route_binding_errors += 1
            else:
                if socket_trace.get("transport_profile") != WMS_ENGINE_ROUTE_SOCKET_PROFILE:
                    errors.append("socket trace profile mismatch")
                    route_binding_errors += 1
                if socket_trace.get("non_loopback") is not True:
                    errors.append("socket trace non_loopback must be true")
                    route_binding_errors += 1
                if socket_trace.get("http_status") != 200:
                    errors.append("socket trace http_status must be 200")
                    route_binding_errors += 1
                self._check_digest(
                    socket_trace.get("response_digest"),
                    "socket_trace.response_digest",
                    errors,
                )

        route_count = trace.get("route_count")
        mtls_authenticated_count = trace.get("mtls_authenticated_count")
        distinct_remote_host_count = trace.get("distinct_remote_host_count")
        if not isinstance(route_count, int) or route_count != len(route_bindings):
            errors.append("route_count must equal route_bindings length")
            route_count = len(route_bindings)
        if not isinstance(mtls_authenticated_count, int):
            errors.append("mtls_authenticated_count must be an integer")
            mtls_authenticated_count = -1
        if not isinstance(distinct_remote_host_count, int):
            errors.append("distinct_remote_host_count must be an integer")
            distinct_remote_host_count = -1
        computed_distinct_remote_host_count = len(set(remote_host_refs))
        if distinct_remote_host_count != computed_distinct_remote_host_count:
            errors.append("distinct_remote_host_count must reflect remote_host_refs")
        cross_host_route_bound = (
            trace.get("trace_status") == "authenticated"
            and trace.get("non_loopback_verified") is True
            and trace.get("authority_plane_bound") is True
            and trace.get("response_digest_bound") is True
            and trace.get("socket_trace_complete") is True
            and trace.get("os_observer_complete") is True
            and trace.get("route_target_discovery_bound") is True
            and trace.get("cross_host_verified") is True
            and route_count >= 2
            and mtls_authenticated_count == route_count
            and distinct_remote_host_count == route_count
            and route_binding_errors == 0
        )
        if not cross_host_route_bound:
            errors.append("route trace must be authenticated cross-host route evidence")
        return {
            "ok": not errors,
            "errors": errors,
            "digest_bound": digest_bound,
            "cross_host_route_bound": cross_host_route_bound,
            "route_binding_refs": route_binding_refs,
            "remote_host_refs": remote_host_refs,
            "remote_host_attestation_refs": remote_host_attestation_refs,
            "os_observer_tuple_digests": os_observer_tuple_digests,
            "os_observer_host_binding_digests": os_observer_host_binding_digests,
        }

    @staticmethod
    def _normalize_engine_required_operations(
        required_operations: Sequence[str] | None,
    ) -> List[str]:
        if required_operations is None:
            return [
                "time_rate_escape_evidence",
                "approval_collection_bound",
                "approval_fanout_bound",
                "physics_rules_apply",
                "physics_rules_revert",
            ]
        required = _dedupe_preserve_order([str(item) for item in required_operations])
        for operation in required:
            if operation not in WMS_ENGINE_TRANSACTION_OPERATIONS:
                raise ValueError("required_operations contains an unsupported operation")
        return required

    def _validate_engine_transaction_entry(
        self,
        entry: Mapping[str, Any],
        *,
        expected_index: int,
        engine_session_ref: str,
        source_artifact_digests: Mapping[str, str],
    ) -> None:
        if entry.get("kind") != "wms_engine_transaction_entry":
            raise ValueError("kind must equal wms_engine_transaction_entry")
        if entry.get("schema_version") != WMS_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {WMS_SCHEMA_VERSION}")
        if entry.get("entry_digest_profile") != WMS_ENGINE_TRANSACTION_ENTRY_DIGEST_PROFILE:
            raise ValueError("entry_digest_profile mismatch")
        if entry.get("transaction_index") != expected_index:
            raise ValueError("transaction_index must follow transaction order")
        for field_name in (
            "transaction_id",
            "operation",
            "source_artifact_kind",
            "source_artifact_ref",
            "engine_session_ref",
            "transaction_status",
            "committed_at",
        ):
            self._normalize_non_empty_string(str(entry.get(field_name) or ""), field_name)
        operation = str(entry["operation"])
        if operation not in WMS_ENGINE_TRANSACTION_OPERATIONS:
            raise ValueError("operation is not allowed")
        if entry.get("engine_session_ref") != engine_session_ref:
            raise ValueError("engine_session_ref must match transaction log")
        if entry.get("transaction_status") != "committed":
            raise ValueError("transaction_status must be committed")
        if entry.get("payload_redacted") is not True:
            raise ValueError("payload_redacted must be true")
        if entry.get("raw_payload_stored") is not False:
            raise ValueError("raw_payload_stored must be false")
        participants = entry.get("participant_ids")
        if not isinstance(participants, list) or not participants:
            raise ValueError("participant_ids must be a non-empty list")
        for participant in participants:
            self._normalize_non_empty_string(str(participant), "participant_id")
        for field_name in (
            "source_artifact_digest",
            "engine_state_before_digest",
            "engine_state_after_digest",
            "entry_digest",
        ):
            self._normalize_digest(entry.get(field_name), field_name)
        if operation in source_artifact_digests:
            expected_digest = source_artifact_digests[operation]
            if entry.get("source_artifact_digest") != expected_digest:
                raise ValueError("source_artifact_digest must match expected source artifact")
        expected_entry_digest = sha256_text(
            canonical_json(_engine_transaction_entry_digest_payload(entry))
        )
        if entry.get("entry_digest") != expected_entry_digest:
            raise ValueError("entry_digest must bind transaction entry payload")

    def validate_state(self, state: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        self._check_non_empty_string(state.get("state_id"), "state_id", errors)
        participants = state.get("participants")
        if not isinstance(participants, list) or not participants:
            errors.append("participants must be a non-empty list")
        else:
            for participant in participants:
                if not isinstance(participant, str) or not participant.strip():
                    errors.append("participants must contain non-empty strings")
                    break

        objects = state.get("objects")
        if not isinstance(objects, list) or not objects:
            errors.append("objects must be a non-empty list")
        else:
            for obj in objects:
                if not isinstance(obj, str) or not obj.strip():
                    errors.append("objects must contain non-empty strings")
                    break

        if state.get("schema_version") != WMS_SCHEMA_VERSION:
            errors.append(f"schema_version must be {WMS_SCHEMA_VERSION}")

        authority = state.get("authority")
        if authority not in WMS_ALLOWED_AUTHORITIES:
            errors.append(f"authority must be one of {sorted(WMS_ALLOWED_AUTHORITIES)}")

        time_rate = state.get("time_rate")
        if not isinstance(time_rate, (int, float)) or float(time_rate) <= 0:
            errors.append("time_rate must be > 0")

        return {
            "ok": not errors,
            "errors": errors,
            "time_rate_locked": float(time_rate or 0) == WMS_DEFAULT_TIME_RATE,
            "authority_valid": authority in WMS_ALLOWED_AUTHORITIES,
            "participants_count": len(participants) if isinstance(participants, list) else 0,
        }

    def validate_physics_rules_change(self, receipt: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        if receipt.get("kind") != "wms_physics_rules_change_receipt":
            errors.append("kind must equal wms_physics_rules_change_receipt")
        if receipt.get("schema_version") != WMS_SCHEMA_VERSION:
            errors.append(f"schema_version must be {WMS_SCHEMA_VERSION}")
        operation = receipt.get("operation")
        if operation not in WMS_PHYSICS_CHANGE_OPERATIONS:
            errors.append(f"operation must be one of {sorted(WMS_PHYSICS_CHANGE_OPERATIONS)}")
        decision = receipt.get("decision")
        if decision not in WMS_PHYSICS_CHANGE_DECISIONS:
            errors.append(f"decision must be one of {sorted(WMS_PHYSICS_CHANGE_DECISIONS)}")
        for field_name in (
            "change_id",
            "session_id",
            "requested_by",
            "recorded_at",
            "rationale",
            "previous_physics_rules_ref",
            "proposed_physics_rules_ref",
            "resulting_physics_rules_ref",
            "rollback_physics_rules_ref",
            "rollback_token_ref",
            "resulting_state_id",
            "audit_event_ref",
        ):
            self._check_non_empty_string(receipt.get(field_name), field_name, errors)
        if receipt.get("approval_policy_id") != WMS_PHYSICS_CHANGE_POLICY_ID:
            errors.append("approval_policy_id mismatch")
        required_approvals = receipt.get("required_approvals")
        participant_approvals = receipt.get("participant_approvals")
        required_set: set[str] = set()
        approval_set: set[str] = set()
        if not isinstance(required_approvals, list) or not required_approvals:
            errors.append("required_approvals must be a non-empty list")
        else:
            required_set = {
                value for value in required_approvals if isinstance(value, str) and value.strip()
            }
            if len(required_set) != len(required_approvals):
                errors.append("required_approvals must contain unique non-empty strings")
        if not isinstance(participant_approvals, list) or not participant_approvals:
            errors.append("participant_approvals must be a non-empty list")
        else:
            approval_set = {
                value for value in participant_approvals if isinstance(value, str) and value.strip()
            }
            if len(approval_set) != len(participant_approvals):
                errors.append("participant_approvals must contain unique non-empty strings")
        approval_quorum_met = bool(required_set) and required_set.issubset(approval_set)
        if receipt.get("approval_quorum_met") is not approval_quorum_met:
            errors.append("approval_quorum_met must reflect required_approvals subset")
        approval_subject_digest = receipt.get("approval_subject_digest")
        if not isinstance(approval_subject_digest, str) or len(approval_subject_digest) != 64:
            errors.append("approval_subject_digest must be a sha256 hex digest")
            approval_subject_digest = None
        if receipt.get("approval_transport_policy_id") != WMS_APPROVAL_TRANSPORT_POLICY_ID:
            errors.append("approval_transport_policy_id mismatch")
        approval_transport_receipts = receipt.get("approval_transport_receipts")
        if not isinstance(approval_transport_receipts, list) or not approval_transport_receipts:
            errors.append("approval_transport_receipts must be a non-empty list")
            approval_transport_receipts = []
        approval_transport_quorum_met = self._approval_transport_quorum_met(
            approval_transport_receipts,
            required_approvals=required_approvals if isinstance(required_approvals, list) else [],
            approval_subject_digest=approval_subject_digest,
        )
        if receipt.get("approval_transport_quorum_met") is not approval_transport_quorum_met:
            errors.append("approval_transport_quorum_met must reflect transport-bound approvals")
        expected_approval_transport_digest = sha256_text(canonical_json(approval_transport_receipts))
        approval_transport_digest_bound = (
            receipt.get("approval_transport_digest") == expected_approval_transport_digest
        )
        if not approval_transport_digest_bound:
            errors.append("approval_transport_digest must match approval_transport_receipts")
        if receipt.get("approval_collection_policy_id") != WMS_APPROVAL_COLLECTION_POLICY_ID:
            errors.append("approval_collection_policy_id mismatch")
        approval_collection_receipt = receipt.get("approval_collection_receipt")
        approval_collection_validation = {"ok": False}
        if not isinstance(approval_collection_receipt, Mapping):
            errors.append("approval_collection_receipt must be an object")
        else:
            approval_collection_validation = self.validate_approval_collection_receipt(
                approval_collection_receipt,
                required_participants=required_approvals if isinstance(required_approvals, list) else [],
                approval_subject_digest=approval_subject_digest,
                approval_transport_receipts=approval_transport_receipts,
            )
            errors.extend(
                f"approval_collection_receipt.{error}"
                for error in approval_collection_validation["errors"]
            )
            if receipt.get("approval_collection_digest") != approval_collection_receipt.get("digest"):
                errors.append("approval_collection_digest must match approval_collection_receipt.digest")
        approval_collection_complete = approval_collection_validation["ok"]
        if receipt.get("approval_collection_complete") is not approval_collection_complete:
            errors.append("approval_collection_complete must reflect approval collection validation")
        fanout_receipt = receipt.get("approval_fanout_receipt")
        approval_fanout_complete = False
        approval_fanout_digest_bound = False
        if fanout_receipt is not None:
            if receipt.get("approval_fanout_policy_id") != WMS_APPROVAL_FANOUT_POLICY_ID:
                errors.append("approval_fanout_policy_id mismatch")
            if not isinstance(fanout_receipt, Mapping):
                errors.append("approval_fanout_receipt must be an object when present")
            else:
                fanout_validation = self.validate_distributed_approval_fanout_receipt(
                    fanout_receipt,
                    required_participants=required_approvals
                    if isinstance(required_approvals, list)
                    else [],
                    approval_subject_digest=approval_subject_digest,
                    approval_collection_digest=receipt.get("approval_collection_digest"),
                )
                errors.extend(
                    f"approval_fanout_receipt.{error}"
                    for error in fanout_validation["errors"]
                )
                approval_fanout_complete = fanout_validation["ok"]
                approval_fanout_digest_bound = (
                    receipt.get("approval_fanout_digest") == fanout_receipt.get("digest")
                )
                if not approval_fanout_digest_bound:
                    errors.append("approval_fanout_digest must match approval_fanout_receipt.digest")
            if receipt.get("approval_fanout_complete") is not approval_fanout_complete:
                errors.append("approval_fanout_complete must reflect fanout validation")
        if receipt.get("guardian_attested") is not True:
            errors.append("guardian_attested must be true")
        if receipt.get("reversible") is not True:
            errors.append("reversible must be true")
        revert_bound = False
        if operation == "apply":
            if decision == "applied":
                revert_bound = (
                    receipt.get("rollback_physics_rules_ref")
                    == receipt.get("previous_physics_rules_ref")
                    and receipt.get("resulting_physics_rules_ref")
                    == receipt.get("proposed_physics_rules_ref")
                    and receipt.get("revert_of_change_id") == ""
                    and receipt.get("reverted") is False
                )
                if not revert_bound:
                    errors.append("applied physics change must bind rollback to previous rules")
            elif decision != "rejected":
                errors.append("apply operation decision must be applied or rejected")
        if operation == "revert":
            revert_bound = (
                decision == "reverted"
                and receipt.get("rollback_physics_rules_ref")
                == receipt.get("resulting_physics_rules_ref")
                and isinstance(receipt.get("revert_of_change_id"), str)
                and bool(receipt.get("revert_of_change_id"))
                and receipt.get("reverted") is True
            )
            if not revert_bound:
                errors.append("revert operation must restore rollback rules and bind revert_of_change_id")
        expected_digest = sha256_text(canonical_json(_physics_rules_change_digest_payload(receipt)))
        digest_bound = receipt.get("digest") == expected_digest
        if not digest_bound:
            errors.append("digest must match physics rules change receipt payload")
        return {
            "ok": not errors,
            "errors": errors,
            "approval_quorum_met": approval_quorum_met,
            "approval_transport_quorum_met": approval_transport_quorum_met,
            "approval_transport_digest_bound": approval_transport_digest_bound,
            "approval_collection_complete": approval_collection_complete,
            "approval_collection_digest_bound": (
                isinstance(approval_collection_receipt, Mapping)
                and receipt.get("approval_collection_digest") == approval_collection_receipt.get("digest")
            ),
            "approval_fanout_complete": approval_fanout_complete,
            "approval_fanout_digest_bound": approval_fanout_digest_bound,
            "guardian_attested": receipt.get("guardian_attested") is True,
            "revert_bound": revert_bound,
            "digest_bound": digest_bound,
        }

    def _classify_diff(
        self,
        session: Mapping[str, Any],
        *,
        proposer_id: str,
        affected_object_ratio: float,
        attested: bool,
        requested_time_rate: float,
    ) -> str:
        participants = set(session["current_state"]["participants"])
        if not attested or proposer_id not in participants:
            return "malicious_inject"
        if requested_time_rate != session["current_state"]["time_rate"]:
            return "major_diff"
        if affected_object_ratio < WMS_MINOR_DIFF_THRESHOLD:
            return "minor_diff"
        return "major_diff"

    def _build_violation(
        self,
        session: Mapping[str, Any],
        *,
        classification: str,
        proposer_id: str,
        affected_object_ratio: float,
        attested: bool,
        requested_time_rate: float,
        audit_event_ref: str,
    ) -> Dict[str, Any]:
        return {
            "session_id": session["session_id"],
            "observed_at": utc_now_iso(),
            "violation_detected": True,
            "classification": classification,
            "proposer_id": proposer_id,
            "attested": attested,
            "affected_object_ratio": affected_object_ratio,
            "requested_time_rate": requested_time_rate,
            "guardian_action": "isolate-session",
            "requires_council_review": False,
            "audit_event_ref": audit_event_ref,
        }

    def _time_rate_deviation_fields(
        self,
        session: Mapping[str, Any],
        *,
        proposer_id: str,
        requested_time_rate: float,
        classification: str,
        time_rate_attestation_receipts: Sequence[Mapping[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        baseline_time_rate = float(session["current_state"]["time_rate"])
        delta = round(abs(requested_time_rate - baseline_time_rate), 3)
        deviation_detected = delta > 0
        attestation_subject = self.build_time_rate_attestation_subject(
            session["session_id"],
            proposer_id=proposer_id,
            requested_time_rate=requested_time_rate,
        )
        required_participants = list(session["current_state"]["participants"])
        receipts = [
            deepcopy(receipt)
            for receipt in (time_rate_attestation_receipts or [])
            if isinstance(receipt, Mapping)
        ]
        receipts_by_participant: Dict[str, Mapping[str, Any]] = {}
        duplicate_participants: List[str] = []
        invalid_receipt_count = 0
        for receipt in receipts:
            participant_id = receipt.get("participant_id")
            if (
                not isinstance(participant_id, str)
                or participant_id not in required_participants
            ):
                invalid_receipt_count += 1
                continue
            if participant_id in receipts_by_participant:
                duplicate_participants.append(participant_id)
                continue
            validation = self.validate_time_rate_attestation_receipt(
                receipt,
                time_rate_attestation_subject_digest=attestation_subject["digest"],
            )
            if not validation["ok"]:
                invalid_receipt_count += 1
                continue
            receipts_by_participant[participant_id] = receipt
        covered_participants = [
            participant
            for participant in required_participants
            if participant in receipts_by_participant
        ]
        missing_participants = [
            participant
            for participant in required_participants
            if participant not in receipts_by_participant
        ]
        ordered_receipts = [
            deepcopy(receipts_by_participant[participant])
            for participant in covered_participants
        ]
        receipt_digests = [receipt["digest"] for receipt in ordered_receipts]
        attestation_required = deviation_detected
        attestation_quorum_met = (
            attestation_required
            and not missing_participants
            and invalid_receipt_count == 0
            and not duplicate_participants
        )
        participant_order_bound = covered_participants == required_participants[: len(covered_participants)]
        attestation_digest = sha256_text(canonical_json(receipt_digests))
        digest_payload = {
            "session_id": session["session_id"],
            "time_rate_policy_id": WMS_TIME_RATE_POLICY_ID,
            "baseline_time_rate": baseline_time_rate,
            "requested_time_rate": requested_time_rate,
            "time_rate_delta": delta,
            "time_rate_deviation_detected": deviation_detected,
            "time_rate_state_locked": baseline_time_rate == WMS_DEFAULT_TIME_RATE,
            "time_rate_escape_required": deviation_detected,
            "classification": classification,
            "time_rate_attestation_policy_id": WMS_TIME_RATE_ATTESTATION_POLICY_ID,
            "time_rate_attestation_subject_digest": attestation_subject["digest"],
            "time_rate_attestation_digest": attestation_digest,
            "time_rate_attestation_quorum_met": attestation_quorum_met,
            "time_rate_attestation_covered_participants": covered_participants,
            "time_rate_attestation_missing_participants": missing_participants,
        }
        return {
            "time_rate_policy_id": WMS_TIME_RATE_POLICY_ID,
            "baseline_time_rate": baseline_time_rate,
            "time_rate_delta": delta,
            "time_rate_deviation_detected": deviation_detected,
            "time_rate_state_locked": baseline_time_rate == WMS_DEFAULT_TIME_RATE,
            "time_rate_escape_required": deviation_detected,
            "time_rate_deviation_digest_profile": WMS_TIME_RATE_DEVIATION_DIGEST_PROFILE,
            "time_rate_deviation_digest": sha256_text(canonical_json(digest_payload)),
            "time_rate_attestation_policy_id": WMS_TIME_RATE_ATTESTATION_POLICY_ID,
            "time_rate_attestation_digest_profile": WMS_TIME_RATE_ATTESTATION_DIGEST_PROFILE,
            "time_rate_attestation_subject_digest": attestation_subject["digest"],
            "time_rate_attestation_required": attestation_required,
            "time_rate_attestation_receipts": ordered_receipts,
            "time_rate_attestation_digest": attestation_digest,
            "time_rate_attestation_quorum_met": attestation_quorum_met,
            "time_rate_attestation_participant_order_bound": participant_order_bound,
            "time_rate_attestation_covered_participants": covered_participants,
            "time_rate_attestation_missing_participants": missing_participants,
            "time_rate_attestation_duplicate_participants": _dedupe_preserve_order(
                duplicate_participants
            ),
            "time_rate_attestation_invalid_receipt_count": invalid_receipt_count,
        }

    @staticmethod
    def _normalize_non_empty_string(value: str, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value.strip()

    def _normalize_string_list(self, values: Sequence[str], field_name: str) -> List[str]:
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            raise ValueError(f"{field_name} must be a sequence of strings")
        normalized = [
            self._normalize_non_empty_string(value, field_name)
            for value in values
        ]
        deduped = _dedupe_preserve_order(normalized)
        if not deduped:
            raise ValueError(f"{field_name} must contain at least one value")
        return deduped

    @staticmethod
    def _normalize_ratio(value: float, field_name: str) -> float:
        if not isinstance(value, (int, float)):
            raise ValueError(f"{field_name} must be numeric")
        normalized = round(float(value), 3)
        if normalized < 0 or normalized > 1:
            raise ValueError(f"{field_name} must be between 0 and 1")
        return normalized

    @staticmethod
    def _normalize_mode(mode: str) -> str:
        if mode not in WMS_ALLOWED_MODES:
            raise ValueError(f"mode must be one of {sorted(WMS_ALLOWED_MODES)}")
        return mode

    @staticmethod
    def _normalize_authority(authority: str) -> str:
        if authority not in WMS_ALLOWED_AUTHORITIES:
            raise ValueError(f"authority must be one of {sorted(WMS_ALLOWED_AUTHORITIES)}")
        return authority

    @staticmethod
    def _normalize_time_rate(value: float) -> float:
        if not isinstance(value, (int, float)):
            raise ValueError("time_rate must be numeric")
        normalized = round(float(value), 3)
        if normalized <= 0:
            raise ValueError("time_rate must be > 0")
        return normalized

    @staticmethod
    def _layout_ref(mode: str, objects: Sequence[str]) -> str:
        return f"scene://{mode}/{len(objects)}-objects"

    def _require_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            raise ValueError(f"unknown session_id: {session_id}")
        return self.sessions[session_id]

    def _approval_transport_quorum_met(
        self,
        receipts: Sequence[Mapping[str, Any]],
        *,
        required_approvals: Sequence[str],
        approval_subject_digest: str | None,
    ) -> bool:
        if not required_approvals or not approval_subject_digest:
            return False
        required_set = set(required_approvals)
        bound_participants: List[str] = []
        for receipt in receipts:
            validation = self.validate_approval_transport_receipt(
                receipt,
                approval_subject_digest=approval_subject_digest,
            )
            participant = receipt.get("participant_id") if isinstance(receipt, Mapping) else None
            if not validation["ok"] or participant not in required_set:
                return False
            bound_participants.append(str(participant))
        return (
            bool(bound_participants)
            and len(bound_participants) == len(set(bound_participants))
            and required_set.issubset(set(bound_participants))
        )

    @staticmethod
    def _normalize_digest(value: str, field_name: str) -> str:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(char not in "0123456789abcdef" for char in value)
        ):
            raise ValueError(f"{field_name} must be a sha256 hex digest")
        return value

    @staticmethod
    def _check_digest(value: Any, field_name: str, errors: List[str]) -> None:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(char not in "0123456789abcdef" for char in value)
        ):
            errors.append(f"{field_name} must be a sha256 hex digest")

    @staticmethod
    def _check_non_empty_string(value: Any, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty string")
