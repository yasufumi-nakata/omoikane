"""Deterministic trust scoring for the reference agent roster."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
import re
from typing import Any, Dict, List, Mapping, Optional

from ..common import canonical_json, new_id, sha256_text, utc_now_iso


TRUST_SNAPSHOT_SCHEMA_VERSION = "1.0.0"
TRUST_TRANSFER_SCHEMA_VERSION = "1.6.0"
TRUST_TRANSFER_POLICY_ID = "bounded-cross-substrate-trust-transfer-v1"
TRUST_TRANSFER_ATTESTATION_POLICY_ID = "bounded-trust-transfer-attestation-federation-v1"
TRUST_TRANSFER_FULL_CLONE_EXPORT_PROFILE_ID = "snapshot-clone-with-history"
TRUST_TRANSFER_REDACTED_EXPORT_PROFILE_ID = "bounded-trust-transfer-redacted-export-v1"
TRUST_TRANSFER_NO_REDACTION_POLICY_ID = "trust-transfer-no-redaction-v1"
TRUST_TRANSFER_HISTORY_REDACTION_POLICY_ID = "bounded-trust-transfer-history-redaction-v1"
TRUST_TRANSFER_REDACTED_SNAPSHOT_SCHEMA_VERSION = "1.0.0"
TRUST_TRANSFER_REDACTED_SNAPSHOT_PROFILE_ID = (
    "bounded-trust-transfer-redacted-snapshot-v1"
)
TRUST_TRANSFER_REDACTED_VERIFIER_FEDERATION_SCHEMA_VERSION = "1.0.0"
TRUST_TRANSFER_REDACTED_VERIFIER_FEDERATION_PROFILE_ID = (
    "bounded-trust-transfer-redacted-verifier-federation-v1"
)
TRUST_TRANSFER_REDACTED_VERIFIER_RECEIPT_SUMMARY_PROFILE_ID = (
    "bounded-trust-transfer-redacted-verifier-receipt-summary-v1"
)
TRUST_TRANSFER_REDACTED_DESTINATION_LIFECYCLE_SCHEMA_VERSION = "1.1.0"
TRUST_TRANSFER_REDACTED_DESTINATION_LIFECYCLE_PROFILE_ID = (
    "bounded-trust-transfer-redacted-destination-lifecycle-v1"
)
TRUST_TRANSFER_VERIFIER_SUMMARY_REDACTION_POLICY_ID = (
    "bounded-trust-transfer-verifier-summary-redaction-v1"
)
TRUST_TRANSFER_DESTINATION_LIFECYCLE_SUMMARY_REDACTION_POLICY_ID = (
    "bounded-trust-transfer-destination-lifecycle-summary-redaction-v1"
)
TRUST_TRANSFER_REMOTE_VERIFIER_FEDERATION_POLICY_ID = (
    "bounded-live-trust-transfer-verifier-federation-v1"
)
TRUST_TRANSFER_REMOTE_VERIFIER_NETWORK_PROFILE_ID = "guardian-reviewer-remote-attestation-v1"
TRUST_TRANSFER_BASELINE_REMOTE_VERIFIER_QUORUM_POLICY_ID = (
    "bounded-trust-transfer-fixed-verifier-pair-v1"
)
TRUST_TRANSFER_RECOVERY_REMOTE_VERIFIER_QUORUM_POLICY_ID = (
    "bounded-trust-transfer-multi-root-recovery-v1"
)
TRUST_TRANSFER_REQUIRED_REMOTE_VERIFIER_COUNT = 2
TRUST_TRANSFER_RECOVERY_REMOTE_VERIFIER_COUNT = 3
TRUST_TRANSFER_BASELINE_TRUST_ROOT_QUORUM = 1
TRUST_TRANSFER_BASELINE_JURISDICTION_QUORUM = 1
TRUST_TRANSFER_RECOVERY_TRUST_ROOT_QUORUM = 2
TRUST_TRANSFER_RECOVERY_JURISDICTION_QUORUM = 2
TRUST_TRANSFER_REATTESTATION_CADENCE_POLICY_ID = (
    "bounded-trust-transfer-re-attestation-cadence-v1"
)
TRUST_TRANSFER_REATTESTATION_INTERVAL_SECONDS = 600
TRUST_TRANSFER_REATTESTATION_GRACE_WINDOW_SECONDS = 240
TRUST_TRANSFER_DESTINATION_LIFECYCLE_POLICY_ID = (
    "bounded-trust-transfer-destination-lifecycle-v1"
)
TRUST_TRANSFER_DESTINATION_CURRENT_STATUS = "current"
TRUST_TRANSFER_DESTINATION_REVOKED_STATUS = "revoked"
TRUST_TRANSFER_DESTINATION_REVOCATION_FAIL_CLOSED_ACTION = (
    "disable-destination-trust-usage"
)
TRUST_TRANSFER_DESTINATION_REVOCATION_CHECK_OFFSET_SECONDS = 60
TRUST_TRANSFER_DESTINATION_RECOVERY_ATTESTATION_OFFSET_SECONDS = 120
TRUST_TRANSFER_REQUIRED_ATTESTATION_ROLES = (
    "source-guardian",
    "destination-guardian",
    "human-reviewer",
)
TRUST_TRANSFER_REDACTED_FIELDS = (
    "pinned_reason",
    "history[].triggered_by",
    "history[].triggered_by_agent_id",
    "history[].rationale",
    "history[].evidence_confidence",
    "history[].raw_delta",
    "history[].applied_delta",
    "history[].global_before",
    "history[].global_after",
    "history[].domain_before",
    "history[].domain_after",
)
TRUST_TRANSFER_REDACTED_VERIFIER_FIELDS = (
    "verifier_receipts[].reviewer_id",
    "verifier_receipts[].challenge_ref",
    "verifier_receipts[].challenge_digest",
    "verifier_receipts[].trust_root_digest",
    "verifier_receipts[].transport_exchange.exchange_id",
    "verifier_receipts[].transport_exchange.challenge_ref",
    "verifier_receipts[].transport_exchange.challenge_digest",
    "verifier_receipts[].transport_exchange.request_payload_kind",
    "verifier_receipts[].transport_exchange.request_payload_ref",
    "verifier_receipts[].transport_exchange.request_payload_digest",
    "verifier_receipts[].transport_exchange.request_size_bytes",
    "verifier_receipts[].transport_exchange.response_payload_kind",
    "verifier_receipts[].transport_exchange.response_payload_ref",
    "verifier_receipts[].transport_exchange.response_payload_digest",
    "verifier_receipts[].transport_exchange.response_size_bytes",
    "verifier_receipts[].transport_exchange.recorded_at",
)
TRUST_TRANSFER_REDACTED_DESTINATION_LIFECYCLE_FIELDS = (
    "destination_lifecycle.active_entry_ref",
    "destination_lifecycle.latest_federation_ref",
    "destination_lifecycle.latest_cadence_ref",
    "destination_lifecycle.history[].entry_id",
    "destination_lifecycle.history[].entry_ref",
    "destination_lifecycle.history[].attested_at",
    "destination_lifecycle.history[].federation_ref",
    "destination_lifecycle.history[].cadence_ref",
    "destination_lifecycle.history[].covered_verifier_receipt_ids",
    "destination_lifecycle.history[].rationale",
)
TRUST_TRANSFER_SUPPORTED_EXPORT_PROFILES = (
    TRUST_TRANSFER_FULL_CLONE_EXPORT_PROFILE_ID,
    TRUST_TRANSFER_REDACTED_EXPORT_PROFILE_ID,
)


def _trust_transfer_quorum_policy_spec(
    quorum_policy_id: str,
) -> Optional[Dict[str, int | str]]:
    if quorum_policy_id == TRUST_TRANSFER_BASELINE_REMOTE_VERIFIER_QUORUM_POLICY_ID:
        return {
            "quorum_policy_id": quorum_policy_id,
            "required_verifier_count": TRUST_TRANSFER_REQUIRED_REMOTE_VERIFIER_COUNT,
            "trust_root_quorum": TRUST_TRANSFER_BASELINE_TRUST_ROOT_QUORUM,
            "jurisdiction_quorum": TRUST_TRANSFER_BASELINE_JURISDICTION_QUORUM,
        }
    if quorum_policy_id == TRUST_TRANSFER_RECOVERY_REMOTE_VERIFIER_QUORUM_POLICY_ID:
        return {
            "quorum_policy_id": quorum_policy_id,
            "required_verifier_count": TRUST_TRANSFER_RECOVERY_REMOTE_VERIFIER_COUNT,
            "trust_root_quorum": TRUST_TRANSFER_RECOVERY_TRUST_ROOT_QUORUM,
            "jurisdiction_quorum": TRUST_TRANSFER_RECOVERY_JURISDICTION_QUORUM,
        }
    return None


def _trust_transfer_verifier_quorum_fields(
    *,
    quorum_policy_id: str,
    verifier_receipts: List[Mapping[str, Any]],
) -> Dict[str, Any]:
    spec = _trust_transfer_quorum_policy_spec(quorum_policy_id)
    if spec is None:
        raise ValueError(f"unsupported verifier quorum policy: {quorum_policy_id}")
    verifier_refs = [
        str(verifier_receipt["verifier_ref"]) for verifier_receipt in verifier_receipts
    ]
    trust_root_refs = sorted(
        {str(verifier_receipt["trust_root_ref"]) for verifier_receipt in verifier_receipts}
    )
    jurisdictions = sorted(
        {str(verifier_receipt["jurisdiction"]) for verifier_receipt in verifier_receipts}
    )
    if len(verifier_receipts) != int(spec["required_verifier_count"]):
        raise ValueError(
            "verifier receipt count must match the selected quorum policy"
        )
    if len(set(verifier_refs)) != len(verifier_refs):
        raise ValueError("verifier quorum requires distinct verifier_ref values")
    if len(trust_root_refs) < int(spec["trust_root_quorum"]):
        raise ValueError("verifier quorum must satisfy trust_root_quorum")
    if len(jurisdictions) < int(spec["jurisdiction_quorum"]):
        raise ValueError("verifier quorum must satisfy jurisdiction_quorum")
    return {
        "quorum_policy_id": quorum_policy_id,
        "required_verifier_count": int(spec["required_verifier_count"]),
        "received_verifier_count": len(verifier_receipts),
        "verifier_refs": verifier_refs,
        "trust_root_refs": trust_root_refs,
        "jurisdictions": jurisdictions,
        "trust_root_quorum": int(spec["trust_root_quorum"]),
        "jurisdiction_quorum": int(spec["jurisdiction_quorum"]),
    }


def _trust_transfer_lifecycle_entry_quorum_bound(entry: Mapping[str, Any]) -> bool:
    spec = _trust_transfer_quorum_policy_spec(str(entry.get("quorum_policy_id", "")))
    if spec is None:
        return False
    covered_verifier_receipt_ids = entry.get("covered_verifier_receipt_ids")
    covered_trust_root_refs = entry.get("covered_trust_root_refs")
    covered_jurisdictions = entry.get("covered_jurisdictions")
    return (
        isinstance(covered_verifier_receipt_ids, list)
        and len(covered_verifier_receipt_ids) == int(spec["required_verifier_count"])
        and len(set(str(receipt_id) for receipt_id in covered_verifier_receipt_ids))
        == int(spec["required_verifier_count"])
        and entry.get("trust_root_quorum") == int(spec["trust_root_quorum"])
        and isinstance(covered_trust_root_refs, list)
        and len(sorted({str(root_ref) for root_ref in covered_trust_root_refs}))
        >= int(spec["trust_root_quorum"])
        and entry.get("jurisdiction_quorum") == int(spec["jurisdiction_quorum"])
        and isinstance(covered_jurisdictions, list)
        and len(sorted({str(jurisdiction) for jurisdiction in covered_jurisdictions}))
        >= int(spec["jurisdiction_quorum"])
    )


def _trust_transfer_redacted_lifecycle_entry_quorum_bound(summary: Mapping[str, Any]) -> bool:
    spec = _trust_transfer_quorum_policy_spec(str(summary.get("quorum_policy_id", "")))
    if spec is None:
        return False
    return (
        summary.get("covered_verifier_count") == int(spec["required_verifier_count"])
        and summary.get("trust_root_quorum") == int(spec["trust_root_quorum"])
        and summary.get("covered_trust_root_count", 0) >= int(spec["trust_root_quorum"])
        and summary.get("jurisdiction_quorum") == int(spec["jurisdiction_quorum"])
        and summary.get("covered_jurisdiction_count", 0)
        >= int(spec["jurisdiction_quorum"])
    )


def _clamp_score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)


def _actor_fingerprint(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _snapshot_history_digest(snapshot: Mapping[str, Any]) -> str:
    return sha256_text(canonical_json(snapshot.get("history", [])))


def _snapshot_threshold_digest(snapshot: Mapping[str, Any]) -> str:
    return sha256_text(canonical_json(snapshot.get("thresholds", {})))


def _snapshot_eligibility_digest(snapshot: Mapping[str, Any]) -> str:
    return sha256_text(canonical_json(snapshot.get("eligibility", {})))


def _trust_transfer_route_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "source_substrate_ref": receipt["source_substrate_ref"],
        "destination_substrate_ref": receipt["destination_substrate_ref"],
        "destination_host_ref": receipt["destination_host_ref"],
    }


def _trust_transfer_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "schema_version": receipt["schema_version"],
        "transfer_policy_id": receipt["transfer_policy_id"],
        "attestation_policy_id": receipt["attestation_policy_id"],
        "export_profile_id": receipt["export_profile_id"],
        "agent_id": receipt["agent_id"],
        "source_substrate_ref": receipt["source_substrate_ref"],
        "destination_substrate_ref": receipt["destination_substrate_ref"],
        "destination_host_ref": receipt["destination_host_ref"],
        "transferred_at": receipt["transferred_at"],
        "source_snapshot_ref": receipt["source_snapshot_ref"],
        "source_snapshot_digest": receipt["source_snapshot_digest"],
        "destination_snapshot_ref": receipt["destination_snapshot_ref"],
        "destination_snapshot_digest": receipt["destination_snapshot_digest"],
        "export_receipt": receipt["export_receipt"],
        "federation_attestation": receipt["federation_attestation"],
        "import_receipt": receipt["import_receipt"],
        "destination_lifecycle": receipt["destination_lifecycle"],
        "status": receipt["status"],
    }
    if "source_snapshot_redacted" in receipt:
        payload["source_snapshot_redacted"] = receipt["source_snapshot_redacted"]
    if "destination_snapshot_redacted" in receipt:
        payload["destination_snapshot_redacted"] = receipt["destination_snapshot_redacted"]
    return payload


def _trust_transfer_history_commitment_payload(
    snapshot: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    history = snapshot.get("history", [])
    if not isinstance(history, list):
        return []
    commitment: List[Dict[str, Any]] = []
    for event in history:
        if not isinstance(event, Mapping):
            continue
        commitment.append(
            {
                "event_id": event.get("event_id"),
                "domain": event.get("domain"),
                "event_type": event.get("event_type"),
                "severity": event.get("severity"),
                "applied": event.get("applied"),
                "provenance_status": event.get("provenance_status"),
                "recorded_at": event.get("recorded_at"),
            }
        )
    return commitment


def _trust_transfer_history_commitment_digest(snapshot: Mapping[str, Any]) -> str:
    return sha256_text(canonical_json(_trust_transfer_history_commitment_payload(snapshot)))


def _trust_transfer_remote_verifier_federation_digest_payload(
    federation: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "federation_id": federation["federation_id"],
        "federation_ref": federation["federation_ref"],
        "federation_policy_id": federation["federation_policy_id"],
        "network_profile_id": federation["network_profile_id"],
        "quorum_policy_id": federation["quorum_policy_id"],
        "human_reviewer_ref": federation["human_reviewer_ref"],
        "required_verifier_count": federation["required_verifier_count"],
        "received_verifier_count": federation["received_verifier_count"],
        "verifier_receipts": federation["verifier_receipts"],
        "verifier_refs": federation["verifier_refs"],
        "trust_root_refs": federation["trust_root_refs"],
        "jurisdictions": federation["jurisdictions"],
        "trust_root_quorum": federation["trust_root_quorum"],
        "jurisdiction_quorum": federation["jurisdiction_quorum"],
        "authority_chain_refs": federation["authority_chain_refs"],
        "reviewer_binding_digest": federation["reviewer_binding_digest"],
        "federation_status": federation["federation_status"],
    }


def _trust_transfer_re_attestation_cadence_digest_payload(
    cadence: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "cadence_id": cadence["cadence_id"],
        "cadence_ref": cadence["cadence_ref"],
        "cadence_policy_id": cadence["cadence_policy_id"],
        "attested_at": cadence["attested_at"],
        "renew_after": cadence["renew_after"],
        "valid_until": cadence["valid_until"],
        "grace_window_seconds": cadence["grace_window_seconds"],
        "covered_verifier_receipt_ids": cadence["covered_verifier_receipt_ids"],
        "bound_federation_ref": cadence["bound_federation_ref"],
        "bound_federation_digest": cadence["bound_federation_digest"],
        "cadence_status": cadence["cadence_status"],
    }


def _trust_transfer_destination_lifecycle_digest_payload(
    lifecycle: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "lifecycle_id": lifecycle["lifecycle_id"],
        "lifecycle_ref": lifecycle["lifecycle_ref"],
        "lifecycle_policy_id": lifecycle["lifecycle_policy_id"],
        "current_status": lifecycle["current_status"],
        "active_entry_ref": lifecycle["active_entry_ref"],
        "latest_federation_ref": lifecycle["latest_federation_ref"],
        "latest_federation_digest": lifecycle["latest_federation_digest"],
        "latest_cadence_ref": lifecycle["latest_cadence_ref"],
        "latest_cadence_digest": lifecycle["latest_cadence_digest"],
        "revocation_fail_closed_action": lifecycle["revocation_fail_closed_action"],
        "history": lifecycle["history"],
    }


def _trust_transfer_redacted_snapshot_digest_payload(
    projection: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "kind": projection["kind"],
        "schema_version": projection["schema_version"],
        "projection_id": projection["projection_id"],
        "projection_ref": projection["projection_ref"],
        "projection_profile_id": projection["projection_profile_id"],
        "sealed_snapshot_ref": projection["sealed_snapshot_ref"],
        "sealed_snapshot_digest": projection["sealed_snapshot_digest"],
        "agent_id": projection["agent_id"],
        "global_score": projection["global_score"],
        "per_domain": projection["per_domain"],
        "pinned_by_human": projection["pinned_by_human"],
        "thresholds": projection["thresholds"],
        "eligibility": projection["eligibility"],
        "history_summary": projection["history_summary"],
        "redaction_policy_id": projection["redaction_policy_id"],
        "redacted_fields": projection["redacted_fields"],
    }


def _trust_transfer_redacted_snapshot_digest(
    projection: Mapping[str, Any],
) -> Optional[str]:
    try:
        return sha256_text(
            canonical_json(_trust_transfer_redacted_snapshot_digest_payload(projection))
        )
    except KeyError:
        return None


def _trust_transfer_redacted_verifier_receipt_summary_digest_payload(
    summary: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "kind": summary["kind"],
        "schema_version": summary["schema_version"],
        "summary_id": summary["summary_id"],
        "summary_ref": summary["summary_ref"],
        "summary_profile_id": summary["summary_profile_id"],
        "receipt_id": summary["receipt_id"],
        "verifier_endpoint": summary["verifier_endpoint"],
        "verifier_ref": summary["verifier_ref"],
        "jurisdiction": summary["jurisdiction"],
        "network_profile_id": summary["network_profile_id"],
        "authority_chain_ref": summary["authority_chain_ref"],
        "trust_root_ref": summary["trust_root_ref"],
        "freshness_window_seconds": summary["freshness_window_seconds"],
        "observed_latency_ms": summary["observed_latency_ms"],
        "recorded_at": summary["recorded_at"],
        "receipt_status": summary["receipt_status"],
        "transport_exchange_digest": summary["transport_exchange_digest"],
        "sealed_receipt_digest": summary["sealed_receipt_digest"],
        "redaction_policy_id": summary["redaction_policy_id"],
        "redacted_fields": summary["redacted_fields"],
    }


def _trust_transfer_redacted_verifier_receipt_summary_digest(
    summary: Mapping[str, Any],
) -> Optional[str]:
    try:
        return sha256_text(
            canonical_json(
                _trust_transfer_redacted_verifier_receipt_summary_digest_payload(summary)
            )
        )
    except KeyError:
        return None


def _trust_transfer_redacted_verifier_receipt_commitment_payload(
    summaries: List[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    commitment: List[Dict[str, Any]] = []
    for summary in summaries:
        commitment.append(
            {
                "receipt_id": summary["receipt_id"],
                "verifier_ref": summary["verifier_ref"],
                "recorded_at": summary["recorded_at"],
                "freshness_window_seconds": summary["freshness_window_seconds"],
                "receipt_status": summary["receipt_status"],
                "transport_exchange_digest": summary["transport_exchange_digest"],
                "sealed_receipt_digest": summary["sealed_receipt_digest"],
            }
        )
    return commitment


def _trust_transfer_redacted_verifier_receipt_commitment_digest(
    summaries: List[Mapping[str, Any]],
) -> Optional[str]:
    try:
        return sha256_text(
            canonical_json(
                _trust_transfer_redacted_verifier_receipt_commitment_payload(summaries)
            )
        )
    except KeyError:
        return None


def _trust_transfer_redacted_verifier_federation_digest_payload(
    federation: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "kind": federation["kind"],
        "schema_version": federation["schema_version"],
        "federation_id": federation["federation_id"],
        "federation_ref": federation["federation_ref"],
        "summary_profile_id": federation["summary_profile_id"],
        "federation_policy_id": federation["federation_policy_id"],
        "network_profile_id": federation["network_profile_id"],
        "quorum_policy_id": federation["quorum_policy_id"],
        "human_reviewer_ref": federation["human_reviewer_ref"],
        "required_verifier_count": federation["required_verifier_count"],
        "received_verifier_count": federation["received_verifier_count"],
        "verifier_receipt_summaries": federation["verifier_receipt_summaries"],
        "verifier_refs": federation["verifier_refs"],
        "trust_root_refs": federation["trust_root_refs"],
        "jurisdictions": federation["jurisdictions"],
        "trust_root_quorum": federation["trust_root_quorum"],
        "jurisdiction_quorum": federation["jurisdiction_quorum"],
        "authority_chain_refs": federation["authority_chain_refs"],
        "reviewer_binding_digest": federation["reviewer_binding_digest"],
        "verifier_receipt_commitment_digest": federation[
            "verifier_receipt_commitment_digest"
        ],
        "sealed_federation_digest": federation["sealed_federation_digest"],
        "redaction_policy_id": federation["redaction_policy_id"],
        "redacted_fields": federation["redacted_fields"],
        "federation_status": federation["federation_status"],
    }


def _trust_transfer_covered_verifier_receipt_commitment_digest(
    covered_verifier_receipt_ids: List[str],
) -> str:
    return sha256_text(canonical_json(list(covered_verifier_receipt_ids)))


def _trust_transfer_redacted_destination_lifecycle_entry_summary_digest_payload(
    summary: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "sequence": summary["sequence"],
        "event_type": summary["event_type"],
        "status": summary["status"],
        "recorded_at": summary["recorded_at"],
        "valid_until": summary["valid_until"],
        "quorum_policy_id": summary["quorum_policy_id"],
        "federation_digest": summary["federation_digest"],
        "cadence_digest": summary["cadence_digest"],
        "trust_root_quorum": summary["trust_root_quorum"],
        "jurisdiction_quorum": summary["jurisdiction_quorum"],
        "covered_verifier_count": summary["covered_verifier_count"],
        "covered_trust_root_count": summary["covered_trust_root_count"],
        "covered_jurisdiction_count": summary["covered_jurisdiction_count"],
        "covered_verifier_receipt_commitment_digest": summary[
            "covered_verifier_receipt_commitment_digest"
        ],
        "destination_snapshot_digest": summary["destination_snapshot_digest"],
    }


def _trust_transfer_redacted_destination_lifecycle_entry_summary_digest(
    summary: Mapping[str, Any],
) -> Optional[str]:
    try:
        return sha256_text(
            canonical_json(
                _trust_transfer_redacted_destination_lifecycle_entry_summary_digest_payload(
                    summary
                )
            )
        )
    except KeyError:
        return None


def _trust_transfer_redacted_destination_lifecycle_history_commitment_payload(
    summaries: List[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    commitment: List[Dict[str, Any]] = []
    for summary in summaries:
        commitment.append(
            _trust_transfer_redacted_destination_lifecycle_entry_summary_digest_payload(
                summary
            )
        )
    return commitment


def _trust_transfer_redacted_destination_lifecycle_history_commitment_digest(
    summaries: List[Mapping[str, Any]],
) -> Optional[str]:
    try:
        return sha256_text(
            canonical_json(
                _trust_transfer_redacted_destination_lifecycle_history_commitment_payload(
                    summaries
                )
            )
        )
    except KeyError:
        return None


def _trust_transfer_redacted_destination_lifecycle_digest_payload(
    lifecycle: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "kind": lifecycle["kind"],
        "schema_version": lifecycle["schema_version"],
        "lifecycle_id": lifecycle["lifecycle_id"],
        "lifecycle_ref": lifecycle["lifecycle_ref"],
        "summary_profile_id": lifecycle["summary_profile_id"],
        "lifecycle_policy_id": lifecycle["lifecycle_policy_id"],
        "current_status": lifecycle["current_status"],
        "active_sequence": lifecycle["active_sequence"],
        "active_entry_digest": lifecycle["active_entry_digest"],
        "latest_federation_digest": lifecycle["latest_federation_digest"],
        "latest_cadence_digest": lifecycle["latest_cadence_digest"],
        "revocation_fail_closed_action": lifecycle["revocation_fail_closed_action"],
        "history_summaries": lifecycle["history_summaries"],
        "history_summary_commitment_digest": lifecycle[
            "history_summary_commitment_digest"
        ],
        "sealed_lifecycle_digest": lifecycle["sealed_lifecycle_digest"],
        "redaction_policy_id": lifecycle["redaction_policy_id"],
        "redacted_fields": lifecycle["redacted_fields"],
    }


def _trust_transfer_remote_reviewer_binding_digest(
    *,
    human_reviewer_ref: str,
    route_digest: str,
    verifier_receipts: List[Mapping[str, Any]],
) -> str:
    return sha256_text(
        canonical_json(
            {
                "human_reviewer_ref": human_reviewer_ref,
                "route_digest": route_digest,
                "verifier_receipt_ids": [
                    receipt["receipt_id"] for receipt in verifier_receipts
                ],
            }
        )
    )


def _parse_datetime(value: str, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO8601 datetime") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include timezone information")
    return parsed


def _trust_transfer_federation_binding_digest(federation: Mapping[str, Any]) -> str:
    sealed_digest = federation.get("sealed_federation_digest")
    if isinstance(sealed_digest, str) and sealed_digest.strip():
        return sealed_digest
    return str(federation.get("receipt_digest", ""))


@dataclass(frozen=True)
class TrustThresholds:
    """Operational trust floors used by the reference runtime."""

    council_invite_floor: float = 0.5
    weighted_vote_floor: float = 0.6
    apply_floor: float = 0.8
    self_modify_floor: float = 0.95
    guardian_floor: float = 0.99
    guardian_requires_human_pin: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrustUpdatePolicy:
    """Fixed trust update policy for the reference runtime."""

    policy_id: str = "reference-v0"
    provenance_policy_id: str = "reference-trust-provenance-v1"
    initial_score: float = 0.3
    base_deltas: Dict[str, float] = field(
        default_factory=lambda: {
            "council_quality_positive": 0.04,
            "guardian_audit_pass": 0.06,
            "human_feedback_good": 0.05,
            "guardian_veto": -0.12,
            "regression_detected": -0.08,
            "human_feedback_bad": -0.10,
            "ethics_violation": -0.25,
        }
    )
    severity_multipliers: Dict[str, float] = field(
        default_factory=lambda: {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5,
            "critical": 2.0,
        }
    )
    event_origin_requirements: Dict[str, str] = field(
        default_factory=lambda: {
            "council_quality_positive": "council",
            "guardian_audit_pass": "guardian",
            "human_feedback_good": "human",
            "guardian_veto": "guardian",
            "regression_detected": "any",
            "human_feedback_bad": "human",
            "ethics_violation": "any",
        }
    )
    blocked_positive_reciprocity_scope: str = "registered-agent-domain-history"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrustEvent:
    """One audited trust update attempt."""

    event_id: str
    agent_id: str
    domain: str
    event_type: str
    severity: str
    evidence_confidence: float
    raw_delta: float
    applied_delta: float
    applied: bool
    triggered_by: str
    triggered_by_agent_id: str
    rationale: str
    global_before: float
    global_after: float
    domain_before: float
    domain_after: float
    policy_id: str
    provenance_status: str
    provenance_policy_id: str
    recorded_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentTrustState:
    """Serializable trust state for one agent."""

    agent_id: str
    global_score: float
    per_domain: Dict[str, float] = field(default_factory=dict)
    history: List[TrustEvent] = field(default_factory=list)
    pinned_by_human: bool = False
    pinned_reason: str = ""

    def to_dict(self, thresholds: TrustThresholds) -> Dict[str, Any]:
        per_domain = {key: _clamp_score(value) for key, value in sorted(self.per_domain.items())}
        self_modify_score = per_domain.get("self_modify", _clamp_score(self.global_score))
        return {
            "kind": "trust_snapshot",
            "schema_version": TRUST_SNAPSHOT_SCHEMA_VERSION,
            "agent_id": self.agent_id,
            "global_score": _clamp_score(self.global_score),
            "per_domain": per_domain,
            "history": [event.to_dict() for event in self.history],
            "pinned_by_human": self.pinned_by_human,
            "pinned_reason": self.pinned_reason,
            "thresholds": thresholds.to_dict(),
            "eligibility": {
                "invite_to_council": self.global_score >= thresholds.council_invite_floor,
                "count_for_weighted_vote": self.global_score >= thresholds.weighted_vote_floor,
                "apply_to_runtime": self.global_score >= thresholds.apply_floor,
                "self_modify_role": (
                    self.global_score >= thresholds.self_modify_floor
                    and self_modify_score >= thresholds.self_modify_floor
                ),
                "guardian_role": (
                    self.global_score >= thresholds.guardian_floor
                    and (not thresholds.guardian_requires_human_pin or self.pinned_by_human)
                ),
            },
        }


class TrustService:
    """Reference trust registry with deterministic scoring and human pinning."""

    def __init__(
        self,
        *,
        policy: Optional[TrustUpdatePolicy] = None,
        thresholds: Optional[TrustThresholds] = None,
    ) -> None:
        self._policy = policy or TrustUpdatePolicy()
        self._thresholds = thresholds or TrustThresholds()
        self._states: Dict[str, AgentTrustState] = {}

    def policy_snapshot(self) -> Dict[str, Any]:
        return {
            "policy": self._policy.to_dict(),
            "thresholds": self._thresholds.to_dict(),
        }

    def register_agent(
        self,
        agent_id: str,
        *,
        initial_score: Optional[float] = None,
        per_domain: Optional[Dict[str, float]] = None,
        pinned_by_human: bool = False,
        pinned_reason: str = "",
    ) -> Dict[str, Any]:
        score = _clamp_score(
            self._policy.initial_score if initial_score is None else float(initial_score)
        )
        domain_scores = {
            name: _clamp_score(value)
            for name, value in sorted((per_domain or {}).items())
            if name.strip()
        }
        state = AgentTrustState(
            agent_id=agent_id,
            global_score=score,
            per_domain=domain_scores,
            pinned_by_human=pinned_by_human,
            pinned_reason=pinned_reason,
        )
        self._states[agent_id] = state
        return state.to_dict(self._thresholds)

    def snapshot(self, agent_id: str) -> Dict[str, Any]:
        return self._state(agent_id).to_dict(self._thresholds)

    def has_agent(self, agent_id: str) -> bool:
        agent_key = self._normalize_non_empty(agent_id, "agent_id")
        return agent_key in self._states

    def all_snapshots(self) -> List[Dict[str, Any]]:
        return [self._states[agent_id].to_dict(self._thresholds) for agent_id in sorted(self._states)]

    def pin_agent(
        self,
        agent_id: str,
        *,
        global_score: Optional[float] = None,
        per_domain: Optional[Dict[str, float]] = None,
        reason: str,
    ) -> Dict[str, Any]:
        state = self._state(agent_id)
        state.pinned_by_human = True
        state.pinned_reason = reason
        if global_score is not None:
            state.global_score = _clamp_score(float(global_score))
        if per_domain:
            for domain, score in per_domain.items():
                if domain.strip():
                    state.per_domain[domain] = _clamp_score(float(score))
        return state.to_dict(self._thresholds)

    def unpin_agent(self, agent_id: str) -> Dict[str, Any]:
        state = self._state(agent_id)
        state.pinned_by_human = False
        state.pinned_reason = ""
        return state.to_dict(self._thresholds)

    def import_snapshot(self, snapshot: Mapping[str, Any]) -> Dict[str, Any]:
        state, errors = self._snapshot_state_from_mapping(snapshot)
        if errors or state is None:
            raise ValueError(
                "trust snapshot import requires a fixed-contract payload: "
                + "; ".join(errors or ["invalid snapshot"])
            )

        self._states[state.agent_id] = state
        imported = self._states[state.agent_id].to_dict(self._thresholds)
        if dict(snapshot) != imported:
            raise ValueError("imported trust snapshot drifted from the fixed contract")
        return imported

    def transfer_snapshot_to(
        self,
        agent_id: str,
        *,
        destination_service: "TrustService",
        source_substrate_ref: str,
        destination_substrate_ref: str,
        destination_host_ref: str,
        source_guardian_agent_id: str,
        destination_guardian_agent_id: str,
        human_reviewer_ref: str,
        remote_verifier_receipts: List[Mapping[str, Any]],
        council_session_ref: str,
        rationale: str,
        export_profile_id: str = TRUST_TRANSFER_FULL_CLONE_EXPORT_PROFILE_ID,
    ) -> Dict[str, Any]:
        normalized_agent_id = self._normalize_non_empty(agent_id, "agent_id")
        normalized_source_substrate = self._normalize_non_empty(
            source_substrate_ref,
            "source_substrate_ref",
        )
        normalized_destination_substrate = self._normalize_non_empty(
            destination_substrate_ref,
            "destination_substrate_ref",
        )
        normalized_destination_host = self._normalize_non_empty(
            destination_host_ref,
            "destination_host_ref",
        )
        normalized_source_guardian = self._normalize_non_empty(
            source_guardian_agent_id,
            "source_guardian_agent_id",
        )
        normalized_destination_guardian = self._normalize_non_empty(
            destination_guardian_agent_id,
            "destination_guardian_agent_id",
        )
        normalized_human_reviewer = self._normalize_non_empty(
            human_reviewer_ref,
            "human_reviewer_ref",
        )
        normalized_remote_verifier_receipts = self._normalize_remote_verifier_receipts(
            remote_verifier_receipts
        )
        normalized_council_session = self._normalize_non_empty(
            council_session_ref,
            "council_session_ref",
        )
        normalized_rationale = self._normalize_non_empty(rationale, "rationale")
        normalized_export_profile = self._normalize_export_profile(export_profile_id)
        if normalized_source_substrate == normalized_destination_substrate:
            raise ValueError("source_substrate_ref and destination_substrate_ref must differ")
        if normalized_source_guardian == normalized_destination_guardian:
            raise ValueError("source and destination guardian attestations must be distinct")
        if not self._is_guardian_authority(normalized_source_guardian):
            raise ValueError("source_guardian_agent_id must hold guardian_role eligibility")
        if not destination_service._is_guardian_authority(normalized_destination_guardian):
            raise ValueError("destination_guardian_agent_id must hold guardian_role eligibility")

        source_snapshot = self.snapshot(normalized_agent_id)
        source_snapshot_digest = sha256_text(canonical_json(source_snapshot))
        source_history_digest = _snapshot_history_digest(source_snapshot)
        source_history_commitment_digest = _trust_transfer_history_commitment_digest(
            source_snapshot
        )
        source_threshold_digest = _snapshot_threshold_digest(source_snapshot)
        source_eligibility_digest = _snapshot_eligibility_digest(source_snapshot)

        destination_snapshot = destination_service.import_snapshot(source_snapshot)
        destination_snapshot_digest = sha256_text(canonical_json(destination_snapshot))
        destination_history_commitment_digest = _trust_transfer_history_commitment_digest(
            destination_snapshot
        )
        transferred_at = utc_now_iso()

        attestors = [
            {
                "role": "source-guardian",
                "actor_ref": f"agent://{normalized_source_guardian}",
                "attestation_ref": f"guardian-attestation://{normalized_source_guardian}",
                "eligibility_gate": "guardian_role",
                "status": "attested",
            },
            {
                "role": "destination-guardian",
                "actor_ref": f"agent://{normalized_destination_guardian}",
                "attestation_ref": f"guardian-attestation://{normalized_destination_guardian}",
                "eligibility_gate": "guardian_role",
                "status": "attested",
            },
            {
                "role": "human-reviewer",
                "actor_ref": normalized_human_reviewer,
                "attestation_ref": f"{normalized_human_reviewer}/trust-transfer",
                "eligibility_gate": "human-explicit-approval",
                "status": "attested",
            },
        ]
        received_roles = [attestor["role"] for attestor in attestors if attestor["status"] == "attested"]
        route_digest = sha256_text(
            canonical_json(
                {
                    "source_substrate_ref": normalized_source_substrate,
                    "destination_substrate_ref": normalized_destination_substrate,
                    "destination_host_ref": normalized_destination_host,
                }
            )
        )
        initial_remote_verifier_federation = self._build_remote_verifier_federation(
            human_reviewer_ref=normalized_human_reviewer,
            route_digest=route_digest,
            verifier_receipts=normalized_remote_verifier_receipts,
            quorum_policy_id=TRUST_TRANSFER_BASELINE_REMOTE_VERIFIER_QUORUM_POLICY_ID,
        )
        renewed_remote_verifier_receipts = self._renew_remote_verifier_receipts(
            verifier_receipts=normalized_remote_verifier_receipts,
            renewed_at=(
                self._build_re_attestation_cadence(
                    federation=initial_remote_verifier_federation
                )["renew_after"]
            ),
        )
        renewed_remote_verifier_federation = self._build_remote_verifier_federation(
            human_reviewer_ref=normalized_human_reviewer,
            route_digest=route_digest,
            verifier_receipts=renewed_remote_verifier_receipts,
            quorum_policy_id=TRUST_TRANSFER_BASELINE_REMOTE_VERIFIER_QUORUM_POLICY_ID,
        )
        renewed_re_attestation_cadence = self._build_re_attestation_cadence(
            federation=renewed_remote_verifier_federation
        )
        recovered_remote_verifier_receipts = self._build_multi_root_recovery_remote_verifier_receipts(
            verifier_receipts=renewed_remote_verifier_receipts,
            recovered_at=str(renewed_re_attestation_cadence["renew_after"]),
        )
        recovered_remote_verifier_federation = self._build_remote_verifier_federation(
            human_reviewer_ref=normalized_human_reviewer,
            route_digest=route_digest,
            verifier_receipts=recovered_remote_verifier_receipts,
            quorum_policy_id=TRUST_TRANSFER_RECOVERY_REMOTE_VERIFIER_QUORUM_POLICY_ID,
        )
        initial_public_remote_verifier_federation = initial_remote_verifier_federation
        renewed_public_remote_verifier_federation = renewed_remote_verifier_federation
        recovered_public_remote_verifier_federation = recovered_remote_verifier_federation
        if normalized_export_profile == TRUST_TRANSFER_REDACTED_EXPORT_PROFILE_ID:
            initial_public_remote_verifier_federation = (
                self._build_redacted_verifier_federation_summary(
                    initial_remote_verifier_federation
                )
            )
            renewed_public_remote_verifier_federation = (
                self._build_redacted_verifier_federation_summary(
                    renewed_remote_verifier_federation
                )
            )
            recovered_public_remote_verifier_federation = (
                self._build_redacted_verifier_federation_summary(
                    recovered_remote_verifier_federation
                )
            )
        initial_re_attestation_cadence = self._build_re_attestation_cadence(
            federation=initial_public_remote_verifier_federation
        )
        renewed_public_re_attestation_cadence = self._build_re_attestation_cadence(
            federation=renewed_public_remote_verifier_federation
        )
        recovered_public_re_attestation_cadence = self._build_re_attestation_cadence(
            federation=recovered_public_remote_verifier_federation
        )
        destination_lifecycle = self._build_destination_lifecycle(
            destination_snapshot_digest=destination_snapshot_digest,
            initial_federation=initial_public_remote_verifier_federation,
            initial_cadence=initial_re_attestation_cadence,
            renewed_federation=renewed_public_remote_verifier_federation,
            renewed_cadence=renewed_public_re_attestation_cadence,
            recovered_federation=recovered_public_remote_verifier_federation,
            recovered_cadence=recovered_public_re_attestation_cadence,
        )
        public_destination_lifecycle = destination_lifecycle
        if normalized_export_profile == TRUST_TRANSFER_REDACTED_EXPORT_PROFILE_ID:
            public_destination_lifecycle = self._build_redacted_destination_lifecycle_summary(
                destination_lifecycle
            )
        receipt = {
            "kind": "trust_transfer_receipt",
            "schema_version": TRUST_TRANSFER_SCHEMA_VERSION,
            "receipt_id": new_id("trust-transfer"),
            "transfer_policy_id": TRUST_TRANSFER_POLICY_ID,
            "attestation_policy_id": TRUST_TRANSFER_ATTESTATION_POLICY_ID,
            "export_profile_id": normalized_export_profile,
            "agent_id": normalized_agent_id,
            "source_substrate_ref": normalized_source_substrate,
            "destination_substrate_ref": normalized_destination_substrate,
            "destination_host_ref": normalized_destination_host,
            "transferred_at": transferred_at,
            "source_snapshot_ref": f"trust-snapshot://source/{normalized_agent_id}",
            "source_snapshot_digest": source_snapshot_digest,
            "destination_snapshot_ref": f"trust-snapshot://destination/{normalized_agent_id}",
            "destination_snapshot_digest": destination_snapshot_digest,
            "export_receipt": {
                "export_id": new_id("trust-export"),
                "export_ref": f"trust-export://{normalized_agent_id}",
                "source_policy_id": self._policy.policy_id,
                "provenance_policy_id": self._policy.provenance_policy_id,
                "threshold_digest": source_threshold_digest,
                "history_digest": source_history_digest,
                "history_commitment_digest": source_history_commitment_digest,
                "eligibility_digest": source_eligibility_digest,
                "history_event_count": len(source_snapshot["history"]),
                "council_session_ref": normalized_council_session,
                "rationale": normalized_rationale,
                "redaction_policy_id": TRUST_TRANSFER_NO_REDACTION_POLICY_ID,
                "redacted_fields": [],
            },
            "federation_attestation": {
                "attestation_id": new_id("trust-attestation"),
                "attestation_ref": f"trust-attestation://{normalized_agent_id}",
                "required_roles": list(TRUST_TRANSFER_REQUIRED_ATTESTATION_ROLES),
                "received_roles": received_roles,
                "attestors": attestors,
                "quorum": len(TRUST_TRANSFER_REQUIRED_ATTESTATION_ROLES),
                "quorum_received": len(received_roles),
                "route_ref": f"trust-transfer-route://{normalized_agent_id}",
                "route_digest": route_digest,
                "remote_verifier_federation": recovered_public_remote_verifier_federation,
                "re_attestation_cadence": recovered_public_re_attestation_cadence,
                "cross_substrate_attested": True,
            },
            "import_receipt": {
                "import_id": new_id("trust-import"),
                "import_ref": f"trust-import://{normalized_agent_id}",
                "destination_policy_id": destination_service._policy.policy_id,
                "provenance_policy_id": destination_service._policy.provenance_policy_id,
                "threshold_digest": _snapshot_threshold_digest(destination_snapshot),
                "history_digest": _snapshot_history_digest(destination_snapshot),
                "history_commitment_digest": destination_history_commitment_digest,
                "eligibility_digest": _snapshot_eligibility_digest(destination_snapshot),
                "history_event_count": len(destination_snapshot["history"]),
                "seed_mode": TRUST_TRANSFER_FULL_CLONE_EXPORT_PROFILE_ID,
                "destination_seeded": destination_service.has_agent(normalized_agent_id),
            },
            "destination_lifecycle": public_destination_lifecycle,
            "validation": {},
            "status": "imported",
            "receipt_digest": "",
        }
        if normalized_export_profile == TRUST_TRANSFER_FULL_CLONE_EXPORT_PROFILE_ID:
            receipt["source_snapshot"] = source_snapshot
            receipt["destination_snapshot"] = destination_snapshot
        else:
            receipt["export_receipt"]["redaction_policy_id"] = (
                TRUST_TRANSFER_HISTORY_REDACTION_POLICY_ID
            )
            receipt["export_receipt"]["redacted_fields"] = list(
                TRUST_TRANSFER_REDACTED_FIELDS
            )
            receipt["source_snapshot_redacted"] = self._build_redacted_snapshot_projection(
                snapshot=source_snapshot,
                snapshot_ref=str(receipt["source_snapshot_ref"]),
                snapshot_digest=str(receipt["source_snapshot_digest"]),
            )
            receipt["destination_snapshot_redacted"] = self._build_redacted_snapshot_projection(
                snapshot=destination_snapshot,
                snapshot_ref=str(receipt["destination_snapshot_ref"]),
                snapshot_digest=str(receipt["destination_snapshot_digest"]),
            )
        receipt["receipt_digest"] = sha256_text(canonical_json(_trust_transfer_digest_payload(receipt)))
        receipt["validation"] = self._transfer_validation_summary(receipt)
        validation = self.validate_transfer_receipt(receipt)
        if not validation["ok"]:
            raise ValueError(
                "reference trust transfer receipt failed validation: "
                + "; ".join(validation["errors"])
            )
        return receipt

    def record_event(
        self,
        agent_id: str,
        *,
        event_type: str,
        domain: str,
        severity: str = "medium",
        evidence_confidence: float = 1.0,
        triggered_by: str,
        rationale: str,
    ) -> Dict[str, Any]:
        state = self._state(agent_id)
        normalized_agent = self._normalize_non_empty(agent_id, "agent_id")
        normalized_domain = self._normalize_non_empty(domain, "domain")
        normalized_trigger = self._normalize_non_empty(triggered_by, "triggered_by")
        normalized_rationale = self._normalize_non_empty(rationale, "rationale")

        if event_type not in self._policy.base_deltas:
            raise ValueError(f"unsupported trust event_type: {event_type}")
        if severity not in self._policy.severity_multipliers:
            raise ValueError(f"unsupported trust severity: {severity}")
        if not 0.0 <= evidence_confidence <= 1.0:
            raise ValueError("evidence_confidence must be between 0.0 and 1.0")

        base_delta = self._policy.base_deltas[event_type]
        multiplier = self._policy.severity_multipliers[severity]
        raw_delta = round(base_delta * multiplier * evidence_confidence, 3)
        triggered_by_agent_id = self._resolve_registered_agent_id(normalized_trigger)
        provenance_status = self._evaluate_provenance(
            agent_id=normalized_agent,
            event_type=event_type,
            domain=normalized_domain,
            raw_delta=raw_delta,
            triggered_by=normalized_trigger,
            triggered_by_agent_id=triggered_by_agent_id,
        )
        global_before = _clamp_score(state.global_score)
        domain_before = _clamp_score(state.per_domain.get(normalized_domain, state.global_score))

        if provenance_status != "accepted":
            applied = False
            applied_delta = 0.0
            global_after = global_before
            domain_after = domain_before
        elif state.pinned_by_human:
            applied = False
            applied_delta = 0.0
            global_after = global_before
            domain_after = domain_before
        else:
            applied = True
            applied_delta = raw_delta
            global_after = _clamp_score(global_before + raw_delta)
            domain_after = _clamp_score(domain_before + raw_delta)
            state.global_score = global_after
            state.per_domain[normalized_domain] = domain_after

        event = TrustEvent(
            event_id=new_id("trust-event"),
            agent_id=agent_id,
            domain=normalized_domain,
            event_type=event_type,
            severity=severity,
            evidence_confidence=round(evidence_confidence, 3),
            raw_delta=raw_delta,
            applied_delta=applied_delta,
            applied=applied,
            triggered_by=normalized_trigger,
            triggered_by_agent_id=triggered_by_agent_id,
            rationale=normalized_rationale,
            global_before=global_before,
            global_after=global_after,
            domain_before=domain_before,
            domain_after=domain_after,
            policy_id=self._policy.policy_id,
            provenance_status=provenance_status,
            provenance_policy_id=self._policy.provenance_policy_id,
        )
        state.history.append(event)
        return event.to_dict()

    def validate_transfer_receipt(self, receipt: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        export_profile_id = receipt.get("export_profile_id")
        if receipt.get("kind") != "trust_transfer_receipt":
            errors.append("kind must equal trust_transfer_receipt")
        if receipt.get("schema_version") != TRUST_TRANSFER_SCHEMA_VERSION:
            errors.append("schema_version mismatch")
        if receipt.get("transfer_policy_id") != TRUST_TRANSFER_POLICY_ID:
            errors.append("transfer_policy_id mismatch")
        if receipt.get("attestation_policy_id") != TRUST_TRANSFER_ATTESTATION_POLICY_ID:
            errors.append("attestation_policy_id mismatch")
        if export_profile_id not in TRUST_TRANSFER_SUPPORTED_EXPORT_PROFILES:
            errors.append("export_profile_id mismatch")

        self._require_mapping_field(receipt.get("export_receipt"), "export_receipt", errors)
        self._require_mapping_field(
            receipt.get("federation_attestation"),
            "federation_attestation",
            errors,
        )
        self._require_mapping_field(receipt.get("import_receipt"), "import_receipt", errors)
        self._require_mapping_field(
            receipt.get("destination_lifecycle"),
            "destination_lifecycle",
            errors,
        )
        self._require_mapping_field(receipt.get("validation"), "validation", errors)
        self._require_non_empty_string(receipt.get("receipt_id"), "receipt_id", errors)
        self._require_non_empty_string(receipt.get("agent_id"), "agent_id", errors)
        self._require_non_empty_string(
            receipt.get("source_substrate_ref"),
            "source_substrate_ref",
            errors,
        )
        self._require_non_empty_string(
            receipt.get("destination_substrate_ref"),
            "destination_substrate_ref",
            errors,
        )
        self._require_non_empty_string(
            receipt.get("destination_host_ref"),
            "destination_host_ref",
            errors,
        )
        self._require_non_empty_string(receipt.get("transferred_at"), "transferred_at", errors)
        self._require_non_empty_string(
            receipt.get("source_snapshot_ref"),
            "source_snapshot_ref",
            errors,
        )
        self._require_non_empty_string(
            receipt.get("destination_snapshot_ref"),
            "destination_snapshot_ref",
            errors,
        )
        source_snapshot: Optional[Mapping[str, Any]] = None
        destination_snapshot: Optional[Mapping[str, Any]] = None
        if export_profile_id == TRUST_TRANSFER_FULL_CLONE_EXPORT_PROFILE_ID:
            source_snapshot, source_snapshot_errors = self._snapshot_payload_errors(
                receipt.get("source_snapshot"),
                "source_snapshot",
            )
            destination_snapshot, destination_snapshot_errors = self._snapshot_payload_errors(
                receipt.get("destination_snapshot"),
                "destination_snapshot",
            )
            errors.extend(source_snapshot_errors)
            errors.extend(destination_snapshot_errors)
            if "source_snapshot_redacted" in receipt or "destination_snapshot_redacted" in receipt:
                errors.append(
                    "redacted snapshot projections are only supported for the redacted export profile"
                )
        elif export_profile_id == TRUST_TRANSFER_REDACTED_EXPORT_PROFILE_ID:
            if "source_snapshot" in receipt or "destination_snapshot" in receipt:
                errors.append(
                    "source_snapshot and destination_snapshot must be omitted for the redacted export profile"
                )
            self._require_mapping_field(
                receipt.get("source_snapshot_redacted"),
                "source_snapshot_redacted",
                errors,
            )
            self._require_mapping_field(
                receipt.get("destination_snapshot_redacted"),
                "destination_snapshot_redacted",
                errors,
            )
            for field_name, expected_ref_field, expected_digest_field in (
                (
                    "source_snapshot_redacted",
                    "source_snapshot_ref",
                    "source_snapshot_digest",
                ),
                (
                    "destination_snapshot_redacted",
                    "destination_snapshot_ref",
                    "destination_snapshot_digest",
                ),
            ):
                projection = receipt.get(field_name)
                if not isinstance(projection, Mapping):
                    continue
                if (
                    projection.get("projection_profile_id")
                    != TRUST_TRANSFER_REDACTED_SNAPSHOT_PROFILE_ID
                ):
                    errors.append(f"{field_name}.projection_profile_id mismatch")
                if (
                    projection.get("redaction_policy_id")
                    != TRUST_TRANSFER_HISTORY_REDACTION_POLICY_ID
                ):
                    errors.append(f"{field_name}.redaction_policy_id mismatch")
                if projection.get("redacted_fields") != list(TRUST_TRANSFER_REDACTED_FIELDS):
                    errors.append(f"{field_name}.redacted_fields mismatch")
                if projection.get("sealed_snapshot_ref") != receipt.get(expected_ref_field):
                    errors.append(f"{field_name}.sealed_snapshot_ref mismatch")
                if projection.get("sealed_snapshot_digest") != receipt.get(expected_digest_field):
                    errors.append(f"{field_name}.sealed_snapshot_digest mismatch")
                expected_projection_digest = _trust_transfer_redacted_snapshot_digest(projection)
                if projection.get("projection_digest") != expected_projection_digest:
                    errors.append(f"{field_name}.projection_digest mismatch")
                if not isinstance(projection.get("history_summary"), Mapping):
                    errors.append(f"{field_name}.history_summary must be a mapping")
        destination_lifecycle = receipt.get("destination_lifecycle", {})
        if isinstance(destination_lifecycle, Mapping):
            history = destination_lifecycle.get("history")
            history_summaries = destination_lifecycle.get("history_summaries")
            if isinstance(history, list):
                if export_profile_id == TRUST_TRANSFER_REDACTED_EXPORT_PROFILE_ID:
                    errors.append(
                        "destination_lifecycle.history must be omitted for the redacted export profile"
                    )
            elif isinstance(history_summaries, list):
                if export_profile_id == TRUST_TRANSFER_FULL_CLONE_EXPORT_PROFILE_ID:
                    errors.append(
                        "redacted destination lifecycle summary is only supported for the redacted export profile"
                    )
                if (
                    destination_lifecycle.get("kind")
                    != "trust_redacted_destination_lifecycle"
                ):
                    errors.append("destination_lifecycle.kind mismatch")
                if (
                    destination_lifecycle.get("schema_version")
                    != TRUST_TRANSFER_REDACTED_DESTINATION_LIFECYCLE_SCHEMA_VERSION
                ):
                    errors.append("destination_lifecycle.schema_version mismatch")
                if (
                    destination_lifecycle.get("summary_profile_id")
                    != TRUST_TRANSFER_REDACTED_DESTINATION_LIFECYCLE_PROFILE_ID
                ):
                    errors.append("destination_lifecycle.summary_profile_id mismatch")
                if (
                    destination_lifecycle.get("lifecycle_policy_id")
                    != TRUST_TRANSFER_DESTINATION_LIFECYCLE_POLICY_ID
                ):
                    errors.append("destination_lifecycle.lifecycle_policy_id mismatch")
                if (
                    destination_lifecycle.get("revocation_fail_closed_action")
                    != TRUST_TRANSFER_DESTINATION_REVOCATION_FAIL_CLOSED_ACTION
                ):
                    errors.append(
                        "destination_lifecycle.revocation_fail_closed_action mismatch"
                    )
                if (
                    destination_lifecycle.get("redaction_policy_id")
                    != TRUST_TRANSFER_DESTINATION_LIFECYCLE_SUMMARY_REDACTION_POLICY_ID
                ):
                    errors.append("destination_lifecycle.redaction_policy_id mismatch")
                if destination_lifecycle.get("redacted_fields") != list(
                    TRUST_TRANSFER_REDACTED_DESTINATION_LIFECYCLE_FIELDS
                ):
                    errors.append("destination_lifecycle.redacted_fields mismatch")
                summary_items = [
                    item for item in history_summaries if isinstance(item, Mapping)
                ]
                if len(summary_items) != len(history_summaries):
                    errors.append(
                        "destination_lifecycle.history_summaries must contain mappings"
                    )
                for index, summary_item in enumerate(summary_items):
                    if not _trust_transfer_redacted_lifecycle_entry_quorum_bound(
                        summary_item
                    ):
                        errors.append(
                            "destination_lifecycle.history_summaries["
                            f"{index}"
                            "].quorum fields mismatch"
                        )
                    expected_entry_digest = (
                        _trust_transfer_redacted_destination_lifecycle_entry_summary_digest(
                            summary_item
                        )
                    )
                    if summary_item.get("entry_digest") != expected_entry_digest:
                        errors.append(
                            "destination_lifecycle.history_summaries["
                            f"{index}"
                            "].entry_digest mismatch"
                        )
                expected_history_summary_commitment_digest = (
                    _trust_transfer_redacted_destination_lifecycle_history_commitment_digest(
                        summary_items
                    )
                )
                if (
                    destination_lifecycle.get("history_summary_commitment_digest")
                    != expected_history_summary_commitment_digest
                ):
                    errors.append(
                        "destination_lifecycle.history_summary_commitment_digest mismatch"
                    )
                try:
                    expected_summary_digest = sha256_text(
                        canonical_json(
                            _trust_transfer_redacted_destination_lifecycle_digest_payload(
                                destination_lifecycle
                            )
                        )
                    )
                except KeyError:
                    errors.append("destination_lifecycle.summary_digest mismatch")
                else:
                    if destination_lifecycle.get("summary_digest") != expected_summary_digest:
                        errors.append("destination_lifecycle.summary_digest mismatch")
                self._require_non_empty_string(
                    destination_lifecycle.get("sealed_lifecycle_digest"),
                    "destination_lifecycle.sealed_lifecycle_digest",
                    errors,
                )
            else:
                errors.append(
                    "destination_lifecycle must expose history or history_summaries"
                )

        summary = self._transfer_validation_summary(receipt)
        if receipt.get("validation") != summary:
            errors.append("validation must match the computed transfer validation summary")
        if receipt.get("receipt_digest") != sha256_text(canonical_json(_trust_transfer_digest_payload(receipt))):
            errors.append("receipt_digest must bind the fixed transfer digest payload")
        if not summary["export_profile_bound"]:
            errors.append("export_profile_id must bind the fixed trust transfer export profile")
        if not summary["history_commitment_bound"]:
            errors.append("history commitment digests must stay aligned with the export profile")
        if not summary["remote_verifier_disclosure_bound"]:
            errors.append(
                "remote verifier federation must match the selected public disclosure profile"
            )
        if not summary["destination_lifecycle_disclosure_bound"]:
            errors.append(
                "destination_lifecycle must match the selected public disclosure profile"
            )
        if not summary["recovery_quorum_bound"]:
            errors.append(
                "recovery quorum must satisfy the multi-root, cross-jurisdiction contract"
            )

        if isinstance(source_snapshot, Mapping) and isinstance(destination_snapshot, Mapping):
            if receipt.get("agent_id") != source_snapshot.get("agent_id"):
                errors.append("agent_id must match source_snapshot.agent_id")
            if receipt.get("agent_id") != destination_snapshot.get("agent_id"):
                errors.append("agent_id must match destination_snapshot.agent_id")
            if receipt.get("source_snapshot_digest") != sha256_text(canonical_json(source_snapshot)):
                errors.append("source_snapshot_digest must match source_snapshot")
            if receipt.get("destination_snapshot_digest") != sha256_text(
                canonical_json(destination_snapshot)
            ):
                errors.append("destination_snapshot_digest must match destination_snapshot")

        export_receipt = receipt.get("export_receipt", {})
        if isinstance(export_receipt, Mapping):
            if export_receipt.get("source_policy_id") != self._policy.policy_id:
                errors.append("export_receipt.source_policy_id mismatch")
            if export_receipt.get("provenance_policy_id") != self._policy.provenance_policy_id:
                errors.append("export_receipt.provenance_policy_id mismatch")
            self._require_non_empty_string(
                export_receipt.get("history_commitment_digest"),
                "export_receipt.history_commitment_digest",
                errors,
            )
            self._require_non_empty_string(
                export_receipt.get("council_session_ref"),
                "export_receipt.council_session_ref",
                errors,
            )
            self._require_non_empty_string(
                export_receipt.get("rationale"),
                "export_receipt.rationale",
                errors,
            )

        import_receipt = receipt.get("import_receipt", {})
        if isinstance(import_receipt, Mapping):
            if import_receipt.get("destination_policy_id") != self._policy.policy_id:
                errors.append("import_receipt.destination_policy_id mismatch")
            if import_receipt.get("provenance_policy_id") != self._policy.provenance_policy_id:
                errors.append("import_receipt.provenance_policy_id mismatch")
            self._require_non_empty_string(
                import_receipt.get("history_commitment_digest"),
                "import_receipt.history_commitment_digest",
                errors,
            )
            if import_receipt.get("seed_mode") != TRUST_TRANSFER_FULL_CLONE_EXPORT_PROFILE_ID:
                errors.append("import_receipt.seed_mode mismatch")
            if import_receipt.get("destination_seeded") is not True:
                errors.append("import_receipt.destination_seeded must be true")

        destination_lifecycle = receipt.get("destination_lifecycle", {})
        if isinstance(destination_lifecycle, Mapping) and isinstance(
            destination_lifecycle.get("history"), list
        ):
            if (
                destination_lifecycle.get("lifecycle_policy_id")
                != TRUST_TRANSFER_DESTINATION_LIFECYCLE_POLICY_ID
            ):
                errors.append("destination_lifecycle.lifecycle_policy_id mismatch")
            if (
                destination_lifecycle.get("revocation_fail_closed_action")
                != TRUST_TRANSFER_DESTINATION_REVOCATION_FAIL_CLOSED_ACTION
            ):
                errors.append("destination_lifecycle.revocation_fail_closed_action mismatch")
            try:
                expected_lifecycle_digest = sha256_text(
                    canonical_json(
                        _trust_transfer_destination_lifecycle_digest_payload(destination_lifecycle)
                    )
                )
            except KeyError:
                errors.append("destination_lifecycle.lifecycle_digest mismatch")
            else:
                if destination_lifecycle.get("lifecycle_digest") != expected_lifecycle_digest:
                    errors.append("destination_lifecycle.lifecycle_digest mismatch")

        federation_attestation = receipt.get("federation_attestation", {})
        if isinstance(federation_attestation, Mapping):
            required_roles = federation_attestation.get("required_roles")
            if required_roles != list(TRUST_TRANSFER_REQUIRED_ATTESTATION_ROLES):
                errors.append("federation_attestation.required_roles mismatch")
            attestors = federation_attestation.get("attestors", [])
            if not isinstance(attestors, list) or len(attestors) != len(
                TRUST_TRANSFER_REQUIRED_ATTESTATION_ROLES
            ):
                errors.append("federation_attestation.attestors must cover the fixed attestation roles")
            if federation_attestation.get("cross_substrate_attested") is not True:
                errors.append("federation_attestation.cross_substrate_attested must be true")
            if federation_attestation.get("route_digest") != sha256_text(
                canonical_json(_trust_transfer_route_digest_payload(receipt))
            ):
                errors.append("federation_attestation.route_digest mismatch")
            received_roles = federation_attestation.get("received_roles", [])
            if received_roles != [
                attestor.get("role")
                for attestor in attestors
                if isinstance(attestor, Mapping) and attestor.get("status") == "attested"
            ]:
                errors.append("federation_attestation.received_roles mismatch")
            remote_verifier_federation = federation_attestation.get(
                "remote_verifier_federation",
                {},
            )
            if not isinstance(remote_verifier_federation, Mapping):
                errors.append("federation_attestation.remote_verifier_federation must be a mapping")
            else:
                if (
                    remote_verifier_federation.get("federation_policy_id")
                    != TRUST_TRANSFER_REMOTE_VERIFIER_FEDERATION_POLICY_ID
                ):
                    errors.append(
                        "federation_attestation.remote_verifier_federation."
                        "federation_policy_id mismatch"
                    )
                if (
                    remote_verifier_federation.get("network_profile_id")
                    != TRUST_TRANSFER_REMOTE_VERIFIER_NETWORK_PROFILE_ID
                ):
                    errors.append(
                        "federation_attestation.remote_verifier_federation."
                        "network_profile_id mismatch"
                    )
                verifier_receipts = remote_verifier_federation.get("verifier_receipts")
                verifier_receipt_summaries = remote_verifier_federation.get(
                    "verifier_receipt_summaries"
                )
                quorum_policy_id = str(
                    remote_verifier_federation.get("quorum_policy_id", "")
                )
                quorum_spec = _trust_transfer_quorum_policy_spec(quorum_policy_id)
                if quorum_spec is None:
                    errors.append(
                        "federation_attestation.remote_verifier_federation.quorum_policy_id mismatch"
                    )
                else:
                    if remote_verifier_federation.get("required_verifier_count") != int(
                        quorum_spec["required_verifier_count"]
                    ):
                        errors.append(
                            "federation_attestation.remote_verifier_federation."
                            "required_verifier_count mismatch"
                        )
                    if remote_verifier_federation.get("trust_root_quorum") != int(
                        quorum_spec["trust_root_quorum"]
                    ):
                        errors.append(
                            "federation_attestation.remote_verifier_federation."
                            "trust_root_quorum mismatch"
                        )
                    if remote_verifier_federation.get("jurisdiction_quorum") != int(
                        quorum_spec["jurisdiction_quorum"]
                    ):
                        errors.append(
                            "federation_attestation.remote_verifier_federation."
                            "jurisdiction_quorum mismatch"
                        )
                if isinstance(verifier_receipts, list):
                    if export_profile_id == TRUST_TRANSFER_REDACTED_EXPORT_PROFILE_ID:
                        errors.append(
                            "federation_attestation.remote_verifier_federation.verifier_receipts "
                            "must be omitted for the redacted export profile"
                        )
                    if remote_verifier_federation.get("received_verifier_count") != len(
                        verifier_receipts
                    ):
                        errors.append(
                            "federation_attestation.remote_verifier_federation."
                            "received_verifier_count mismatch"
                        )
                    expected_jurisdictions = sorted(
                        {
                            verifier_receipt.get("jurisdiction")
                            for verifier_receipt in verifier_receipts
                            if isinstance(verifier_receipt, Mapping)
                        }
                    )
                    if remote_verifier_federation.get("jurisdictions") != expected_jurisdictions:
                        errors.append(
                            "federation_attestation.remote_verifier_federation."
                            "jurisdictions mismatch"
                        )
                    expected_binding_digest = _trust_transfer_remote_reviewer_binding_digest(
                        human_reviewer_ref=str(
                            remote_verifier_federation.get("human_reviewer_ref", "")
                        ),
                        route_digest=str(federation_attestation.get("route_digest", "")),
                        verifier_receipts=[
                            verifier_receipt
                            for verifier_receipt in verifier_receipts
                            if isinstance(verifier_receipt, Mapping)
                        ],
                    )
                    if (
                        remote_verifier_federation.get("reviewer_binding_digest")
                        != expected_binding_digest
                    ):
                        errors.append(
                            "federation_attestation.remote_verifier_federation."
                            "reviewer_binding_digest mismatch"
                        )
                    if remote_verifier_federation.get("receipt_digest") != sha256_text(
                        canonical_json(
                            _trust_transfer_remote_verifier_federation_digest_payload(
                                remote_verifier_federation
                            )
                        )
                    ):
                        errors.append(
                            "federation_attestation.remote_verifier_federation.receipt_digest mismatch"
                        )
                elif isinstance(verifier_receipt_summaries, list):
                    if export_profile_id == TRUST_TRANSFER_FULL_CLONE_EXPORT_PROFILE_ID:
                        errors.append(
                            "redacted verifier federation summary is only supported for the redacted export profile"
                        )
                    if (
                        remote_verifier_federation.get("summary_profile_id")
                        != TRUST_TRANSFER_REDACTED_VERIFIER_FEDERATION_PROFILE_ID
                    ):
                        errors.append(
                            "federation_attestation.remote_verifier_federation.summary_profile_id mismatch"
                        )
                    if (
                        remote_verifier_federation.get("redaction_policy_id")
                        != TRUST_TRANSFER_VERIFIER_SUMMARY_REDACTION_POLICY_ID
                    ):
                        errors.append(
                            "federation_attestation.remote_verifier_federation.redaction_policy_id mismatch"
                        )
                    if remote_verifier_federation.get("redacted_fields") != list(
                        TRUST_TRANSFER_REDACTED_VERIFIER_FIELDS
                    ):
                        errors.append(
                            "federation_attestation.remote_verifier_federation.redacted_fields mismatch"
                        )
                    if remote_verifier_federation.get("received_verifier_count") != len(
                        verifier_receipt_summaries
                    ):
                        errors.append(
                            "federation_attestation.remote_verifier_federation."
                            "received_verifier_count mismatch"
                        )
                    expected_jurisdictions = sorted(
                        {
                            summary_item.get("jurisdiction")
                            for summary_item in verifier_receipt_summaries
                            if isinstance(summary_item, Mapping)
                        }
                    )
                    if remote_verifier_federation.get("jurisdictions") != expected_jurisdictions:
                        errors.append(
                            "federation_attestation.remote_verifier_federation."
                            "jurisdictions mismatch"
                        )
                    for index, summary_item in enumerate(verifier_receipt_summaries):
                        if not isinstance(summary_item, Mapping):
                            errors.append(
                                "federation_attestation.remote_verifier_federation."
                                "verifier_receipt_summaries must contain mappings"
                            )
                            continue
                        if (
                            summary_item.get("summary_profile_id")
                            != TRUST_TRANSFER_REDACTED_VERIFIER_RECEIPT_SUMMARY_PROFILE_ID
                        ):
                            errors.append(
                                "federation_attestation.remote_verifier_federation."
                                f"verifier_receipt_summaries[{index}].summary_profile_id mismatch"
                            )
                        if (
                            summary_item.get("redaction_policy_id")
                            != TRUST_TRANSFER_VERIFIER_SUMMARY_REDACTION_POLICY_ID
                        ):
                            errors.append(
                                "federation_attestation.remote_verifier_federation."
                                f"verifier_receipt_summaries[{index}].redaction_policy_id mismatch"
                            )
                        if summary_item.get("redacted_fields") != list(
                            TRUST_TRANSFER_REDACTED_VERIFIER_FIELDS
                        ):
                            errors.append(
                                "federation_attestation.remote_verifier_federation."
                                f"verifier_receipt_summaries[{index}].redacted_fields mismatch"
                            )
                        expected_summary_digest = (
                            _trust_transfer_redacted_verifier_receipt_summary_digest(
                                summary_item
                            )
                        )
                        if summary_item.get("summary_digest") != expected_summary_digest:
                            errors.append(
                                "federation_attestation.remote_verifier_federation."
                                f"verifier_receipt_summaries[{index}].summary_digest mismatch"
                            )
                    expected_binding_digest = _trust_transfer_remote_reviewer_binding_digest(
                        human_reviewer_ref=str(
                            remote_verifier_federation.get("human_reviewer_ref", "")
                        ),
                        route_digest=str(federation_attestation.get("route_digest", "")),
                        verifier_receipts=[
                            summary_item
                            for summary_item in verifier_receipt_summaries
                            if isinstance(summary_item, Mapping)
                        ],
                    )
                    if (
                        remote_verifier_federation.get("reviewer_binding_digest")
                        != expected_binding_digest
                    ):
                        errors.append(
                            "federation_attestation.remote_verifier_federation."
                            "reviewer_binding_digest mismatch"
                        )
                    expected_commitment_digest = (
                        _trust_transfer_redacted_verifier_receipt_commitment_digest(
                            [
                                summary_item
                                for summary_item in verifier_receipt_summaries
                                if isinstance(summary_item, Mapping)
                            ]
                        )
                    )
                    if (
                        remote_verifier_federation.get("verifier_receipt_commitment_digest")
                        != expected_commitment_digest
                    ):
                        errors.append(
                            "federation_attestation.remote_verifier_federation."
                            "verifier_receipt_commitment_digest mismatch"
                        )
                    expected_federation_digest = sha256_text(
                        canonical_json(
                            _trust_transfer_redacted_verifier_federation_digest_payload(
                                remote_verifier_federation
                            )
                        )
                    )
                    if remote_verifier_federation.get("receipt_digest") != expected_federation_digest:
                        errors.append(
                            "federation_attestation.remote_verifier_federation.receipt_digest mismatch"
                        )
                    self._require_non_empty_string(
                        remote_verifier_federation.get("sealed_federation_digest"),
                        "federation_attestation.remote_verifier_federation.sealed_federation_digest",
                        errors,
                    )
                else:
                    errors.append(
                        "federation_attestation.remote_verifier_federation must expose verifier_receipts or verifier_receipt_summaries"
                    )
            re_attestation_cadence = federation_attestation.get("re_attestation_cadence", {})
            if not isinstance(re_attestation_cadence, Mapping):
                errors.append("federation_attestation.re_attestation_cadence must be a mapping")
            else:
                if (
                    re_attestation_cadence.get("cadence_policy_id")
                    != TRUST_TRANSFER_REATTESTATION_CADENCE_POLICY_ID
                ):
                    errors.append(
                        "federation_attestation.re_attestation_cadence.cadence_policy_id mismatch"
                    )
                if re_attestation_cadence.get("grace_window_seconds") != (
                    TRUST_TRANSFER_REATTESTATION_GRACE_WINDOW_SECONDS
                ):
                    errors.append(
                        "federation_attestation.re_attestation_cadence.grace_window_seconds mismatch"
                    )
                if re_attestation_cadence.get("receipt_digest") != sha256_text(
                    canonical_json(
                        _trust_transfer_re_attestation_cadence_digest_payload(
                            re_attestation_cadence
                        )
                    )
                ):
                    errors.append(
                        "federation_attestation.re_attestation_cadence.receipt_digest mismatch"
                    )

        ok = not errors and summary["ok"]
        return {
            **summary,
            "ok": ok,
            "errors": errors,
        }

    def _state(self, agent_id: str) -> AgentTrustState:
        agent_key = self._normalize_non_empty(agent_id, "agent_id")
        if agent_key not in self._states:
            self.register_agent(agent_key)
        return self._states[agent_key]

    def _evaluate_provenance(
        self,
        *,
        agent_id: str,
        event_type: str,
        domain: str,
        raw_delta: float,
        triggered_by: str,
        triggered_by_agent_id: str,
    ) -> str:
        if raw_delta <= 0:
            return self._check_event_origin(event_type, triggered_by, triggered_by_agent_id)

        if self._same_actor(agent_id, triggered_by, triggered_by_agent_id):
            return "blocked-self-issued-positive"

        origin_status = self._check_event_origin(event_type, triggered_by, triggered_by_agent_id)
        if origin_status != "accepted":
            return origin_status

        if triggered_by_agent_id and self._has_reciprocal_positive_history(
            agent_id=agent_id,
            evaluator_agent_id=triggered_by_agent_id,
            domain=domain,
        ):
            return "blocked-reciprocal-positive"
        return "accepted"

    def _check_event_origin(
        self,
        event_type: str,
        triggered_by: str,
        triggered_by_agent_id: str,
    ) -> str:
        expected_origin = self._policy.event_origin_requirements.get(event_type, "any")
        if expected_origin == "any":
            return "accepted"
        if expected_origin == "council":
            return (
                "accepted"
                if _actor_fingerprint(triggered_by) == "council"
                else "blocked-provenance-mismatch"
            )
        if expected_origin == "guardian":
            if triggered_by_agent_id and self._is_guardian_authority(triggered_by_agent_id):
                return "accepted"
            return "blocked-provenance-mismatch"
        if expected_origin == "human":
            if _actor_fingerprint(triggered_by) == "council" or triggered_by_agent_id:
                return "blocked-provenance-mismatch"
            return "accepted"
        return "accepted"

    def _resolve_registered_agent_id(self, actor: str) -> str:
        actor_fingerprint = _actor_fingerprint(actor)
        for registered_agent_id in self._states:
            if _actor_fingerprint(registered_agent_id) == actor_fingerprint:
                return registered_agent_id
        return ""

    def _is_guardian_authority(self, agent_id: str) -> bool:
        state = self._states.get(agent_id)
        if state is None:
            return False
        return bool(state.to_dict(self._thresholds)["eligibility"]["guardian_role"])

    def _has_reciprocal_positive_history(
        self,
        *,
        agent_id: str,
        evaluator_agent_id: str,
        domain: str,
    ) -> bool:
        evaluator_state = self._states.get(evaluator_agent_id)
        if evaluator_state is None:
            return False
        for event in evaluator_state.history:
            if (
                event.domain == domain
                and event.raw_delta > 0
                and event.provenance_status == "accepted"
                and event.triggered_by_agent_id
                and self._same_actor(agent_id, event.triggered_by, event.triggered_by_agent_id)
            ):
                return True
        return False

    def _snapshot_state_from_mapping(
        self,
        snapshot: Mapping[str, Any] | Any,
    ) -> tuple[Optional[AgentTrustState], List[str]]:
        errors: List[str] = []
        if not isinstance(snapshot, Mapping):
            return None, ["snapshot must be a mapping"]

        agent_id = snapshot.get("agent_id")
        if not isinstance(agent_id, str) or not agent_id.strip():
            errors.append("snapshot.agent_id must be a non-empty string")
            normalized_agent_id = ""
        else:
            normalized_agent_id = agent_id.strip()

        try:
            global_score = _clamp_score(float(snapshot.get("global_score", 0.0)))
        except (TypeError, ValueError):
            errors.append("snapshot.global_score must be numeric")
            global_score = 0.0

        raw_per_domain = snapshot.get("per_domain")
        if not isinstance(raw_per_domain, Mapping):
            errors.append("snapshot.per_domain must be a mapping")
            per_domain: Dict[str, float] = {}
        else:
            per_domain = {}
            for domain, score in sorted(raw_per_domain.items()):
                if not isinstance(domain, str) or not domain.strip():
                    errors.append("snapshot.per_domain keys must be non-empty strings")
                    continue
                try:
                    per_domain[domain.strip()] = _clamp_score(float(score))
                except (TypeError, ValueError):
                    errors.append(
                        f"snapshot.per_domain.{domain} must be numeric within the trust range"
                    )

        raw_history = snapshot.get("history")
        if not isinstance(raw_history, list):
            errors.append("snapshot.history must be a list")
            raw_history = []
        history: List[TrustEvent] = []
        for index, event_payload in enumerate(raw_history):
            if not isinstance(event_payload, Mapping):
                errors.append(f"snapshot.history[{index}] must be a mapping")
                continue
            try:
                event = TrustEvent(**dict(event_payload))
            except TypeError as exc:
                errors.append(f"snapshot.history[{index}] is invalid: {exc}")
                continue
            if normalized_agent_id and event.agent_id != normalized_agent_id:
                errors.append(
                    f"snapshot.history[{index}].agent_id must match snapshot.agent_id"
                )
            if event.policy_id != self._policy.policy_id:
                errors.append(
                    f"snapshot.history[{index}].policy_id must equal {self._policy.policy_id}"
                )
            if event.provenance_policy_id != self._policy.provenance_policy_id:
                errors.append(
                    "snapshot.history["
                    f"{index}"
                    "].provenance_policy_id must equal "
                    f"{self._policy.provenance_policy_id}"
                )
            history.append(event)

        pinned_by_human = snapshot.get("pinned_by_human")
        if not isinstance(pinned_by_human, bool):
            errors.append("snapshot.pinned_by_human must be a boolean")
            pinned_by_human = False
        pinned_reason = snapshot.get("pinned_reason")
        if not isinstance(pinned_reason, str):
            errors.append("snapshot.pinned_reason must be a string")
            pinned_reason = ""

        state = AgentTrustState(
            agent_id=normalized_agent_id,
            global_score=global_score,
            per_domain=per_domain,
            history=history,
            pinned_by_human=pinned_by_human,
            pinned_reason=pinned_reason,
        )
        expected_snapshot = state.to_dict(self._thresholds)

        if snapshot.get("kind") != "trust_snapshot":
            errors.append("snapshot.kind must equal trust_snapshot")
        if snapshot.get("schema_version") != TRUST_SNAPSHOT_SCHEMA_VERSION:
            errors.append("snapshot.schema_version mismatch")
        if snapshot.get("thresholds") != self._thresholds.to_dict():
            errors.append("snapshot.thresholds must equal the fixed trust thresholds")
        if dict(snapshot) != expected_snapshot:
            errors.append("snapshot must match the fixed trust snapshot contract")

        return state, errors

    def _snapshot_payload_errors(
        self,
        snapshot: Mapping[str, Any] | Any,
        field_name: str,
    ) -> tuple[Optional[Mapping[str, Any]], List[str]]:
        _, errors = self._snapshot_state_from_mapping(snapshot)
        return (
            snapshot if isinstance(snapshot, Mapping) else None,
            [f"{field_name}: {error}" for error in errors],
        )

    def _transfer_validation_summary(self, receipt: Mapping[str, Any]) -> Dict[str, Any]:
        export_profile_id = receipt.get("export_profile_id")
        source_snapshot = receipt.get("source_snapshot")
        destination_snapshot = receipt.get("destination_snapshot")
        source_snapshot_redacted = receipt.get("source_snapshot_redacted")
        destination_snapshot_redacted = receipt.get("destination_snapshot_redacted")
        export_receipt = receipt.get("export_receipt", {})
        import_receipt = receipt.get("import_receipt", {})
        federation_attestation = receipt.get("federation_attestation", {})
        destination_lifecycle = receipt.get("destination_lifecycle", {})
        expected_redacted_fields = list(TRUST_TRANSFER_REDACTED_FIELDS)
        source_snapshot_digest_bound = False
        destination_snapshot_digest_bound = False
        export_profile_bound = False
        history_commitment_bound = False
        history_preserved = False
        thresholds_preserved = False
        provenance_policy_preserved = isinstance(export_receipt, Mapping) and isinstance(
            import_receipt,
            Mapping,
        ) and (
            export_receipt.get("provenance_policy_id")
            == import_receipt.get("provenance_policy_id")
            == self._policy.provenance_policy_id
        )
        eligibility_preserved = False
        if (
            export_profile_id == TRUST_TRANSFER_FULL_CLONE_EXPORT_PROFILE_ID
            and isinstance(source_snapshot, Mapping)
            and isinstance(destination_snapshot, Mapping)
        ):
            source_snapshot_digest_bound = receipt.get("source_snapshot_digest") == sha256_text(
                canonical_json(source_snapshot)
            )
            destination_snapshot_digest_bound = receipt.get(
                "destination_snapshot_digest"
            ) == sha256_text(canonical_json(destination_snapshot))
            history_commitment_bound = (
                isinstance(export_receipt, Mapping)
                and isinstance(import_receipt, Mapping)
                and export_receipt.get("redaction_policy_id")
                == TRUST_TRANSFER_NO_REDACTION_POLICY_ID
                and export_receipt.get("redacted_fields") == []
                and export_receipt.get("history_commitment_digest")
                == _trust_transfer_history_commitment_digest(source_snapshot)
                and import_receipt.get("history_commitment_digest")
                == _trust_transfer_history_commitment_digest(destination_snapshot)
                and export_receipt.get("history_commitment_digest")
                == import_receipt.get("history_commitment_digest")
            )
            export_profile_bound = (
                "source_snapshot_redacted" not in receipt
                and "destination_snapshot_redacted" not in receipt
                and history_commitment_bound
            )
            history_preserved = (
                source_snapshot.get("history") == destination_snapshot.get("history")
                and isinstance(export_receipt, Mapping)
                and isinstance(import_receipt, Mapping)
                and export_receipt.get("history_digest") == _snapshot_history_digest(source_snapshot)
                and import_receipt.get("history_digest")
                == _snapshot_history_digest(destination_snapshot)
                and export_receipt.get("history_digest") == import_receipt.get("history_digest")
                and history_commitment_bound
            )
            thresholds_preserved = (
                source_snapshot.get("thresholds") == destination_snapshot.get("thresholds")
                and isinstance(export_receipt, Mapping)
                and isinstance(import_receipt, Mapping)
                and export_receipt.get("threshold_digest")
                == _snapshot_threshold_digest(source_snapshot)
                and import_receipt.get("threshold_digest")
                == _snapshot_threshold_digest(destination_snapshot)
                and export_receipt.get("threshold_digest")
                == import_receipt.get("threshold_digest")
            )
            eligibility_preserved = (
                source_snapshot.get("eligibility") == destination_snapshot.get("eligibility")
                and isinstance(export_receipt, Mapping)
                and isinstance(import_receipt, Mapping)
                and export_receipt.get("eligibility_digest")
                == _snapshot_eligibility_digest(source_snapshot)
                and import_receipt.get("eligibility_digest")
                == _snapshot_eligibility_digest(destination_snapshot)
                and export_receipt.get("eligibility_digest")
                == import_receipt.get("eligibility_digest")
            )
        elif (
            export_profile_id == TRUST_TRANSFER_REDACTED_EXPORT_PROFILE_ID
            and isinstance(source_snapshot_redacted, Mapping)
            and isinstance(destination_snapshot_redacted, Mapping)
        ):
            source_projection_digest = _trust_transfer_redacted_snapshot_digest(
                source_snapshot_redacted
            )
            destination_projection_digest = _trust_transfer_redacted_snapshot_digest(
                destination_snapshot_redacted
            )
            source_redacted_digest_bound = (
                source_snapshot_redacted.get("projection_digest") == source_projection_digest
            )
            destination_redacted_digest_bound = (
                destination_snapshot_redacted.get("projection_digest")
                == destination_projection_digest
            )
            source_snapshot_digest_bound = (
                source_redacted_digest_bound
                and source_snapshot_redacted.get("projection_profile_id")
                == TRUST_TRANSFER_REDACTED_SNAPSHOT_PROFILE_ID
                and source_snapshot_redacted.get("agent_id") == receipt.get("agent_id")
                and source_snapshot_redacted.get("redaction_policy_id")
                == TRUST_TRANSFER_HISTORY_REDACTION_POLICY_ID
                and source_snapshot_redacted.get("redacted_fields") == expected_redacted_fields
                and source_snapshot_redacted.get("sealed_snapshot_ref")
                == receipt.get("source_snapshot_ref")
                and source_snapshot_redacted.get("sealed_snapshot_digest")
                == receipt.get("source_snapshot_digest")
            )
            destination_snapshot_digest_bound = (
                destination_redacted_digest_bound
                and destination_snapshot_redacted.get("projection_profile_id")
                == TRUST_TRANSFER_REDACTED_SNAPSHOT_PROFILE_ID
                and destination_snapshot_redacted.get("agent_id") == receipt.get("agent_id")
                and destination_snapshot_redacted.get("redaction_policy_id")
                == TRUST_TRANSFER_HISTORY_REDACTION_POLICY_ID
                and destination_snapshot_redacted.get("redacted_fields") == expected_redacted_fields
                and destination_snapshot_redacted.get("sealed_snapshot_ref")
                == receipt.get("destination_snapshot_ref")
                and destination_snapshot_redacted.get("sealed_snapshot_digest")
                == receipt.get("destination_snapshot_digest")
            )
            source_history_summary = source_snapshot_redacted.get("history_summary", {})
            destination_history_summary = destination_snapshot_redacted.get(
                "history_summary",
                {},
            )
            history_commitment_digest = (
                source_history_summary.get("history_commitment_digest")
                if isinstance(source_history_summary, Mapping)
                else None
            )
            history_commitment_bound = (
                isinstance(export_receipt, Mapping)
                and isinstance(import_receipt, Mapping)
                and isinstance(source_history_summary, Mapping)
                and isinstance(destination_history_summary, Mapping)
                and export_receipt.get("redaction_policy_id")
                == TRUST_TRANSFER_HISTORY_REDACTION_POLICY_ID
                and export_receipt.get("redacted_fields") == expected_redacted_fields
                and history_commitment_digest
                == destination_history_summary.get("history_commitment_digest")
                == export_receipt.get("history_commitment_digest")
                == import_receipt.get("history_commitment_digest")
                and source_history_summary.get("event_count")
                == destination_history_summary.get("event_count")
                == export_receipt.get("history_event_count")
                == import_receipt.get("history_event_count")
                and source_history_summary.get("applied_event_count", 0)
                + source_history_summary.get("blocked_event_count", 0)
                == source_history_summary.get("event_count")
                and destination_history_summary.get("applied_event_count", 0)
                + destination_history_summary.get("blocked_event_count", 0)
                == destination_history_summary.get("event_count")
            )
            export_profile_bound = (
                "source_snapshot" not in receipt
                and "destination_snapshot" not in receipt
                and history_commitment_bound
            )
            history_preserved = (
                isinstance(source_history_summary, Mapping)
                and isinstance(destination_history_summary, Mapping)
                and isinstance(export_receipt, Mapping)
                and isinstance(import_receipt, Mapping)
                and export_receipt.get("history_digest") == import_receipt.get("history_digest")
                and export_receipt.get("history_event_count")
                == source_history_summary.get("event_count")
                == destination_history_summary.get("event_count")
                and history_commitment_bound
            )
            thresholds_preserved = (
                source_snapshot_redacted.get("thresholds")
                == destination_snapshot_redacted.get("thresholds")
                and isinstance(export_receipt, Mapping)
                and isinstance(import_receipt, Mapping)
                and export_receipt.get("threshold_digest") == import_receipt.get("threshold_digest")
            )
            eligibility_preserved = (
                source_snapshot_redacted.get("eligibility")
                == destination_snapshot_redacted.get("eligibility")
                and isinstance(export_receipt, Mapping)
                and isinstance(import_receipt, Mapping)
                and export_receipt.get("eligibility_digest")
                == import_receipt.get("eligibility_digest")
            )
        federation_quorum_attested = False
        live_remote_verifier_attested = False
        remote_verifier_receipts_bound = False
        remote_verifier_disclosure_bound = False
        re_attestation_cadence_bound = False
        re_attestation_current = False
        destination_lifecycle_bound = False
        destination_lifecycle_disclosure_bound = False
        destination_renewal_history_bound = False
        destination_revocation_history_bound = False
        destination_recovery_history_bound = False
        recovery_quorum_bound = False
        destination_current = False
        if isinstance(federation_attestation, Mapping):
            attestors = federation_attestation.get("attestors", [])
            received_roles = [
                attestor.get("role")
                for attestor in attestors
                if isinstance(attestor, Mapping) and attestor.get("status") == "attested"
            ]
            federation_quorum_attested = (
                federation_attestation.get("required_roles")
                == list(TRUST_TRANSFER_REQUIRED_ATTESTATION_ROLES)
                and federation_attestation.get("received_roles") == received_roles
                and federation_attestation.get("quorum")
                == len(TRUST_TRANSFER_REQUIRED_ATTESTATION_ROLES)
                and federation_attestation.get("quorum_received") == len(received_roles)
                and set(received_roles) == set(TRUST_TRANSFER_REQUIRED_ATTESTATION_ROLES)
                and federation_attestation.get("route_digest")
                == sha256_text(canonical_json(_trust_transfer_route_digest_payload(receipt)))
                and federation_attestation.get("cross_substrate_attested") is True
            )
            remote_verifier_federation = federation_attestation.get(
                "remote_verifier_federation",
                {},
            )
            re_attestation_cadence = federation_attestation.get("re_attestation_cadence", {})
            if isinstance(remote_verifier_federation, Mapping):
                verifier_entries: List[Mapping[str, Any]] = []
                verifier_refs: List[Any] = []
                if isinstance(remote_verifier_federation.get("verifier_receipts"), list):
                    verifier_entries = [
                        verifier_receipt
                        for verifier_receipt in remote_verifier_federation.get(
                            "verifier_receipts",
                            [],
                        )
                        if isinstance(verifier_receipt, Mapping)
                    ]
                    verifier_refs = [
                        verifier_receipt.get("verifier_ref")
                        for verifier_receipt in verifier_entries
                    ]
                    verifier_quorum_spec = _trust_transfer_quorum_policy_spec(
                        str(remote_verifier_federation.get("quorum_policy_id", ""))
                    )
                    required_verifier_count = (
                        int(verifier_quorum_spec["required_verifier_count"])
                        if verifier_quorum_spec is not None
                        else -1
                    )
                    live_remote_verifier_attested = (
                        remote_verifier_federation.get("federation_policy_id")
                        == TRUST_TRANSFER_REMOTE_VERIFIER_FEDERATION_POLICY_ID
                        and remote_verifier_federation.get("network_profile_id")
                        == TRUST_TRANSFER_REMOTE_VERIFIER_NETWORK_PROFILE_ID
                        and verifier_quorum_spec is not None
                        and remote_verifier_federation.get("required_verifier_count")
                        == required_verifier_count
                        and remote_verifier_federation.get("received_verifier_count")
                        == len(verifier_entries)
                        and len(verifier_entries) == required_verifier_count
                        and len(set(verifier_refs)) == required_verifier_count
                        and all(
                            verifier_receipt.get("network_profile_id")
                            == TRUST_TRANSFER_REMOTE_VERIFIER_NETWORK_PROFILE_ID
                            and verifier_receipt.get("receipt_status") == "verified"
                            and bool(verifier_receipt.get("jurisdiction"))
                            and isinstance(verifier_receipt.get("transport_exchange"), Mapping)
                            and bool(
                                verifier_receipt["transport_exchange"].get(
                                    "request_payload_digest"
                                )
                            )
                            and bool(
                                verifier_receipt["transport_exchange"].get(
                                    "response_payload_digest"
                                )
                            )
                            for verifier_receipt in verifier_entries
                        )
                    )
                    remote_verifier_receipts_bound = (
                        live_remote_verifier_attested
                        and remote_verifier_federation.get("verifier_refs") == verifier_refs
                        and remote_verifier_federation.get("trust_root_refs")
                        == sorted(
                            {
                                verifier_receipt.get("trust_root_ref")
                                for verifier_receipt in verifier_entries
                            }
                        )
                        and remote_verifier_federation.get("authority_chain_refs")
                        == sorted(
                            {
                                verifier_receipt.get("authority_chain_ref")
                                for verifier_receipt in verifier_entries
                            }
                        )
                        and remote_verifier_federation.get("jurisdictions")
                        == sorted(
                            {
                                verifier_receipt.get("jurisdiction")
                                for verifier_receipt in verifier_entries
                            }
                        )
                        and remote_verifier_federation.get("trust_root_quorum")
                        == int(verifier_quorum_spec["trust_root_quorum"])
                        and remote_verifier_federation.get("jurisdiction_quorum")
                        == int(verifier_quorum_spec["jurisdiction_quorum"])
                        and len(remote_verifier_federation.get("trust_root_refs", []))
                        >= int(verifier_quorum_spec["trust_root_quorum"])
                        and len(remote_verifier_federation.get("jurisdictions", []))
                        >= int(verifier_quorum_spec["jurisdiction_quorum"])
                        and remote_verifier_federation.get("reviewer_binding_digest")
                        == _trust_transfer_remote_reviewer_binding_digest(
                            human_reviewer_ref=str(
                                remote_verifier_federation.get("human_reviewer_ref", "")
                            ),
                            route_digest=str(federation_attestation.get("route_digest", "")),
                            verifier_receipts=verifier_entries,
                        )
                        and remote_verifier_federation.get("receipt_digest")
                        == sha256_text(
                            canonical_json(
                                _trust_transfer_remote_verifier_federation_digest_payload(
                                    remote_verifier_federation
                                )
                            )
                        )
                        and remote_verifier_federation.get("federation_status") == "verified"
                    )
                    remote_verifier_disclosure_bound = (
                        remote_verifier_receipts_bound
                        and export_profile_id == TRUST_TRANSFER_FULL_CLONE_EXPORT_PROFILE_ID
                        and "verifier_receipt_summaries" not in remote_verifier_federation
                    )
                elif isinstance(remote_verifier_federation.get("verifier_receipt_summaries"), list):
                    verifier_entries = [
                        verifier_receipt
                        for verifier_receipt in remote_verifier_federation.get(
                            "verifier_receipt_summaries",
                            [],
                        )
                        if isinstance(verifier_receipt, Mapping)
                    ]
                    verifier_refs = [
                        verifier_receipt.get("verifier_ref")
                        for verifier_receipt in verifier_entries
                    ]
                    verifier_quorum_spec = _trust_transfer_quorum_policy_spec(
                        str(remote_verifier_federation.get("quorum_policy_id", ""))
                    )
                    required_verifier_count = (
                        int(verifier_quorum_spec["required_verifier_count"])
                        if verifier_quorum_spec is not None
                        else -1
                    )
                    summary_digests_match = all(
                        verifier_receipt.get("summary_profile_id")
                        == TRUST_TRANSFER_REDACTED_VERIFIER_RECEIPT_SUMMARY_PROFILE_ID
                        and verifier_receipt.get("network_profile_id")
                        == TRUST_TRANSFER_REMOTE_VERIFIER_NETWORK_PROFILE_ID
                        and verifier_receipt.get("receipt_status") == "verified"
                        and verifier_receipt.get("redaction_policy_id")
                        == TRUST_TRANSFER_VERIFIER_SUMMARY_REDACTION_POLICY_ID
                        and verifier_receipt.get("redacted_fields")
                        == list(TRUST_TRANSFER_REDACTED_VERIFIER_FIELDS)
                        and bool(verifier_receipt.get("transport_exchange_digest"))
                        and bool(verifier_receipt.get("sealed_receipt_digest"))
                        and verifier_receipt.get("summary_digest")
                        == _trust_transfer_redacted_verifier_receipt_summary_digest(
                            verifier_receipt
                        )
                        for verifier_receipt in verifier_entries
                    )
                    live_remote_verifier_attested = (
                        remote_verifier_federation.get("federation_policy_id")
                        == TRUST_TRANSFER_REMOTE_VERIFIER_FEDERATION_POLICY_ID
                        and remote_verifier_federation.get("network_profile_id")
                        == TRUST_TRANSFER_REMOTE_VERIFIER_NETWORK_PROFILE_ID
                        and verifier_quorum_spec is not None
                        and remote_verifier_federation.get("required_verifier_count")
                        == required_verifier_count
                        and remote_verifier_federation.get("received_verifier_count")
                        == len(verifier_entries)
                        and len(verifier_entries) == required_verifier_count
                        and len(set(verifier_refs)) == required_verifier_count
                        and summary_digests_match
                    )
                    remote_verifier_receipts_bound = (
                        live_remote_verifier_attested
                        and remote_verifier_federation.get("kind")
                        == "trust_redacted_verifier_federation"
                        and remote_verifier_federation.get("schema_version")
                        == TRUST_TRANSFER_REDACTED_VERIFIER_FEDERATION_SCHEMA_VERSION
                        and remote_verifier_federation.get("summary_profile_id")
                        == TRUST_TRANSFER_REDACTED_VERIFIER_FEDERATION_PROFILE_ID
                        and remote_verifier_federation.get("redaction_policy_id")
                        == TRUST_TRANSFER_VERIFIER_SUMMARY_REDACTION_POLICY_ID
                        and remote_verifier_federation.get("redacted_fields")
                        == list(TRUST_TRANSFER_REDACTED_VERIFIER_FIELDS)
                        and remote_verifier_federation.get("verifier_refs") == verifier_refs
                        and remote_verifier_federation.get("trust_root_refs")
                        == sorted(
                            {
                                verifier_receipt.get("trust_root_ref")
                                for verifier_receipt in verifier_entries
                            }
                        )
                        and remote_verifier_federation.get("authority_chain_refs")
                        == sorted(
                            {
                                verifier_receipt.get("authority_chain_ref")
                                for verifier_receipt in verifier_entries
                            }
                        )
                        and remote_verifier_federation.get("jurisdictions")
                        == sorted(
                            {
                                verifier_receipt.get("jurisdiction")
                                for verifier_receipt in verifier_entries
                            }
                        )
                        and remote_verifier_federation.get("trust_root_quorum")
                        == int(verifier_quorum_spec["trust_root_quorum"])
                        and remote_verifier_federation.get("jurisdiction_quorum")
                        == int(verifier_quorum_spec["jurisdiction_quorum"])
                        and len(remote_verifier_federation.get("trust_root_refs", []))
                        >= int(verifier_quorum_spec["trust_root_quorum"])
                        and len(remote_verifier_federation.get("jurisdictions", []))
                        >= int(verifier_quorum_spec["jurisdiction_quorum"])
                        and remote_verifier_federation.get("reviewer_binding_digest")
                        == _trust_transfer_remote_reviewer_binding_digest(
                            human_reviewer_ref=str(
                                remote_verifier_federation.get("human_reviewer_ref", "")
                            ),
                            route_digest=str(federation_attestation.get("route_digest", "")),
                            verifier_receipts=verifier_entries,
                        )
                        and remote_verifier_federation.get(
                            "verifier_receipt_commitment_digest"
                        )
                        == _trust_transfer_redacted_verifier_receipt_commitment_digest(
                            verifier_entries
                        )
                        and bool(remote_verifier_federation.get("sealed_federation_digest"))
                        and remote_verifier_federation.get("receipt_digest")
                        == sha256_text(
                            canonical_json(
                                _trust_transfer_redacted_verifier_federation_digest_payload(
                                    remote_verifier_federation
                                )
                            )
                        )
                        and remote_verifier_federation.get("federation_status") == "verified"
                    )
                    remote_verifier_disclosure_bound = (
                        remote_verifier_receipts_bound
                        and export_profile_id == TRUST_TRANSFER_REDACTED_EXPORT_PROFILE_ID
                        and "verifier_receipts" not in remote_verifier_federation
                    )
                if remote_verifier_receipts_bound and isinstance(re_attestation_cadence, Mapping):
                    try:
                        attested_at = max(
                            _parse_datetime(
                                str(verifier_receipt.get("recorded_at", "")),
                                "remote_verifier_receipts[].recorded_at",
                            )
                            for verifier_receipt in verifier_entries
                        )
                        valid_until = min(
                            _parse_datetime(
                                str(verifier_receipt.get("recorded_at", "")),
                                "remote_verifier_receipts[].recorded_at",
                            )
                            + timedelta(
                                seconds=int(verifier_receipt.get("freshness_window_seconds", 0))
                            )
                            for verifier_receipt in verifier_entries
                        )
                        renew_after = attested_at + timedelta(
                            seconds=TRUST_TRANSFER_REATTESTATION_INTERVAL_SECONDS
                        )
                        re_attestation_cadence_bound = (
                            re_attestation_cadence.get("cadence_policy_id")
                            == TRUST_TRANSFER_REATTESTATION_CADENCE_POLICY_ID
                            and re_attestation_cadence.get("attested_at")
                            == attested_at.isoformat()
                            and re_attestation_cadence.get("renew_after")
                            == renew_after.isoformat()
                            and re_attestation_cadence.get("valid_until")
                            == valid_until.isoformat()
                            and re_attestation_cadence.get("grace_window_seconds")
                            == TRUST_TRANSFER_REATTESTATION_GRACE_WINDOW_SECONDS
                            and re_attestation_cadence.get("covered_verifier_receipt_ids")
                            == [
                                verifier_receipt.get("receipt_id")
                                for verifier_receipt in verifier_entries
                            ]
                            and re_attestation_cadence.get("bound_federation_ref")
                            == remote_verifier_federation.get("federation_ref")
                            and re_attestation_cadence.get("bound_federation_digest")
                            == _trust_transfer_federation_binding_digest(
                                remote_verifier_federation
                            )
                            and re_attestation_cadence.get("receipt_digest")
                            == sha256_text(
                                canonical_json(
                                    _trust_transfer_re_attestation_cadence_digest_payload(
                                        re_attestation_cadence
                                    )
                                )
                            )
                        )
                        re_attestation_current = (
                            re_attestation_cadence_bound
                            and renew_after
                            + timedelta(
                                seconds=TRUST_TRANSFER_REATTESTATION_GRACE_WINDOW_SECONDS
                            )
                            <= valid_until
                            and re_attestation_cadence.get("cadence_status") == "scheduled"
                        )
                    except (TypeError, ValueError):
                        re_attestation_cadence_bound = False
                        re_attestation_current = False
        if isinstance(destination_lifecycle, Mapping):
            remote_verifier_federation = (
                federation_attestation.get("remote_verifier_federation", {})
                if isinstance(federation_attestation, Mapping)
                else {}
            )
            re_attestation_cadence = (
                federation_attestation.get("re_attestation_cadence", {})
                if isinstance(federation_attestation, Mapping)
                else {}
            )
            cadence_receipt_ids = (
                re_attestation_cadence.get("covered_verifier_receipt_ids")
                if isinstance(re_attestation_cadence, Mapping)
                else None
            )
            current_verifier_receipt_commitment_digest = None
            if (
                isinstance(cadence_receipt_ids, list)
                and len(cadence_receipt_ids) >= TRUST_TRANSFER_REQUIRED_REMOTE_VERIFIER_COUNT
                and all(
                    isinstance(receipt_id, str) and receipt_id.strip()
                    for receipt_id in cadence_receipt_ids
                )
            ):
                current_verifier_receipt_commitment_digest = (
                    _trust_transfer_covered_verifier_receipt_commitment_digest(
                        [str(receipt_id) for receipt_id in cadence_receipt_ids]
                    )
                )
            history = destination_lifecycle.get("history")
            history_summaries = destination_lifecycle.get("history_summaries")
            if isinstance(history, list):
                history_entries = [
                    entry for entry in history if isinstance(entry, Mapping)
                ]
                final_entry = history_entries[-1] if len(history_entries) == len(history) and history_entries else None
                try:
                    lifecycle_digest = sha256_text(
                        canonical_json(
                            _trust_transfer_destination_lifecycle_digest_payload(destination_lifecycle)
                        )
                    )
                except KeyError:
                    lifecycle_digest = ""
                destination_lifecycle_bound = (
                    len(history_entries) == len(history)
                    and destination_lifecycle.get("lifecycle_policy_id")
                    == TRUST_TRANSFER_DESTINATION_LIFECYCLE_POLICY_ID
                    and destination_lifecycle.get("lifecycle_digest") == lifecycle_digest
                    and isinstance(final_entry, Mapping)
                    and destination_lifecycle.get("active_entry_ref") == final_entry.get("entry_ref")
                    and destination_lifecycle.get("latest_federation_ref")
                    == remote_verifier_federation.get("federation_ref")
                    and destination_lifecycle.get("latest_federation_digest")
                    == _trust_transfer_federation_binding_digest(remote_verifier_federation)
                    and destination_lifecycle.get("latest_cadence_ref")
                    == re_attestation_cadence.get("cadence_ref")
                    and destination_lifecycle.get("latest_cadence_digest")
                    == re_attestation_cadence.get("receipt_digest")
                    and destination_lifecycle.get("revocation_fail_closed_action")
                    == TRUST_TRANSFER_DESTINATION_REVOCATION_FAIL_CLOSED_ACTION
                )
                destination_lifecycle_disclosure_bound = (
                    destination_lifecycle_bound
                    and export_profile_id == TRUST_TRANSFER_FULL_CLONE_EXPORT_PROFILE_ID
                    and "history_summaries" not in destination_lifecycle
                )
                if destination_lifecycle_bound and isinstance(final_entry, Mapping):
                    sequences = [entry.get("sequence") for entry in history_entries]
                    history_event_types = [
                        entry.get("event_type") for entry in history_entries
                    ]
                    imported_entry = history_entries[0] if len(history_entries) > 0 else None
                    latest_renewed_entry = (
                        history_entries[1] if len(history_entries) > 1 else None
                    )
                    revoked_entry = history_entries[2] if len(history_entries) > 2 else None
                    recovered_entry = history_entries[3] if len(history_entries) > 3 else None
                    try:
                        imported_recorded_at = (
                            _parse_datetime(
                                str(imported_entry.get("recorded_at", "")),
                                "destination_lifecycle.history[].recorded_at",
                            )
                            if isinstance(imported_entry, Mapping)
                            else None
                        )
                        imported_valid_until = (
                            _parse_datetime(
                                str(imported_entry.get("valid_until", "")),
                                "destination_lifecycle.history[].valid_until",
                            )
                            if isinstance(imported_entry, Mapping)
                            else None
                        )
                        latest_renewed_recorded_at = (
                            _parse_datetime(
                                str(latest_renewed_entry.get("recorded_at", "")),
                                "destination_lifecycle.history[].recorded_at",
                            )
                            if isinstance(latest_renewed_entry, Mapping)
                            else None
                        )
                        revoked_recorded_at = (
                            _parse_datetime(
                                str(revoked_entry.get("recorded_at", "")),
                                "destination_lifecycle.history[].recorded_at",
                            )
                            if isinstance(revoked_entry, Mapping)
                            else None
                        )
                        revoked_valid_until = (
                            _parse_datetime(
                                str(revoked_entry.get("valid_until", "")),
                                "destination_lifecycle.history[].valid_until",
                            )
                            if isinstance(revoked_entry, Mapping)
                            else None
                        )
                        recovered_recorded_at = (
                            _parse_datetime(
                                str(recovered_entry.get("recorded_at", "")),
                                "destination_lifecycle.history[].recorded_at",
                            )
                            if isinstance(recovered_entry, Mapping)
                            else None
                        )
                        recovered_valid_until = (
                            _parse_datetime(
                                str(recovered_entry.get("valid_until", "")),
                                "destination_lifecycle.history[].valid_until",
                            )
                            if isinstance(recovered_entry, Mapping)
                            else None
                        )
                    except (TypeError, ValueError):
                        imported_recorded_at = None
                        imported_valid_until = None
                        latest_renewed_recorded_at = None
                        revoked_recorded_at = None
                        revoked_valid_until = None
                        recovered_recorded_at = None
                        recovered_valid_until = None

                    destination_renewal_history_bound = (
                        sequences == list(range(len(history_entries)))
                        and len(history_entries) == 4
                        and history_event_types
                        == ["imported", "renewed", "revoked", "recovered"]
                        and isinstance(imported_entry, Mapping)
                        and isinstance(latest_renewed_entry, Mapping)
                        and imported_entry.get("status")
                        == TRUST_TRANSFER_DESTINATION_CURRENT_STATUS
                        and latest_renewed_entry.get("status")
                        == TRUST_TRANSFER_DESTINATION_CURRENT_STATUS
                        and imported_entry.get("destination_snapshot_digest")
                        == receipt.get("destination_snapshot_digest")
                        and all(
                            entry.get("destination_snapshot_digest")
                            == receipt.get("destination_snapshot_digest")
                            for entry in history_entries
                        )
                        and all(
                            _trust_transfer_lifecycle_entry_quorum_bound(entry)
                            for entry in history_entries
                        )
                        and imported_recorded_at is not None
                        and imported_valid_until is not None
                        and latest_renewed_recorded_at is not None
                        and imported_recorded_at <= latest_renewed_recorded_at <= imported_valid_until
                        and imported_entry.get("federation_digest")
                        != latest_renewed_entry.get("federation_digest")
                        and imported_entry.get("cadence_digest")
                        != latest_renewed_entry.get("cadence_digest")
                    )
                    destination_revocation_history_bound = (
                        destination_renewal_history_bound
                        and isinstance(revoked_entry, Mapping)
                        and revoked_entry.get("status")
                        == TRUST_TRANSFER_DESTINATION_REVOKED_STATUS
                        and revoked_entry.get("federation_ref")
                        == latest_renewed_entry.get("federation_ref")
                        and revoked_entry.get("federation_digest")
                        == latest_renewed_entry.get("federation_digest")
                        and revoked_entry.get("cadence_ref")
                        == latest_renewed_entry.get("cadence_ref")
                        and revoked_entry.get("cadence_digest")
                        == latest_renewed_entry.get("cadence_digest")
                        and revoked_entry.get("covered_verifier_receipt_ids")
                        == latest_renewed_entry.get("covered_verifier_receipt_ids")
                        and latest_renewed_recorded_at is not None
                        and revoked_recorded_at is not None
                        and revoked_valid_until is not None
                        and latest_renewed_recorded_at <= revoked_recorded_at <= revoked_valid_until
                    )
                    destination_recovery_history_bound = (
                        destination_revocation_history_bound
                        and isinstance(recovered_entry, Mapping)
                        and recovered_entry == final_entry
                        and final_entry.get("entry_ref")
                        == destination_lifecycle.get("active_entry_ref")
                        and final_entry.get("federation_ref")
                        == destination_lifecycle.get("latest_federation_ref")
                        and final_entry.get("federation_digest")
                        == destination_lifecycle.get("latest_federation_digest")
                        and final_entry.get("cadence_ref")
                        == destination_lifecycle.get("latest_cadence_ref")
                        and final_entry.get("cadence_digest")
                        == destination_lifecycle.get("latest_cadence_digest")
                        and final_entry.get("quorum_policy_id")
                        == remote_verifier_federation.get("quorum_policy_id")
                        and final_entry.get("trust_root_quorum")
                        == remote_verifier_federation.get("trust_root_quorum")
                        and final_entry.get("jurisdiction_quorum")
                        == remote_verifier_federation.get("jurisdiction_quorum")
                        and final_entry.get("covered_trust_root_refs")
                        == remote_verifier_federation.get("trust_root_refs")
                        and final_entry.get("covered_jurisdictions")
                        == remote_verifier_federation.get("jurisdictions")
                        and final_entry.get("covered_verifier_receipt_ids")
                        == re_attestation_cadence.get("covered_verifier_receipt_ids")
                        and final_entry.get("event_type") == "recovered"
                        and final_entry.get("status")
                        == TRUST_TRANSFER_DESTINATION_CURRENT_STATUS
                        and final_entry.get("federation_digest")
                        != revoked_entry.get("federation_digest")
                        and final_entry.get("cadence_digest")
                        != revoked_entry.get("cadence_digest")
                        and revoked_recorded_at is not None
                        and recovered_recorded_at is not None
                        and recovered_valid_until is not None
                        and revoked_recorded_at <= recovered_recorded_at <= recovered_valid_until
                    )
                    recovery_quorum_bound = (
                        destination_recovery_history_bound
                        and remote_verifier_federation.get("quorum_policy_id")
                        == TRUST_TRANSFER_RECOVERY_REMOTE_VERIFIER_QUORUM_POLICY_ID
                        and remote_verifier_federation.get("required_verifier_count")
                        == TRUST_TRANSFER_RECOVERY_REMOTE_VERIFIER_COUNT
                        and remote_verifier_federation.get("trust_root_quorum")
                        == TRUST_TRANSFER_RECOVERY_TRUST_ROOT_QUORUM
                        and remote_verifier_federation.get("jurisdiction_quorum")
                        == TRUST_TRANSFER_RECOVERY_JURISDICTION_QUORUM
                        and isinstance(recovered_entry, Mapping)
                        and recovered_entry.get("quorum_policy_id")
                        == TRUST_TRANSFER_RECOVERY_REMOTE_VERIFIER_QUORUM_POLICY_ID
                        and recovered_entry.get("trust_root_quorum")
                        == TRUST_TRANSFER_RECOVERY_TRUST_ROOT_QUORUM
                        and recovered_entry.get("jurisdiction_quorum")
                        == TRUST_TRANSFER_RECOVERY_JURISDICTION_QUORUM
                        and len(recovered_entry.get("covered_trust_root_refs", []))
                        >= TRUST_TRANSFER_RECOVERY_TRUST_ROOT_QUORUM
                        and len(recovered_entry.get("covered_jurisdictions", []))
                        >= TRUST_TRANSFER_RECOVERY_JURISDICTION_QUORUM
                    )
                    destination_current = (
                        destination_recovery_history_bound
                        and destination_lifecycle.get("current_status")
                        == TRUST_TRANSFER_DESTINATION_CURRENT_STATUS
                        and final_entry.get("status")
                        == TRUST_TRANSFER_DESTINATION_CURRENT_STATUS
                        and re_attestation_current
                    )
            elif isinstance(history_summaries, list):
                history_entries = [
                    entry for entry in history_summaries if isinstance(entry, Mapping)
                ]
                final_entry = (
                    history_entries[-1]
                    if len(history_entries) == len(history_summaries) and history_entries
                    else None
                )
                history_summary_commitment_digest = (
                    _trust_transfer_redacted_destination_lifecycle_history_commitment_digest(
                        history_entries
                    )
                )
                try:
                    lifecycle_summary_digest = sha256_text(
                        canonical_json(
                            _trust_transfer_redacted_destination_lifecycle_digest_payload(
                                destination_lifecycle
                            )
                        )
                    )
                except KeyError:
                    lifecycle_summary_digest = ""
                summary_entries_valid = all(
                    _trust_transfer_redacted_lifecycle_entry_quorum_bound(entry)
                    and bool(entry.get("covered_verifier_receipt_commitment_digest"))
                    and entry.get("entry_digest")
                    == _trust_transfer_redacted_destination_lifecycle_entry_summary_digest(
                        entry
                    )
                    for entry in history_entries
                )
                destination_lifecycle_bound = (
                    len(history_entries) == len(history_summaries)
                    and destination_lifecycle.get("kind")
                    == "trust_redacted_destination_lifecycle"
                    and destination_lifecycle.get("schema_version")
                    == TRUST_TRANSFER_REDACTED_DESTINATION_LIFECYCLE_SCHEMA_VERSION
                    and destination_lifecycle.get("summary_profile_id")
                    == TRUST_TRANSFER_REDACTED_DESTINATION_LIFECYCLE_PROFILE_ID
                    and destination_lifecycle.get("lifecycle_policy_id")
                    == TRUST_TRANSFER_DESTINATION_LIFECYCLE_POLICY_ID
                    and destination_lifecycle.get("summary_digest") == lifecycle_summary_digest
                    and destination_lifecycle.get("history_summary_commitment_digest")
                    == history_summary_commitment_digest
                    and destination_lifecycle.get("redaction_policy_id")
                    == TRUST_TRANSFER_DESTINATION_LIFECYCLE_SUMMARY_REDACTION_POLICY_ID
                    and destination_lifecycle.get("redacted_fields")
                    == list(TRUST_TRANSFER_REDACTED_DESTINATION_LIFECYCLE_FIELDS)
                    and bool(destination_lifecycle.get("sealed_lifecycle_digest"))
                    and isinstance(final_entry, Mapping)
                    and destination_lifecycle.get("active_sequence")
                    == final_entry.get("sequence")
                    and destination_lifecycle.get("active_entry_digest")
                    == final_entry.get("entry_digest")
                    and destination_lifecycle.get("latest_federation_digest")
                    == _trust_transfer_federation_binding_digest(remote_verifier_federation)
                    and destination_lifecycle.get("latest_cadence_digest")
                    == re_attestation_cadence.get("receipt_digest")
                    and destination_lifecycle.get("revocation_fail_closed_action")
                    == TRUST_TRANSFER_DESTINATION_REVOCATION_FAIL_CLOSED_ACTION
                    and summary_entries_valid
                )
                destination_lifecycle_disclosure_bound = (
                    destination_lifecycle_bound
                    and export_profile_id == TRUST_TRANSFER_REDACTED_EXPORT_PROFILE_ID
                    and "history" not in destination_lifecycle
                    and "active_entry_ref" not in destination_lifecycle
                    and "latest_federation_ref" not in destination_lifecycle
                    and "latest_cadence_ref" not in destination_lifecycle
                )
                if destination_lifecycle_bound and isinstance(final_entry, Mapping):
                    sequences = [entry.get("sequence") for entry in history_entries]
                    history_event_types = [
                        entry.get("event_type") for entry in history_entries
                    ]
                    imported_entry = history_entries[0] if len(history_entries) > 0 else None
                    latest_renewed_entry = (
                        history_entries[1] if len(history_entries) > 1 else None
                    )
                    revoked_entry = history_entries[2] if len(history_entries) > 2 else None
                    recovered_entry = history_entries[3] if len(history_entries) > 3 else None
                    try:
                        imported_recorded_at = (
                            _parse_datetime(
                                str(imported_entry.get("recorded_at", "")),
                                "destination_lifecycle.history_summaries[].recorded_at",
                            )
                            if isinstance(imported_entry, Mapping)
                            else None
                        )
                        imported_valid_until = (
                            _parse_datetime(
                                str(imported_entry.get("valid_until", "")),
                                "destination_lifecycle.history_summaries[].valid_until",
                            )
                            if isinstance(imported_entry, Mapping)
                            else None
                        )
                        latest_renewed_recorded_at = (
                            _parse_datetime(
                                str(latest_renewed_entry.get("recorded_at", "")),
                                "destination_lifecycle.history_summaries[].recorded_at",
                            )
                            if isinstance(latest_renewed_entry, Mapping)
                            else None
                        )
                        revoked_recorded_at = (
                            _parse_datetime(
                                str(revoked_entry.get("recorded_at", "")),
                                "destination_lifecycle.history_summaries[].recorded_at",
                            )
                            if isinstance(revoked_entry, Mapping)
                            else None
                        )
                        revoked_valid_until = (
                            _parse_datetime(
                                str(revoked_entry.get("valid_until", "")),
                                "destination_lifecycle.history_summaries[].valid_until",
                            )
                            if isinstance(revoked_entry, Mapping)
                            else None
                        )
                        recovered_recorded_at = (
                            _parse_datetime(
                                str(recovered_entry.get("recorded_at", "")),
                                "destination_lifecycle.history_summaries[].recorded_at",
                            )
                            if isinstance(recovered_entry, Mapping)
                            else None
                        )
                        recovered_valid_until = (
                            _parse_datetime(
                                str(recovered_entry.get("valid_until", "")),
                                "destination_lifecycle.history_summaries[].valid_until",
                            )
                            if isinstance(recovered_entry, Mapping)
                            else None
                        )
                    except (TypeError, ValueError):
                        imported_recorded_at = None
                        imported_valid_until = None
                        latest_renewed_recorded_at = None
                        revoked_recorded_at = None
                        revoked_valid_until = None
                        recovered_recorded_at = None
                        recovered_valid_until = None

                    destination_renewal_history_bound = (
                        sequences == list(range(len(history_entries)))
                        and len(history_entries) == 4
                        and history_event_types
                        == ["imported", "renewed", "revoked", "recovered"]
                        and isinstance(imported_entry, Mapping)
                        and isinstance(latest_renewed_entry, Mapping)
                        and imported_entry.get("status")
                        == TRUST_TRANSFER_DESTINATION_CURRENT_STATUS
                        and latest_renewed_entry.get("status")
                        == TRUST_TRANSFER_DESTINATION_CURRENT_STATUS
                        and imported_entry.get("destination_snapshot_digest")
                        == receipt.get("destination_snapshot_digest")
                        and all(
                            entry.get("destination_snapshot_digest")
                            == receipt.get("destination_snapshot_digest")
                            for entry in history_entries
                        )
                        and all(
                            _trust_transfer_redacted_lifecycle_entry_quorum_bound(entry)
                            and bool(entry.get("covered_verifier_receipt_commitment_digest"))
                            for entry in history_entries
                        )
                        and current_verifier_receipt_commitment_digest is not None
                        and imported_recorded_at is not None
                        and imported_valid_until is not None
                        and latest_renewed_recorded_at is not None
                        and imported_recorded_at <= latest_renewed_recorded_at <= imported_valid_until
                        and imported_entry.get("federation_digest")
                        != latest_renewed_entry.get("federation_digest")
                        and imported_entry.get("cadence_digest")
                        != latest_renewed_entry.get("cadence_digest")
                    )
                    destination_revocation_history_bound = (
                        destination_renewal_history_bound
                        and isinstance(revoked_entry, Mapping)
                        and revoked_entry.get("status")
                        == TRUST_TRANSFER_DESTINATION_REVOKED_STATUS
                        and revoked_entry.get("federation_digest")
                        == latest_renewed_entry.get("federation_digest")
                        and revoked_entry.get("cadence_digest")
                        == latest_renewed_entry.get("cadence_digest")
                        and revoked_entry.get(
                            "covered_verifier_receipt_commitment_digest"
                        )
                        == latest_renewed_entry.get(
                            "covered_verifier_receipt_commitment_digest"
                        )
                        and latest_renewed_recorded_at is not None
                        and revoked_recorded_at is not None
                        and revoked_valid_until is not None
                        and latest_renewed_recorded_at <= revoked_recorded_at <= revoked_valid_until
                    )
                    destination_recovery_history_bound = (
                        destination_revocation_history_bound
                        and isinstance(recovered_entry, Mapping)
                        and recovered_entry == final_entry
                        and final_entry.get("sequence")
                        == destination_lifecycle.get("active_sequence")
                        and final_entry.get("entry_digest")
                        == destination_lifecycle.get("active_entry_digest")
                        and final_entry.get("federation_digest")
                        == destination_lifecycle.get("latest_federation_digest")
                        and final_entry.get("cadence_digest")
                        == destination_lifecycle.get("latest_cadence_digest")
                        and final_entry.get("quorum_policy_id")
                        == remote_verifier_federation.get("quorum_policy_id")
                        and final_entry.get("trust_root_quorum")
                        == remote_verifier_federation.get("trust_root_quorum")
                        and final_entry.get("jurisdiction_quorum")
                        == remote_verifier_federation.get("jurisdiction_quorum")
                        and final_entry.get("covered_trust_root_count")
                        == len(remote_verifier_federation.get("trust_root_refs", []))
                        and final_entry.get("covered_jurisdiction_count")
                        == len(remote_verifier_federation.get("jurisdictions", []))
                        and current_verifier_receipt_commitment_digest is not None
                        and final_entry.get(
                            "covered_verifier_receipt_commitment_digest"
                        )
                        == current_verifier_receipt_commitment_digest
                        and final_entry.get("event_type") == "recovered"
                        and final_entry.get("status")
                        == TRUST_TRANSFER_DESTINATION_CURRENT_STATUS
                        and final_entry.get("federation_digest")
                        != revoked_entry.get("federation_digest")
                        and final_entry.get("cadence_digest")
                        != revoked_entry.get("cadence_digest")
                        and revoked_recorded_at is not None
                        and recovered_recorded_at is not None
                        and recovered_valid_until is not None
                        and revoked_recorded_at <= recovered_recorded_at <= recovered_valid_until
                    )
                    recovery_quorum_bound = (
                        destination_recovery_history_bound
                        and remote_verifier_federation.get("quorum_policy_id")
                        == TRUST_TRANSFER_RECOVERY_REMOTE_VERIFIER_QUORUM_POLICY_ID
                        and remote_verifier_federation.get("required_verifier_count")
                        == TRUST_TRANSFER_RECOVERY_REMOTE_VERIFIER_COUNT
                        and remote_verifier_federation.get("trust_root_quorum")
                        == TRUST_TRANSFER_RECOVERY_TRUST_ROOT_QUORUM
                        and remote_verifier_federation.get("jurisdiction_quorum")
                        == TRUST_TRANSFER_RECOVERY_JURISDICTION_QUORUM
                        and isinstance(recovered_entry, Mapping)
                        and recovered_entry.get("quorum_policy_id")
                        == TRUST_TRANSFER_RECOVERY_REMOTE_VERIFIER_QUORUM_POLICY_ID
                        and recovered_entry.get("trust_root_quorum")
                        == TRUST_TRANSFER_RECOVERY_TRUST_ROOT_QUORUM
                        and recovered_entry.get("jurisdiction_quorum")
                        == TRUST_TRANSFER_RECOVERY_JURISDICTION_QUORUM
                        and recovered_entry.get("covered_trust_root_count", 0)
                        >= TRUST_TRANSFER_RECOVERY_TRUST_ROOT_QUORUM
                        and recovered_entry.get("covered_jurisdiction_count", 0)
                        >= TRUST_TRANSFER_RECOVERY_JURISDICTION_QUORUM
                    )
                    destination_current = (
                        destination_recovery_history_bound
                        and destination_lifecycle.get("current_status")
                        == TRUST_TRANSFER_DESTINATION_CURRENT_STATUS
                        and final_entry.get("status")
                        == TRUST_TRANSFER_DESTINATION_CURRENT_STATUS
                        and re_attestation_current
                    )
        destination_seeded_agent_id = None
        if isinstance(destination_snapshot, Mapping):
            destination_seeded_agent_id = destination_snapshot.get("agent_id")
        elif isinstance(destination_snapshot_redacted, Mapping):
            destination_seeded_agent_id = destination_snapshot_redacted.get("agent_id")
        destination_seeded = isinstance(import_receipt, Mapping) and (
            import_receipt.get("destination_seeded") is True
            and destination_seeded_agent_id == receipt.get("agent_id")
        )
        receipt_digest_bound = receipt.get("receipt_digest") == sha256_text(
            canonical_json(_trust_transfer_digest_payload(receipt))
        )
        summary = {
            "source_snapshot_digest_bound": source_snapshot_digest_bound,
            "destination_snapshot_digest_bound": destination_snapshot_digest_bound,
            "export_profile_bound": export_profile_bound,
            "history_commitment_bound": history_commitment_bound,
            "history_preserved": history_preserved,
            "thresholds_preserved": thresholds_preserved,
            "provenance_policy_preserved": provenance_policy_preserved,
            "eligibility_preserved": eligibility_preserved,
            "federation_quorum_attested": federation_quorum_attested,
            "live_remote_verifier_attested": live_remote_verifier_attested,
            "remote_verifier_receipts_bound": remote_verifier_receipts_bound,
            "remote_verifier_disclosure_bound": remote_verifier_disclosure_bound,
            "re_attestation_cadence_bound": re_attestation_cadence_bound,
            "re_attestation_current": re_attestation_current,
            "destination_lifecycle_bound": destination_lifecycle_bound,
            "destination_lifecycle_disclosure_bound": destination_lifecycle_disclosure_bound,
            "destination_renewal_history_bound": destination_renewal_history_bound,
            "destination_revocation_history_bound": destination_revocation_history_bound,
            "destination_recovery_history_bound": destination_recovery_history_bound,
            "recovery_quorum_bound": recovery_quorum_bound,
            "destination_current": destination_current,
            "destination_seeded": destination_seeded,
            "receipt_digest_bound": receipt_digest_bound,
        }
        summary["ok"] = all(summary.values())
        return summary

    def _build_remote_verifier_federation(
        self,
        *,
        human_reviewer_ref: str,
        route_digest: str,
        verifier_receipts: List[Mapping[str, Any]],
        quorum_policy_id: str,
    ) -> Dict[str, Any]:
        quorum_fields = _trust_transfer_verifier_quorum_fields(
            quorum_policy_id=quorum_policy_id,
            verifier_receipts=verifier_receipts,
        )
        federation = {
            "federation_id": new_id("trust-verifier-federation"),
            "federation_ref": f"trust-verifier-federation://{sha256_text(human_reviewer_ref)[:12]}",
            "federation_policy_id": TRUST_TRANSFER_REMOTE_VERIFIER_FEDERATION_POLICY_ID,
            "network_profile_id": TRUST_TRANSFER_REMOTE_VERIFIER_NETWORK_PROFILE_ID,
            "quorum_policy_id": quorum_fields["quorum_policy_id"],
            "human_reviewer_ref": human_reviewer_ref,
            "required_verifier_count": quorum_fields["required_verifier_count"],
            "received_verifier_count": quorum_fields["received_verifier_count"],
            "verifier_receipts": [dict(verifier_receipt) for verifier_receipt in verifier_receipts],
            "verifier_refs": quorum_fields["verifier_refs"],
            "trust_root_refs": quorum_fields["trust_root_refs"],
            "jurisdictions": quorum_fields["jurisdictions"],
            "trust_root_quorum": quorum_fields["trust_root_quorum"],
            "jurisdiction_quorum": quorum_fields["jurisdiction_quorum"],
            "authority_chain_refs": sorted(
                {verifier_receipt["authority_chain_ref"] for verifier_receipt in verifier_receipts}
            ),
            "reviewer_binding_digest": _trust_transfer_remote_reviewer_binding_digest(
                human_reviewer_ref=human_reviewer_ref,
                route_digest=route_digest,
                verifier_receipts=verifier_receipts,
            ),
            "federation_status": "verified",
            "receipt_digest": "",
        }
        federation["receipt_digest"] = sha256_text(
            canonical_json(_trust_transfer_remote_verifier_federation_digest_payload(federation))
        )
        return federation

    def _build_redacted_verifier_receipt_summary(
        self,
        verifier_receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        transport_exchange = verifier_receipt.get("transport_exchange", {})
        if not isinstance(transport_exchange, Mapping):
            raise ValueError("verifier receipt transport_exchange must be a mapping")
        summary = {
            "kind": "trust_redacted_verifier_receipt_summary",
            "schema_version": TRUST_TRANSFER_REDACTED_VERIFIER_FEDERATION_SCHEMA_VERSION,
            "summary_id": new_id("trust-verifier-summary"),
            "summary_ref": (
                "trust-redacted-verifier-receipt://"
                f"{sha256_text(str(verifier_receipt['receipt_id']))[:12]}"
            ),
            "summary_profile_id": (
                TRUST_TRANSFER_REDACTED_VERIFIER_RECEIPT_SUMMARY_PROFILE_ID
            ),
            "receipt_id": verifier_receipt["receipt_id"],
            "verifier_endpoint": verifier_receipt["verifier_endpoint"],
            "verifier_ref": verifier_receipt["verifier_ref"],
            "jurisdiction": verifier_receipt["jurisdiction"],
            "network_profile_id": verifier_receipt["network_profile_id"],
            "authority_chain_ref": verifier_receipt["authority_chain_ref"],
            "trust_root_ref": verifier_receipt["trust_root_ref"],
            "freshness_window_seconds": verifier_receipt["freshness_window_seconds"],
            "observed_latency_ms": verifier_receipt["observed_latency_ms"],
            "recorded_at": verifier_receipt["recorded_at"],
            "receipt_status": verifier_receipt["receipt_status"],
            "transport_exchange_digest": transport_exchange["digest"],
            "sealed_receipt_digest": verifier_receipt["digest"],
            "redaction_policy_id": TRUST_TRANSFER_VERIFIER_SUMMARY_REDACTION_POLICY_ID,
            "redacted_fields": list(TRUST_TRANSFER_REDACTED_VERIFIER_FIELDS),
            "summary_digest": "",
        }
        summary["summary_digest"] = sha256_text(
            canonical_json(
                _trust_transfer_redacted_verifier_receipt_summary_digest_payload(summary)
            )
        )
        return summary

    def _build_redacted_verifier_federation_summary(
        self,
        federation: Mapping[str, Any],
    ) -> Dict[str, Any]:
        verifier_receipts = federation.get("verifier_receipts", [])
        if not isinstance(verifier_receipts, list) or not verifier_receipts:
            raise ValueError("verifier federation summary requires verifier receipts")
        verifier_receipt_summaries = [
            self._build_redacted_verifier_receipt_summary(verifier_receipt)
            for verifier_receipt in verifier_receipts
            if isinstance(verifier_receipt, Mapping)
        ]
        if len(verifier_receipt_summaries) != len(verifier_receipts):
            raise ValueError("verifier federation summary requires mapping verifier receipts")
        summary = {
            "kind": "trust_redacted_verifier_federation",
            "schema_version": TRUST_TRANSFER_REDACTED_VERIFIER_FEDERATION_SCHEMA_VERSION,
            "federation_id": federation["federation_id"],
            "federation_ref": federation["federation_ref"],
            "summary_profile_id": TRUST_TRANSFER_REDACTED_VERIFIER_FEDERATION_PROFILE_ID,
            "federation_policy_id": federation["federation_policy_id"],
            "network_profile_id": federation["network_profile_id"],
            "quorum_policy_id": federation["quorum_policy_id"],
            "human_reviewer_ref": federation["human_reviewer_ref"],
            "required_verifier_count": federation["required_verifier_count"],
            "received_verifier_count": federation["received_verifier_count"],
            "verifier_receipt_summaries": verifier_receipt_summaries,
            "verifier_refs": [
                verifier_receipt["verifier_ref"]
                for verifier_receipt in verifier_receipt_summaries
            ],
            "trust_root_refs": sorted(
                {
                    verifier_receipt["trust_root_ref"]
                    for verifier_receipt in verifier_receipt_summaries
                }
            ),
            "jurisdictions": sorted(
                {
                    verifier_receipt["jurisdiction"]
                    for verifier_receipt in verifier_receipt_summaries
                }
            ),
            "trust_root_quorum": federation["trust_root_quorum"],
            "jurisdiction_quorum": federation["jurisdiction_quorum"],
            "authority_chain_refs": sorted(
                {
                    verifier_receipt["authority_chain_ref"]
                    for verifier_receipt in verifier_receipt_summaries
                }
            ),
            "reviewer_binding_digest": federation["reviewer_binding_digest"],
            "verifier_receipt_commitment_digest": (
                _trust_transfer_redacted_verifier_receipt_commitment_digest(
                    verifier_receipt_summaries
                )
            ),
            "sealed_federation_digest": federation["receipt_digest"],
            "redaction_policy_id": TRUST_TRANSFER_VERIFIER_SUMMARY_REDACTION_POLICY_ID,
            "redacted_fields": list(TRUST_TRANSFER_REDACTED_VERIFIER_FIELDS),
            "federation_status": federation["federation_status"],
            "receipt_digest": "",
        }
        summary["receipt_digest"] = sha256_text(
            canonical_json(
                _trust_transfer_redacted_verifier_federation_digest_payload(summary)
            )
        )
        return summary

    def _build_re_attestation_cadence(
        self,
        *,
        federation: Mapping[str, Any],
    ) -> Dict[str, Any]:
        verifier_receipts = federation.get("verifier_receipts")
        verifier_receipt_summaries = federation.get("verifier_receipt_summaries")
        verifier_entries = verifier_receipts
        if not isinstance(verifier_entries, list):
            verifier_entries = verifier_receipt_summaries
        if not isinstance(verifier_entries, list) or not verifier_entries:
            raise ValueError("remote verifier federation requires at least one verifier receipt")
        attested_at = max(
            _parse_datetime(
                str(verifier_receipt.get("recorded_at", "")),
                "remote_verifier_receipts[].recorded_at",
            )
            for verifier_receipt in verifier_entries
            if isinstance(verifier_receipt, Mapping)
        )
        valid_until = min(
            _parse_datetime(
                str(verifier_receipt.get("recorded_at", "")),
                "remote_verifier_receipts[].recorded_at",
            )
            + timedelta(seconds=int(verifier_receipt.get("freshness_window_seconds", 0)))
            for verifier_receipt in verifier_entries
            if isinstance(verifier_receipt, Mapping)
        )
        renew_after = attested_at + timedelta(seconds=TRUST_TRANSFER_REATTESTATION_INTERVAL_SECONDS)
        cadence = {
            "cadence_id": new_id("trust-re-attestation"),
            "cadence_ref": f"trust-re-attestation://{federation['federation_id']}",
            "cadence_policy_id": TRUST_TRANSFER_REATTESTATION_CADENCE_POLICY_ID,
            "attested_at": attested_at.isoformat(),
            "renew_after": renew_after.isoformat(),
            "valid_until": valid_until.isoformat(),
            "grace_window_seconds": TRUST_TRANSFER_REATTESTATION_GRACE_WINDOW_SECONDS,
            "covered_verifier_receipt_ids": [
                verifier_receipt["receipt_id"]
                for verifier_receipt in verifier_entries
                if isinstance(verifier_receipt, Mapping)
            ],
            "bound_federation_ref": federation["federation_ref"],
            "bound_federation_digest": _trust_transfer_federation_binding_digest(
                federation
            ),
            "cadence_status": "scheduled",
            "receipt_digest": "",
        }
        cadence["receipt_digest"] = sha256_text(
            canonical_json(_trust_transfer_re_attestation_cadence_digest_payload(cadence))
        )
        return cadence

    def _build_remote_verifier_receipt(
        self,
        *,
        reviewer_id: str,
        verifier_endpoint: str,
        verifier_ref: str,
        jurisdiction: str,
        authority_chain_ref: str,
        trust_root_ref: str,
        trust_root_digest: str,
        recorded_at: str,
        freshness_window_seconds: int,
        observed_latency_ms: float,
        challenge_stage: str,
    ) -> Dict[str, Any]:
        recorded_at_dt = _parse_datetime(recorded_at, "recorded_at")
        recorded_at_iso = recorded_at_dt.isoformat()
        verifier_slug = verifier_ref.rstrip("/").rsplit("/", 1)[-1]
        stage_slug = challenge_stage.strip().replace("_", "-")
        challenge_ref = (
            "challenge://trust-transfer/"
            f"{verifier_slug}/{stage_slug}/{recorded_at_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        )
        challenge_digest = (
            "sha256:trust-transfer-"
            f"{verifier_slug}-{stage_slug}-{recorded_at_dt.strftime('%Y%m%d%H%M%SZ').lower()}"
        )
        transport_exchange = {
            "kind": "guardian_verifier_transport_exchange",
            "schema_version": "1.0.0",
            "exchange_id": new_id("verifier-transport-exchange"),
            "verifier_endpoint": verifier_endpoint,
            "verifier_ref": verifier_ref,
            "jurisdiction": jurisdiction,
            "transport_profile": "reviewer-live-proof-bridge-v1",
            "exchange_profile_id": "digest-bound-reviewer-transport-exchange-v1",
            "challenge_ref": challenge_ref,
            "challenge_digest": challenge_digest,
            "request_payload_kind": "reviewer-live-proof-request",
            "request_payload_ref": f"sealed://trust-transfer/{verifier_slug}/{stage_slug}/request",
            "request_payload_digest": sha256_text(
                canonical_json(
                    {
                        "verifier_ref": verifier_ref,
                        "recorded_at": recorded_at_iso,
                        "payload_kind": "request",
                    }
                )
            ),
            "request_size_bytes": 296,
            "response_payload_kind": "reviewer-live-proof-response",
            "response_payload_ref": f"sealed://trust-transfer/{verifier_slug}/{stage_slug}/response",
            "response_payload_digest": sha256_text(
                canonical_json(
                    {
                        "verifier_ref": verifier_ref,
                        "recorded_at": recorded_at_iso,
                        "payload_kind": "response",
                    }
                )
            ),
            "response_size_bytes": 298,
            "recorded_at": recorded_at_iso,
            "digest": "",
        }
        transport_exchange["digest"] = sha256_text(
            canonical_json(
                {
                    "exchange_id": transport_exchange["exchange_id"],
                    "verifier_ref": verifier_ref,
                    "challenge_ref": challenge_ref,
                    "request_payload_digest": transport_exchange["request_payload_digest"],
                    "response_payload_digest": transport_exchange["response_payload_digest"],
                    "recorded_at": recorded_at_iso,
                }
            )
        )
        receipt = {
            "kind": "guardian_verifier_network_receipt",
            "schema_version": "1.0.0",
            "receipt_id": new_id("verifier-network-receipt"),
            "reviewer_id": reviewer_id,
            "verifier_endpoint": verifier_endpoint,
            "verifier_ref": verifier_ref,
            "jurisdiction": jurisdiction,
            "transport_profile": "reviewer-live-proof-bridge-v1",
            "network_profile_id": TRUST_TRANSFER_REMOTE_VERIFIER_NETWORK_PROFILE_ID,
            "challenge_ref": challenge_ref,
            "challenge_digest": challenge_digest,
            "authority_chain_ref": authority_chain_ref,
            "trust_root_ref": trust_root_ref,
            "trust_root_digest": trust_root_digest,
            "transport_exchange": transport_exchange,
            "freshness_window_seconds": freshness_window_seconds,
            "observed_latency_ms": round(float(observed_latency_ms), 1),
            "receipt_status": "verified",
            "recorded_at": recorded_at_iso,
            "digest": "",
        }
        receipt["digest"] = sha256_text(
            canonical_json(
                {
                    "receipt_id": receipt["receipt_id"],
                    "verifier_ref": verifier_ref,
                    "challenge_ref": challenge_ref,
                    "recorded_at": recorded_at_iso,
                    "transport_exchange_digest": transport_exchange["digest"],
                }
            )
        )
        return receipt

    def _build_multi_root_recovery_remote_verifier_receipts(
        self,
        *,
        verifier_receipts: List[Mapping[str, Any]],
        recovered_at: str,
    ) -> List[Dict[str, Any]]:
        recovered_at_dt = _parse_datetime(recovered_at, "recovered_at")
        reviewer_id = str(
            verifier_receipts[0].get("reviewer_id", "human-reviewer-trust-transfer-001")
        )
        receipt_templates = [
            {
                "verifier_endpoint": "verifier://guardian-oversight.jp",
                "verifier_ref": "verifier://guardian-oversight.jp/reviewer-alpha-recovery",
                "jurisdiction": "JP-13",
                "authority_chain_ref": "authority://guardian-oversight.jp/reviewer-attestation",
                "trust_root_ref": "root://guardian-oversight.jp/reviewer-live-pki",
                "trust_root_digest": "sha256:guardian-oversight-jp-reviewer-live-pki-v2",
                "freshness_window_seconds": 900,
                "observed_latency_ms": 49.2,
            },
            {
                "verifier_endpoint": "verifier://guardian-oversight.us",
                "verifier_ref": "verifier://guardian-oversight.us/reviewer-beta-recovery",
                "jurisdiction": "US-CA",
                "authority_chain_ref": "authority://guardian-oversight.us/reviewer-attestation",
                "trust_root_ref": "root://guardian-oversight.us/reviewer-live-pki",
                "trust_root_digest": "sha256:guardian-oversight-us-reviewer-live-pki-v1",
                "freshness_window_seconds": 960,
                "observed_latency_ms": 52.4,
            },
            {
                "verifier_endpoint": "verifier://guardian-oversight.eu",
                "verifier_ref": "verifier://guardian-oversight.eu/reviewer-gamma-recovery",
                "jurisdiction": "EU-DE",
                "authority_chain_ref": "authority://guardian-oversight.eu/reviewer-attestation",
                "trust_root_ref": "root://guardian-oversight.eu/reviewer-live-pki",
                "trust_root_digest": "sha256:guardian-oversight-eu-reviewer-live-pki-v1",
                "freshness_window_seconds": 1020,
                "observed_latency_ms": 55.1,
            },
        ]
        recovered_receipts = [
            self._build_remote_verifier_receipt(
                reviewer_id=reviewer_id,
                verifier_endpoint=str(template["verifier_endpoint"]),
                verifier_ref=str(template["verifier_ref"]),
                jurisdiction=str(template["jurisdiction"]),
                authority_chain_ref=str(template["authority_chain_ref"]),
                trust_root_ref=str(template["trust_root_ref"]),
                trust_root_digest=str(template["trust_root_digest"]),
                recorded_at=(recovered_at_dt + timedelta(seconds=index * 30)).isoformat(),
                freshness_window_seconds=int(template["freshness_window_seconds"]),
                observed_latency_ms=float(template["observed_latency_ms"]),
                challenge_stage="recovery",
            )
            for index, template in enumerate(receipt_templates)
        ]
        return self._normalize_remote_verifier_receipts(recovered_receipts)

    def _renew_remote_verifier_receipts(
        self,
        *,
        verifier_receipts: List[Mapping[str, Any]],
        renewed_at: str,
    ) -> List[Dict[str, Any]]:
        renewed_at_dt = _parse_datetime(renewed_at, "renewed_at")
        renewed_at_iso = renewed_at_dt.isoformat()
        renewed_receipts: List[Dict[str, Any]] = []
        for verifier_receipt in verifier_receipts:
            renewed_receipt = dict(verifier_receipt)
            verifier_ref = str(renewed_receipt["verifier_ref"])
            verifier_slug = verifier_ref.rstrip("/").rsplit("/", 1)[-1]
            challenge_ref = (
                "challenge://trust-transfer/"
                f"{verifier_slug}/renewal/{renewed_at_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}"
            )
            challenge_digest = (
                "sha256:trust-transfer-"
                f"{verifier_slug}-renewal-{renewed_at_dt.strftime('%Y%m%d%H%M%SZ').lower()}"
            )
            transport_exchange = dict(renewed_receipt["transport_exchange"])
            transport_exchange.update(
                {
                    "exchange_id": new_id("verifier-transport-exchange"),
                    "challenge_ref": challenge_ref,
                    "challenge_digest": challenge_digest,
                    "request_payload_ref": (
                        f"sealed://trust-transfer/{verifier_slug}/renewal/request"
                    ),
                    "request_payload_digest": sha256_text(
                        canonical_json(
                            {
                                "verifier_ref": verifier_ref,
                                "recorded_at": renewed_at_iso,
                                "payload_kind": "request",
                            }
                        )
                    ),
                    "response_payload_ref": (
                        f"sealed://trust-transfer/{verifier_slug}/renewal/response"
                    ),
                    "response_payload_digest": sha256_text(
                        canonical_json(
                            {
                                "verifier_ref": verifier_ref,
                                "recorded_at": renewed_at_iso,
                                "payload_kind": "response",
                            }
                        )
                    ),
                    "recorded_at": renewed_at_iso,
                }
            )
            transport_exchange["digest"] = sha256_text(
                canonical_json(
                    {
                        "exchange_id": transport_exchange["exchange_id"],
                        "verifier_ref": verifier_ref,
                        "challenge_ref": challenge_ref,
                        "request_payload_digest": transport_exchange["request_payload_digest"],
                        "response_payload_digest": transport_exchange["response_payload_digest"],
                        "recorded_at": renewed_at_iso,
                    }
                )
            )
            renewed_receipt.update(
                {
                    "receipt_id": new_id("verifier-network-receipt"),
                    "challenge_ref": challenge_ref,
                    "challenge_digest": challenge_digest,
                    "transport_exchange": transport_exchange,
                    "recorded_at": renewed_at_iso,
                    "observed_latency_ms": round(
                        float(renewed_receipt["observed_latency_ms"]) + 1.0,
                        1,
                    ),
                }
            )
            renewed_receipt["digest"] = sha256_text(
                canonical_json(
                    {
                        "receipt_id": renewed_receipt["receipt_id"],
                        "verifier_ref": verifier_ref,
                        "challenge_ref": challenge_ref,
                        "recorded_at": renewed_at_iso,
                        "transport_exchange_digest": transport_exchange["digest"],
                    }
                )
            )
            renewed_receipts.append(renewed_receipt)
        return self._normalize_remote_verifier_receipts(renewed_receipts)

    def _build_destination_lifecycle(
        self,
        *,
        destination_snapshot_digest: str,
        initial_federation: Mapping[str, Any],
        initial_cadence: Mapping[str, Any],
        renewed_federation: Mapping[str, Any],
        renewed_cadence: Mapping[str, Any],
        recovered_federation: Mapping[str, Any],
        recovered_cadence: Mapping[str, Any],
    ) -> Dict[str, Any]:
        revoked_at = (
            _parse_datetime(
                str(renewed_cadence["attested_at"]),
                "renewed_cadence.attested_at",
            )
            + timedelta(seconds=TRUST_TRANSFER_DESTINATION_REVOCATION_CHECK_OFFSET_SECONDS)
        ).isoformat()
        recovered_at = (
            _parse_datetime(
                str(recovered_cadence["attested_at"]),
                "recovered_cadence.attested_at",
            )
            + timedelta(seconds=TRUST_TRANSFER_DESTINATION_RECOVERY_ATTESTATION_OFFSET_SECONDS)
        ).isoformat()
        history = [
            {
                "sequence": 0,
                "entry_id": new_id("trust-destination-entry"),
                "entry_ref": "trust-destination-entry://imported",
                "event_type": "imported",
                "status": TRUST_TRANSFER_DESTINATION_CURRENT_STATUS,
                "recorded_at": initial_cadence["attested_at"],
                "attested_at": initial_cadence["attested_at"],
                "valid_until": initial_cadence["valid_until"],
                "quorum_policy_id": initial_federation["quorum_policy_id"],
                "federation_ref": initial_federation["federation_ref"],
                "federation_digest": _trust_transfer_federation_binding_digest(
                    initial_federation
                ),
                "cadence_ref": initial_cadence["cadence_ref"],
                "cadence_digest": initial_cadence["receipt_digest"],
                "trust_root_quorum": initial_federation["trust_root_quorum"],
                "jurisdiction_quorum": initial_federation["jurisdiction_quorum"],
                "covered_verifier_receipt_ids": list(
                    initial_cadence["covered_verifier_receipt_ids"]
                ),
                "covered_trust_root_refs": list(initial_federation["trust_root_refs"]),
                "covered_jurisdictions": list(initial_federation["jurisdictions"]),
                "destination_snapshot_digest": destination_snapshot_digest,
                "rationale": "initial destination seed completed with guardian and human attestation",
            },
            {
                "sequence": 1,
                "entry_id": new_id("trust-destination-entry"),
                "entry_ref": "trust-destination-entry://renewed",
                "event_type": "renewed",
                "status": TRUST_TRANSFER_DESTINATION_CURRENT_STATUS,
                "recorded_at": renewed_cadence["attested_at"],
                "attested_at": renewed_cadence["attested_at"],
                "valid_until": renewed_cadence["valid_until"],
                "quorum_policy_id": renewed_federation["quorum_policy_id"],
                "federation_ref": renewed_federation["federation_ref"],
                "federation_digest": _trust_transfer_federation_binding_digest(
                    renewed_federation
                ),
                "cadence_ref": renewed_cadence["cadence_ref"],
                "cadence_digest": renewed_cadence["receipt_digest"],
                "trust_root_quorum": renewed_federation["trust_root_quorum"],
                "jurisdiction_quorum": renewed_federation["jurisdiction_quorum"],
                "covered_verifier_receipt_ids": list(
                    renewed_cadence["covered_verifier_receipt_ids"]
                ),
                "covered_trust_root_refs": list(renewed_federation["trust_root_refs"]),
                "covered_jurisdictions": list(renewed_federation["jurisdictions"]),
                "destination_snapshot_digest": destination_snapshot_digest,
                "rationale": "destination verifier federation renewed before freshness expiry",
            },
            {
                "sequence": 2,
                "entry_id": new_id("trust-destination-entry"),
                "entry_ref": "trust-destination-entry://revoked",
                "event_type": "revoked",
                "status": TRUST_TRANSFER_DESTINATION_REVOKED_STATUS,
                "recorded_at": revoked_at,
                "attested_at": renewed_cadence["attested_at"],
                "valid_until": renewed_cadence["valid_until"],
                "quorum_policy_id": renewed_federation["quorum_policy_id"],
                "federation_ref": renewed_federation["federation_ref"],
                "federation_digest": _trust_transfer_federation_binding_digest(
                    renewed_federation
                ),
                "cadence_ref": renewed_cadence["cadence_ref"],
                "cadence_digest": renewed_cadence["receipt_digest"],
                "trust_root_quorum": renewed_federation["trust_root_quorum"],
                "jurisdiction_quorum": renewed_federation["jurisdiction_quorum"],
                "covered_verifier_receipt_ids": list(
                    renewed_cadence["covered_verifier_receipt_ids"]
                ),
                "covered_trust_root_refs": list(renewed_federation["trust_root_refs"]),
                "covered_jurisdictions": list(renewed_federation["jurisdictions"]),
                "destination_snapshot_digest": destination_snapshot_digest,
                "rationale": "destination revocation signal raised and trust usage was disabled fail-closed",
            },
            {
                "sequence": 3,
                "entry_id": new_id("trust-destination-entry"),
                "entry_ref": "trust-destination-entry://recovered",
                "event_type": "recovered",
                "status": TRUST_TRANSFER_DESTINATION_CURRENT_STATUS,
                "recorded_at": recovered_at,
                "attested_at": recovered_cadence["attested_at"],
                "valid_until": recovered_cadence["valid_until"],
                "quorum_policy_id": recovered_federation["quorum_policy_id"],
                "federation_ref": recovered_federation["federation_ref"],
                "federation_digest": _trust_transfer_federation_binding_digest(
                    recovered_federation
                ),
                "cadence_ref": recovered_cadence["cadence_ref"],
                "cadence_digest": recovered_cadence["receipt_digest"],
                "trust_root_quorum": recovered_federation["trust_root_quorum"],
                "jurisdiction_quorum": recovered_federation["jurisdiction_quorum"],
                "covered_verifier_receipt_ids": list(
                    recovered_cadence["covered_verifier_receipt_ids"]
                ),
                "covered_trust_root_refs": list(recovered_federation["trust_root_refs"]),
                "covered_jurisdictions": list(recovered_federation["jurisdictions"]),
                "destination_snapshot_digest": destination_snapshot_digest,
                "rationale": (
                    "destination trust was re-enabled after multi-root, cross-jurisdiction "
                    "verifier quorum cleared recovery review"
                ),
            },
        ]
        lifecycle = {
            "lifecycle_id": new_id("trust-destination-lifecycle"),
            "lifecycle_ref": (
                f"trust-destination-lifecycle://{recovered_federation['federation_id']}"
            ),
            "lifecycle_policy_id": TRUST_TRANSFER_DESTINATION_LIFECYCLE_POLICY_ID,
            "current_status": TRUST_TRANSFER_DESTINATION_CURRENT_STATUS,
            "active_entry_ref": history[-1]["entry_ref"],
            "latest_federation_ref": recovered_federation["federation_ref"],
            "latest_federation_digest": _trust_transfer_federation_binding_digest(
                recovered_federation
            ),
            "latest_cadence_ref": recovered_cadence["cadence_ref"],
            "latest_cadence_digest": recovered_cadence["receipt_digest"],
            "revocation_fail_closed_action": (
                TRUST_TRANSFER_DESTINATION_REVOCATION_FAIL_CLOSED_ACTION
            ),
            "history": history,
            "lifecycle_digest": "",
        }
        lifecycle["lifecycle_digest"] = sha256_text(
            canonical_json(_trust_transfer_destination_lifecycle_digest_payload(lifecycle))
        )
        return lifecycle

    def _build_redacted_destination_lifecycle_summary(
        self,
        lifecycle: Mapping[str, Any],
    ) -> Dict[str, Any]:
        history = lifecycle.get("history", [])
        if not isinstance(history, list) or not history:
            raise ValueError("destination lifecycle summary requires history entries")
        history_summaries: List[Dict[str, Any]] = []
        for entry in history:
            if not isinstance(entry, Mapping):
                raise ValueError("destination lifecycle summary requires mapping history entries")
            covered_verifier_receipt_ids = entry.get("covered_verifier_receipt_ids", [])
            if not isinstance(covered_verifier_receipt_ids, list):
                raise ValueError(
                    "destination lifecycle summary requires covered_verifier_receipt_ids"
                )
            entry_summary = {
                "sequence": entry["sequence"],
                "event_type": entry["event_type"],
                "status": entry["status"],
                "recorded_at": entry["recorded_at"],
                "valid_until": entry["valid_until"],
                "quorum_policy_id": entry["quorum_policy_id"],
                "federation_digest": entry["federation_digest"],
                "cadence_digest": entry["cadence_digest"],
                "trust_root_quorum": entry["trust_root_quorum"],
                "jurisdiction_quorum": entry["jurisdiction_quorum"],
                "covered_verifier_count": len(covered_verifier_receipt_ids),
                "covered_trust_root_count": len(
                    list(entry.get("covered_trust_root_refs", []))
                ),
                "covered_jurisdiction_count": len(
                    list(entry.get("covered_jurisdictions", []))
                ),
                "covered_verifier_receipt_commitment_digest": (
                    _trust_transfer_covered_verifier_receipt_commitment_digest(
                        [str(receipt_id) for receipt_id in covered_verifier_receipt_ids]
                    )
                ),
                "destination_snapshot_digest": entry["destination_snapshot_digest"],
                "entry_digest": "",
            }
            entry_summary["entry_digest"] = sha256_text(
                canonical_json(
                    _trust_transfer_redacted_destination_lifecycle_entry_summary_digest_payload(
                        entry_summary
                    )
                )
            )
            history_summaries.append(entry_summary)

        active_entry = history_summaries[-1]
        summary = {
            "kind": "trust_redacted_destination_lifecycle",
            "schema_version": TRUST_TRANSFER_REDACTED_DESTINATION_LIFECYCLE_SCHEMA_VERSION,
            "lifecycle_id": lifecycle["lifecycle_id"],
            "lifecycle_ref": lifecycle["lifecycle_ref"],
            "summary_profile_id": TRUST_TRANSFER_REDACTED_DESTINATION_LIFECYCLE_PROFILE_ID,
            "lifecycle_policy_id": lifecycle["lifecycle_policy_id"],
            "current_status": lifecycle["current_status"],
            "active_sequence": active_entry["sequence"],
            "active_entry_digest": active_entry["entry_digest"],
            "latest_federation_digest": lifecycle["latest_federation_digest"],
            "latest_cadence_digest": lifecycle["latest_cadence_digest"],
            "revocation_fail_closed_action": lifecycle["revocation_fail_closed_action"],
            "history_summaries": history_summaries,
            "history_summary_commitment_digest": (
                _trust_transfer_redacted_destination_lifecycle_history_commitment_digest(
                    history_summaries
                )
            ),
            "sealed_lifecycle_digest": lifecycle["lifecycle_digest"],
            "redaction_policy_id": (
                TRUST_TRANSFER_DESTINATION_LIFECYCLE_SUMMARY_REDACTION_POLICY_ID
            ),
            "redacted_fields": list(TRUST_TRANSFER_REDACTED_DESTINATION_LIFECYCLE_FIELDS),
            "summary_digest": "",
        }
        summary["summary_digest"] = sha256_text(
            canonical_json(
                _trust_transfer_redacted_destination_lifecycle_digest_payload(summary)
            )
        )
        return summary

    def _build_redacted_snapshot_projection(
        self,
        *,
        snapshot: Mapping[str, Any],
        snapshot_ref: str,
        snapshot_digest: str,
    ) -> Dict[str, Any]:
        history = snapshot.get("history", [])
        history_entries = [entry for entry in history if isinstance(entry, Mapping)] if isinstance(history, list) else []
        latest_recorded_at = None
        if history_entries:
            latest_recorded_at = max(
                _parse_datetime(
                    str(entry.get("recorded_at", "")),
                    "history[].recorded_at",
                )
                for entry in history_entries
            ).isoformat()
        projection = {
            "kind": "trust_redacted_snapshot",
            "schema_version": TRUST_TRANSFER_REDACTED_SNAPSHOT_SCHEMA_VERSION,
            "projection_id": new_id("trust-redacted-snapshot"),
            "projection_ref": f"trust-redacted-snapshot://{sha256_text(snapshot_ref)[:12]}",
            "projection_profile_id": TRUST_TRANSFER_REDACTED_SNAPSHOT_PROFILE_ID,
            "sealed_snapshot_ref": snapshot_ref,
            "sealed_snapshot_digest": snapshot_digest,
            "agent_id": snapshot["agent_id"],
            "global_score": snapshot["global_score"],
            "per_domain": dict(snapshot["per_domain"]),
            "pinned_by_human": snapshot["pinned_by_human"],
            "thresholds": dict(snapshot["thresholds"]),
            "eligibility": dict(snapshot["eligibility"]),
            "history_summary": {
                "event_count": len(history_entries),
                "applied_event_count": sum(
                    1 for entry in history_entries if entry.get("applied") is True
                ),
                "blocked_event_count": sum(
                    1 for entry in history_entries if entry.get("applied") is not True
                ),
                "event_types": sorted(
                    {
                        str(entry.get("event_type", ""))
                        for entry in history_entries
                        if str(entry.get("event_type", "")).strip()
                    }
                ),
                "domains": sorted(
                    {
                        str(entry.get("domain", ""))
                        for entry in history_entries
                        if str(entry.get("domain", "")).strip()
                    }
                ),
                "provenance_statuses": sorted(
                    {
                        str(entry.get("provenance_status", ""))
                        for entry in history_entries
                        if str(entry.get("provenance_status", "")).strip()
                    }
                ),
                "latest_recorded_at": latest_recorded_at,
                "history_commitment_digest": _trust_transfer_history_commitment_digest(
                    snapshot
                ),
            },
            "redaction_policy_id": TRUST_TRANSFER_HISTORY_REDACTION_POLICY_ID,
            "redacted_fields": list(TRUST_TRANSFER_REDACTED_FIELDS),
            "projection_digest": "",
        }
        projection["projection_digest"] = sha256_text(
            canonical_json(_trust_transfer_redacted_snapshot_digest_payload(projection))
        )
        return projection

    def _normalize_export_profile(self, export_profile_id: str) -> str:
        normalized_profile = self._normalize_non_empty(
            export_profile_id,
            "export_profile_id",
        )
        if normalized_profile not in TRUST_TRANSFER_SUPPORTED_EXPORT_PROFILES:
            raise ValueError(
                "export_profile_id must be one of "
                + ", ".join(TRUST_TRANSFER_SUPPORTED_EXPORT_PROFILES)
            )
        return normalized_profile

    @staticmethod
    def _same_actor(agent_id: str, triggered_by: str, triggered_by_agent_id: str) -> bool:
        if triggered_by_agent_id:
            return triggered_by_agent_id == agent_id
        return _actor_fingerprint(agent_id) == _actor_fingerprint(triggered_by)

    @staticmethod
    def _require_mapping_field(value: Any, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, Mapping):
            errors.append(f"{field_name} must be a mapping")

    @staticmethod
    def _require_non_empty_string(value: Any, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty string")

    @staticmethod
    def _normalize_remote_verifier_receipts(
        receipts: Any,
    ) -> List[Dict[str, Any]]:
        if not isinstance(receipts, list):
            raise ValueError("remote_verifier_receipts must be a list")
        normalized: List[Dict[str, Any]] = []
        for index, receipt in enumerate(receipts):
            if not isinstance(receipt, Mapping):
                raise ValueError(f"remote_verifier_receipts[{index}] must be a mapping")
            normalized_receipt = dict(receipt)
            required_strings = (
                "receipt_id",
                "verifier_endpoint",
                "verifier_ref",
                "jurisdiction",
                "network_profile_id",
                "challenge_ref",
                "challenge_digest",
                "authority_chain_ref",
                "trust_root_ref",
                "trust_root_digest",
                "recorded_at",
                "receipt_status",
                "digest",
            )
            for field_name in required_strings:
                if not isinstance(normalized_receipt.get(field_name), str) or not str(
                    normalized_receipt.get(field_name)
                ).strip():
                    raise ValueError(
                        f"remote_verifier_receipts[{index}].{field_name} must be a non-empty string"
                    )
            if (
                normalized_receipt["network_profile_id"]
                != TRUST_TRANSFER_REMOTE_VERIFIER_NETWORK_PROFILE_ID
            ):
                raise ValueError(
                    "remote_verifier_receipts["
                    f"{index}"
                    "].network_profile_id must equal "
                    f"{TRUST_TRANSFER_REMOTE_VERIFIER_NETWORK_PROFILE_ID}"
                )
            if normalized_receipt["receipt_status"] != "verified":
                raise ValueError(
                    f"remote_verifier_receipts[{index}].receipt_status must equal verified"
                )
            freshness_window_seconds = normalized_receipt.get("freshness_window_seconds")
            if not isinstance(freshness_window_seconds, int) or freshness_window_seconds < 1:
                raise ValueError(
                    "remote_verifier_receipts["
                    f"{index}"
                    "].freshness_window_seconds must be a positive integer"
                )
            observed_latency_ms = normalized_receipt.get("observed_latency_ms")
            if not isinstance(observed_latency_ms, (int, float)) or observed_latency_ms < 0:
                raise ValueError(
                    "remote_verifier_receipts["
                    f"{index}"
                    "].observed_latency_ms must be a non-negative number"
                )
            _parse_datetime(
                normalized_receipt["recorded_at"],
                f"remote_verifier_receipts[{index}].recorded_at",
            )
            transport_exchange = normalized_receipt.get("transport_exchange")
            if not isinstance(transport_exchange, Mapping):
                raise ValueError(
                    f"remote_verifier_receipts[{index}].transport_exchange must be a mapping"
                )
            for field_name in (
                "exchange_id",
                "request_payload_digest",
                "response_payload_digest",
                "digest",
            ):
                if not isinstance(transport_exchange.get(field_name), str) or not str(
                    transport_exchange.get(field_name)
                ).strip():
                    raise ValueError(
                        "remote_verifier_receipts["
                        f"{index}"
                        f"].transport_exchange.{field_name} must be a non-empty string"
                    )
            normalized.append(normalized_receipt)
        verifier_refs = [normalized_receipt["verifier_ref"] for normalized_receipt in normalized]
        if len(normalized) < TRUST_TRANSFER_REQUIRED_REMOTE_VERIFIER_COUNT:
            raise ValueError(
                "remote_verifier_receipts must contain "
                f"at least {TRUST_TRANSFER_REQUIRED_REMOTE_VERIFIER_COUNT} verified receipts"
            )
        if len(set(verifier_refs)) != len(verifier_refs):
            raise ValueError("remote_verifier_receipts must use distinct verifier_ref values")
        return normalized

    @staticmethod
    def _normalize_non_empty(value: str, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value.strip()
