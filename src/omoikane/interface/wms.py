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
WMS_APPROVAL_COLLECTION_MAX_BATCH_SIZE = 2
WMS_APPROVAL_TRANSPORT_KIND = "imc"
WMS_APPROVAL_DECISION = "approve"
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


def _time_rate_attestation_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: deepcopy(value) for key, value in receipt.items() if key != "digest"}


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
                "approval_collection_max_batch_size": WMS_APPROVAL_COLLECTION_MAX_BATCH_SIZE,
                "approval_transport_kind": WMS_APPROVAL_TRANSPORT_KIND,
                "guardian_attestation_required": True,
                "rollback_token_required": True,
                "revert_operation_required": True,
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
    def _check_non_empty_string(value: Any, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty string")
