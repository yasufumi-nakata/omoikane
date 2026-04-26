"""Bounded collective identity and merge-thought reference model."""

from __future__ import annotations

from copy import deepcopy
import json
import time
from typing import Any, Dict, List, Mapping, Sequence, Set
from urllib import error, request

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

COLLECTIVE_SCHEMA_VERSION = "1.0"
COLLECTIVE_MIN_MEMBERS = 2
COLLECTIVE_MAX_MEMBERS = 4
COLLECTIVE_MAX_DURATION_SECONDS = 10.0
COLLECTIVE_ALLOWED_STATUSES = {"active", "recovery", "dissolved"}
COLLECTIVE_ALLOWED_MERGE_STATUSES = {"open", "completed", "recovery-required"}
COLLECTIVE_ALLOWED_WMS_MODES = {"shared_reality", "private_reality", "mixed"}
COLLECTIVE_DISSOLUTION_RECOVERY_BINDING_PROFILE_ID = (
    "collective-dissolution-identity-confirmation-binding-v1"
)
COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID = (
    "collective-dissolution-recovery-verifier-transport-v1"
)
COLLECTIVE_RECOVERY_ROUTE_TRACE_PROFILE_ID = (
    "collective-recovery-non-loopback-route-trace-binding-v1"
)
COLLECTIVE_RECOVERY_ROUTE_TRACE_DIGEST_PROFILE_ID = (
    "collective-recovery-route-trace-binding-digest-v1"
)
COLLECTIVE_RECOVERY_CAPTURE_EXPORT_PROFILE_ID = (
    "collective-recovery-route-trace-capture-export-v1"
)
COLLECTIVE_RECOVERY_CAPTURE_EXPORT_DIGEST_PROFILE_ID = (
    "collective-recovery-capture-export-binding-digest-v1"
)
COLLECTIVE_EXTERNAL_REGISTRY_SYNC_PROFILE_ID = (
    "collective-dissolution-external-registry-sync-v1"
)
COLLECTIVE_EXTERNAL_REGISTRY_SYNC_DIGEST_PROFILE_ID = (
    "collective-external-registry-sync-digest-v1"
)
COLLECTIVE_EXTERNAL_REGISTRY_ENTRY_DIGEST_PROFILE_ID = (
    "collective-external-registry-entry-digest-v1"
)
COLLECTIVE_EXTERNAL_REGISTRY_SUBMISSION_PROFILE_ID = (
    "collective-external-registry-submission-v1"
)
COLLECTIVE_EXTERNAL_REGISTRY_ACK_PROFILE_ID = "collective-external-registry-ack-v1"
COLLECTIVE_EXTERNAL_REGISTRY_ACK_QUORUM_PROFILE_ID = (
    "collective-external-registry-ack-quorum-v1"
)
COLLECTIVE_EXTERNAL_REGISTRY_ACK_QUORUM_DIGEST_PROFILE_ID = (
    "collective-external-registry-ack-quorum-digest-v1"
)
COLLECTIVE_EXTERNAL_REGISTRY_ACK_QUORUM_REQUIRED_AUTHORITIES = 2
COLLECTIVE_EXTERNAL_REGISTRY_ACK_QUORUM_REQUIRED_JURISDICTIONS = 2
COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_TRACE_PROFILE_ID = (
    "collective-external-registry-ack-route-trace-v1"
)
COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_TRACE_DIGEST_PROFILE_ID = (
    "collective-external-registry-ack-route-trace-digest-v1"
)
COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_CAPTURE_EXPORT_PROFILE_ID = (
    "collective-external-registry-ack-route-capture-export-v1"
)
COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_CAPTURE_EXPORT_DIGEST_PROFILE_ID = (
    "collective-external-registry-ack-route-capture-export-digest-v1"
)
COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_PROFILE_ID = (
    "collective-external-registry-ack-live-endpoint-probe-v1"
)
COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_DIGEST_PROFILE_ID = (
    "collective-external-registry-ack-live-endpoint-probe-digest-v1"
)
COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_TRANSPORT_PROFILE = (
    "live-http-json-collective-registry-ack-v1"
)
COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_LATENCY_BUDGET_MS = 1_000.0
COLLECTIVE_PACKET_CAPTURE_PROFILE = "trace-bound-pcap-export-v1"
COLLECTIVE_PACKET_CAPTURE_FORMAT = "pcap"
COLLECTIVE_PRIVILEGED_CAPTURE_PROFILE = "bounded-live-interface-capture-acquisition-v1"
COLLECTIVE_PRIVILEGED_CAPTURE_MODE = "delegated-broker"
COLLECTIVE_IDENTITY_CONFIRMATION_PROFILE_ID = "multidimensional-identity-confirmation-v1"
COLLECTIVE_IDENTITY_CONFIRMATION_CONSISTENCY_POLICY_ID = (
    "identity-self-report-witness-consistency-v1"
)
COLLECTIVE_VERIFIER_NETWORK_PROFILE_ID = "guardian-reviewer-remote-attestation-v1"
COLLECTIVE_VERIFIER_TRANSPORT_PROFILE = "reviewer-live-proof-bridge-v1"
COLLECTIVE_VERIFIER_TRANSPORT_EXCHANGE_PROFILE_ID = (
    "digest-bound-reviewer-transport-exchange-v1"
)
COLLECTIVE_RECOVERY_VERIFIER_JURISDICTIONS = ["JP-13", "US-CA", "EU-DE", "SG-01"]
COLLECTIVE_REQUIRED_IDENTITY_CONFIRMATION_DIMENSIONS = [
    "episodic_recall",
    "self_model_alignment",
    "subjective_self_report",
    "third_party_witness_alignment",
]


def _dedupe_preserve_order(values: Sequence[str]) -> List[str]:
    seen: Set[str] = set()
    ordered: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _is_live_http_endpoint(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


class CollectiveIdentityService:
    """Deterministic reference model for bounded collective identity formation."""

    def __init__(self) -> None:
        self.records: Dict[str, Dict[str, Any]] = {}
        self.merge_sessions: Dict[str, Dict[str, Any]] = {}

    def reference_profile(self) -> Dict[str, Any]:
        return {
            "schema_version": COLLECTIVE_SCHEMA_VERSION,
            "formation_mode": "bounded-collective-merge-v0",
            "member_count_bounds": {
                "min": COLLECTIVE_MIN_MEMBERS,
                "max": COLLECTIVE_MAX_MEMBERS,
            },
            "governance_mode": "meta-council",
            "merge_policy": {
                "merge_mode": "merge_thought",
                "max_duration_seconds": COLLECTIVE_MAX_DURATION_SECONDS,
                "single_active_merge_per_collective": True,
                "council_witness_required": True,
                "federation_attestation_required": True,
                "guardian_observation_required": True,
                "post_disconnect_identity_confirmation": "all-members",
                "escape_route": "private_reality",
            },
            "dissolution_policy": {
                "member_quorum": "unanimous",
                "active_merge_required": False,
                "member_recovery_required": True,
                "member_recovery_binding_profile": COLLECTIVE_DISSOLUTION_RECOVERY_BINDING_PROFILE_ID,
                "identity_confirmation_profile": COLLECTIVE_IDENTITY_CONFIRMATION_PROFILE_ID,
                "member_recovery_verifier_transport_profile": (
                    COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID
                ),
                "member_recovery_route_trace_profile": COLLECTIVE_RECOVERY_ROUTE_TRACE_PROFILE_ID,
                "member_recovery_capture_export_profile": (
                    COLLECTIVE_RECOVERY_CAPTURE_EXPORT_PROFILE_ID
                ),
                "external_registry_sync_profile": (
                    COLLECTIVE_EXTERNAL_REGISTRY_SYNC_PROFILE_ID
                ),
                "external_registry_ack_quorum_profile": (
                    COLLECTIVE_EXTERNAL_REGISTRY_ACK_QUORUM_PROFILE_ID
                ),
                "external_registry_ack_route_trace_profile": (
                    COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_TRACE_PROFILE_ID
                ),
                "external_registry_ack_route_capture_export_profile": (
                    COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_CAPTURE_EXPORT_PROFILE_ID
                ),
                "external_registry_ack_live_endpoint_probe_profile": (
                    COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_PROFILE_ID
                ),
                "raw_identity_confirmation_profiles_stored": False,
                "raw_external_registry_payload_stored": False,
                "raw_external_registry_ack_endpoint_payload_stored": False,
            },
        }

    def register_collective(
        self,
        *,
        collective_identity_id: str,
        member_ids: Sequence[str],
        purpose: str,
        proposed_name: str,
        council_witnessed: bool,
        federation_attested: bool,
        guardian_observed: bool,
    ) -> Dict[str, Any]:
        collective_id = self._normalize_non_empty_string(collective_identity_id, "collective_identity_id")
        if collective_id in self.records:
            raise ValueError(f"collective already registered: {collective_id}")

        members = self._normalize_member_ids(member_ids)
        purpose_text = self._normalize_non_empty_string(purpose, "purpose")
        proposed_name_text = self._normalize_non_empty_string(proposed_name, "proposed_name")
        self._require_oversight(
            council_witnessed=council_witnessed,
            federation_attested=federation_attested,
            guardian_observed=guardian_observed,
        )

        created_at = utc_now_iso()
        record = {
            "schema_version": COLLECTIVE_SCHEMA_VERSION,
            "collective_id": collective_id,
            "created_at": created_at,
            "display_name": proposed_name_text,
            "status": "active",
            "member_ids": members,
            "governance_mode": "meta-council",
            "formation_mode": "bounded-collective-merge-v0",
            "purpose": purpose_text,
            "merge_policy": {
                "merge_mode": "merge_thought",
                "max_duration_seconds": COLLECTIVE_MAX_DURATION_SECONDS,
                "post_disconnect_identity_confirmation": "all-members",
                "escape_route": "private_reality",
                "single_active_merge_per_collective": True,
            },
            "oversight": {
                "council_witnessed": True,
                "federation_attested": True,
                "guardian_observed": True,
            },
            "active_merge_session_ids": [],
            "last_merge_status": "none",
            "dissolved_at": None,
            "last_dissolution": None,
        }
        self.records[collective_id] = record
        return deepcopy(record)

    def open_merge_session(
        self,
        *,
        collective_id: str,
        imc_session_id: str,
        wms_session_id: str,
        requested_duration_seconds: float,
        council_witnessed: bool,
        federation_attested: bool,
        guardian_observed: bool,
        shared_world_mode: str,
    ) -> Dict[str, Any]:
        record = self._require_record(collective_id)
        if record["status"] != "active":
            raise ValueError("collective must be active before opening a merge session")
        if record["active_merge_session_ids"]:
            raise ValueError("collective already has an active merge session")

        self._require_oversight(
            council_witnessed=council_witnessed,
            federation_attested=federation_attested,
            guardian_observed=guardian_observed,
        )
        imc_ref = self._normalize_non_empty_string(imc_session_id, "imc_session_id")
        wms_ref = self._normalize_non_empty_string(wms_session_id, "wms_session_id")
        requested = self._normalize_duration(requested_duration_seconds, "requested_duration_seconds")
        granted = min(requested, COLLECTIVE_MAX_DURATION_SECONDS)
        mode = self._normalize_wms_mode(shared_world_mode, "shared_world_mode")
        merge_session_id = new_id("collective-merge")
        opened_at = utc_now_iso()
        session = {
            "schema_version": COLLECTIVE_SCHEMA_VERSION,
            "merge_session_id": merge_session_id,
            "collective_id": record["collective_id"],
            "opened_at": opened_at,
            "closed_at": None,
            "status": "open",
            "merge_mode": "merge_thought",
            "imc_session_id": imc_ref,
            "wms_session_id": wms_ref,
            "requested_duration_seconds": requested,
            "granted_duration_seconds": granted,
            "duration_capped": requested > COLLECTIVE_MAX_DURATION_SECONDS,
            "shared_world_mode": mode,
            "oversight": {
                "council_witnessed": True,
                "federation_attested": True,
                "guardian_observed": True,
            },
            "identity_confirmation_required": list(record["member_ids"]),
            "disconnect_reason": "",
            "identity_confirmations": {},
            "time_in_merge_seconds": None,
            "within_budget": None,
            "resulting_wms_mode": None,
            "private_escape_honored": False,
            "audit_event_ref": "",
        }
        self.merge_sessions[merge_session_id] = session
        record["active_merge_session_ids"].append(merge_session_id)
        record["last_merge_status"] = "open"
        return deepcopy(session)

    def close_merge_session(
        self,
        merge_session_id: str,
        *,
        disconnect_reason: str,
        time_in_merge_seconds: float,
        resulting_wms_mode: str,
        identity_confirmations: Mapping[str, bool],
    ) -> Dict[str, Any]:
        session = self._require_merge_session(merge_session_id)
        if session["status"] != "open":
            raise ValueError("merge session must be open before it can be closed")

        reason_text = self._normalize_non_empty_string(disconnect_reason, "disconnect_reason")
        elapsed = self._normalize_duration(time_in_merge_seconds, "time_in_merge_seconds")
        resulting_mode = self._normalize_wms_mode(resulting_wms_mode, "resulting_wms_mode")
        confirmations = self._normalize_confirmations(
            identity_confirmations,
            session["identity_confirmation_required"],
        )
        within_budget = elapsed <= session["granted_duration_seconds"]
        all_confirmed = all(confirmations.values())
        status = "completed" if within_budget and all_confirmed else "recovery-required"
        closed_at = utc_now_iso()

        session["closed_at"] = closed_at
        session["status"] = status
        session["disconnect_reason"] = reason_text
        session["identity_confirmations"] = confirmations
        session["time_in_merge_seconds"] = elapsed
        session["within_budget"] = within_budget
        session["resulting_wms_mode"] = resulting_mode
        session["private_escape_honored"] = resulting_mode == "private_reality"
        session["audit_event_ref"] = f"ledger://collective-merge/{new_id('collective-audit')}"

        record = self._require_record(session["collective_id"])
        record["active_merge_session_ids"] = [
            merge_id for merge_id in record["active_merge_session_ids"] if merge_id != merge_session_id
        ]
        record["last_merge_status"] = status
        if status == "recovery-required":
            record["status"] = "recovery"

        return deepcopy(session)

    def dissolve_collective(
        self,
        collective_id: str,
        *,
        requested_by: str,
        member_confirmations: Mapping[str, bool],
        identity_confirmation_profiles: Mapping[str, Mapping[str, Any]],
        reason: str,
    ) -> Dict[str, Any]:
        record = self._require_record(collective_id)
        if record["active_merge_session_ids"]:
            raise ValueError("cannot dissolve a collective while a merge session is active")

        requester = self._normalize_non_empty_string(requested_by, "requested_by")
        reason_text = self._normalize_non_empty_string(reason, "reason")
        confirmations = self._normalize_confirmations(member_confirmations, record["member_ids"])
        if not all(confirmations.values()):
            raise PermissionError("dissolution requires unanimous member confirmation")
        recovery_proofs = self._derive_member_recovery_proofs(
            identity_confirmation_profiles,
            record["member_ids"],
        )
        recovery_digest_set = [
            proof["identity_confirmation_digest"] for proof in recovery_proofs.values()
        ]

        dissolved_at = utc_now_iso()
        recovery_binding_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": COLLECTIVE_DISSOLUTION_RECOVERY_BINDING_PROFILE_ID,
                    "collective_id": record["collective_id"],
                    "member_ids": record["member_ids"],
                    "member_recovery_proofs": recovery_proofs,
                    "member_recovery_confirmation_digest_set": recovery_digest_set,
                }
            )
        )
        receipt = {
            "schema_version": COLLECTIVE_SCHEMA_VERSION,
            "collective_id": record["collective_id"],
            "recorded_at": dissolved_at,
            "requested_by": requester,
            "status": "dissolved",
            "member_confirmations": confirmations,
            "reason": reason_text,
            "member_recovery_required": True,
            "member_recovery_binding_profile": COLLECTIVE_DISSOLUTION_RECOVERY_BINDING_PROFILE_ID,
            "member_recovery_proofs": recovery_proofs,
            "member_recovery_confirmation_digest_set": recovery_digest_set,
            "member_recovery_binding_digest": recovery_binding_digest,
            "raw_identity_confirmation_profiles_stored": False,
            "audit_event_ref": f"ledger://collective-dissolution/{new_id('collective-dissolution')}",
        }
        record["status"] = "dissolved"
        record["dissolved_at"] = dissolved_at
        record["last_dissolution"] = receipt
        return deepcopy(receipt)

    def bind_recovery_verifier_transport(
        self,
        dissolution_receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        dissolution_validation = self.validate_dissolution_receipt(dissolution_receipt)
        if not dissolution_validation["ok"]:
            raise ValueError(
                "dissolution_receipt must pass validation before verifier transport binding"
            )

        collective_id = str(dissolution_receipt["collective_id"])
        recovery_proofs = dissolution_receipt["member_recovery_proofs"]
        member_ids = list(dissolution_receipt["member_confirmations"])
        member_recovery_binding_digest = str(
            dissolution_receipt["member_recovery_binding_digest"]
        )
        dissolution_receipt_digest = sha256_text(canonical_json(dissolution_receipt))
        recorded_at = utc_now_iso()

        verifier_receipts: Dict[str, Dict[str, Any]] = {}
        verifier_digest_set: List[str] = []
        for index, member_id in enumerate(member_ids):
            proof = recovery_proofs[member_id]
            receipt = self._build_member_recovery_verifier_transport_receipt(
                collective_id=collective_id,
                member_id=member_id,
                proof=proof,
                member_recovery_binding_digest=member_recovery_binding_digest,
                dissolution_receipt_digest=dissolution_receipt_digest,
                recorded_at=recorded_at,
                index=index,
            )
            verifier_receipts[member_id] = receipt
            verifier_digest_set.append(receipt["digest"])

        binding_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID,
                    "collective_id": collective_id,
                    "member_ids": member_ids,
                    "dissolution_receipt_digest": dissolution_receipt_digest,
                    "member_recovery_binding_digest": member_recovery_binding_digest,
                    "verifier_transport_digest_set": verifier_digest_set,
                }
            )
        )
        return {
            "kind": "collective_recovery_verifier_transport_binding",
            "schema_version": "1.0.0",
            "profile_id": COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID,
            "collective_id": collective_id,
            "recorded_at": recorded_at,
            "status": "verified",
            "dissolution_receipt_digest": dissolution_receipt_digest,
            "member_recovery_binding_digest": member_recovery_binding_digest,
            "member_recovery_confirmation_digest_set": list(
                dissolution_receipt["member_recovery_confirmation_digest_set"]
            ),
            "verifier_transport_receipts": verifier_receipts,
            "verifier_transport_digest_set": verifier_digest_set,
            "verifier_transport_binding_digest": binding_digest,
            "verifier_transport_receipt_count": len(verifier_receipts),
            "all_member_recovery_proofs_transport_bound": True,
            "all_verifier_transport_receipts_verified": True,
            "raw_verifier_payload_stored": False,
        }

    def bind_recovery_verifier_route_trace(
        self,
        recovery_verifier_transport_binding: Mapping[str, Any],
        authority_route_trace: Mapping[str, Any],
    ) -> Dict[str, Any]:
        transport_validation = self.validate_recovery_verifier_transport_binding(
            recovery_verifier_transport_binding,
        )
        if not transport_validation["ok"]:
            raise ValueError(
                "recovery_verifier_transport_binding must pass validation before route trace binding"
            )
        self._validate_authority_route_trace_contract(authority_route_trace)

        verifier_receipts = recovery_verifier_transport_binding[
            "verifier_transport_receipts"
        ]
        if not isinstance(verifier_receipts, Mapping):
            raise ValueError("verifier_transport_receipts must be an object")
        route_bindings = authority_route_trace["route_bindings"]
        if len(route_bindings) < len(verifier_receipts):
            raise ValueError("authority_route_trace must cover every recovery verifier receipt")

        member_route_bindings: List[Dict[str, Any]] = []
        member_route_binding_digests: List[str] = []
        for index, (member_id, verifier_receipt) in enumerate(verifier_receipts.items()):
            if not isinstance(verifier_receipt, Mapping):
                raise ValueError(f"verifier transport receipt for {member_id} must be an object")
            route_binding = route_bindings[index]
            if not isinstance(route_binding, Mapping):
                raise ValueError(f"route_bindings[{index}] must be an object")
            socket_trace = route_binding.get("socket_trace")
            if not isinstance(socket_trace, Mapping):
                raise ValueError(f"route_bindings[{index}].socket_trace must be an object")
            os_observer = route_binding.get("os_observer_receipt")
            if not isinstance(os_observer, Mapping):
                raise ValueError(
                    f"route_bindings[{index}].os_observer_receipt must be an object"
                )

            route_binding_digest = self._collective_member_route_binding_digest(
                member_id=member_id,
                verifier_receipt_digest=str(verifier_receipt["digest"]),
                authority_route_trace_digest=str(authority_route_trace["digest"]),
                route_binding_ref=str(route_binding["route_binding_ref"]),
                response_digest=str(socket_trace["response_digest"]),
                remote_host_ref=str(route_binding["remote_host_ref"]),
                remote_host_attestation_ref=str(
                    route_binding["remote_host_attestation_ref"]
                ),
                authority_cluster_ref=str(route_binding["authority_cluster_ref"]),
            )
            member_route_bindings.append(
                {
                    "member_id": member_id,
                    "verifier_transport_receipt_id": verifier_receipt["receipt_id"],
                    "verifier_transport_receipt_digest": verifier_receipt["digest"],
                    "verifier_ref": verifier_receipt["verifier_ref"],
                    "jurisdiction": verifier_receipt["jurisdiction"],
                    "route_binding_ref": route_binding["route_binding_ref"],
                    "remote_host_ref": route_binding["remote_host_ref"],
                    "remote_host_attestation_ref": route_binding[
                        "remote_host_attestation_ref"
                    ],
                    "authority_cluster_ref": route_binding["authority_cluster_ref"],
                    "remote_jurisdiction": route_binding["remote_jurisdiction"],
                    "remote_network_zone": route_binding["remote_network_zone"],
                    "os_observer_receipt_id": os_observer["receipt_id"],
                    "os_observer_host_binding_digest": os_observer[
                        "host_binding_digest"
                    ],
                    "socket_response_digest": socket_trace["response_digest"],
                    "mtls_status": route_binding["mtls_status"],
                    "member_route_binding_digest": route_binding_digest,
                }
            )
            member_route_binding_digests.append(route_binding_digest)

        route_binding_refs = [
            item["route_binding_ref"] for item in member_route_bindings
        ]
        remote_host_refs = [item["remote_host_ref"] for item in member_route_bindings]
        remote_host_attestation_refs = [
            item["remote_host_attestation_ref"] for item in member_route_bindings
        ]
        recorded_at = utc_now_iso()
        digest_payload = {
            "profile_id": COLLECTIVE_RECOVERY_ROUTE_TRACE_PROFILE_ID,
            "collective_id": recovery_verifier_transport_binding["collective_id"],
            "recovery_verifier_transport_binding_digest": (
                recovery_verifier_transport_binding[
                    "verifier_transport_binding_digest"
                ]
            ),
            "authority_route_trace_digest": authority_route_trace["digest"],
            "member_route_binding_digest_set": member_route_binding_digests,
        }
        receipt = {
            "kind": "collective_recovery_route_trace_binding",
            "schema_version": "1.0.0",
            "profile_id": COLLECTIVE_RECOVERY_ROUTE_TRACE_PROFILE_ID,
            "digest_profile": COLLECTIVE_RECOVERY_ROUTE_TRACE_DIGEST_PROFILE_ID,
            "collective_id": recovery_verifier_transport_binding["collective_id"],
            "recorded_at": recorded_at,
            "status": "route-trace-bound",
            "recovery_verifier_transport_profile_id": (
                COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID
            ),
            "recovery_verifier_transport_binding_digest": (
                recovery_verifier_transport_binding[
                    "verifier_transport_binding_digest"
                ]
            ),
            "verifier_transport_digest_set_digest": sha256_text(
                canonical_json(
                    recovery_verifier_transport_binding[
                        "verifier_transport_digest_set"
                    ]
                )
            ),
            "dissolution_receipt_digest": recovery_verifier_transport_binding[
                "dissolution_receipt_digest"
            ],
            "member_recovery_binding_digest": recovery_verifier_transport_binding[
                "member_recovery_binding_digest"
            ],
            "authority_route_trace_ref": authority_route_trace["trace_ref"],
            "authority_route_trace_digest": authority_route_trace["digest"],
            "authority_plane_ref": authority_route_trace["authority_plane_ref"],
            "authority_plane_digest": authority_route_trace["authority_plane_digest"],
            "route_target_discovery_ref": authority_route_trace[
                "route_target_discovery_ref"
            ],
            "route_target_discovery_digest": authority_route_trace[
                "route_target_discovery_digest"
            ],
            "council_tier": authority_route_trace["council_tier"],
            "transport_profile": authority_route_trace["transport_profile"],
            "trace_profile": authority_route_trace["trace_profile"],
            "socket_trace_profile": authority_route_trace["socket_trace_profile"],
            "os_observer_profile": authority_route_trace["os_observer_profile"],
            "cross_host_binding_profile": authority_route_trace[
                "cross_host_binding_profile"
            ],
            "route_target_discovery_profile": authority_route_trace[
                "route_target_discovery_profile"
            ],
            "route_count": authority_route_trace["route_count"],
            "mtls_authenticated_count": authority_route_trace[
                "mtls_authenticated_count"
            ],
            "distinct_remote_host_count": authority_route_trace[
                "distinct_remote_host_count"
            ],
            "route_binding_refs": route_binding_refs,
            "remote_host_refs": remote_host_refs,
            "remote_host_attestation_refs": remote_host_attestation_refs,
            "member_route_bindings": member_route_bindings,
            "member_route_binding_digest_set": member_route_binding_digests,
            "member_route_binding_digest_set_digest": sha256_text(
                canonical_json(member_route_binding_digests)
            ),
            "member_route_binding_count": len(member_route_bindings),
            "recovery_transport_bound": True,
            "authority_route_trace_bound": True,
            "all_member_receipts_route_traced": True,
            "non_loopback_verified": authority_route_trace["non_loopback_verified"],
            "cross_host_verified": authority_route_trace["cross_host_verified"],
            "socket_trace_complete": authority_route_trace["socket_trace_complete"],
            "os_observer_complete": authority_route_trace["os_observer_complete"],
            "route_target_discovery_bound": authority_route_trace[
                "route_target_discovery_bound"
            ],
            "raw_verifier_payload_stored": False,
            "raw_route_payload_stored": False,
            "digest": sha256_text(canonical_json(digest_payload)),
        }
        return deepcopy(receipt)

    def bind_recovery_route_trace_capture_export(
        self,
        recovery_route_trace_binding: Mapping[str, Any],
        packet_capture_export: Mapping[str, Any],
        privileged_capture_acquisition: Mapping[str, Any],
    ) -> Dict[str, Any]:
        route_trace_validation = self.validate_recovery_verifier_route_trace_binding(
            recovery_route_trace_binding,
        )
        if not route_trace_validation["ok"]:
            raise ValueError(
                "recovery_route_trace_binding must pass validation before capture export binding"
            )
        capture_validation = self._validate_packet_capture_export(
            packet_capture_export,
            recovery_route_trace_binding=recovery_route_trace_binding,
        )
        acquisition_validation = self._validate_privileged_capture_acquisition(
            privileged_capture_acquisition,
            recovery_route_trace_binding=recovery_route_trace_binding,
            packet_capture_export=packet_capture_export,
        )
        if not capture_validation["ok"]:
            raise ValueError("packet_capture_export must validate before binding")
        if not acquisition_validation["ok"]:
            raise ValueError("privileged_capture_acquisition must validate before binding")

        route_binding_refs = list(recovery_route_trace_binding["route_binding_refs"])
        route_binding_set_digest = sha256_text(canonical_json(route_binding_refs))
        capture_route_binding_refs = capture_validation["route_binding_refs"]
        capture_route_binding_set_digest = sha256_text(
            canonical_json(capture_route_binding_refs)
        )
        acquisition_route_binding_refs = list(
            privileged_capture_acquisition["route_binding_refs"]
        )
        acquisition_route_binding_set_digest = sha256_text(
            canonical_json(sorted(acquisition_route_binding_refs))
        )
        route_binding_set_bound = (
            route_binding_set_digest == capture_route_binding_set_digest
            and sorted(route_binding_refs) == sorted(acquisition_route_binding_refs)
        )

        route_exports_by_ref = {
            route_export["route_binding_ref"]: route_export
            for route_export in packet_capture_export["route_exports"]
            if isinstance(route_export, Mapping)
        }
        member_capture_bindings: List[Dict[str, Any]] = []
        member_capture_binding_digests: List[str] = []
        for member_route_binding in recovery_route_trace_binding["member_route_bindings"]:
            route_binding_ref = member_route_binding["route_binding_ref"]
            route_export = route_exports_by_ref.get(route_binding_ref)
            if not isinstance(route_export, Mapping):
                raise ValueError(
                    f"packet_capture_export missing route export for {route_binding_ref}"
                )
            route_export_digest = sha256_text(canonical_json(route_export))
            member_capture_digest = self._collective_member_capture_binding_digest(
                collective_id=str(recovery_route_trace_binding["collective_id"]),
                member_id=str(member_route_binding["member_id"]),
                recovery_route_trace_binding_digest=str(
                    recovery_route_trace_binding["digest"]
                ),
                member_route_binding_digest=str(
                    member_route_binding["member_route_binding_digest"]
                ),
                packet_capture_digest=str(packet_capture_export["digest"]),
                privileged_capture_digest=str(privileged_capture_acquisition["digest"]),
                route_binding_ref=str(route_binding_ref),
                route_export_digest=route_export_digest,
            )
            member_capture_bindings.append(
                {
                    "member_id": member_route_binding["member_id"],
                    "verifier_transport_receipt_digest": member_route_binding[
                        "verifier_transport_receipt_digest"
                    ],
                    "member_route_binding_digest": member_route_binding[
                        "member_route_binding_digest"
                    ],
                    "route_binding_ref": route_binding_ref,
                    "packet_capture_route_export_digest": route_export_digest,
                    "outbound_tuple_digest": route_export["outbound_tuple_digest"],
                    "inbound_tuple_digest": route_export["inbound_tuple_digest"],
                    "outbound_payload_digest": route_export["outbound_payload_digest"],
                    "inbound_payload_digest": route_export["inbound_payload_digest"],
                    "readback_packet_count": route_export["readback_packet_count"],
                    "readback_verified": route_export["readback_verified"],
                    "os_native_readback_verified": route_export.get(
                        "os_native_readback_verified",
                        False,
                    ),
                    "privileged_capture_route_ref": route_binding_ref,
                    "member_capture_binding_digest": member_capture_digest,
                }
            )
            member_capture_binding_digests.append(member_capture_digest)

        complete = (
            route_trace_validation["ok"]
            and capture_validation["ok"]
            and acquisition_validation["ok"]
            and route_binding_set_bound
            and bool(member_capture_bindings)
        )
        digest_payload = {
            "profile_id": COLLECTIVE_RECOVERY_CAPTURE_EXPORT_PROFILE_ID,
            "collective_id": recovery_route_trace_binding["collective_id"],
            "recovery_route_trace_binding_digest": recovery_route_trace_binding["digest"],
            "packet_capture_digest": packet_capture_export["digest"],
            "privileged_capture_digest": privileged_capture_acquisition["digest"],
            "member_capture_binding_digest_set": member_capture_binding_digests,
        }
        receipt = {
            "kind": "collective_recovery_capture_export_binding",
            "schema_version": "1.0.0",
            "profile_id": COLLECTIVE_RECOVERY_CAPTURE_EXPORT_PROFILE_ID,
            "digest_profile": COLLECTIVE_RECOVERY_CAPTURE_EXPORT_DIGEST_PROFILE_ID,
            "collective_id": recovery_route_trace_binding["collective_id"],
            "recorded_at": utc_now_iso(),
            "status": "capture-export-bound" if complete else "capture-export-incomplete",
            "recovery_route_trace_profile_id": COLLECTIVE_RECOVERY_ROUTE_TRACE_PROFILE_ID,
            "recovery_route_trace_binding_digest": recovery_route_trace_binding["digest"],
            "recovery_verifier_transport_binding_digest": (
                recovery_route_trace_binding[
                    "recovery_verifier_transport_binding_digest"
                ]
            ),
            "dissolution_receipt_digest": recovery_route_trace_binding[
                "dissolution_receipt_digest"
            ],
            "member_recovery_binding_digest": recovery_route_trace_binding[
                "member_recovery_binding_digest"
            ],
            "authority_route_trace_ref": recovery_route_trace_binding[
                "authority_route_trace_ref"
            ],
            "authority_route_trace_digest": recovery_route_trace_binding[
                "authority_route_trace_digest"
            ],
            "authority_plane_ref": recovery_route_trace_binding["authority_plane_ref"],
            "authority_plane_digest": recovery_route_trace_binding[
                "authority_plane_digest"
            ],
            "council_tier": recovery_route_trace_binding["council_tier"],
            "transport_profile": recovery_route_trace_binding["transport_profile"],
            "route_count": recovery_route_trace_binding["route_count"],
            "route_binding_refs": route_binding_refs,
            "route_binding_digest_set_digest": route_binding_set_digest,
            "packet_capture_ref": packet_capture_export["capture_ref"],
            "packet_capture_digest": packet_capture_export["digest"],
            "packet_capture_profile": packet_capture_export["capture_profile"],
            "packet_capture_artifact_format": packet_capture_export["artifact_format"],
            "packet_capture_artifact_digest": packet_capture_export["artifact_digest"],
            "packet_capture_readback_digest": packet_capture_export["readback_digest"],
            "packet_count": packet_capture_export["packet_count"],
            "packet_capture_export_status": packet_capture_export["export_status"],
            "packet_capture_route_binding_refs": capture_route_binding_refs,
            "packet_capture_route_binding_set_digest": capture_route_binding_set_digest,
            "os_native_readback_available": packet_capture_export[
                "os_native_readback_available"
            ],
            "os_native_readback_ok": packet_capture_export["os_native_readback_ok"],
            "privileged_capture_ref": privileged_capture_acquisition["acquisition_ref"],
            "privileged_capture_digest": privileged_capture_acquisition["digest"],
            "privileged_capture_profile": privileged_capture_acquisition[
                "acquisition_profile"
            ],
            "privilege_mode": privileged_capture_acquisition["privilege_mode"],
            "broker_profile": privileged_capture_acquisition["broker_profile"],
            "broker_attestation_ref": privileged_capture_acquisition[
                "broker_attestation_ref"
            ],
            "lease_ref": privileged_capture_acquisition["lease_ref"],
            "interface_name": privileged_capture_acquisition["interface_name"],
            "local_ips": list(privileged_capture_acquisition["local_ips"]),
            "capture_filter_digest": privileged_capture_acquisition["filter_digest"],
            "capture_command_digest": sha256_text(
                canonical_json(privileged_capture_acquisition["capture_command"])
            ),
            "acquisition_route_binding_refs": acquisition_route_binding_refs,
            "acquisition_route_binding_set_digest": acquisition_route_binding_set_digest,
            "member_capture_bindings": member_capture_bindings,
            "member_capture_binding_digest_set": member_capture_binding_digests,
            "member_capture_binding_digest_set_digest": sha256_text(
                canonical_json(member_capture_binding_digests)
            ),
            "member_capture_binding_count": len(member_capture_bindings),
            "recovery_route_trace_bound": route_trace_validation["ok"],
            "packet_capture_bound": capture_validation["ok"],
            "privileged_capture_bound": acquisition_validation["ok"],
            "route_binding_set_bound": route_binding_set_bound,
            "all_member_route_traces_capture_bound": True,
            "raw_verifier_payload_stored": False,
            "raw_route_payload_stored": False,
            "raw_packet_body_stored": False,
            "capture_binding_status": "complete" if complete else "incomplete",
            "digest": sha256_text(canonical_json(digest_payload)),
        }
        return deepcopy(receipt)

    def sync_dissolution_external_registry(
        self,
        recovery_capture_export_binding: Mapping[str, Any],
        *,
        registry_ack_authority_route_trace: Mapping[str, Any],
        registry_ack_packet_capture_export: Mapping[str, Any],
        registry_ack_privileged_capture_acquisition: Mapping[str, Any],
        legal_registry_ref: str = "legal-registry://collective-dissolution/jp-13/v1",
        governance_registry_ref: str = (
            "governance-registry://collective-dissolution/federation/v1"
        ),
        legal_jurisdiction: str = "JP-13",
        governance_jurisdiction: str = "FEDERATION",
    ) -> Dict[str, Any]:
        capture_validation = self.validate_recovery_route_trace_capture_export_binding(
            recovery_capture_export_binding,
        )
        if not capture_validation["ok"]:
            raise ValueError(
                "recovery_capture_export_binding must validate before external registry sync"
            )

        legal_ref = self._normalize_non_empty_string(legal_registry_ref, "legal_registry_ref")
        governance_ref = self._normalize_non_empty_string(
            governance_registry_ref,
            "governance_registry_ref",
        )
        legal_zone = self._normalize_non_empty_string(legal_jurisdiction, "legal_jurisdiction")
        governance_zone = self._normalize_non_empty_string(
            governance_jurisdiction,
            "governance_jurisdiction",
        )
        if not legal_ref.startswith("legal-registry://"):
            raise ValueError("legal_registry_ref must start with legal-registry://")
        if not governance_ref.startswith("governance-registry://"):
            raise ValueError(
                "governance_registry_ref must start with governance-registry://"
            )
        if legal_zone == governance_zone:
            raise ValueError(
                "legal_jurisdiction and governance_jurisdiction must be distinct for ack quorum"
            )
        self._validate_authority_route_trace_contract(registry_ack_authority_route_trace)

        recorded_at = utc_now_iso()
        collective_id = str(recovery_capture_export_binding["collective_id"])
        capture_binding_digest = str(recovery_capture_export_binding["digest"])
        route_trace_binding_digest = str(
            recovery_capture_export_binding["recovery_route_trace_binding_digest"]
        )
        verifier_transport_binding_digest = str(
            recovery_capture_export_binding["recovery_verifier_transport_binding_digest"]
        )
        dissolution_receipt_digest = str(
            recovery_capture_export_binding.get("dissolution_receipt_digest", "")
        )
        member_capture_digest_set_digest = str(
            recovery_capture_export_binding["member_capture_binding_digest_set_digest"]
        )
        registry_authority_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": COLLECTIVE_EXTERNAL_REGISTRY_SYNC_PROFILE_ID,
                    "legal_registry_ref": legal_ref,
                    "governance_registry_ref": governance_ref,
                    "legal_jurisdiction": legal_zone,
                    "governance_jurisdiction": governance_zone,
                    "collective_id": collective_id,
                    "dissolution_receipt_digest": dissolution_receipt_digest,
                    "recovery_capture_export_binding_digest": capture_binding_digest,
                }
            )
        )
        legal_registry_digest = self._external_registry_digest(
            registry_ref=legal_ref,
            jurisdiction=legal_zone,
            collective_id=collective_id,
            dissolution_receipt_digest=dissolution_receipt_digest,
            recovery_capture_export_binding_digest=capture_binding_digest,
            registry_kind="legal",
        )
        governance_registry_digest = self._external_registry_digest(
            registry_ref=governance_ref,
            jurisdiction=governance_zone,
            collective_id=collective_id,
            dissolution_receipt_digest=dissolution_receipt_digest,
            recovery_capture_export_binding_digest=capture_binding_digest,
            registry_kind="governance",
        )
        registry_entry_digest = self._collective_external_registry_entry_digest(
            collective_id=collective_id,
            dissolution_receipt_digest=dissolution_receipt_digest,
            recovery_capture_export_binding_digest=capture_binding_digest,
            legal_registry_digest=legal_registry_digest,
            governance_registry_digest=governance_registry_digest,
            member_capture_binding_digest_set_digest=member_capture_digest_set_digest,
        )
        suffix = registry_entry_digest[:12]
        registry_entry_ref = (
            f"registry-entry://collective-dissolution/{collective_id}/{suffix}"
        )
        submission_receipt_ref = (
            f"registry-submission://collective-dissolution/{collective_id}/{suffix}"
        )
        submission_receipt_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": COLLECTIVE_EXTERNAL_REGISTRY_SUBMISSION_PROFILE_ID,
                    "registry_entry_ref": registry_entry_ref,
                    "registry_entry_digest": registry_entry_digest,
                    "legal_registry_digest": legal_registry_digest,
                    "governance_registry_digest": governance_registry_digest,
                }
            )
        )
        ack_receipt_ref = f"registry-ack://collective-dissolution/{collective_id}/{suffix}"
        ack_receipt_digest = self._collective_external_registry_ack_digest(
            submission_receipt_ref=submission_receipt_ref,
            submission_receipt_digest=submission_receipt_digest,
            registry_authority_digest=registry_authority_digest,
            registry_authority_ref=legal_ref,
            registry_jurisdiction=legal_zone,
            registry_digest=legal_registry_digest,
        )
        governance_ack_receipt_ref = (
            f"registry-ack://collective-dissolution/{collective_id}/{suffix}/governance"
        )
        governance_ack_receipt_digest = self._collective_external_registry_ack_digest(
            submission_receipt_ref=submission_receipt_ref,
            submission_receipt_digest=submission_receipt_digest,
            registry_authority_digest=registry_authority_digest,
            registry_authority_ref=governance_ref,
            registry_jurisdiction=governance_zone,
            registry_digest=governance_registry_digest,
        )
        ack_quorum_receipts = [
            {
                "ack_receipt_ref": ack_receipt_ref,
                "ack_receipt_digest": ack_receipt_digest,
                "ack_status": "accepted",
                "registry_authority_ref": legal_ref,
                "registry_jurisdiction": legal_zone,
                "registry_digest": legal_registry_digest,
                "submission_receipt_digest": submission_receipt_digest,
                "raw_ack_payload_stored": False,
            },
            {
                "ack_receipt_ref": governance_ack_receipt_ref,
                "ack_receipt_digest": governance_ack_receipt_digest,
                "ack_status": "accepted",
                "registry_authority_ref": governance_ref,
                "registry_jurisdiction": governance_zone,
                "registry_digest": governance_registry_digest,
                "submission_receipt_digest": submission_receipt_digest,
                "raw_ack_payload_stored": False,
            },
        ]
        ack_quorum_authority_refs = [legal_ref, governance_ref]
        ack_quorum_jurisdictions = _dedupe_preserve_order([legal_zone, governance_zone])
        ack_quorum_digest_set = [
            ack_receipt_digest,
            governance_ack_receipt_digest,
        ]
        ack_quorum_digest_set_digest = sha256_text(
            canonical_json(ack_quorum_digest_set)
        )
        ack_quorum_digest = self._collective_external_registry_ack_quorum_digest(
            collective_id=collective_id,
            submission_receipt_digest=submission_receipt_digest,
            ack_quorum_digest_set_digest=ack_quorum_digest_set_digest,
            ack_quorum_authority_refs=ack_quorum_authority_refs,
            ack_quorum_jurisdictions=ack_quorum_jurisdictions,
        )
        ack_route_trace_bindings = (
            self._build_collective_external_registry_ack_route_trace_bindings(
                collective_id=collective_id,
                ack_quorum_receipts=ack_quorum_receipts,
                authority_route_trace=registry_ack_authority_route_trace,
            )
        )
        ack_route_trace_binding_digest_set = [
            binding["ack_route_binding_digest"]
            for binding in ack_route_trace_bindings
        ]
        ack_route_trace_binding_digest_set_digest = sha256_text(
            canonical_json(ack_route_trace_binding_digest_set)
        )
        ack_route_trace_route_binding_refs = [
            binding["route_binding_ref"] for binding in ack_route_trace_bindings
        ]
        ack_route_trace_remote_host_refs = [
            binding["remote_host_ref"] for binding in ack_route_trace_bindings
        ]
        ack_route_trace_remote_host_attestation_refs = [
            binding["remote_host_attestation_ref"]
            for binding in ack_route_trace_bindings
        ]
        ack_route_trace_remote_jurisdictions = [
            binding["remote_jurisdiction"] for binding in ack_route_trace_bindings
        ]
        ack_route_trace_binding_digest = (
            self._collective_external_registry_ack_route_trace_digest(
                collective_id=collective_id,
                ack_quorum_digest=ack_quorum_digest,
                authority_route_trace_digest=str(registry_ack_authority_route_trace["digest"]),
                ack_route_trace_binding_digest_set_digest=(
                    ack_route_trace_binding_digest_set_digest
                ),
                ack_quorum_authority_refs=ack_quorum_authority_refs,
                route_binding_refs=ack_route_trace_route_binding_refs,
            )
        )
        ack_route_trace_bound = (
            len(ack_route_trace_bindings) == len(ack_quorum_receipts)
            and registry_ack_authority_route_trace.get("non_loopback_verified") is True
            and registry_ack_authority_route_trace.get("cross_host_verified") is True
            and registry_ack_authority_route_trace.get("socket_trace_complete") is True
            and registry_ack_authority_route_trace.get("os_observer_complete") is True
            and all(
                binding["mtls_status"] == "authenticated"
                for binding in ack_route_trace_bindings
            )
        )
        ack_route_packet_capture_route_binding_refs = [
            route_export["route_binding_ref"]
            for route_export in registry_ack_packet_capture_export.get(
                "route_exports",
                [],
            )
            if isinstance(route_export, Mapping)
            and isinstance(route_export.get("route_binding_ref"), str)
        ]
        ack_route_trace_for_capture = {
            "authority_route_trace_ref": registry_ack_authority_route_trace["trace_ref"],
            "authority_route_trace_digest": registry_ack_authority_route_trace["digest"],
            "route_binding_refs": ack_route_packet_capture_route_binding_refs,
            "route_count": len(ack_route_packet_capture_route_binding_refs),
        }
        ack_packet_capture_validation = self._validate_packet_capture_export(
            registry_ack_packet_capture_export,
            recovery_route_trace_binding=ack_route_trace_for_capture,
        )
        ack_privileged_capture_validation = (
            self._validate_privileged_capture_acquisition(
                registry_ack_privileged_capture_acquisition,
                recovery_route_trace_binding=ack_route_trace_for_capture,
                packet_capture_export=registry_ack_packet_capture_export,
            )
        )
        if not ack_packet_capture_validation["ok"]:
            raise ValueError("registry_ack_packet_capture_export must validate before binding")
        if not ack_privileged_capture_validation["ok"]:
            raise ValueError(
                "registry_ack_privileged_capture_acquisition must validate before binding"
            )
        ack_route_capture_bindings = (
            self._build_collective_external_registry_ack_route_capture_bindings(
                collective_id=collective_id,
                ack_route_trace_bindings=ack_route_trace_bindings,
                packet_capture_export=registry_ack_packet_capture_export,
                privileged_capture_acquisition=registry_ack_privileged_capture_acquisition,
                ack_route_trace_binding_digest=ack_route_trace_binding_digest,
            )
        )
        ack_route_capture_binding_digest_set = [
            binding["ack_route_capture_binding_digest"]
            for binding in ack_route_capture_bindings
        ]
        ack_route_capture_binding_digest_set_digest = sha256_text(
            canonical_json(ack_route_capture_binding_digest_set)
        )
        ack_route_packet_capture_route_binding_set_digest = sha256_text(
            canonical_json(ack_route_packet_capture_route_binding_refs)
        )
        ack_route_acquisition_route_binding_refs = list(
            registry_ack_privileged_capture_acquisition["route_binding_refs"]
        )
        ack_route_acquisition_route_binding_set_digest = sha256_text(
            canonical_json(sorted(ack_route_acquisition_route_binding_refs))
        )
        ack_route_capture_route_binding_set_bound = (
            sorted(ack_route_trace_route_binding_refs)
            == sorted(ack_route_packet_capture_route_binding_refs)
            and sorted(ack_route_trace_route_binding_refs)
            == sorted(ack_route_acquisition_route_binding_refs)
        )
        ack_route_capture_binding_digest = (
            self._collective_external_registry_ack_route_capture_export_digest(
                collective_id=collective_id,
                ack_route_trace_binding_digest=ack_route_trace_binding_digest,
                packet_capture_digest=str(registry_ack_packet_capture_export["digest"]),
                privileged_capture_digest=str(
                    registry_ack_privileged_capture_acquisition["digest"]
                ),
                ack_route_capture_binding_digest_set_digest=(
                    ack_route_capture_binding_digest_set_digest
                ),
            )
        )
        ack_route_capture_export_bound = (
            ack_route_trace_bound
            and ack_packet_capture_validation["ok"]
            and ack_privileged_capture_validation["ok"]
            and ack_route_capture_route_binding_set_bound
            and len(ack_route_capture_bindings) == len(ack_route_trace_bindings)
        )
        registry_digest_set = [
            legal_registry_digest,
            governance_registry_digest,
            registry_entry_digest,
            submission_receipt_digest,
            ack_receipt_digest,
            ack_quorum_digest,
            ack_route_trace_binding_digest,
            ack_route_capture_binding_digest,
        ]
        registry_digest_set_digest = sha256_text(canonical_json(registry_digest_set))
        digest_payload = {
            "profile_id": COLLECTIVE_EXTERNAL_REGISTRY_SYNC_PROFILE_ID,
            "collective_id": collective_id,
            "recovery_capture_export_binding_digest": capture_binding_digest,
            "registry_entry_digest": registry_entry_digest,
            "ack_receipt_digest": ack_receipt_digest,
            "ack_quorum_digest": ack_quorum_digest,
            "ack_route_trace_binding_digest": ack_route_trace_binding_digest,
            "ack_route_capture_binding_digest": ack_route_capture_binding_digest,
            "registry_digest_set_digest": registry_digest_set_digest,
        }
        receipt = {
            "kind": "collective_external_registry_sync",
            "schema_version": "1.0.0",
            "profile_id": COLLECTIVE_EXTERNAL_REGISTRY_SYNC_PROFILE_ID,
            "digest_profile": COLLECTIVE_EXTERNAL_REGISTRY_SYNC_DIGEST_PROFILE_ID,
            "registry_entry_digest_profile": (
                COLLECTIVE_EXTERNAL_REGISTRY_ENTRY_DIGEST_PROFILE_ID
            ),
            "collective_id": collective_id,
            "recorded_at": recorded_at,
            "status": "synced",
            "source_capture_export_profile_id": COLLECTIVE_RECOVERY_CAPTURE_EXPORT_PROFILE_ID,
            "recovery_capture_export_binding_digest": capture_binding_digest,
            "recovery_route_trace_binding_digest": route_trace_binding_digest,
            "recovery_verifier_transport_binding_digest": verifier_transport_binding_digest,
            "dissolution_receipt_digest": dissolution_receipt_digest,
            "member_recovery_binding_digest": recovery_capture_export_binding[
                "member_recovery_binding_digest"
            ],
            "packet_capture_digest": recovery_capture_export_binding[
                "packet_capture_digest"
            ],
            "privileged_capture_digest": recovery_capture_export_binding[
                "privileged_capture_digest"
            ],
            "member_capture_binding_digest_set_digest": member_capture_digest_set_digest,
            "legal_registry_ref": legal_ref,
            "legal_jurisdiction": legal_zone,
            "legal_registry_digest": legal_registry_digest,
            "governance_registry_ref": governance_ref,
            "governance_jurisdiction": governance_zone,
            "governance_registry_digest": governance_registry_digest,
            "registry_authority_digest": registry_authority_digest,
            "registry_entry_ref": registry_entry_ref,
            "registry_entry_digest": registry_entry_digest,
            "submission_profile_id": COLLECTIVE_EXTERNAL_REGISTRY_SUBMISSION_PROFILE_ID,
            "submission_receipt_ref": submission_receipt_ref,
            "submission_receipt_digest": submission_receipt_digest,
            "ack_profile_id": COLLECTIVE_EXTERNAL_REGISTRY_ACK_PROFILE_ID,
            "ack_receipt_ref": ack_receipt_ref,
            "ack_receipt_digest": ack_receipt_digest,
            "ack_quorum_profile_id": COLLECTIVE_EXTERNAL_REGISTRY_ACK_QUORUM_PROFILE_ID,
            "ack_quorum_digest_profile": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_QUORUM_DIGEST_PROFILE_ID
            ),
            "ack_quorum_required_authority_count": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_QUORUM_REQUIRED_AUTHORITIES
            ),
            "ack_quorum_required_jurisdiction_count": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_QUORUM_REQUIRED_JURISDICTIONS
            ),
            "ack_quorum_authority_refs": ack_quorum_authority_refs,
            "ack_quorum_jurisdictions": ack_quorum_jurisdictions,
            "ack_quorum_receipts": ack_quorum_receipts,
            "ack_quorum_digest_set": ack_quorum_digest_set,
            "ack_quorum_digest_set_digest": ack_quorum_digest_set_digest,
            "ack_quorum_digest": ack_quorum_digest,
            "ack_quorum_status": "complete",
            "ack_route_trace_profile_id": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_TRACE_PROFILE_ID
            ),
            "ack_route_trace_digest_profile": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_TRACE_DIGEST_PROFILE_ID
            ),
            "ack_authority_route_trace_ref": registry_ack_authority_route_trace[
                "trace_ref"
            ],
            "ack_authority_route_trace_digest": registry_ack_authority_route_trace[
                "digest"
            ],
            "ack_authority_plane_ref": registry_ack_authority_route_trace[
                "authority_plane_ref"
            ],
            "ack_authority_plane_digest": registry_ack_authority_route_trace[
                "authority_plane_digest"
            ],
            "ack_route_trace_route_binding_refs": ack_route_trace_route_binding_refs,
            "ack_route_trace_remote_host_refs": ack_route_trace_remote_host_refs,
            "ack_route_trace_remote_host_attestation_refs": (
                ack_route_trace_remote_host_attestation_refs
            ),
            "ack_route_trace_remote_jurisdictions": (
                ack_route_trace_remote_jurisdictions
            ),
            "ack_route_trace_bindings": ack_route_trace_bindings,
            "ack_route_trace_binding_digest_set": ack_route_trace_binding_digest_set,
            "ack_route_trace_binding_digest_set_digest": (
                ack_route_trace_binding_digest_set_digest
            ),
            "ack_route_trace_binding_digest": ack_route_trace_binding_digest,
            "ack_route_trace_binding_count": len(ack_route_trace_bindings),
            "ack_route_capture_export_profile_id": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_CAPTURE_EXPORT_PROFILE_ID
            ),
            "ack_route_capture_export_digest_profile": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_CAPTURE_EXPORT_DIGEST_PROFILE_ID
            ),
            "ack_route_packet_capture_ref": registry_ack_packet_capture_export[
                "capture_ref"
            ],
            "ack_route_packet_capture_digest": registry_ack_packet_capture_export[
                "digest"
            ],
            "ack_route_packet_capture_profile": registry_ack_packet_capture_export[
                "capture_profile"
            ],
            "ack_route_packet_capture_artifact_format": (
                registry_ack_packet_capture_export["artifact_format"]
            ),
            "ack_route_packet_capture_artifact_digest": (
                registry_ack_packet_capture_export["artifact_digest"]
            ),
            "ack_route_packet_capture_readback_digest": (
                registry_ack_packet_capture_export["readback_digest"]
            ),
            "ack_route_packet_count": registry_ack_packet_capture_export["packet_count"],
            "ack_route_packet_capture_export_status": (
                registry_ack_packet_capture_export["export_status"]
            ),
            "ack_route_packet_capture_route_binding_refs": (
                ack_route_packet_capture_route_binding_refs
            ),
            "ack_route_packet_capture_route_binding_set_digest": (
                ack_route_packet_capture_route_binding_set_digest
            ),
            "ack_route_os_native_readback_available": (
                registry_ack_packet_capture_export["os_native_readback_available"]
            ),
            "ack_route_os_native_readback_ok": (
                registry_ack_packet_capture_export["os_native_readback_ok"]
            ),
            "ack_route_privileged_capture_ref": (
                registry_ack_privileged_capture_acquisition["acquisition_ref"]
            ),
            "ack_route_privileged_capture_digest": (
                registry_ack_privileged_capture_acquisition["digest"]
            ),
            "ack_route_privileged_capture_profile": (
                registry_ack_privileged_capture_acquisition["acquisition_profile"]
            ),
            "ack_route_privilege_mode": registry_ack_privileged_capture_acquisition[
                "privilege_mode"
            ],
            "ack_route_broker_profile": registry_ack_privileged_capture_acquisition[
                "broker_profile"
            ],
            "ack_route_broker_attestation_ref": (
                registry_ack_privileged_capture_acquisition["broker_attestation_ref"]
            ),
            "ack_route_lease_ref": registry_ack_privileged_capture_acquisition[
                "lease_ref"
            ],
            "ack_route_interface_name": registry_ack_privileged_capture_acquisition[
                "interface_name"
            ],
            "ack_route_local_ips": list(
                registry_ack_privileged_capture_acquisition["local_ips"]
            ),
            "ack_route_capture_filter_digest": (
                registry_ack_privileged_capture_acquisition["filter_digest"]
            ),
            "ack_route_capture_command_digest": sha256_text(
                canonical_json(
                    registry_ack_privileged_capture_acquisition["capture_command"]
                )
            ),
            "ack_route_acquisition_route_binding_refs": (
                ack_route_acquisition_route_binding_refs
            ),
            "ack_route_acquisition_route_binding_set_digest": (
                ack_route_acquisition_route_binding_set_digest
            ),
            "ack_route_capture_bindings": ack_route_capture_bindings,
            "ack_route_capture_binding_digest_set": (
                ack_route_capture_binding_digest_set
            ),
            "ack_route_capture_binding_digest_set_digest": (
                ack_route_capture_binding_digest_set_digest
            ),
            "ack_route_capture_binding_digest": ack_route_capture_binding_digest,
            "ack_route_capture_binding_count": len(ack_route_capture_bindings),
            "registry_digest_set": registry_digest_set,
            "registry_digest_set_digest": registry_digest_set_digest,
            "capture_export_bound": True,
            "legal_registry_bound": True,
            "governance_registry_bound": True,
            "registry_entry_bound": True,
            "submission_ack_bound": True,
            "ack_quorum_bound": True,
            "ack_route_trace_bound": ack_route_trace_bound,
            "ack_route_capture_export_bound": ack_route_capture_export_bound,
            "ack_route_capture_route_binding_set_bound": (
                ack_route_capture_route_binding_set_bound
            ),
            "external_registry_sync_complete": ack_route_capture_export_bound,
            "raw_dissolution_payload_stored": False,
            "raw_registry_payload_stored": False,
            "raw_ack_payload_stored": False,
            "raw_ack_route_payload_stored": False,
            "raw_packet_body_stored": False,
            "digest": sha256_text(canonical_json(digest_payload)),
        }
        return deepcopy(receipt)

    def external_registry_ack_endpoint_payload(
        self,
        external_registry_sync: Mapping[str, Any],
        ack_receipt: Mapping[str, Any],
        *,
        checked_at: str | None = None,
    ) -> Dict[str, Any]:
        """Build the compact JSON a live registry acknowledgement endpoint returns."""

        if not isinstance(external_registry_sync, Mapping):
            raise ValueError("external_registry_sync must be a mapping")
        if not isinstance(ack_receipt, Mapping):
            raise ValueError("ack_receipt must be a mapping")
        return {
            "kind": "collective_external_registry_ack_endpoint_status",
            "schema_version": "1.0.0",
            "profile_id": COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_PROFILE_ID,
            "ack_receipt_ref": ack_receipt["ack_receipt_ref"],
            "ack_receipt_digest": ack_receipt["ack_receipt_digest"],
            "ack_status": ack_receipt["ack_status"],
            "registry_authority_ref": ack_receipt["registry_authority_ref"],
            "registry_jurisdiction": ack_receipt["registry_jurisdiction"],
            "registry_digest": ack_receipt["registry_digest"],
            "submission_receipt_digest": ack_receipt["submission_receipt_digest"],
            "registry_entry_digest": external_registry_sync["registry_entry_digest"],
            "ack_quorum_digest": external_registry_sync["ack_quorum_digest"],
            "ack_route_trace_binding_digest": external_registry_sync[
                "ack_route_trace_binding_digest"
            ],
            "ack_route_capture_binding_digest": external_registry_sync[
                "ack_route_capture_binding_digest"
            ],
            "checked_at": checked_at or utc_now_iso(),
            "raw_ack_payload_stored": False,
        }

    def probe_external_registry_ack_endpoint(
        self,
        *,
        registry_ack_endpoint: str,
        external_registry_sync: Mapping[str, Any],
        ack_receipt: Mapping[str, Any],
        request_timeout_ms: int = 1_000,
    ) -> Dict[str, Any]:
        """Probe one live registry acknowledgement endpoint and return a digest-only receipt."""

        normalized_endpoint = self._normalize_non_empty_string(
            registry_ack_endpoint,
            "registry_ack_endpoint",
        )
        if not _is_live_http_endpoint(normalized_endpoint):
            raise ValueError("registry_ack_endpoint must be http:// or https://")
        normalized_timeout_ms = int(request_timeout_ms)
        if normalized_timeout_ms <= 0:
            raise ValueError("request_timeout_ms must be positive")
        if not isinstance(external_registry_sync, Mapping):
            raise ValueError("external_registry_sync must be a mapping")
        if not isinstance(ack_receipt, Mapping):
            raise ValueError("ack_receipt must be a mapping")

        request_started = time.monotonic()
        try:
            with request.urlopen(
                normalized_endpoint,
                timeout=normalized_timeout_ms / 1000.0,
            ) as response:
                http_status = int(getattr(response, "status", 200))
                payload_text = response.read().decode("utf-8")
        except error.URLError as exc:
            raise ValueError(
                f"collective registry ack endpoint unreachable: {normalized_endpoint}"
            ) from exc
        observed_probe_latency_ms = round(
            (time.monotonic() - request_started) * 1000.0,
            3,
        )
        if http_status != 200:
            raise ValueError(
                "collective registry ack endpoint returned unexpected status "
                f"{http_status}"
            )
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise ValueError("collective registry ack endpoint must return JSON") from exc
        if not isinstance(payload, Mapping):
            raise ValueError("collective registry ack endpoint payload must be a mapping")

        expected_payload = self.external_registry_ack_endpoint_payload(
            external_registry_sync,
            ack_receipt,
            checked_at=str(payload.get("checked_at") or ""),
        )
        for field_name, expected_value in expected_payload.items():
            if field_name == "checked_at":
                self._normalize_non_empty_string(
                    payload.get(field_name),
                    "registry_ack_endpoint_payload.checked_at",
                )
                continue
            if payload.get(field_name) != expected_value:
                raise ValueError(
                    "collective registry ack endpoint field mismatch: "
                    f"{field_name}"
                )

        network_response_digest = sha256_text(canonical_json(payload))
        network_probe_bound = (
            _is_live_http_endpoint(normalized_endpoint)
            and http_status == 200
            and observed_probe_latency_ms
            <= COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_LATENCY_BUDGET_MS
            and len(network_response_digest) == 64
            and payload.get("raw_ack_payload_stored") is False
        )
        receipt = {
            "kind": "collective_external_registry_ack_endpoint_probe",
            "schema_version": "1.0.0",
            "probe_id": new_id("collective-registry-ack-probe"),
            "profile_id": COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_PROFILE_ID,
            "digest_profile": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_DIGEST_PROFILE_ID
            ),
            "transport_profile": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_TRANSPORT_PROFILE
            ),
            "registry_ack_endpoint_ref": normalized_endpoint,
            "ack_receipt_ref": ack_receipt["ack_receipt_ref"],
            "ack_receipt_digest": ack_receipt["ack_receipt_digest"],
            "ack_status": ack_receipt["ack_status"],
            "registry_authority_ref": ack_receipt["registry_authority_ref"],
            "registry_jurisdiction": ack_receipt["registry_jurisdiction"],
            "registry_digest": ack_receipt["registry_digest"],
            "submission_receipt_digest": ack_receipt["submission_receipt_digest"],
            "registry_entry_digest": external_registry_sync["registry_entry_digest"],
            "ack_quorum_digest": external_registry_sync["ack_quorum_digest"],
            "ack_route_trace_binding_digest": external_registry_sync[
                "ack_route_trace_binding_digest"
            ],
            "ack_route_capture_binding_digest": external_registry_sync[
                "ack_route_capture_binding_digest"
            ],
            "http_status": http_status,
            "request_timeout_ms": normalized_timeout_ms,
            "observed_probe_latency_ms": observed_probe_latency_ms,
            "latency_budget_ms": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_LATENCY_BUDGET_MS
            ),
            "network_response_digest": network_response_digest,
            "network_probe_status": "reachable",
            "network_probe_bound": network_probe_bound,
            "checked_at": payload["checked_at"],
            "raw_ack_payload_stored": False,
            "raw_endpoint_payload_stored": False,
        }
        receipt["digest"] = sha256_text(
            canonical_json(
                self._collective_external_registry_ack_endpoint_probe_digest_payload(
                    receipt
                )
            )
        )
        return receipt

    def bind_external_registry_ack_endpoint_probes(
        self,
        external_registry_sync: Mapping[str, Any],
        ack_endpoint_probe_receipts: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        """Attach live acknowledgement endpoint probe receipts to registry sync."""

        if not isinstance(external_registry_sync, Mapping):
            raise ValueError("external_registry_sync must be a mapping")
        if not isinstance(ack_endpoint_probe_receipts, Sequence):
            raise ValueError("ack_endpoint_probe_receipts must be a sequence")
        ack_quorum_receipts = external_registry_sync.get("ack_quorum_receipts")
        if not isinstance(ack_quorum_receipts, list) or not ack_quorum_receipts:
            raise ValueError("external_registry_sync must carry ack_quorum_receipts")
        if len(ack_endpoint_probe_receipts) != len(ack_quorum_receipts):
            raise ValueError(
                "ack_endpoint_probe_receipts must cover every registry acknowledgement"
            )

        bound_probes: List[Dict[str, Any]] = []
        probe_digests: List[str] = []
        authority_refs: List[str] = []
        jurisdictions: List[str] = []
        network_response_digests: List[str] = []
        for probe_receipt, ack_receipt in zip(
            ack_endpoint_probe_receipts,
            ack_quorum_receipts,
        ):
            validation = self.validate_external_registry_ack_endpoint_probe_receipt(
                probe_receipt,
                external_registry_sync,
                ack_receipt,
            )
            if not validation["ok"]:
                raise ValueError(
                    "ack_endpoint_probe_receipts must validate before binding: "
                    + "; ".join(validation["errors"])
                )
            probe_copy = dict(probe_receipt)
            bound_probes.append(probe_copy)
            probe_digests.append(str(probe_copy["digest"]))
            authority_refs.append(str(probe_copy["registry_authority_ref"]))
            jurisdictions.append(str(probe_copy["registry_jurisdiction"]))
            network_response_digests.append(str(probe_copy["network_response_digest"]))

        probe_set_digest = sha256_text(canonical_json(probe_digests))
        response_digest_set_digest = sha256_text(
            canonical_json(network_response_digests)
        )
        receipt = dict(external_registry_sync)
        receipt.update(
            {
                "ack_live_endpoint_probe_profile_id": (
                    COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_PROFILE_ID
                ),
                "ack_live_endpoint_probe_digest_profile": (
                    COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_DIGEST_PROFILE_ID
                ),
                "ack_live_endpoint_probe_transport_profile": (
                    COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_TRANSPORT_PROFILE
                ),
                "ack_live_endpoint_probe_receipts": bound_probes,
                "ack_live_endpoint_probe_digests": probe_digests,
                "ack_live_endpoint_probe_set_digest": probe_set_digest,
                "ack_live_endpoint_probe_authority_refs": authority_refs,
                "ack_live_endpoint_probe_jurisdictions": jurisdictions,
                "ack_live_endpoint_network_response_digests": (
                    network_response_digests
                ),
                "ack_live_endpoint_network_response_digest_set_digest": (
                    response_digest_set_digest
                ),
                "ack_live_endpoint_probe_count": len(bound_probes),
                "ack_live_endpoint_probe_bound": True,
                "raw_ack_endpoint_payload_stored": False,
            }
        )
        receipt["registry_digest_set"] = [
            receipt["legal_registry_digest"],
            receipt["governance_registry_digest"],
            receipt["registry_entry_digest"],
            receipt["submission_receipt_digest"],
            receipt["ack_receipt_digest"],
            receipt["ack_quorum_digest"],
            receipt["ack_route_trace_binding_digest"],
            receipt["ack_route_capture_binding_digest"],
            receipt["ack_live_endpoint_probe_set_digest"],
        ]
        receipt["registry_digest_set_digest"] = sha256_text(
            canonical_json(receipt["registry_digest_set"])
        )
        receipt["external_registry_sync_complete"] = bool(
            receipt.get("ack_route_capture_export_bound")
            and receipt["ack_live_endpoint_probe_bound"]
        )
        receipt["digest"] = sha256_text(
            canonical_json(
                self._collective_external_registry_sync_digest_payload(receipt)
            )
        )
        return receipt

    def snapshot(self, collective_id: str) -> Dict[str, Any]:
        return deepcopy(self._require_record(collective_id))

    def merge_snapshot(self, merge_session_id: str) -> Dict[str, Any]:
        return deepcopy(self._require_merge_session(merge_session_id))

    def validate_record(self, record: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(record, Mapping):
            raise ValueError("record must be a mapping")

        self._check_non_empty_string(record.get("collective_id"), "collective_id", errors)
        self._check_non_empty_string(record.get("display_name"), "display_name", errors)
        self._check_non_empty_string(record.get("created_at"), "created_at", errors)
        if record.get("schema_version") != COLLECTIVE_SCHEMA_VERSION:
            errors.append(f"schema_version must be {COLLECTIVE_SCHEMA_VERSION}")
        if record.get("status") not in COLLECTIVE_ALLOWED_STATUSES:
            errors.append(f"status must be one of {sorted(COLLECTIVE_ALLOWED_STATUSES)}")

        member_ids = record.get("member_ids")
        if not isinstance(member_ids, list):
            errors.append("member_ids must be a list")
            member_count = 0
        else:
            member_count = len(member_ids)
            if member_count < COLLECTIVE_MIN_MEMBERS or member_count > COLLECTIVE_MAX_MEMBERS:
                errors.append(
                    f"member_ids must contain between {COLLECTIVE_MIN_MEMBERS} and {COLLECTIVE_MAX_MEMBERS} entries"
                )
            if len(set(member_ids)) != len(member_ids):
                errors.append("member_ids must be unique")

        merge_policy = record.get("merge_policy")
        if not isinstance(merge_policy, Mapping):
            errors.append("merge_policy must be an object")
            merge_window_bounded = False
        else:
            merge_window_bounded = merge_policy.get("max_duration_seconds") == COLLECTIVE_MAX_DURATION_SECONDS
            if merge_policy.get("merge_mode") != "merge_thought":
                errors.append("merge_policy.merge_mode must equal merge_thought")
            if not merge_window_bounded:
                errors.append(
                    f"merge_policy.max_duration_seconds must equal {COLLECTIVE_MAX_DURATION_SECONDS}"
                )
            if merge_policy.get("post_disconnect_identity_confirmation") != "all-members":
                errors.append("merge_policy.post_disconnect_identity_confirmation must equal all-members")
            if merge_policy.get("escape_route") != "private_reality":
                errors.append("merge_policy.escape_route must equal private_reality")

        oversight = record.get("oversight")
        oversight_bound = self._oversight_bound(oversight)
        if not oversight_bound:
            errors.append("oversight must record council witness, federation attestation, and guardian observation")

        active_merge_session_ids = record.get("active_merge_session_ids")
        if not isinstance(active_merge_session_ids, list):
            errors.append("active_merge_session_ids must be a list")
            active_merge_bound = False
        else:
            active_merge_bound = len(active_merge_session_ids) <= 1
            if not active_merge_bound:
                errors.append("active_merge_session_ids must contain at most one session")

        return {
            "ok": not errors,
            "errors": errors,
            "member_count": member_count,
            "merge_window_bounded": merge_window_bounded,
            "oversight_bound": oversight_bound,
            "active_merge_bound": active_merge_bound,
        }

    def validate_merge_session(self, session: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(session, Mapping):
            raise ValueError("session must be a mapping")

        self._check_non_empty_string(session.get("merge_session_id"), "merge_session_id", errors)
        self._check_non_empty_string(session.get("collective_id"), "collective_id", errors)
        self._check_non_empty_string(session.get("opened_at"), "opened_at", errors)
        if session.get("schema_version") != COLLECTIVE_SCHEMA_VERSION:
            errors.append(f"schema_version must be {COLLECTIVE_SCHEMA_VERSION}")
        if session.get("status") not in COLLECTIVE_ALLOWED_MERGE_STATUSES:
            errors.append(f"status must be one of {sorted(COLLECTIVE_ALLOWED_MERGE_STATUSES)}")
        if session.get("merge_mode") != "merge_thought":
            errors.append("merge_mode must equal merge_thought")

        granted = session.get("granted_duration_seconds")
        merge_window_bounded = isinstance(granted, (int, float)) and granted <= COLLECTIVE_MAX_DURATION_SECONDS
        if not merge_window_bounded:
            errors.append(f"granted_duration_seconds must be <= {COLLECTIVE_MAX_DURATION_SECONDS}")

        oversight_bound = self._oversight_bound(session.get("oversight"))
        if not oversight_bound:
            errors.append("oversight must record council witness, federation attestation, and guardian observation")

        required_confirmations = session.get("identity_confirmation_required")
        if not isinstance(required_confirmations, list) or not required_confirmations:
            errors.append("identity_confirmation_required must be a non-empty list")

        resulting_mode = session.get("resulting_wms_mode")
        if resulting_mode is not None and resulting_mode not in COLLECTIVE_ALLOWED_WMS_MODES:
            errors.append(f"resulting_wms_mode must be one of {sorted(COLLECTIVE_ALLOWED_WMS_MODES)}")

        return {
            "ok": not errors,
            "errors": errors,
            "merge_window_bounded": merge_window_bounded,
            "oversight_bound": oversight_bound,
            "identity_confirmation_complete": bool(session.get("identity_confirmations"))
            and all(bool(value) for value in session.get("identity_confirmations", {}).values()),
            "private_escape_honored": session.get("private_escape_honored") is True,
        }

    def validate_dissolution_receipt(self, receipt: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")

        self._check_non_empty_string(receipt.get("collective_id"), "collective_id", errors)
        self._check_non_empty_string(receipt.get("recorded_at"), "recorded_at", errors)
        self._check_non_empty_string(receipt.get("requested_by"), "requested_by", errors)
        self._check_non_empty_string(receipt.get("reason"), "reason", errors)
        self._check_non_empty_string(receipt.get("audit_event_ref"), "audit_event_ref", errors)
        if receipt.get("schema_version") != COLLECTIVE_SCHEMA_VERSION:
            errors.append(f"schema_version must be {COLLECTIVE_SCHEMA_VERSION}")
        if receipt.get("status") != "dissolved":
            errors.append("status must equal dissolved")
        if receipt.get("member_recovery_required") is not True:
            errors.append("member_recovery_required must be true")
        if (
            receipt.get("member_recovery_binding_profile")
            != COLLECTIVE_DISSOLUTION_RECOVERY_BINDING_PROFILE_ID
        ):
            errors.append(
                "member_recovery_binding_profile must equal "
                f"{COLLECTIVE_DISSOLUTION_RECOVERY_BINDING_PROFILE_ID}"
            )
        if receipt.get("raw_identity_confirmation_profiles_stored") is not False:
            errors.append("raw_identity_confirmation_profiles_stored must be false")

        confirmations = receipt.get("member_confirmations")
        if not isinstance(confirmations, Mapping):
            errors.append("member_confirmations must be an object")
            member_confirmation_complete = False
            expected_member_ids: List[str] = []
        else:
            expected_member_ids = list(confirmations)
            member_confirmation_complete = len(confirmations) >= COLLECTIVE_MIN_MEMBERS and all(
                value is True for value in confirmations.values()
            )
            if not member_confirmation_complete:
                errors.append("member_confirmations must include every member with true confirmation")

        recovery_proofs = receipt.get("member_recovery_proofs")
        if not isinstance(recovery_proofs, Mapping):
            errors.append("member_recovery_proofs must be an object")
            recovery_proofs_bound = False
            recovery_digest_set_bound = False
        else:
            recovery_proofs_bound = set(recovery_proofs) == set(expected_member_ids)
            if not recovery_proofs_bound:
                errors.append("member_recovery_proofs must include exactly the confirmed members")
            for member_id, proof in recovery_proofs.items():
                if not isinstance(proof, Mapping):
                    errors.append(f"member_recovery_proofs[{member_id}] must be an object")
                    recovery_proofs_bound = False
                    continue
                if proof.get("member_id") != member_id:
                    errors.append(f"member_recovery_proofs[{member_id}].member_id must match its key")
                    recovery_proofs_bound = False
                if (
                    proof.get("identity_confirmation_profile_id")
                    != COLLECTIVE_IDENTITY_CONFIRMATION_PROFILE_ID
                ):
                    errors.append(
                        f"member_recovery_proofs[{member_id}].identity_confirmation_profile_id "
                        f"must equal {COLLECTIVE_IDENTITY_CONFIRMATION_PROFILE_ID}"
                    )
                    recovery_proofs_bound = False
                if proof.get("active_transition_allowed") is not True:
                    errors.append(
                        f"member_recovery_proofs[{member_id}].active_transition_allowed must be true"
                    )
                    recovery_proofs_bound = False
                if proof.get("result") != "passed":
                    errors.append(f"member_recovery_proofs[{member_id}].result must equal passed")
                    recovery_proofs_bound = False
                if proof.get("required_dimensions") != COLLECTIVE_REQUIRED_IDENTITY_CONFIRMATION_DIMENSIONS:
                    errors.append(
                        f"member_recovery_proofs[{member_id}].required_dimensions must match "
                        "the four-dimensional identity confirmation profile"
                    )
                    recovery_proofs_bound = False
                if proof.get("witness_quorum_status") != "met":
                    errors.append(
                        f"member_recovery_proofs[{member_id}].witness_quorum_status must equal met"
                    )
                    recovery_proofs_bound = False
                if proof.get("self_report_witness_consistency_status") != "bound":
                    errors.append(
                        f"member_recovery_proofs[{member_id}].self_report_witness_consistency_status "
                        "must equal bound"
                    )
                    recovery_proofs_bound = False
                if proof.get("raw_profile_stored") is not False:
                    errors.append(f"member_recovery_proofs[{member_id}].raw_profile_stored must be false")
                    recovery_proofs_bound = False
                if not self._looks_like_digest(proof.get("identity_confirmation_digest")):
                    errors.append(
                        f"member_recovery_proofs[{member_id}].identity_confirmation_digest must be sha256 hex"
                    )
                    recovery_proofs_bound = False
                if not self._looks_like_digest(proof.get("self_report_witness_consistency_digest")):
                    errors.append(
                        f"member_recovery_proofs[{member_id}].self_report_witness_consistency_digest "
                        "must be sha256 hex"
                    )
                    recovery_proofs_bound = False
            recovery_digest_set = receipt.get("member_recovery_confirmation_digest_set")
            expected_digest_set = [
                recovery_proofs[member_id]["identity_confirmation_digest"]
                for member_id in expected_member_ids
                if isinstance(recovery_proofs.get(member_id), Mapping)
                and self._looks_like_digest(
                    recovery_proofs[member_id].get("identity_confirmation_digest")
                )
            ]
            recovery_digest_set_bound = recovery_digest_set == expected_digest_set
            if not recovery_digest_set_bound:
                errors.append(
                    "member_recovery_confirmation_digest_set must match member recovery proof order"
                )

        binding_digest = receipt.get("member_recovery_binding_digest")
        expected_binding_digest = None
        if isinstance(recovery_proofs, Mapping) and isinstance(receipt.get("member_recovery_confirmation_digest_set"), list):
            expected_binding_digest = sha256_text(
                canonical_json(
                    {
                        "profile_id": COLLECTIVE_DISSOLUTION_RECOVERY_BINDING_PROFILE_ID,
                        "collective_id": receipt.get("collective_id"),
                        "member_ids": expected_member_ids,
                        "member_recovery_proofs": recovery_proofs,
                        "member_recovery_confirmation_digest_set": receipt.get(
                            "member_recovery_confirmation_digest_set"
                        ),
                    }
                )
            )
        recovery_binding_digest_bound = (
            isinstance(expected_binding_digest, str) and binding_digest == expected_binding_digest
        )
        if not recovery_binding_digest_bound:
            errors.append("member_recovery_binding_digest must match digest-only recovery proof bundle")

        return {
            "ok": not errors,
            "errors": errors,
            "schema_version_bound": receipt.get("schema_version") == COLLECTIVE_SCHEMA_VERSION,
            "member_confirmation_complete": member_confirmation_complete,
            "member_recovery_required": receipt.get("member_recovery_required") is True,
            "member_recovery_proofs_bound": recovery_proofs_bound,
            "member_recovery_digest_set_bound": recovery_digest_set_bound,
            "member_recovery_binding_digest_bound": recovery_binding_digest_bound,
            "raw_identity_confirmation_profiles_stored": receipt.get(
                "raw_identity_confirmation_profiles_stored"
            )
            is True,
            "audit_bound": isinstance(receipt.get("audit_event_ref"), str)
            and bool(receipt.get("audit_event_ref")),
        }

    def validate_recovery_verifier_transport_binding(
        self,
        binding: Mapping[str, Any],
        dissolution_receipt: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(binding, Mapping):
            raise ValueError("binding must be a mapping")

        self._check_non_empty_string(binding.get("collective_id"), "collective_id", errors)
        self._check_non_empty_string(binding.get("recorded_at"), "recorded_at", errors)
        if binding.get("kind") != "collective_recovery_verifier_transport_binding":
            errors.append("kind must equal collective_recovery_verifier_transport_binding")
        if binding.get("schema_version") != "1.0.0":
            errors.append("schema_version must equal 1.0.0")
        if binding.get("profile_id") != COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID:
            errors.append(
                f"profile_id must equal {COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID}"
            )
        if binding.get("status") != "verified":
            errors.append("status must equal verified")
        if binding.get("raw_verifier_payload_stored") is not False:
            errors.append("raw_verifier_payload_stored must be false")

        if dissolution_receipt is not None:
            dissolution_validation = self.validate_dissolution_receipt(dissolution_receipt)
            if not dissolution_validation["ok"]:
                errors.append("dissolution_receipt must validate before transport binding")
            expected_dissolution_digest = sha256_text(canonical_json(dissolution_receipt))
            member_ids = list(dissolution_receipt.get("member_confirmations", {}))
            recovery_proofs = dissolution_receipt.get("member_recovery_proofs", {})
            expected_member_recovery_binding_digest = dissolution_receipt.get(
                "member_recovery_binding_digest"
            )
            expected_recovery_digest_set = dissolution_receipt.get(
                "member_recovery_confirmation_digest_set"
            )
        else:
            expected_dissolution_digest = binding.get("dissolution_receipt_digest")
            member_ids = list(binding.get("verifier_transport_receipts", {}))
            recovery_proofs = {}
            expected_member_recovery_binding_digest = binding.get(
                "member_recovery_binding_digest"
            )
            expected_recovery_digest_set = binding.get(
                "member_recovery_confirmation_digest_set"
            )

        dissolution_digest_bound = (
            binding.get("dissolution_receipt_digest") == expected_dissolution_digest
            and self._looks_like_digest(binding.get("dissolution_receipt_digest"))
        )
        if not dissolution_digest_bound:
            errors.append("dissolution_receipt_digest must match the dissolution receipt")

        member_recovery_binding_digest_bound = (
            binding.get("member_recovery_binding_digest")
            == expected_member_recovery_binding_digest
            and self._looks_like_digest(binding.get("member_recovery_binding_digest"))
        )
        if not member_recovery_binding_digest_bound:
            errors.append("member_recovery_binding_digest must match dissolution receipt")

        recovery_digest_set_bound = (
            binding.get("member_recovery_confirmation_digest_set")
            == expected_recovery_digest_set
        )
        if not recovery_digest_set_bound:
            errors.append("member_recovery_confirmation_digest_set must match dissolution receipt")

        verifier_receipts = binding.get("verifier_transport_receipts")
        if not isinstance(verifier_receipts, Mapping):
            errors.append("verifier_transport_receipts must be an object")
            verifier_receipts_bound = False
            verifier_digest_set_bound = False
        else:
            verifier_receipts_bound = set(verifier_receipts) == set(member_ids)
            if not verifier_receipts_bound:
                errors.append("verifier_transport_receipts must include exactly every member")
            digest_set: List[str] = []
            for member_id in member_ids:
                receipt = verifier_receipts.get(member_id)
                if not isinstance(receipt, Mapping):
                    errors.append(f"verifier_transport_receipts[{member_id}] must be an object")
                    verifier_receipts_bound = False
                    continue
                proof = recovery_proofs.get(member_id, {}) if isinstance(recovery_proofs, Mapping) else {}
                receipt_ok = self._validate_member_recovery_verifier_transport_receipt(
                    receipt,
                    member_id=member_id,
                    proof=proof if isinstance(proof, Mapping) else {},
                    member_recovery_binding_digest=str(
                        expected_member_recovery_binding_digest
                    ),
                    dissolution_receipt_digest=str(expected_dissolution_digest),
                    errors=errors,
                )
                verifier_receipts_bound = verifier_receipts_bound and receipt_ok
                if self._looks_like_digest(receipt.get("digest")):
                    digest_set.append(str(receipt["digest"]))
            verifier_digest_set_bound = binding.get("verifier_transport_digest_set") == digest_set
            if not verifier_digest_set_bound:
                errors.append("verifier_transport_digest_set must match member receipt order")
            if binding.get("verifier_transport_receipt_count") != len(verifier_receipts):
                errors.append(
                    "verifier_transport_receipt_count must match verifier receipt count"
                )
                verifier_receipts_bound = False

        expected_binding_digest = None
        if isinstance(binding.get("verifier_transport_digest_set"), list):
            expected_binding_digest = sha256_text(
                canonical_json(
                    {
                        "profile_id": COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID,
                        "collective_id": binding.get("collective_id"),
                        "member_ids": member_ids,
                        "dissolution_receipt_digest": binding.get(
                            "dissolution_receipt_digest"
                        ),
                        "member_recovery_binding_digest": binding.get(
                            "member_recovery_binding_digest"
                        ),
                        "verifier_transport_digest_set": binding.get(
                            "verifier_transport_digest_set"
                        ),
                    }
                )
            )
        verifier_transport_binding_digest_bound = (
            isinstance(expected_binding_digest, str)
            and binding.get("verifier_transport_binding_digest") == expected_binding_digest
        )
        if not verifier_transport_binding_digest_bound:
            errors.append("verifier_transport_binding_digest must match transport receipt set")

        all_member_recovery_proofs_transport_bound = (
            verifier_receipts_bound
            and verifier_digest_set_bound
            and member_recovery_binding_digest_bound
            and binding.get("all_member_recovery_proofs_transport_bound") is True
        )
        if not all_member_recovery_proofs_transport_bound:
            errors.append("all_member_recovery_proofs_transport_bound must be true")

        all_verifier_transport_receipts_verified = (
            isinstance(verifier_receipts, Mapping)
            and all(
                isinstance(receipt, Mapping) and receipt.get("receipt_status") == "verified"
                for receipt in verifier_receipts.values()
            )
            and binding.get("all_verifier_transport_receipts_verified") is True
        )
        if not all_verifier_transport_receipts_verified:
            errors.append("all_verifier_transport_receipts_verified must be true")

        return {
            "ok": not errors,
            "errors": errors,
            "profile_bound": (
                binding.get("profile_id")
                == COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID
            ),
            "dissolution_receipt_digest_bound": dissolution_digest_bound,
            "member_recovery_binding_digest_bound": member_recovery_binding_digest_bound,
            "member_recovery_confirmation_digest_set_bound": recovery_digest_set_bound,
            "verifier_transport_receipts_bound": verifier_receipts_bound,
            "verifier_transport_digest_set_bound": verifier_digest_set_bound,
            "verifier_transport_binding_digest_bound": (
                verifier_transport_binding_digest_bound
            ),
            "all_member_recovery_proofs_transport_bound": (
                all_member_recovery_proofs_transport_bound
            ),
            "all_verifier_transport_receipts_verified": all_verifier_transport_receipts_verified,
            "raw_verifier_payload_stored": binding.get("raw_verifier_payload_stored") is True,
        }

    def validate_recovery_verifier_route_trace_binding(
        self,
        binding: Mapping[str, Any],
        recovery_verifier_transport_binding: Mapping[str, Any] | None = None,
        authority_route_trace: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(binding, Mapping):
            raise ValueError("binding must be a mapping")

        expected_fields = {
            "kind": "collective_recovery_route_trace_binding",
            "schema_version": "1.0.0",
            "profile_id": COLLECTIVE_RECOVERY_ROUTE_TRACE_PROFILE_ID,
            "digest_profile": COLLECTIVE_RECOVERY_ROUTE_TRACE_DIGEST_PROFILE_ID,
            "status": "route-trace-bound",
            "recovery_verifier_transport_profile_id": (
                COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID
            ),
        }
        for field_name, expected in expected_fields.items():
            if binding.get(field_name) != expected:
                errors.append(f"{field_name} must equal {expected}")
        self._check_non_empty_string(binding.get("collective_id"), "collective_id", errors)
        self._check_non_empty_string(binding.get("recorded_at"), "recorded_at", errors)

        if recovery_verifier_transport_binding is not None:
            transport_validation = self.validate_recovery_verifier_transport_binding(
                recovery_verifier_transport_binding,
            )
            if not transport_validation["ok"]:
                errors.append("recovery_verifier_transport_binding must validate")
            expected_transport_digest = recovery_verifier_transport_binding.get(
                "verifier_transport_binding_digest"
            )
            expected_verifier_digest_set_digest = sha256_text(
                canonical_json(
                    recovery_verifier_transport_binding.get(
                        "verifier_transport_digest_set",
                        [],
                    )
                )
            )
            expected_dissolution_digest = recovery_verifier_transport_binding.get(
                "dissolution_receipt_digest"
            )
            expected_member_recovery_binding_digest = (
                recovery_verifier_transport_binding.get(
                    "member_recovery_binding_digest"
                )
            )
        else:
            expected_transport_digest = binding.get(
                "recovery_verifier_transport_binding_digest"
            )
            expected_verifier_digest_set_digest = binding.get(
                "verifier_transport_digest_set_digest"
            )
            expected_dissolution_digest = binding.get("dissolution_receipt_digest")
            expected_member_recovery_binding_digest = binding.get(
                "member_recovery_binding_digest"
            )

        recovery_transport_bound = (
            binding.get("recovery_verifier_transport_binding_digest")
            == expected_transport_digest
            and self._looks_like_digest(
                binding.get("recovery_verifier_transport_binding_digest")
            )
            and binding.get("verifier_transport_digest_set_digest")
            == expected_verifier_digest_set_digest
            and binding.get("dissolution_receipt_digest") == expected_dissolution_digest
            and binding.get("member_recovery_binding_digest")
            == expected_member_recovery_binding_digest
            and binding.get("recovery_transport_bound") is True
        )
        if not recovery_transport_bound:
            errors.append("recovery transport binding digests must match")

        route_trace_bound = False
        route_trace_authenticated = False
        if authority_route_trace is not None:
            try:
                self._validate_authority_route_trace_contract(authority_route_trace)
                route_trace_authenticated = True
            except ValueError as exc:
                errors.append(str(exc))
            expected_route_trace_ref = authority_route_trace.get("trace_ref")
            expected_route_trace_digest = authority_route_trace.get("digest")
            expected_route_binding_refs = [
                route["route_binding_ref"]
                for route in authority_route_trace.get("route_bindings", [])
                if isinstance(route, Mapping)
            ][: len(binding.get("member_route_bindings", []))]
        else:
            expected_route_trace_ref = binding.get("authority_route_trace_ref")
            expected_route_trace_digest = binding.get("authority_route_trace_digest")
            expected_route_binding_refs = binding.get("route_binding_refs", [])
            route_trace_authenticated = (
                binding.get("non_loopback_verified") is True
                and binding.get("cross_host_verified") is True
                and binding.get("socket_trace_complete") is True
                and binding.get("os_observer_complete") is True
                and binding.get("route_target_discovery_bound") is True
            )

        route_trace_bound = (
            binding.get("authority_route_trace_ref") == expected_route_trace_ref
            and binding.get("authority_route_trace_digest") == expected_route_trace_digest
            and self._looks_like_digest(binding.get("authority_route_trace_digest"))
            and binding.get("route_binding_refs") == expected_route_binding_refs
            and binding.get("authority_route_trace_bound") is True
            and route_trace_authenticated
        )
        if not route_trace_bound:
            errors.append("authority route trace metadata must match authenticated trace")

        member_route_bindings = binding.get("member_route_bindings")
        member_route_binding_digest_set = binding.get("member_route_binding_digest_set")
        member_route_bindings_bound = False
        if not isinstance(member_route_bindings, list) or not member_route_bindings:
            errors.append("member_route_bindings must be a non-empty list")
        elif not isinstance(member_route_binding_digest_set, list):
            errors.append("member_route_binding_digest_set must be a list")
        else:
            recomputed_digests: List[str] = []
            member_route_bindings_bound = True
            for index, item in enumerate(member_route_bindings):
                if not isinstance(item, Mapping):
                    errors.append(f"member_route_bindings[{index}] must be an object")
                    member_route_bindings_bound = False
                    continue
                for field_name in (
                    "member_id",
                    "verifier_transport_receipt_id",
                    "verifier_transport_receipt_digest",
                    "route_binding_ref",
                    "remote_host_ref",
                    "remote_host_attestation_ref",
                    "authority_cluster_ref",
                    "socket_response_digest",
                    "member_route_binding_digest",
                ):
                    if not item.get(field_name):
                        errors.append(
                            f"member_route_bindings[{index}].{field_name} must be present"
                        )
                        member_route_bindings_bound = False
                if item.get("mtls_status") != "authenticated":
                    errors.append(
                        f"member_route_bindings[{index}].mtls_status must be authenticated"
                    )
                    member_route_bindings_bound = False
                recomputed_digest = self._collective_member_route_binding_digest(
                    member_id=str(item.get("member_id")),
                    verifier_receipt_digest=str(
                        item.get("verifier_transport_receipt_digest")
                    ),
                    authority_route_trace_digest=str(
                        binding.get("authority_route_trace_digest")
                    ),
                    route_binding_ref=str(item.get("route_binding_ref")),
                    response_digest=str(item.get("socket_response_digest")),
                    remote_host_ref=str(item.get("remote_host_ref")),
                    remote_host_attestation_ref=str(
                        item.get("remote_host_attestation_ref")
                    ),
                    authority_cluster_ref=str(item.get("authority_cluster_ref")),
                )
                recomputed_digests.append(recomputed_digest)
                if item.get("member_route_binding_digest") != recomputed_digest:
                    errors.append(
                        f"member_route_bindings[{index}].member_route_binding_digest mismatch"
                    )
                    member_route_bindings_bound = False
            if member_route_binding_digest_set != recomputed_digests:
                errors.append("member_route_binding_digest_set must match member bindings")
                member_route_bindings_bound = False
            if binding.get("member_route_binding_count") != len(member_route_bindings):
                errors.append("member_route_binding_count must match member bindings")
                member_route_bindings_bound = False
            if binding.get("member_route_binding_digest_set_digest") != sha256_text(
                canonical_json(recomputed_digests)
            ):
                errors.append(
                    "member_route_binding_digest_set_digest must match member digests"
                )
                member_route_bindings_bound = False
            if binding.get("all_member_receipts_route_traced") is not True:
                errors.append("all_member_receipts_route_traced must be true")
                member_route_bindings_bound = False

        expected_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": COLLECTIVE_RECOVERY_ROUTE_TRACE_PROFILE_ID,
                    "collective_id": binding.get("collective_id"),
                    "recovery_verifier_transport_binding_digest": binding.get(
                        "recovery_verifier_transport_binding_digest"
                    ),
                    "authority_route_trace_digest": binding.get(
                        "authority_route_trace_digest"
                    ),
                    "member_route_binding_digest_set": binding.get(
                        "member_route_binding_digest_set"
                    ),
                }
            )
        )
        digest_bound = binding.get("digest") == expected_digest
        if not digest_bound:
            errors.append("digest must match collective recovery route trace binding payload")

        raw_verifier_payload_stored = binding.get("raw_verifier_payload_stored") is True
        raw_route_payload_stored = binding.get("raw_route_payload_stored") is True
        if raw_verifier_payload_stored:
            errors.append("raw_verifier_payload_stored must be false")
        if raw_route_payload_stored:
            errors.append("raw_route_payload_stored must be false")

        return {
            "ok": not errors,
            "errors": errors,
            "profile_bound": binding.get("profile_id")
            == COLLECTIVE_RECOVERY_ROUTE_TRACE_PROFILE_ID,
            "recovery_transport_bound": recovery_transport_bound,
            "authority_route_trace_bound": route_trace_bound,
            "route_trace_authenticated": route_trace_authenticated,
            "member_route_bindings_bound": member_route_bindings_bound,
            "all_member_receipts_route_traced": (
                binding.get("all_member_receipts_route_traced") is True
            ),
            "digest_bound": digest_bound,
            "raw_verifier_payload_stored": raw_verifier_payload_stored,
            "raw_route_payload_stored": raw_route_payload_stored,
        }

    def validate_recovery_route_trace_capture_export_binding(
        self,
        binding: Mapping[str, Any],
        recovery_route_trace_binding: Mapping[str, Any] | None = None,
        packet_capture_export: Mapping[str, Any] | None = None,
        privileged_capture_acquisition: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(binding, Mapping):
            raise ValueError("binding must be a mapping")

        expected_fields = {
            "kind": "collective_recovery_capture_export_binding",
            "schema_version": "1.0.0",
            "profile_id": COLLECTIVE_RECOVERY_CAPTURE_EXPORT_PROFILE_ID,
            "digest_profile": COLLECTIVE_RECOVERY_CAPTURE_EXPORT_DIGEST_PROFILE_ID,
            "status": "capture-export-bound",
            "recovery_route_trace_profile_id": COLLECTIVE_RECOVERY_ROUTE_TRACE_PROFILE_ID,
            "packet_capture_profile": COLLECTIVE_PACKET_CAPTURE_PROFILE,
            "packet_capture_artifact_format": COLLECTIVE_PACKET_CAPTURE_FORMAT,
            "packet_capture_export_status": "verified",
            "privileged_capture_profile": COLLECTIVE_PRIVILEGED_CAPTURE_PROFILE,
            "privilege_mode": COLLECTIVE_PRIVILEGED_CAPTURE_MODE,
            "capture_binding_status": "complete",
        }
        for field_name, expected in expected_fields.items():
            if binding.get(field_name) != expected:
                errors.append(f"{field_name} must equal {expected}")
        self._check_non_empty_string(binding.get("collective_id"), "collective_id", errors)
        self._check_non_empty_string(binding.get("recorded_at"), "recorded_at", errors)

        if recovery_route_trace_binding is not None:
            route_trace_validation = self.validate_recovery_verifier_route_trace_binding(
                recovery_route_trace_binding,
            )
            expected_route_trace_binding_digest = recovery_route_trace_binding.get(
                "digest"
            )
            expected_authority_trace_ref = recovery_route_trace_binding.get(
                "authority_route_trace_ref"
            )
            expected_authority_trace_digest = recovery_route_trace_binding.get(
                "authority_route_trace_digest"
            )
            expected_route_binding_refs = list(
                recovery_route_trace_binding.get("route_binding_refs", [])
            )
        else:
            route_trace_validation = {
                "ok": binding.get("recovery_route_trace_bound") is True
            }
            expected_route_trace_binding_digest = binding.get(
                "recovery_route_trace_binding_digest"
            )
            expected_authority_trace_ref = binding.get("authority_route_trace_ref")
            expected_authority_trace_digest = binding.get("authority_route_trace_digest")
            expected_route_binding_refs = list(binding.get("route_binding_refs", []))

        route_trace_bound = (
            route_trace_validation["ok"]
            and binding.get("recovery_route_trace_binding_digest")
            == expected_route_trace_binding_digest
            and binding.get("authority_route_trace_ref") == expected_authority_trace_ref
            and binding.get("authority_route_trace_digest")
            == expected_authority_trace_digest
            and binding.get("route_binding_refs") == expected_route_binding_refs
            and self._looks_like_digest(binding.get("recovery_route_trace_binding_digest"))
            and binding.get("recovery_route_trace_bound") is True
        )
        if not route_trace_bound:
            errors.append("recovery route trace binding metadata must match")

        if packet_capture_export is not None:
            capture_validation = self._validate_packet_capture_export(
                packet_capture_export,
                recovery_route_trace_binding=recovery_route_trace_binding or binding,
            )
            packet_capture_bound = (
                capture_validation["ok"]
                and binding.get("packet_capture_ref")
                == packet_capture_export.get("capture_ref")
                and binding.get("packet_capture_digest")
                == packet_capture_export.get("digest")
                and binding.get("packet_capture_artifact_digest")
                == packet_capture_export.get("artifact_digest")
                and binding.get("packet_capture_readback_digest")
                == packet_capture_export.get("readback_digest")
                and binding.get("packet_count")
                == packet_capture_export.get("packet_count")
                and binding.get("packet_capture_route_binding_refs")
                == capture_validation["route_binding_refs"]
            )
        else:
            capture_validation = {"ok": binding.get("packet_capture_bound") is True}
            packet_capture_bound = (
                binding.get("packet_capture_bound") is True
                and self._looks_like_digest(binding.get("packet_capture_digest"))
                and self._looks_like_digest(
                    binding.get("packet_capture_artifact_digest")
                )
                and self._looks_like_digest(
                    binding.get("packet_capture_readback_digest")
                )
            )
        if not packet_capture_bound:
            errors.append("packet capture export metadata must match")

        if privileged_capture_acquisition is not None:
            acquisition_validation = self._validate_privileged_capture_acquisition(
                privileged_capture_acquisition,
                recovery_route_trace_binding=recovery_route_trace_binding or binding,
                packet_capture_export=packet_capture_export,
            )
            privileged_capture_bound = (
                acquisition_validation["ok"]
                and binding.get("privileged_capture_ref")
                == privileged_capture_acquisition.get("acquisition_ref")
                and binding.get("privileged_capture_digest")
                == privileged_capture_acquisition.get("digest")
                and binding.get("broker_attestation_ref")
                == privileged_capture_acquisition.get("broker_attestation_ref")
                and binding.get("lease_ref")
                == privileged_capture_acquisition.get("lease_ref")
                and binding.get("capture_filter_digest")
                == privileged_capture_acquisition.get("filter_digest")
                and binding.get("capture_command_digest")
                == sha256_text(
                    canonical_json(privileged_capture_acquisition.get("capture_command", []))
                )
            )
        else:
            acquisition_validation = {
                "ok": binding.get("privileged_capture_bound") is True
            }
            privileged_capture_bound = (
                binding.get("privileged_capture_bound") is True
                and self._looks_like_digest(binding.get("privileged_capture_digest"))
                and self._looks_like_digest(binding.get("capture_filter_digest"))
            )
        if not privileged_capture_bound:
            errors.append("privileged capture acquisition metadata must match")

        route_binding_refs = list(binding.get("route_binding_refs", []))
        packet_capture_route_binding_refs = list(
            binding.get("packet_capture_route_binding_refs", [])
        )
        acquisition_route_binding_refs = list(
            binding.get("acquisition_route_binding_refs", [])
        )
        route_binding_set_bound = (
            binding.get("route_binding_digest_set_digest")
            == sha256_text(canonical_json(route_binding_refs))
            and binding.get("packet_capture_route_binding_set_digest")
            == sha256_text(canonical_json(packet_capture_route_binding_refs))
            and binding.get("acquisition_route_binding_set_digest")
            == sha256_text(canonical_json(sorted(acquisition_route_binding_refs)))
            and route_binding_refs == packet_capture_route_binding_refs
            and sorted(route_binding_refs) == sorted(acquisition_route_binding_refs)
            and binding.get("route_binding_set_bound") is True
        )
        if not route_binding_set_bound:
            errors.append("route binding refs must match across trace/capture/acquisition")

        member_capture_bindings = binding.get("member_capture_bindings")
        member_capture_binding_digest_set = binding.get(
            "member_capture_binding_digest_set"
        )
        member_capture_bindings_bound = False
        if not isinstance(member_capture_bindings, list) or not member_capture_bindings:
            errors.append("member_capture_bindings must be a non-empty list")
        elif not isinstance(member_capture_binding_digest_set, list):
            errors.append("member_capture_binding_digest_set must be a list")
        else:
            recomputed_digests: List[str] = []
            member_capture_bindings_bound = True
            for index, item in enumerate(member_capture_bindings):
                if not isinstance(item, Mapping):
                    errors.append(f"member_capture_bindings[{index}] must be an object")
                    member_capture_bindings_bound = False
                    continue
                for field_name in (
                    "member_id",
                    "verifier_transport_receipt_digest",
                    "member_route_binding_digest",
                    "route_binding_ref",
                    "packet_capture_route_export_digest",
                    "outbound_tuple_digest",
                    "inbound_tuple_digest",
                    "outbound_payload_digest",
                    "inbound_payload_digest",
                    "member_capture_binding_digest",
                ):
                    if not item.get(field_name):
                        errors.append(
                            f"member_capture_bindings[{index}].{field_name} must be present"
                        )
                        member_capture_bindings_bound = False
                if item.get("readback_verified") is not True:
                    errors.append(
                        f"member_capture_bindings[{index}].readback_verified must be true"
                    )
                    member_capture_bindings_bound = False
                if item.get("readback_packet_count") != 2:
                    errors.append(
                        f"member_capture_bindings[{index}].readback_packet_count must equal 2"
                    )
                    member_capture_bindings_bound = False
                recomputed_digest = self._collective_member_capture_binding_digest(
                    collective_id=str(binding.get("collective_id")),
                    member_id=str(item.get("member_id")),
                    recovery_route_trace_binding_digest=str(
                        binding.get("recovery_route_trace_binding_digest")
                    ),
                    member_route_binding_digest=str(
                        item.get("member_route_binding_digest")
                    ),
                    packet_capture_digest=str(binding.get("packet_capture_digest")),
                    privileged_capture_digest=str(
                        binding.get("privileged_capture_digest")
                    ),
                    route_binding_ref=str(item.get("route_binding_ref")),
                    route_export_digest=str(
                        item.get("packet_capture_route_export_digest")
                    ),
                )
                recomputed_digests.append(recomputed_digest)
                if item.get("member_capture_binding_digest") != recomputed_digest:
                    errors.append(
                        f"member_capture_bindings[{index}].member_capture_binding_digest mismatch"
                    )
                    member_capture_bindings_bound = False
            if member_capture_binding_digest_set != recomputed_digests:
                errors.append(
                    "member_capture_binding_digest_set must match member capture bindings"
                )
                member_capture_bindings_bound = False
            if binding.get("member_capture_binding_count") != len(
                member_capture_bindings
            ):
                errors.append(
                    "member_capture_binding_count must match member capture bindings"
                )
                member_capture_bindings_bound = False
            if binding.get("member_capture_binding_digest_set_digest") != sha256_text(
                canonical_json(recomputed_digests)
            ):
                errors.append(
                    "member_capture_binding_digest_set_digest must match member capture digests"
                )
                member_capture_bindings_bound = False

        expected_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": COLLECTIVE_RECOVERY_CAPTURE_EXPORT_PROFILE_ID,
                    "collective_id": binding.get("collective_id"),
                    "recovery_route_trace_binding_digest": binding.get(
                        "recovery_route_trace_binding_digest"
                    ),
                    "packet_capture_digest": binding.get("packet_capture_digest"),
                    "privileged_capture_digest": binding.get(
                        "privileged_capture_digest"
                    ),
                    "member_capture_binding_digest_set": binding.get(
                        "member_capture_binding_digest_set"
                    ),
                }
            )
        )
        digest_bound = binding.get("digest") == expected_digest
        if not digest_bound:
            errors.append("digest must match collective recovery capture export binding")

        raw_verifier_payload_stored = binding.get("raw_verifier_payload_stored") is True
        raw_route_payload_stored = binding.get("raw_route_payload_stored") is True
        raw_packet_body_stored = binding.get("raw_packet_body_stored") is True
        if raw_verifier_payload_stored:
            errors.append("raw_verifier_payload_stored must be false")
        if raw_route_payload_stored:
            errors.append("raw_route_payload_stored must be false")
        if raw_packet_body_stored:
            errors.append("raw_packet_body_stored must be false")

        complete = (
            route_trace_bound
            and packet_capture_bound
            and privileged_capture_bound
            and route_binding_set_bound
            and member_capture_bindings_bound
            and not raw_verifier_payload_stored
            and not raw_route_payload_stored
            and not raw_packet_body_stored
        )
        if binding.get("capture_binding_status") != ("complete" if complete else "incomplete"):
            errors.append("capture_binding_status must reflect binding completeness")

        return {
            "ok": not errors,
            "errors": errors,
            "profile_bound": (
                binding.get("profile_id") == COLLECTIVE_RECOVERY_CAPTURE_EXPORT_PROFILE_ID
            ),
            "recovery_route_trace_bound": route_trace_bound,
            "packet_capture_bound": packet_capture_bound,
            "privileged_capture_bound": privileged_capture_bound,
            "route_binding_set_bound": route_binding_set_bound,
            "member_capture_bindings_bound": member_capture_bindings_bound,
            "capture_binding_complete": complete,
            "digest_bound": digest_bound,
            "raw_verifier_payload_stored": raw_verifier_payload_stored,
            "raw_route_payload_stored": raw_route_payload_stored,
            "raw_packet_body_stored": raw_packet_body_stored,
        }

    def validate_collective_external_registry_sync(
        self,
        receipt: Mapping[str, Any],
        recovery_capture_export_binding: Mapping[str, Any] | None = None,
        registry_ack_authority_route_trace: Mapping[str, Any] | None = None,
        registry_ack_packet_capture_export: Mapping[str, Any] | None = None,
        registry_ack_privileged_capture_acquisition: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")

        expected_fields = {
            "kind": "collective_external_registry_sync",
            "schema_version": "1.0.0",
            "profile_id": COLLECTIVE_EXTERNAL_REGISTRY_SYNC_PROFILE_ID,
            "digest_profile": COLLECTIVE_EXTERNAL_REGISTRY_SYNC_DIGEST_PROFILE_ID,
            "registry_entry_digest_profile": (
                COLLECTIVE_EXTERNAL_REGISTRY_ENTRY_DIGEST_PROFILE_ID
            ),
            "status": "synced",
            "source_capture_export_profile_id": COLLECTIVE_RECOVERY_CAPTURE_EXPORT_PROFILE_ID,
            "submission_profile_id": COLLECTIVE_EXTERNAL_REGISTRY_SUBMISSION_PROFILE_ID,
            "ack_profile_id": COLLECTIVE_EXTERNAL_REGISTRY_ACK_PROFILE_ID,
            "ack_quorum_profile_id": COLLECTIVE_EXTERNAL_REGISTRY_ACK_QUORUM_PROFILE_ID,
            "ack_quorum_digest_profile": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_QUORUM_DIGEST_PROFILE_ID
            ),
            "ack_route_trace_profile_id": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_TRACE_PROFILE_ID
            ),
            "ack_route_trace_digest_profile": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_TRACE_DIGEST_PROFILE_ID
            ),
            "ack_route_capture_export_profile_id": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_CAPTURE_EXPORT_PROFILE_ID
            ),
            "ack_route_capture_export_digest_profile": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_CAPTURE_EXPORT_DIGEST_PROFILE_ID
            ),
            "ack_live_endpoint_probe_profile_id": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_PROFILE_ID
            ),
            "ack_live_endpoint_probe_digest_profile": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_DIGEST_PROFILE_ID
            ),
            "ack_live_endpoint_probe_transport_profile": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_TRANSPORT_PROFILE
            ),
        }
        for field_name, expected in expected_fields.items():
            if receipt.get(field_name) != expected:
                errors.append(f"{field_name} must equal {expected}")
        self._check_non_empty_string(receipt.get("collective_id"), "collective_id", errors)
        self._check_non_empty_string(receipt.get("recorded_at"), "recorded_at", errors)

        if recovery_capture_export_binding is not None:
            capture_validation = self.validate_recovery_route_trace_capture_export_binding(
                recovery_capture_export_binding,
            )
            expected_capture_digest = recovery_capture_export_binding.get("digest")
            expected_route_trace_digest = recovery_capture_export_binding.get(
                "recovery_route_trace_binding_digest"
            )
            expected_verifier_transport_digest = recovery_capture_export_binding.get(
                "recovery_verifier_transport_binding_digest"
            )
            expected_dissolution_digest = recovery_capture_export_binding.get(
                "dissolution_receipt_digest"
            )
            expected_member_recovery_binding_digest = recovery_capture_export_binding.get(
                "member_recovery_binding_digest"
            )
            expected_packet_capture_digest = recovery_capture_export_binding.get(
                "packet_capture_digest"
            )
            expected_privileged_capture_digest = recovery_capture_export_binding.get(
                "privileged_capture_digest"
            )
            expected_member_capture_set_digest = recovery_capture_export_binding.get(
                "member_capture_binding_digest_set_digest"
            )
        else:
            capture_validation = {"ok": receipt.get("capture_export_bound") is True}
            expected_capture_digest = receipt.get("recovery_capture_export_binding_digest")
            expected_route_trace_digest = receipt.get("recovery_route_trace_binding_digest")
            expected_verifier_transport_digest = receipt.get(
                "recovery_verifier_transport_binding_digest"
            )
            expected_dissolution_digest = receipt.get("dissolution_receipt_digest")
            expected_member_recovery_binding_digest = receipt.get(
                "member_recovery_binding_digest"
            )
            expected_packet_capture_digest = receipt.get("packet_capture_digest")
            expected_privileged_capture_digest = receipt.get("privileged_capture_digest")
            expected_member_capture_set_digest = receipt.get(
                "member_capture_binding_digest_set_digest"
            )

        capture_export_bound = (
            capture_validation["ok"]
            and receipt.get("recovery_capture_export_binding_digest")
            == expected_capture_digest
            and receipt.get("recovery_route_trace_binding_digest")
            == expected_route_trace_digest
            and receipt.get("recovery_verifier_transport_binding_digest")
            == expected_verifier_transport_digest
            and receipt.get("dissolution_receipt_digest")
            == expected_dissolution_digest
            and receipt.get("member_recovery_binding_digest")
            == expected_member_recovery_binding_digest
            and receipt.get("packet_capture_digest") == expected_packet_capture_digest
            and receipt.get("privileged_capture_digest")
            == expected_privileged_capture_digest
            and receipt.get("member_capture_binding_digest_set_digest")
            == expected_member_capture_set_digest
            and receipt.get("capture_export_bound") is True
        )
        if not capture_export_bound:
            errors.append("capture export metadata must match external registry sync")

        for field_name in (
            "recovery_capture_export_binding_digest",
            "recovery_route_trace_binding_digest",
            "recovery_verifier_transport_binding_digest",
            "dissolution_receipt_digest",
            "member_recovery_binding_digest",
            "packet_capture_digest",
            "privileged_capture_digest",
            "member_capture_binding_digest_set_digest",
            "legal_registry_digest",
            "governance_registry_digest",
            "registry_authority_digest",
            "registry_entry_digest",
            "submission_receipt_digest",
            "ack_receipt_digest",
            "ack_quorum_digest_set_digest",
            "ack_quorum_digest",
            "ack_authority_route_trace_digest",
            "ack_authority_plane_digest",
            "ack_route_trace_binding_digest_set_digest",
            "ack_route_trace_binding_digest",
            "ack_route_packet_capture_digest",
            "ack_route_packet_capture_artifact_digest",
            "ack_route_packet_capture_readback_digest",
            "ack_route_privileged_capture_digest",
            "ack_route_capture_filter_digest",
            "ack_route_capture_command_digest",
            "ack_route_capture_binding_digest_set_digest",
            "ack_route_capture_binding_digest",
            "ack_live_endpoint_probe_set_digest",
            "ack_live_endpoint_network_response_digest_set_digest",
            "registry_digest_set_digest",
            "digest",
        ):
            if not self._looks_like_digest(receipt.get(field_name)):
                errors.append(f"{field_name} must be sha256 hex")

        legal_ref = receipt.get("legal_registry_ref")
        governance_ref = receipt.get("governance_registry_ref")
        legal_jurisdiction = receipt.get("legal_jurisdiction")
        governance_jurisdiction = receipt.get("governance_jurisdiction")
        legal_registry_bound = (
            isinstance(legal_ref, str)
            and legal_ref.startswith("legal-registry://")
            and isinstance(legal_jurisdiction, str)
            and bool(legal_jurisdiction)
            and receipt.get("legal_registry_digest")
            == self._external_registry_digest(
                registry_ref=legal_ref,
                jurisdiction=legal_jurisdiction,
                collective_id=str(receipt.get("collective_id")),
                dissolution_receipt_digest=str(receipt.get("dissolution_receipt_digest")),
                recovery_capture_export_binding_digest=str(
                    receipt.get("recovery_capture_export_binding_digest")
                ),
                registry_kind="legal",
            )
            and receipt.get("legal_registry_bound") is True
        )
        if not legal_registry_bound:
            errors.append("legal registry ref/digest must be bound")

        governance_registry_bound = (
            isinstance(governance_ref, str)
            and governance_ref.startswith("governance-registry://")
            and isinstance(governance_jurisdiction, str)
            and bool(governance_jurisdiction)
            and receipt.get("governance_registry_digest")
            == self._external_registry_digest(
                registry_ref=governance_ref,
                jurisdiction=governance_jurisdiction,
                collective_id=str(receipt.get("collective_id")),
                dissolution_receipt_digest=str(receipt.get("dissolution_receipt_digest")),
                recovery_capture_export_binding_digest=str(
                    receipt.get("recovery_capture_export_binding_digest")
                ),
                registry_kind="governance",
            )
            and receipt.get("governance_registry_bound") is True
        )
        if not governance_registry_bound:
            errors.append("governance registry ref/digest must be bound")

        expected_authority_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": COLLECTIVE_EXTERNAL_REGISTRY_SYNC_PROFILE_ID,
                    "legal_registry_ref": legal_ref,
                    "governance_registry_ref": governance_ref,
                    "legal_jurisdiction": legal_jurisdiction,
                    "governance_jurisdiction": governance_jurisdiction,
                    "collective_id": receipt.get("collective_id"),
                    "dissolution_receipt_digest": receipt.get(
                        "dissolution_receipt_digest"
                    ),
                    "recovery_capture_export_binding_digest": receipt.get(
                        "recovery_capture_export_binding_digest"
                    ),
                }
            )
        )
        if receipt.get("registry_authority_digest") != expected_authority_digest:
            errors.append("registry_authority_digest mismatch")

        expected_entry_digest = self._collective_external_registry_entry_digest(
            collective_id=str(receipt.get("collective_id")),
            dissolution_receipt_digest=str(receipt.get("dissolution_receipt_digest")),
            recovery_capture_export_binding_digest=str(
                receipt.get("recovery_capture_export_binding_digest")
            ),
            legal_registry_digest=str(receipt.get("legal_registry_digest")),
            governance_registry_digest=str(receipt.get("governance_registry_digest")),
            member_capture_binding_digest_set_digest=str(
                receipt.get("member_capture_binding_digest_set_digest")
            ),
        )
        registry_entry_bound = (
            receipt.get("registry_entry_digest") == expected_entry_digest
            and isinstance(receipt.get("registry_entry_ref"), str)
            and str(receipt.get("registry_entry_ref")).startswith(
                "registry-entry://collective-dissolution/"
            )
            and receipt.get("registry_entry_bound") is True
        )
        if not registry_entry_bound:
            errors.append("registry entry digest must bind source artifacts")

        expected_submission_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": COLLECTIVE_EXTERNAL_REGISTRY_SUBMISSION_PROFILE_ID,
                    "registry_entry_ref": receipt.get("registry_entry_ref"),
                    "registry_entry_digest": receipt.get("registry_entry_digest"),
                    "legal_registry_digest": receipt.get("legal_registry_digest"),
                    "governance_registry_digest": receipt.get("governance_registry_digest"),
                }
            )
        )
        expected_ack_digest = self._collective_external_registry_ack_digest(
            submission_receipt_ref=str(receipt.get("submission_receipt_ref")),
            submission_receipt_digest=str(receipt.get("submission_receipt_digest")),
            registry_authority_digest=str(receipt.get("registry_authority_digest")),
            registry_authority_ref=str(legal_ref),
            registry_jurisdiction=str(legal_jurisdiction),
            registry_digest=str(receipt.get("legal_registry_digest")),
        )
        submission_ack_bound = (
            receipt.get("submission_receipt_digest") == expected_submission_digest
            and receipt.get("ack_receipt_digest") == expected_ack_digest
            and isinstance(receipt.get("submission_receipt_ref"), str)
            and str(receipt.get("submission_receipt_ref")).startswith(
                "registry-submission://collective-dissolution/"
            )
            and isinstance(receipt.get("ack_receipt_ref"), str)
            and str(receipt.get("ack_receipt_ref")).startswith(
                "registry-ack://collective-dissolution/"
            )
            and receipt.get("submission_ack_bound") is True
        )
        if not submission_ack_bound:
            errors.append("submission and acknowledgement digests must be bound")

        expected_governance_ack_digest = self._collective_external_registry_ack_digest(
            submission_receipt_ref=str(receipt.get("submission_receipt_ref")),
            submission_receipt_digest=str(receipt.get("submission_receipt_digest")),
            registry_authority_digest=str(receipt.get("registry_authority_digest")),
            registry_authority_ref=str(governance_ref),
            registry_jurisdiction=str(governance_jurisdiction),
            registry_digest=str(receipt.get("governance_registry_digest")),
        )
        expected_ack_quorum_receipts = [
            {
                "ack_receipt_ref": receipt.get("ack_receipt_ref"),
                "ack_receipt_digest": receipt.get("ack_receipt_digest"),
                "ack_status": "accepted",
                "registry_authority_ref": legal_ref,
                "registry_jurisdiction": legal_jurisdiction,
                "registry_digest": receipt.get("legal_registry_digest"),
                "submission_receipt_digest": receipt.get("submission_receipt_digest"),
                "raw_ack_payload_stored": False,
            },
            {
                "ack_receipt_ref": f"{receipt.get('ack_receipt_ref')}/governance",
                "ack_receipt_digest": expected_governance_ack_digest,
                "ack_status": "accepted",
                "registry_authority_ref": governance_ref,
                "registry_jurisdiction": governance_jurisdiction,
                "registry_digest": receipt.get("governance_registry_digest"),
                "submission_receipt_digest": receipt.get("submission_receipt_digest"),
                "raw_ack_payload_stored": False,
            },
        ]
        expected_ack_quorum_digest_set = [
            receipt.get("ack_receipt_digest"),
            expected_governance_ack_digest,
        ]
        expected_ack_quorum_jurisdictions = _dedupe_preserve_order(
            [str(legal_jurisdiction), str(governance_jurisdiction)]
        )
        ack_quorum_authority_refs = receipt.get("ack_quorum_authority_refs")
        ack_quorum_jurisdictions = receipt.get("ack_quorum_jurisdictions")
        ack_quorum_receipts = receipt.get("ack_quorum_receipts")
        ack_quorum_digest_set = receipt.get("ack_quorum_digest_set")
        expected_ack_quorum_digest_set_digest = sha256_text(
            canonical_json(expected_ack_quorum_digest_set)
        )
        expected_ack_quorum_digest = self._collective_external_registry_ack_quorum_digest(
            collective_id=str(receipt.get("collective_id")),
            submission_receipt_digest=str(receipt.get("submission_receipt_digest")),
            ack_quorum_digest_set_digest=expected_ack_quorum_digest_set_digest,
            ack_quorum_authority_refs=[str(legal_ref), str(governance_ref)],
            ack_quorum_jurisdictions=expected_ack_quorum_jurisdictions,
        )
        raw_ack_payload_stored = receipt.get("raw_ack_payload_stored") is True
        ack_quorum_bound = (
            receipt.get("ack_quorum_required_authority_count")
            == COLLECTIVE_EXTERNAL_REGISTRY_ACK_QUORUM_REQUIRED_AUTHORITIES
            and receipt.get("ack_quorum_required_jurisdiction_count")
            == COLLECTIVE_EXTERNAL_REGISTRY_ACK_QUORUM_REQUIRED_JURISDICTIONS
            and ack_quorum_authority_refs == [legal_ref, governance_ref]
            and ack_quorum_jurisdictions == expected_ack_quorum_jurisdictions
            and len(expected_ack_quorum_jurisdictions)
            >= COLLECTIVE_EXTERNAL_REGISTRY_ACK_QUORUM_REQUIRED_JURISDICTIONS
            and ack_quorum_receipts == expected_ack_quorum_receipts
            and ack_quorum_digest_set == expected_ack_quorum_digest_set
            and receipt.get("ack_quorum_digest_set_digest")
            == expected_ack_quorum_digest_set_digest
            and receipt.get("ack_quorum_digest") == expected_ack_quorum_digest
            and receipt.get("ack_quorum_status") == "complete"
            and receipt.get("ack_quorum_bound") is True
            and not raw_ack_payload_stored
        )
        if not ack_quorum_bound:
            errors.append("ack quorum must bind legal/governance registry acknowledgements")
        if raw_ack_payload_stored:
            errors.append("raw_ack_payload_stored must be false")

        raw_ack_route_payload_stored = (
            receipt.get("raw_ack_route_payload_stored") is True
        )
        ack_route_trace_bindings = receipt.get("ack_route_trace_bindings")
        expected_ack_route_trace_bindings: List[Dict[str, Any]] = []
        if not isinstance(ack_route_trace_bindings, list):
            errors.append("ack_route_trace_bindings must be a list")
            ack_route_trace_bound = False
        else:
            if registry_ack_authority_route_trace is not None:
                try:
                    self._validate_authority_route_trace_contract(
                        registry_ack_authority_route_trace
                    )
                    expected_ack_route_trace_bindings = (
                        self._build_collective_external_registry_ack_route_trace_bindings(
                            collective_id=str(receipt.get("collective_id")),
                            ack_quorum_receipts=expected_ack_quorum_receipts,
                            authority_route_trace=registry_ack_authority_route_trace,
                        )
                    )
                    expected_trace_ref = registry_ack_authority_route_trace.get(
                        "trace_ref"
                    )
                    expected_trace_digest = registry_ack_authority_route_trace.get(
                        "digest"
                    )
                    expected_plane_ref = registry_ack_authority_route_trace.get(
                        "authority_plane_ref"
                    )
                    expected_plane_digest = registry_ack_authority_route_trace.get(
                        "authority_plane_digest"
                    )
                except ValueError as exc:
                    errors.append(str(exc))
                    expected_trace_ref = receipt.get("ack_authority_route_trace_ref")
                    expected_trace_digest = receipt.get(
                        "ack_authority_route_trace_digest"
                    )
                    expected_plane_ref = receipt.get("ack_authority_plane_ref")
                    expected_plane_digest = receipt.get("ack_authority_plane_digest")
            else:
                expected_trace_ref = receipt.get("ack_authority_route_trace_ref")
                expected_trace_digest = receipt.get("ack_authority_route_trace_digest")
                expected_plane_ref = receipt.get("ack_authority_plane_ref")
                expected_plane_digest = receipt.get("ack_authority_plane_digest")
                for binding, ack_receipt in zip(
                    ack_route_trace_bindings,
                    expected_ack_quorum_receipts,
                ):
                    if not isinstance(binding, Mapping):
                        errors.append("ack_route_trace_bindings entries must be objects")
                        continue
                    expected_binding = dict(binding)
                    expected_binding["ack_route_binding_digest"] = (
                        self._collective_external_registry_ack_route_binding_digest(
                            collective_id=str(receipt.get("collective_id")),
                            ack_receipt_digest=str(ack_receipt["ack_receipt_digest"]),
                            registry_authority_ref=str(
                                ack_receipt["registry_authority_ref"]
                            ),
                            registry_jurisdiction=str(
                                ack_receipt["registry_jurisdiction"]
                            ),
                            authority_route_trace_digest=str(
                                receipt.get("ack_authority_route_trace_digest")
                            ),
                            route_binding_ref=str(binding.get("route_binding_ref")),
                            remote_host_ref=str(binding.get("remote_host_ref")),
                            remote_host_attestation_ref=str(
                                binding.get("remote_host_attestation_ref")
                            ),
                            os_observer_host_binding_digest=str(
                                binding.get("os_observer_host_binding_digest")
                            ),
                            socket_response_digest=str(
                                binding.get("socket_response_digest")
                            ),
                        )
                    )
                    expected_ack_route_trace_bindings.append(expected_binding)

            expected_ack_route_trace_digest_set = [
                binding["ack_route_binding_digest"]
                for binding in expected_ack_route_trace_bindings
            ]
            expected_ack_route_trace_digest_set_digest = sha256_text(
                canonical_json(expected_ack_route_trace_digest_set)
            )
            expected_ack_route_trace_route_binding_refs = [
                binding["route_binding_ref"]
                for binding in expected_ack_route_trace_bindings
            ]
            expected_ack_route_trace_binding_digest = (
                self._collective_external_registry_ack_route_trace_digest(
                    collective_id=str(receipt.get("collective_id")),
                    ack_quorum_digest=str(receipt.get("ack_quorum_digest")),
                    authority_route_trace_digest=str(
                        receipt.get("ack_authority_route_trace_digest")
                    ),
                    ack_route_trace_binding_digest_set_digest=(
                        expected_ack_route_trace_digest_set_digest
                    ),
                    ack_quorum_authority_refs=[str(legal_ref), str(governance_ref)],
                    route_binding_refs=expected_ack_route_trace_route_binding_refs,
                )
            )
            ack_route_trace_bound = (
                receipt.get("ack_authority_route_trace_ref") == expected_trace_ref
                and receipt.get("ack_authority_route_trace_digest")
                == expected_trace_digest
                and receipt.get("ack_authority_plane_ref") == expected_plane_ref
                and receipt.get("ack_authority_plane_digest") == expected_plane_digest
                and isinstance(receipt.get("ack_authority_route_trace_ref"), str)
                and str(receipt.get("ack_authority_route_trace_ref")).startswith(
                    "authority-route-trace://"
                )
                and ack_route_trace_bindings == expected_ack_route_trace_bindings
                and receipt.get("ack_route_trace_route_binding_refs")
                == expected_ack_route_trace_route_binding_refs
                and receipt.get("ack_route_trace_remote_host_refs")
                == [
                    binding["remote_host_ref"]
                    for binding in expected_ack_route_trace_bindings
                ]
                and receipt.get("ack_route_trace_remote_host_attestation_refs")
                == [
                    binding["remote_host_attestation_ref"]
                    for binding in expected_ack_route_trace_bindings
                ]
                and receipt.get("ack_route_trace_remote_jurisdictions")
                == [
                    binding["remote_jurisdiction"]
                    for binding in expected_ack_route_trace_bindings
                ]
                and receipt.get("ack_route_trace_binding_digest_set")
                == expected_ack_route_trace_digest_set
                and receipt.get("ack_route_trace_binding_digest_set_digest")
                == expected_ack_route_trace_digest_set_digest
                and receipt.get("ack_route_trace_binding_digest")
                == expected_ack_route_trace_binding_digest
                and receipt.get("ack_route_trace_binding_count")
                == len(expected_ack_route_trace_bindings)
                and receipt.get("ack_route_trace_bound") is True
                and all(
                    binding.get("mtls_status") == "authenticated"
                    and binding.get("raw_ack_route_payload_stored") is False
                    for binding in ack_route_trace_bindings
                    if isinstance(binding, Mapping)
                )
                and not raw_ack_route_payload_stored
            )
        if not ack_route_trace_bound:
            errors.append("ack route trace must bind registry acknowledgements")
        if raw_ack_route_payload_stored:
            errors.append("raw_ack_route_payload_stored must be false")

        expected_ack_route_trace_route_binding_refs = [
            binding["route_binding_ref"]
            for binding in expected_ack_route_trace_bindings
        ]
        if registry_ack_packet_capture_export is not None:
            expected_packet_capture_route_refs = [
                route_export["route_binding_ref"]
                for route_export in registry_ack_packet_capture_export.get(
                    "route_exports",
                    [],
                )
                if isinstance(route_export, Mapping)
                and isinstance(route_export.get("route_binding_ref"), str)
            ]
        else:
            expected_packet_capture_route_refs = list(
                receipt.get("ack_route_packet_capture_route_binding_refs", [])
            )
        ack_route_trace_for_capture = {
            "authority_route_trace_ref": receipt.get("ack_authority_route_trace_ref"),
            "authority_route_trace_digest": receipt.get(
                "ack_authority_route_trace_digest"
            ),
            "route_binding_refs": expected_packet_capture_route_refs,
            "route_count": len(expected_packet_capture_route_refs),
        }
        if registry_ack_packet_capture_export is not None:
            ack_packet_capture_validation = self._validate_packet_capture_export(
                registry_ack_packet_capture_export,
                recovery_route_trace_binding=ack_route_trace_for_capture,
            )
            ack_route_packet_capture_bound = (
                ack_packet_capture_validation["ok"]
                and receipt.get("ack_route_packet_capture_ref")
                == registry_ack_packet_capture_export.get("capture_ref")
                and receipt.get("ack_route_packet_capture_digest")
                == registry_ack_packet_capture_export.get("digest")
                and receipt.get("ack_route_packet_capture_artifact_digest")
                == registry_ack_packet_capture_export.get("artifact_digest")
                and receipt.get("ack_route_packet_capture_readback_digest")
                == registry_ack_packet_capture_export.get("readback_digest")
                and receipt.get("ack_route_packet_count")
                == registry_ack_packet_capture_export.get("packet_count")
                and receipt.get("ack_route_packet_capture_route_binding_refs")
                == expected_packet_capture_route_refs
            )
        else:
            ack_route_packet_capture_bound = (
                receipt.get("ack_route_packet_capture_profile")
                == COLLECTIVE_PACKET_CAPTURE_PROFILE
                and receipt.get("ack_route_packet_capture_artifact_format")
                == COLLECTIVE_PACKET_CAPTURE_FORMAT
                and receipt.get("ack_route_packet_capture_export_status") == "verified"
                and self._looks_like_digest(
                    receipt.get("ack_route_packet_capture_digest")
                )
                and self._looks_like_digest(
                    receipt.get("ack_route_packet_capture_artifact_digest")
                )
                and self._looks_like_digest(
                    receipt.get("ack_route_packet_capture_readback_digest")
                )
            )
        if not ack_route_packet_capture_bound:
            errors.append("ack route packet capture metadata must match")

        if registry_ack_privileged_capture_acquisition is not None:
            ack_privileged_capture_validation = (
                self._validate_privileged_capture_acquisition(
                    registry_ack_privileged_capture_acquisition,
                    recovery_route_trace_binding=ack_route_trace_for_capture,
                    packet_capture_export=registry_ack_packet_capture_export,
                )
            )
            expected_acquisition_route_refs = list(
                registry_ack_privileged_capture_acquisition.get(
                    "route_binding_refs",
                    [],
                )
            )
            ack_route_privileged_capture_bound = (
                ack_privileged_capture_validation["ok"]
                and receipt.get("ack_route_privileged_capture_ref")
                == registry_ack_privileged_capture_acquisition.get("acquisition_ref")
                and receipt.get("ack_route_privileged_capture_digest")
                == registry_ack_privileged_capture_acquisition.get("digest")
                and receipt.get("ack_route_broker_attestation_ref")
                == registry_ack_privileged_capture_acquisition.get(
                    "broker_attestation_ref"
                )
                and receipt.get("ack_route_lease_ref")
                == registry_ack_privileged_capture_acquisition.get("lease_ref")
                and receipt.get("ack_route_capture_filter_digest")
                == registry_ack_privileged_capture_acquisition.get("filter_digest")
                and receipt.get("ack_route_capture_command_digest")
                == sha256_text(
                    canonical_json(
                        registry_ack_privileged_capture_acquisition.get(
                            "capture_command",
                            [],
                        )
                    )
                )
            )
        else:
            expected_acquisition_route_refs = list(
                receipt.get("ack_route_acquisition_route_binding_refs", [])
            )
            ack_route_privileged_capture_bound = (
                receipt.get("ack_route_privileged_capture_profile")
                == COLLECTIVE_PRIVILEGED_CAPTURE_PROFILE
                and receipt.get("ack_route_privilege_mode")
                == COLLECTIVE_PRIVILEGED_CAPTURE_MODE
                and self._looks_like_digest(
                    receipt.get("ack_route_privileged_capture_digest")
                )
                and self._looks_like_digest(
                    receipt.get("ack_route_capture_filter_digest")
                )
            )
        if not ack_route_privileged_capture_bound:
            errors.append("ack route privileged capture metadata must match")

        ack_route_capture_route_binding_set_bound = (
            receipt.get("ack_route_packet_capture_route_binding_set_digest")
            == sha256_text(canonical_json(expected_packet_capture_route_refs))
            and receipt.get("ack_route_acquisition_route_binding_set_digest")
            == sha256_text(canonical_json(sorted(expected_acquisition_route_refs)))
            and sorted(expected_packet_capture_route_refs)
            == sorted(expected_ack_route_trace_route_binding_refs)
            and sorted(expected_acquisition_route_refs)
            == sorted(expected_ack_route_trace_route_binding_refs)
            and receipt.get("ack_route_capture_route_binding_set_bound") is True
        )
        if not ack_route_capture_route_binding_set_bound:
            errors.append("ack route capture refs must match route trace refs")

        ack_route_capture_bindings = receipt.get("ack_route_capture_bindings")
        expected_ack_route_capture_bindings: List[Dict[str, Any]] = []
        if not isinstance(ack_route_capture_bindings, list):
            errors.append("ack_route_capture_bindings must be a list")
            ack_route_capture_bindings_bound = False
        elif (
            registry_ack_packet_capture_export is not None
            and registry_ack_privileged_capture_acquisition is not None
        ):
            expected_ack_route_capture_bindings = (
                self._build_collective_external_registry_ack_route_capture_bindings(
                    collective_id=str(receipt.get("collective_id")),
                    ack_route_trace_bindings=expected_ack_route_trace_bindings,
                    packet_capture_export=registry_ack_packet_capture_export,
                    privileged_capture_acquisition=(
                        registry_ack_privileged_capture_acquisition
                    ),
                    ack_route_trace_binding_digest=str(
                        receipt.get("ack_route_trace_binding_digest")
                    ),
                )
            )
            ack_route_capture_bindings_bound = (
                ack_route_capture_bindings == expected_ack_route_capture_bindings
            )
        else:
            for binding, route_binding in zip(
                ack_route_capture_bindings,
                expected_ack_route_trace_bindings,
            ):
                if not isinstance(binding, Mapping):
                    errors.append("ack_route_capture_bindings entries must be objects")
                    continue
                expected_binding = dict(binding)
                expected_binding["ack_route_capture_binding_digest"] = (
                    self._collective_external_registry_ack_route_capture_binding_digest(
                        collective_id=str(receipt.get("collective_id")),
                        ack_receipt_digest=str(route_binding.get("ack_receipt_digest")),
                        ack_route_binding_digest=str(
                            route_binding.get("ack_route_binding_digest")
                        ),
                        ack_route_trace_binding_digest=str(
                            receipt.get("ack_route_trace_binding_digest")
                        ),
                        packet_capture_digest=str(
                            receipt.get("ack_route_packet_capture_digest")
                        ),
                        privileged_capture_digest=str(
                            receipt.get("ack_route_privileged_capture_digest")
                        ),
                        route_binding_ref=str(binding.get("route_binding_ref")),
                        route_export_digest=str(
                            binding.get("packet_capture_route_export_digest")
                        ),
                    )
                )
                expected_ack_route_capture_bindings.append(expected_binding)
            ack_route_capture_bindings_bound = (
                ack_route_capture_bindings == expected_ack_route_capture_bindings
            )

        expected_ack_route_capture_digest_set = [
            binding["ack_route_capture_binding_digest"]
            for binding in expected_ack_route_capture_bindings
        ]
        expected_ack_route_capture_digest_set_digest = sha256_text(
            canonical_json(expected_ack_route_capture_digest_set)
        )
        expected_ack_route_capture_binding_digest = (
            self._collective_external_registry_ack_route_capture_export_digest(
                collective_id=str(receipt.get("collective_id")),
                ack_route_trace_binding_digest=str(
                    receipt.get("ack_route_trace_binding_digest")
                ),
                packet_capture_digest=str(
                    receipt.get("ack_route_packet_capture_digest")
                ),
                privileged_capture_digest=str(
                    receipt.get("ack_route_privileged_capture_digest")
                ),
                ack_route_capture_binding_digest_set_digest=(
                    expected_ack_route_capture_digest_set_digest
                ),
            )
        )
        ack_route_capture_bindings_bound = (
            ack_route_capture_bindings_bound
            and receipt.get("ack_route_capture_binding_digest_set")
            == expected_ack_route_capture_digest_set
            and receipt.get("ack_route_capture_binding_digest_set_digest")
            == expected_ack_route_capture_digest_set_digest
            and receipt.get("ack_route_capture_binding_digest")
            == expected_ack_route_capture_binding_digest
            and receipt.get("ack_route_capture_binding_count")
            == len(expected_ack_route_capture_bindings)
            and all(
                binding.get("readback_verified") is True
                and binding.get("readback_packet_count") == 2
                and binding.get("raw_packet_body_stored") is False
                for binding in ack_route_capture_bindings
                if isinstance(binding, Mapping)
            )
        )
        if not ack_route_capture_bindings_bound:
            errors.append("ack route capture bindings must bind packet readback evidence")

        ack_route_capture_export_bound = (
            ack_route_trace_bound
            and ack_route_packet_capture_bound
            and ack_route_privileged_capture_bound
            and ack_route_capture_route_binding_set_bound
            and ack_route_capture_bindings_bound
            and receipt.get("ack_route_capture_export_bound") is True
        )
        if not ack_route_capture_export_bound:
            errors.append("ack route capture export must bind ack route trace evidence")

        ack_live_endpoint_probe_receipts = receipt.get(
            "ack_live_endpoint_probe_receipts"
        )
        expected_ack_live_endpoint_probe_digests: List[str] = []
        expected_ack_live_endpoint_authority_refs: List[str] = []
        expected_ack_live_endpoint_jurisdictions: List[str] = []
        expected_ack_live_endpoint_response_digests: List[str] = []
        ack_live_endpoint_probe_bound = False
        raw_ack_endpoint_payload_stored = (
            receipt.get("raw_ack_endpoint_payload_stored") is True
        )
        if not isinstance(ack_live_endpoint_probe_receipts, list):
            errors.append("ack_live_endpoint_probe_receipts must be a list")
        elif len(ack_live_endpoint_probe_receipts) != len(expected_ack_quorum_receipts):
            errors.append(
                "ack_live_endpoint_probe_receipts must cover every ack quorum receipt"
            )
        else:
            probe_receipts_valid = True
            for probe_receipt, ack_receipt in zip(
                ack_live_endpoint_probe_receipts,
                expected_ack_quorum_receipts,
            ):
                if not isinstance(probe_receipt, Mapping):
                    errors.append("ack_live_endpoint_probe_receipts entries must be objects")
                    probe_receipts_valid = False
                    continue
                probe_validation = (
                    self.validate_external_registry_ack_endpoint_probe_receipt(
                        probe_receipt,
                        receipt,
                        ack_receipt,
                    )
                )
                if not probe_validation["ok"]:
                    errors.extend(
                        "ack_live_endpoint_probe_receipts: " + error
                        for error in probe_validation["errors"]
                    )
                    probe_receipts_valid = False
                expected_ack_live_endpoint_probe_digests.append(
                    str(probe_receipt.get("digest"))
                )
                expected_ack_live_endpoint_authority_refs.append(
                    str(probe_receipt.get("registry_authority_ref"))
                )
                expected_ack_live_endpoint_jurisdictions.append(
                    str(probe_receipt.get("registry_jurisdiction"))
                )
                expected_ack_live_endpoint_response_digests.append(
                    str(probe_receipt.get("network_response_digest"))
                )
            expected_probe_set_digest = sha256_text(
                canonical_json(expected_ack_live_endpoint_probe_digests)
            )
            expected_response_digest_set_digest = sha256_text(
                canonical_json(expected_ack_live_endpoint_response_digests)
            )
            ack_live_endpoint_probe_bound = (
                probe_receipts_valid
                and receipt.get("ack_live_endpoint_probe_digests")
                == expected_ack_live_endpoint_probe_digests
                and receipt.get("ack_live_endpoint_probe_set_digest")
                == expected_probe_set_digest
                and receipt.get("ack_live_endpoint_probe_authority_refs")
                == expected_ack_live_endpoint_authority_refs
                and receipt.get("ack_live_endpoint_probe_jurisdictions")
                == expected_ack_live_endpoint_jurisdictions
                and receipt.get("ack_live_endpoint_network_response_digests")
                == expected_ack_live_endpoint_response_digests
                and receipt.get(
                    "ack_live_endpoint_network_response_digest_set_digest"
                )
                == expected_response_digest_set_digest
                and receipt.get("ack_live_endpoint_probe_count")
                == len(expected_ack_live_endpoint_probe_digests)
                and receipt.get("ack_live_endpoint_probe_bound") is True
                and not raw_ack_endpoint_payload_stored
            )
        if not ack_live_endpoint_probe_bound:
            errors.append("ack live endpoint probes must bind every registry acknowledgement")
        if raw_ack_endpoint_payload_stored:
            errors.append("raw_ack_endpoint_payload_stored must be false")

        registry_digest_set = receipt.get("registry_digest_set")
        registry_digest_set_bound = (
            isinstance(registry_digest_set, list)
            and registry_digest_set
            == [
                receipt.get("legal_registry_digest"),
                receipt.get("governance_registry_digest"),
                receipt.get("registry_entry_digest"),
                receipt.get("submission_receipt_digest"),
                receipt.get("ack_receipt_digest"),
                receipt.get("ack_quorum_digest"),
                receipt.get("ack_route_trace_binding_digest"),
                receipt.get("ack_route_capture_binding_digest"),
                receipt.get("ack_live_endpoint_probe_set_digest"),
            ]
            and receipt.get("registry_digest_set_digest")
            == sha256_text(canonical_json(registry_digest_set))
        )
        if not registry_digest_set_bound:
            errors.append("registry digest set must bind legal/governance/entry/ack")

        expected_digest = sha256_text(
            canonical_json(self._collective_external_registry_sync_digest_payload(receipt))
        )
        digest_bound = receipt.get("digest") == expected_digest
        if not digest_bound:
            errors.append("digest must match external registry sync payload")

        raw_dissolution_payload_stored = (
            receipt.get("raw_dissolution_payload_stored") is True
        )
        raw_registry_payload_stored = receipt.get("raw_registry_payload_stored") is True
        raw_packet_body_stored = receipt.get("raw_packet_body_stored") is True
        if raw_dissolution_payload_stored:
            errors.append("raw_dissolution_payload_stored must be false")
        if raw_registry_payload_stored:
            errors.append("raw_registry_payload_stored must be false")
        if raw_packet_body_stored:
            errors.append("raw_packet_body_stored must be false")

        complete = (
            capture_export_bound
            and legal_registry_bound
            and governance_registry_bound
            and registry_entry_bound
            and submission_ack_bound
            and ack_quorum_bound
            and ack_route_trace_bound
            and ack_route_capture_export_bound
            and ack_live_endpoint_probe_bound
            and registry_digest_set_bound
            and digest_bound
            and not raw_dissolution_payload_stored
            and not raw_registry_payload_stored
            and not raw_ack_payload_stored
            and not raw_ack_route_payload_stored
            and not raw_ack_endpoint_payload_stored
            and not raw_packet_body_stored
        )
        if receipt.get("external_registry_sync_complete") is not complete:
            errors.append("external_registry_sync_complete must reflect validation result")

        return {
            "ok": not errors,
            "errors": errors,
            "profile_bound": (
                receipt.get("profile_id") == COLLECTIVE_EXTERNAL_REGISTRY_SYNC_PROFILE_ID
            ),
            "capture_export_bound": capture_export_bound,
            "legal_registry_bound": legal_registry_bound,
            "governance_registry_bound": governance_registry_bound,
            "registry_entry_bound": registry_entry_bound,
            "submission_ack_bound": submission_ack_bound,
            "ack_quorum_bound": ack_quorum_bound,
            "ack_route_trace_bound": ack_route_trace_bound,
            "ack_route_packet_capture_bound": ack_route_packet_capture_bound,
            "ack_route_privileged_capture_bound": ack_route_privileged_capture_bound,
            "ack_route_capture_bindings_bound": ack_route_capture_bindings_bound,
            "ack_route_capture_route_binding_set_bound": (
                ack_route_capture_route_binding_set_bound
            ),
            "ack_route_capture_export_bound": ack_route_capture_export_bound,
            "ack_live_endpoint_probe_bound": ack_live_endpoint_probe_bound,
            "registry_digest_set_bound": registry_digest_set_bound,
            "external_registry_sync_complete": complete,
            "digest_bound": digest_bound,
            "raw_dissolution_payload_stored": raw_dissolution_payload_stored,
            "raw_registry_payload_stored": raw_registry_payload_stored,
            "raw_ack_payload_stored": raw_ack_payload_stored,
            "raw_ack_route_payload_stored": raw_ack_route_payload_stored,
            "raw_ack_endpoint_payload_stored": raw_ack_endpoint_payload_stored,
            "raw_packet_body_stored": raw_packet_body_stored,
        }

    def validate_external_registry_ack_endpoint_probe_receipt(
        self,
        receipt: Mapping[str, Any],
        external_registry_sync: Mapping[str, Any],
        ack_receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")
        if not isinstance(external_registry_sync, Mapping):
            raise ValueError("external_registry_sync must be a mapping")
        if not isinstance(ack_receipt, Mapping):
            raise ValueError("ack_receipt must be a mapping")

        expected_fields = {
            "kind": "collective_external_registry_ack_endpoint_probe",
            "schema_version": "1.0.0",
            "profile_id": COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_PROFILE_ID,
            "digest_profile": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_DIGEST_PROFILE_ID
            ),
            "transport_profile": (
                COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_TRANSPORT_PROFILE
            ),
            "ack_receipt_ref": ack_receipt.get("ack_receipt_ref"),
            "ack_receipt_digest": ack_receipt.get("ack_receipt_digest"),
            "ack_status": ack_receipt.get("ack_status"),
            "registry_authority_ref": ack_receipt.get("registry_authority_ref"),
            "registry_jurisdiction": ack_receipt.get("registry_jurisdiction"),
            "registry_digest": ack_receipt.get("registry_digest"),
            "submission_receipt_digest": ack_receipt.get(
                "submission_receipt_digest"
            ),
            "registry_entry_digest": external_registry_sync.get(
                "registry_entry_digest"
            ),
            "ack_quorum_digest": external_registry_sync.get("ack_quorum_digest"),
            "ack_route_trace_binding_digest": external_registry_sync.get(
                "ack_route_trace_binding_digest"
            ),
            "ack_route_capture_binding_digest": external_registry_sync.get(
                "ack_route_capture_binding_digest"
            ),
            "http_status": 200,
            "network_probe_status": "reachable",
            "network_probe_bound": True,
            "raw_ack_payload_stored": False,
            "raw_endpoint_payload_stored": False,
        }
        for field_name, expected in expected_fields.items():
            if receipt.get(field_name) != expected:
                errors.append(f"{field_name} must equal {expected}")
        for field_name in (
            "ack_receipt_digest",
            "registry_digest",
            "submission_receipt_digest",
            "registry_entry_digest",
            "ack_quorum_digest",
            "ack_route_trace_binding_digest",
            "ack_route_capture_binding_digest",
            "network_response_digest",
            "digest",
        ):
            if not self._looks_like_digest(receipt.get(field_name)):
                errors.append(f"{field_name} must be sha256 hex")
        endpoint = receipt.get("registry_ack_endpoint_ref")
        if not isinstance(endpoint, str) or not _is_live_http_endpoint(endpoint):
            errors.append("registry_ack_endpoint_ref must be a live http(s) endpoint")
        if not isinstance(receipt.get("probe_id"), str) or not receipt.get("probe_id"):
            errors.append("probe_id must be present")
        if not isinstance(receipt.get("request_timeout_ms"), int) or receipt.get(
            "request_timeout_ms"
        ) <= 0:
            errors.append("request_timeout_ms must be positive")
        latency = receipt.get("observed_probe_latency_ms")
        if not isinstance(latency, (int, float)) or latency < 0:
            errors.append("observed_probe_latency_ms must be non-negative")
        if (
            isinstance(latency, (int, float))
            and latency
            > COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_LATENCY_BUDGET_MS
        ):
            errors.append("observed_probe_latency_ms must fit latency budget")
        if (
            receipt.get("latency_budget_ms")
            != COLLECTIVE_EXTERNAL_REGISTRY_ACK_LIVE_ENDPOINT_LATENCY_BUDGET_MS
        ):
            errors.append("latency_budget_ms mismatch")
        if not isinstance(receipt.get("checked_at"), str) or not receipt.get(
            "checked_at"
        ):
            errors.append("checked_at must be present")
        expected_digest = sha256_text(
            canonical_json(
                self._collective_external_registry_ack_endpoint_probe_digest_payload(
                    receipt
                )
            )
        )
        if receipt.get("digest") != expected_digest:
            errors.append("digest must match ack endpoint probe payload")

        return {
            "ok": not errors,
            "errors": errors,
            "network_probe_bound": receipt.get("network_probe_bound") is True,
            "raw_ack_payload_stored": receipt.get("raw_ack_payload_stored") is True,
            "raw_endpoint_payload_stored": receipt.get("raw_endpoint_payload_stored")
            is True,
        }

    def _derive_member_recovery_proofs(
        self,
        identity_confirmation_profiles: Mapping[str, Mapping[str, Any]],
        required_member_ids: Sequence[str],
    ) -> Dict[str, Dict[str, Any]]:
        if not isinstance(identity_confirmation_profiles, Mapping):
            raise ValueError("identity_confirmation_profiles must be a mapping")
        recovery_proofs: Dict[str, Dict[str, Any]] = {}
        for member_id in required_member_ids:
            profile = identity_confirmation_profiles.get(member_id)
            if not isinstance(profile, Mapping):
                raise ValueError(f"missing identity confirmation profile for {member_id}")
            confirmation_id = self._normalize_non_empty_string(
                profile.get("confirmation_id"),
                f"identity_confirmation_profiles[{member_id}].confirmation_id",
            )
            confirmation_digest = self._normalize_digest(
                profile.get("confirmation_digest"),
                f"identity_confirmation_profiles[{member_id}].confirmation_digest",
            )
            consistency = profile.get("self_report_witness_consistency")
            if not isinstance(consistency, Mapping):
                raise ValueError(
                    f"identity_confirmation_profiles[{member_id}].self_report_witness_consistency "
                    "must be an object"
                )
            consistency_digest = self._normalize_digest(
                consistency.get("consistency_digest"),
                f"identity_confirmation_profiles[{member_id}].self_report_witness_consistency.consistency_digest",
            )
            required_dimensions = list(profile.get("required_dimensions", []))
            if required_dimensions != COLLECTIVE_REQUIRED_IDENTITY_CONFIRMATION_DIMENSIONS:
                raise ValueError(
                    f"identity confirmation profile for {member_id} must carry the fixed "
                    "four-dimensional recovery profile"
                )
            if profile.get("identity_id") != member_id:
                raise ValueError(f"identity confirmation profile for {member_id} must match member_id")
            if profile.get("profile_id") != COLLECTIVE_IDENTITY_CONFIRMATION_PROFILE_ID:
                raise ValueError(
                    f"identity confirmation profile for {member_id} must use "
                    f"{COLLECTIVE_IDENTITY_CONFIRMATION_PROFILE_ID}"
                )
            if profile.get("result") != "passed" or profile.get("active_transition_allowed") is not True:
                raise PermissionError(
                    f"identity confirmation profile for {member_id} must pass before dissolution"
                )
            witness_quorum = profile.get("witness_quorum", {})
            if not isinstance(witness_quorum, Mapping) or witness_quorum.get("status") != "met":
                raise PermissionError(
                    f"identity confirmation profile for {member_id} must have witness quorum"
                )
            if consistency.get("policy_id") != COLLECTIVE_IDENTITY_CONFIRMATION_CONSISTENCY_POLICY_ID:
                raise ValueError(
                    f"identity confirmation profile for {member_id} must bind self-report witness consistency"
                )
            if consistency.get("status") != "bound":
                raise PermissionError(
                    f"identity confirmation profile for {member_id} must bind self-report witness consistency"
                )
            recovery_proofs[member_id] = {
                "member_id": member_id,
                "identity_confirmation_ref": f"identity-confirmation://{confirmation_id}",
                "identity_confirmation_profile_id": COLLECTIVE_IDENTITY_CONFIRMATION_PROFILE_ID,
                "identity_confirmation_digest": confirmation_digest,
                "active_transition_allowed": True,
                "result": "passed",
                "required_dimensions": list(COLLECTIVE_REQUIRED_IDENTITY_CONFIRMATION_DIMENSIONS),
                "witness_quorum_status": "met",
                "self_report_witness_consistency_status": "bound",
                "self_report_witness_consistency_digest": consistency_digest,
                "recovery_status": "confirmed",
                "raw_profile_stored": False,
            }
        return recovery_proofs

    def _build_member_recovery_verifier_transport_receipt(
        self,
        *,
        collective_id: str,
        member_id: str,
        proof: Mapping[str, Any],
        member_recovery_binding_digest: str,
        dissolution_receipt_digest: str,
        recorded_at: str,
        index: int,
    ) -> Dict[str, Any]:
        jurisdiction = COLLECTIVE_RECOVERY_VERIFIER_JURISDICTIONS[
            index % len(COLLECTIVE_RECOVERY_VERIFIER_JURISDICTIONS)
        ]
        suffix = sha256_text(
            canonical_json(
                {
                    "collective_id": collective_id,
                    "member_id": member_id,
                    "identity_confirmation_digest": proof["identity_confirmation_digest"],
                    "member_recovery_binding_digest": member_recovery_binding_digest,
                    "dissolution_receipt_digest": dissolution_receipt_digest,
                    "jurisdiction": jurisdiction,
                }
            )
        )[:12]
        challenge_ref = f"challenge://collective-recovery/{collective_id}/{member_id}/{suffix}"
        challenge_digest = sha256_text(
            canonical_json(
                {
                    "challenge_ref": challenge_ref,
                    "identity_confirmation_digest": proof["identity_confirmation_digest"],
                    "member_recovery_binding_digest": member_recovery_binding_digest,
                    "dissolution_receipt_digest": dissolution_receipt_digest,
                }
            )
        )
        request_payload_digest = sha256_text(
            canonical_json(
                {
                    "payload_kind": "collective-recovery-verifier-request",
                    "member_id": member_id,
                    "identity_confirmation_ref": proof["identity_confirmation_ref"],
                    "challenge_digest": challenge_digest,
                }
            )
        )
        response_payload_digest = sha256_text(
            canonical_json(
                {
                    "payload_kind": "collective-recovery-verifier-response",
                    "member_id": member_id,
                    "receipt_status": "verified",
                    "challenge_digest": challenge_digest,
                    "request_payload_digest": request_payload_digest,
                }
            )
        )
        exchange_digest = sha256_text(
            canonical_json(
                {
                    "exchange_id": f"verifier-transport-exchange-{suffix}",
                    "challenge_digest": challenge_digest,
                    "request_payload_digest": request_payload_digest,
                    "response_payload_digest": response_payload_digest,
                }
            )
        )
        receipt = {
            "kind": "collective_recovery_verifier_transport_receipt",
            "schema_version": "1.0.0",
            "receipt_id": f"collective-recovery-verifier-receipt-{suffix}",
            "collective_id": collective_id,
            "member_id": member_id,
            "profile_id": COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID,
            "identity_confirmation_ref": proof["identity_confirmation_ref"],
            "identity_confirmation_digest": proof["identity_confirmation_digest"],
            "self_report_witness_consistency_digest": proof[
                "self_report_witness_consistency_digest"
            ],
            "member_recovery_binding_digest": member_recovery_binding_digest,
            "dissolution_receipt_digest": dissolution_receipt_digest,
            "verifier_network_receipt_id": f"verifier-network-receipt-{suffix}",
            "verifier_ref": f"verifier://collective-recovery/{jurisdiction}/{suffix}",
            "verifier_endpoint": f"verifier://collective-recovery/{jurisdiction.lower()}",
            "jurisdiction": jurisdiction,
            "network_profile_id": COLLECTIVE_VERIFIER_NETWORK_PROFILE_ID,
            "transport_profile": COLLECTIVE_VERIFIER_TRANSPORT_PROFILE,
            "transport_exchange_profile_id": COLLECTIVE_VERIFIER_TRANSPORT_EXCHANGE_PROFILE_ID,
            "transport_exchange_id": f"verifier-transport-exchange-{suffix}",
            "transport_exchange_digest": exchange_digest,
            "challenge_ref": challenge_ref,
            "challenge_digest": challenge_digest,
            "request_payload_ref": f"sealed://collective-recovery/{member_id}/request/{suffix}",
            "request_payload_digest": request_payload_digest,
            "response_payload_ref": f"sealed://collective-recovery/{member_id}/response/{suffix}",
            "response_payload_digest": response_payload_digest,
            "receipt_status": "verified",
            "observed_latency_ms": 42.0 + index,
            "recorded_at": recorded_at,
            "raw_verifier_payload_stored": False,
        }
        receipt["digest"] = sha256_text(
            canonical_json(self._member_recovery_verifier_transport_receipt_digest_payload(receipt))
        )
        return receipt

    def _validate_member_recovery_verifier_transport_receipt(
        self,
        receipt: Mapping[str, Any],
        *,
        member_id: str,
        proof: Mapping[str, Any],
        member_recovery_binding_digest: str,
        dissolution_receipt_digest: str,
        errors: List[str],
    ) -> bool:
        ok = True
        expected_fields = {
            "kind": "collective_recovery_verifier_transport_receipt",
            "schema_version": "1.0.0",
            "member_id": member_id,
            "profile_id": COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID,
            "member_recovery_binding_digest": member_recovery_binding_digest,
            "dissolution_receipt_digest": dissolution_receipt_digest,
            "network_profile_id": COLLECTIVE_VERIFIER_NETWORK_PROFILE_ID,
            "transport_profile": COLLECTIVE_VERIFIER_TRANSPORT_PROFILE,
            "transport_exchange_profile_id": COLLECTIVE_VERIFIER_TRANSPORT_EXCHANGE_PROFILE_ID,
            "receipt_status": "verified",
        }
        for field_name, expected in expected_fields.items():
            if receipt.get(field_name) != expected:
                errors.append(
                    f"verifier_transport_receipts[{member_id}].{field_name} must equal {expected}"
                )
                ok = False
        if proof:
            for field_name in (
                "identity_confirmation_ref",
                "identity_confirmation_digest",
                "self_report_witness_consistency_digest",
            ):
                if receipt.get(field_name) != proof.get(field_name):
                    errors.append(
                        f"verifier_transport_receipts[{member_id}].{field_name} "
                        "must match member recovery proof"
                    )
                    ok = False
        digest_fields = (
            "identity_confirmation_digest",
            "self_report_witness_consistency_digest",
            "member_recovery_binding_digest",
            "dissolution_receipt_digest",
            "transport_exchange_digest",
            "challenge_digest",
            "request_payload_digest",
            "response_payload_digest",
            "digest",
        )
        for field_name in digest_fields:
            if not self._looks_like_digest(receipt.get(field_name)):
                errors.append(
                    f"verifier_transport_receipts[{member_id}].{field_name} must be sha256 hex"
                )
                ok = False
        if receipt.get("raw_verifier_payload_stored") is not False:
            errors.append(
                f"verifier_transport_receipts[{member_id}].raw_verifier_payload_stored must be false"
            )
            ok = False
        if not isinstance(receipt.get("observed_latency_ms"), (int, float)):
            errors.append(
                f"verifier_transport_receipts[{member_id}].observed_latency_ms must be numeric"
            )
            ok = False
        expected_digest = sha256_text(
            canonical_json(self._member_recovery_verifier_transport_receipt_digest_payload(receipt))
        )
        if receipt.get("digest") != expected_digest:
            errors.append(f"verifier_transport_receipts[{member_id}].digest mismatch")
            ok = False
        return ok

    @staticmethod
    def _member_recovery_verifier_transport_receipt_digest_payload(
        receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        return {
            "receipt_id": receipt.get("receipt_id"),
            "collective_id": receipt.get("collective_id"),
            "member_id": receipt.get("member_id"),
            "profile_id": receipt.get("profile_id"),
            "identity_confirmation_digest": receipt.get("identity_confirmation_digest"),
            "self_report_witness_consistency_digest": receipt.get(
                "self_report_witness_consistency_digest"
            ),
            "member_recovery_binding_digest": receipt.get(
                "member_recovery_binding_digest"
            ),
            "dissolution_receipt_digest": receipt.get("dissolution_receipt_digest"),
            "verifier_network_receipt_id": receipt.get("verifier_network_receipt_id"),
            "verifier_ref": receipt.get("verifier_ref"),
            "jurisdiction": receipt.get("jurisdiction"),
            "network_profile_id": receipt.get("network_profile_id"),
            "transport_profile": receipt.get("transport_profile"),
            "transport_exchange_profile_id": receipt.get(
                "transport_exchange_profile_id"
            ),
            "transport_exchange_digest": receipt.get("transport_exchange_digest"),
            "challenge_digest": receipt.get("challenge_digest"),
            "request_payload_digest": receipt.get("request_payload_digest"),
            "response_payload_digest": receipt.get("response_payload_digest"),
            "receipt_status": receipt.get("receipt_status"),
            "raw_verifier_payload_stored": receipt.get("raw_verifier_payload_stored"),
        }

    @staticmethod
    def _collective_member_route_binding_digest(
        *,
        member_id: str,
        verifier_receipt_digest: str,
        authority_route_trace_digest: str,
        route_binding_ref: str,
        response_digest: str,
        remote_host_ref: str,
        remote_host_attestation_ref: str,
        authority_cluster_ref: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "member_id": member_id,
                    "verifier_transport_receipt_digest": verifier_receipt_digest,
                    "authority_route_trace_digest": authority_route_trace_digest,
                    "route_binding_ref": route_binding_ref,
                    "response_digest": response_digest,
                    "remote_host_ref": remote_host_ref,
                    "remote_host_attestation_ref": remote_host_attestation_ref,
                    "authority_cluster_ref": authority_cluster_ref,
                }
            )
        )

    @staticmethod
    def _collective_member_capture_binding_digest(
        *,
        collective_id: str,
        member_id: str,
        recovery_route_trace_binding_digest: str,
        member_route_binding_digest: str,
        packet_capture_digest: str,
        privileged_capture_digest: str,
        route_binding_ref: str,
        route_export_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "collective_id": collective_id,
                    "member_id": member_id,
                    "recovery_route_trace_binding_digest": (
                        recovery_route_trace_binding_digest
                    ),
                    "member_route_binding_digest": member_route_binding_digest,
                    "packet_capture_digest": packet_capture_digest,
                    "privileged_capture_digest": privileged_capture_digest,
                    "route_binding_ref": route_binding_ref,
                    "route_export_digest": route_export_digest,
                }
            )
        )

    def _build_collective_external_registry_ack_route_trace_bindings(
        self,
        *,
        collective_id: str,
        ack_quorum_receipts: Sequence[Mapping[str, Any]],
        authority_route_trace: Mapping[str, Any],
    ) -> List[Dict[str, Any]]:
        route_bindings = authority_route_trace.get("route_bindings")
        if not isinstance(route_bindings, list):
            raise ValueError("registry_ack_authority_route_trace.route_bindings must be a list")
        if len(route_bindings) < len(ack_quorum_receipts):
            raise ValueError(
                "registry_ack_authority_route_trace must cover every external registry ack"
            )

        used_indices: Set[int] = set()
        bound: List[Dict[str, Any]] = []
        for ack_receipt in ack_quorum_receipts:
            route_binding = self._select_registry_ack_route_binding(
                ack_receipt=ack_receipt,
                route_bindings=route_bindings,
                used_indices=used_indices,
            )
            socket_trace = route_binding.get("socket_trace")
            if not isinstance(socket_trace, Mapping):
                raise ValueError("ack route binding must carry socket_trace")
            os_observer = route_binding.get("os_observer_receipt")
            if not isinstance(os_observer, Mapping):
                raise ValueError("ack route binding must carry os_observer_receipt")
            if route_binding.get("mtls_status") != "authenticated":
                raise ValueError("ack route binding must be authenticated")

            ack_route_binding_digest = (
                self._collective_external_registry_ack_route_binding_digest(
                    collective_id=collective_id,
                    ack_receipt_digest=str(ack_receipt["ack_receipt_digest"]),
                    registry_authority_ref=str(
                        ack_receipt["registry_authority_ref"]
                    ),
                    registry_jurisdiction=str(
                        ack_receipt["registry_jurisdiction"]
                    ),
                    authority_route_trace_digest=str(authority_route_trace["digest"]),
                    route_binding_ref=str(route_binding["route_binding_ref"]),
                    remote_host_ref=str(route_binding["remote_host_ref"]),
                    remote_host_attestation_ref=str(
                        route_binding["remote_host_attestation_ref"]
                    ),
                    os_observer_host_binding_digest=str(
                        os_observer["host_binding_digest"]
                    ),
                    socket_response_digest=str(socket_trace["response_digest"]),
                )
            )
            bound.append(
                {
                    "ack_receipt_ref": ack_receipt["ack_receipt_ref"],
                    "ack_receipt_digest": ack_receipt["ack_receipt_digest"],
                    "registry_authority_ref": ack_receipt["registry_authority_ref"],
                    "registry_jurisdiction": ack_receipt["registry_jurisdiction"],
                    "authority_route_trace_ref": authority_route_trace["trace_ref"],
                    "authority_route_trace_digest": authority_route_trace["digest"],
                    "route_binding_ref": route_binding["route_binding_ref"],
                    "remote_host_ref": route_binding["remote_host_ref"],
                    "remote_host_attestation_ref": route_binding[
                        "remote_host_attestation_ref"
                    ],
                    "authority_cluster_ref": route_binding["authority_cluster_ref"],
                    "remote_jurisdiction": route_binding["remote_jurisdiction"],
                    "remote_network_zone": route_binding["remote_network_zone"],
                    "os_observer_receipt_id": os_observer["receipt_id"],
                    "os_observer_host_binding_digest": os_observer[
                        "host_binding_digest"
                    ],
                    "socket_response_digest": socket_trace["response_digest"],
                    "mtls_status": route_binding["mtls_status"],
                    "ack_route_binding_digest": ack_route_binding_digest,
                    "raw_ack_route_payload_stored": False,
                }
            )
        return bound

    def _build_collective_external_registry_ack_route_capture_bindings(
        self,
        *,
        collective_id: str,
        ack_route_trace_bindings: Sequence[Mapping[str, Any]],
        packet_capture_export: Mapping[str, Any],
        privileged_capture_acquisition: Mapping[str, Any],
        ack_route_trace_binding_digest: str,
    ) -> List[Dict[str, Any]]:
        route_exports = packet_capture_export.get("route_exports")
        if not isinstance(route_exports, list):
            raise ValueError("registry_ack_packet_capture_export.route_exports must be a list")
        acquisition_route_refs = privileged_capture_acquisition.get("route_binding_refs")
        if not isinstance(acquisition_route_refs, list):
            raise ValueError(
                "registry_ack_privileged_capture_acquisition.route_binding_refs must be a list"
            )
        route_exports_by_ref = {
            route_export["route_binding_ref"]: route_export
            for route_export in route_exports
            if isinstance(route_export, Mapping)
            and isinstance(route_export.get("route_binding_ref"), str)
        }
        bound: List[Dict[str, Any]] = []
        for route_binding in ack_route_trace_bindings:
            route_binding_ref = str(route_binding["route_binding_ref"])
            if route_binding_ref not in acquisition_route_refs:
                raise ValueError(
                    "registry_ack_privileged_capture_acquisition must cover every ack route"
                )
            route_export = route_exports_by_ref.get(route_binding_ref)
            if not isinstance(route_export, Mapping):
                raise ValueError(
                    f"registry_ack_packet_capture_export missing route export for {route_binding_ref}"
                )
            route_export_digest = sha256_text(canonical_json(route_export))
            binding_digest = (
                self._collective_external_registry_ack_route_capture_binding_digest(
                    collective_id=collective_id,
                    ack_receipt_digest=str(route_binding["ack_receipt_digest"]),
                    ack_route_binding_digest=str(
                        route_binding["ack_route_binding_digest"]
                    ),
                    ack_route_trace_binding_digest=ack_route_trace_binding_digest,
                    packet_capture_digest=str(packet_capture_export["digest"]),
                    privileged_capture_digest=str(
                        privileged_capture_acquisition["digest"]
                    ),
                    route_binding_ref=route_binding_ref,
                    route_export_digest=route_export_digest,
                )
            )
            bound.append(
                {
                    "ack_receipt_ref": route_binding["ack_receipt_ref"],
                    "ack_receipt_digest": route_binding["ack_receipt_digest"],
                    "registry_authority_ref": route_binding[
                        "registry_authority_ref"
                    ],
                    "registry_jurisdiction": route_binding[
                        "registry_jurisdiction"
                    ],
                    "ack_route_binding_digest": route_binding[
                        "ack_route_binding_digest"
                    ],
                    "route_binding_ref": route_binding_ref,
                    "packet_capture_route_export_digest": route_export_digest,
                    "outbound_tuple_digest": route_export["outbound_tuple_digest"],
                    "inbound_tuple_digest": route_export["inbound_tuple_digest"],
                    "outbound_payload_digest": route_export["outbound_payload_digest"],
                    "inbound_payload_digest": route_export["inbound_payload_digest"],
                    "readback_packet_count": route_export["readback_packet_count"],
                    "readback_verified": route_export["readback_verified"],
                    "os_native_readback_verified": route_export.get(
                        "os_native_readback_verified",
                        False,
                    ),
                    "privileged_capture_route_ref": route_binding_ref,
                    "ack_route_capture_binding_digest": binding_digest,
                    "raw_packet_body_stored": False,
                }
            )
        return bound

    @staticmethod
    def _select_registry_ack_route_binding(
        *,
        ack_receipt: Mapping[str, Any],
        route_bindings: Sequence[Any],
        used_indices: Set[int],
    ) -> Mapping[str, Any]:
        preferred_jurisdiction = str(ack_receipt.get("registry_jurisdiction"))
        for index, route_binding in enumerate(route_bindings):
            if index in used_indices or not isinstance(route_binding, Mapping):
                continue
            if route_binding.get("remote_jurisdiction") == preferred_jurisdiction:
                used_indices.add(index)
                return route_binding
        for index, route_binding in enumerate(route_bindings):
            if index in used_indices or not isinstance(route_binding, Mapping):
                continue
            used_indices.add(index)
            return route_binding
        raise ValueError("no unused route binding available for registry acknowledgement")

    @staticmethod
    def _collective_external_registry_ack_route_binding_digest(
        *,
        collective_id: str,
        ack_receipt_digest: str,
        registry_authority_ref: str,
        registry_jurisdiction: str,
        authority_route_trace_digest: str,
        route_binding_ref: str,
        remote_host_ref: str,
        remote_host_attestation_ref: str,
        os_observer_host_binding_digest: str,
        socket_response_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_TRACE_PROFILE_ID
                    ),
                    "collective_id": collective_id,
                    "ack_receipt_digest": ack_receipt_digest,
                    "registry_authority_ref": registry_authority_ref,
                    "registry_jurisdiction": registry_jurisdiction,
                    "authority_route_trace_digest": authority_route_trace_digest,
                    "route_binding_ref": route_binding_ref,
                    "remote_host_ref": remote_host_ref,
                    "remote_host_attestation_ref": remote_host_attestation_ref,
                    "os_observer_host_binding_digest": (
                        os_observer_host_binding_digest
                    ),
                    "socket_response_digest": socket_response_digest,
                }
            )
        )

    @staticmethod
    def _collective_external_registry_ack_route_capture_binding_digest(
        *,
        collective_id: str,
        ack_receipt_digest: str,
        ack_route_binding_digest: str,
        ack_route_trace_binding_digest: str,
        packet_capture_digest: str,
        privileged_capture_digest: str,
        route_binding_ref: str,
        route_export_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_CAPTURE_EXPORT_PROFILE_ID
                    ),
                    "collective_id": collective_id,
                    "ack_receipt_digest": ack_receipt_digest,
                    "ack_route_binding_digest": ack_route_binding_digest,
                    "ack_route_trace_binding_digest": ack_route_trace_binding_digest,
                    "packet_capture_digest": packet_capture_digest,
                    "privileged_capture_digest": privileged_capture_digest,
                    "route_binding_ref": route_binding_ref,
                    "route_export_digest": route_export_digest,
                }
            )
        )

    @staticmethod
    def _collective_external_registry_ack_route_capture_export_digest(
        *,
        collective_id: str,
        ack_route_trace_binding_digest: str,
        packet_capture_digest: str,
        privileged_capture_digest: str,
        ack_route_capture_binding_digest_set_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_CAPTURE_EXPORT_PROFILE_ID
                    ),
                    "collective_id": collective_id,
                    "ack_route_trace_binding_digest": ack_route_trace_binding_digest,
                    "packet_capture_digest": packet_capture_digest,
                    "privileged_capture_digest": privileged_capture_digest,
                    "ack_route_capture_binding_digest_set_digest": (
                        ack_route_capture_binding_digest_set_digest
                    ),
                }
            )
        )

    @staticmethod
    def _collective_external_registry_ack_route_trace_digest(
        *,
        collective_id: str,
        ack_quorum_digest: str,
        authority_route_trace_digest: str,
        ack_route_trace_binding_digest_set_digest: str,
        ack_quorum_authority_refs: Sequence[str],
        route_binding_refs: Sequence[str],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        COLLECTIVE_EXTERNAL_REGISTRY_ACK_ROUTE_TRACE_PROFILE_ID
                    ),
                    "collective_id": collective_id,
                    "ack_quorum_digest": ack_quorum_digest,
                    "authority_route_trace_digest": authority_route_trace_digest,
                    "ack_route_trace_binding_digest_set_digest": (
                        ack_route_trace_binding_digest_set_digest
                    ),
                    "ack_quorum_authority_refs": list(ack_quorum_authority_refs),
                    "route_binding_refs": list(route_binding_refs),
                }
            )
        )

    @staticmethod
    def _collective_external_registry_ack_endpoint_probe_digest_payload(
        receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        return {
            "probe_id": receipt.get("probe_id"),
            "profile_id": receipt.get("profile_id"),
            "transport_profile": receipt.get("transport_profile"),
            "registry_ack_endpoint_ref": receipt.get("registry_ack_endpoint_ref"),
            "ack_receipt_ref": receipt.get("ack_receipt_ref"),
            "ack_receipt_digest": receipt.get("ack_receipt_digest"),
            "registry_authority_ref": receipt.get("registry_authority_ref"),
            "registry_jurisdiction": receipt.get("registry_jurisdiction"),
            "registry_digest": receipt.get("registry_digest"),
            "submission_receipt_digest": receipt.get("submission_receipt_digest"),
            "registry_entry_digest": receipt.get("registry_entry_digest"),
            "ack_quorum_digest": receipt.get("ack_quorum_digest"),
            "ack_route_trace_binding_digest": receipt.get(
                "ack_route_trace_binding_digest"
            ),
            "ack_route_capture_binding_digest": receipt.get(
                "ack_route_capture_binding_digest"
            ),
            "network_response_digest": receipt.get("network_response_digest"),
            "network_probe_bound": receipt.get("network_probe_bound"),
            "raw_ack_payload_stored": receipt.get("raw_ack_payload_stored"),
            "raw_endpoint_payload_stored": receipt.get("raw_endpoint_payload_stored"),
        }

    @staticmethod
    def _collective_external_registry_sync_digest_payload(
        receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        return {
            "profile_id": COLLECTIVE_EXTERNAL_REGISTRY_SYNC_PROFILE_ID,
            "collective_id": receipt.get("collective_id"),
            "recovery_capture_export_binding_digest": receipt.get(
                "recovery_capture_export_binding_digest"
            ),
            "registry_entry_digest": receipt.get("registry_entry_digest"),
            "ack_receipt_digest": receipt.get("ack_receipt_digest"),
            "ack_quorum_digest": receipt.get("ack_quorum_digest"),
            "ack_route_trace_binding_digest": receipt.get(
                "ack_route_trace_binding_digest"
            ),
            "ack_route_capture_binding_digest": receipt.get(
                "ack_route_capture_binding_digest"
            ),
            "ack_live_endpoint_probe_set_digest": receipt.get(
                "ack_live_endpoint_probe_set_digest"
            ),
            "registry_digest_set_digest": receipt.get("registry_digest_set_digest"),
        }

    @staticmethod
    def _external_registry_digest(
        *,
        registry_ref: str,
        jurisdiction: str,
        collective_id: str,
        dissolution_receipt_digest: str,
        recovery_capture_export_binding_digest: str,
        registry_kind: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "registry_ref": registry_ref,
                    "jurisdiction": jurisdiction,
                    "collective_id": collective_id,
                    "dissolution_receipt_digest": dissolution_receipt_digest,
                    "recovery_capture_export_binding_digest": (
                        recovery_capture_export_binding_digest
                    ),
                    "registry_kind": registry_kind,
                    "profile_id": COLLECTIVE_EXTERNAL_REGISTRY_SYNC_PROFILE_ID,
                }
            )
        )

    @staticmethod
    def _collective_external_registry_entry_digest(
        *,
        collective_id: str,
        dissolution_receipt_digest: str,
        recovery_capture_export_binding_digest: str,
        legal_registry_digest: str,
        governance_registry_digest: str,
        member_capture_binding_digest_set_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": COLLECTIVE_EXTERNAL_REGISTRY_ENTRY_DIGEST_PROFILE_ID,
                    "collective_id": collective_id,
                    "dissolution_receipt_digest": dissolution_receipt_digest,
                    "recovery_capture_export_binding_digest": (
                        recovery_capture_export_binding_digest
                    ),
                    "legal_registry_digest": legal_registry_digest,
                    "governance_registry_digest": governance_registry_digest,
                    "member_capture_binding_digest_set_digest": (
                        member_capture_binding_digest_set_digest
                    ),
                }
            )
        )

    @staticmethod
    def _collective_external_registry_ack_digest(
        *,
        submission_receipt_ref: str,
        submission_receipt_digest: str,
        registry_authority_digest: str,
        registry_authority_ref: str,
        registry_jurisdiction: str,
        registry_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": COLLECTIVE_EXTERNAL_REGISTRY_ACK_PROFILE_ID,
                    "submission_receipt_ref": submission_receipt_ref,
                    "submission_receipt_digest": submission_receipt_digest,
                    "ack_status": "accepted",
                    "registry_authority_digest": registry_authority_digest,
                    "registry_authority_ref": registry_authority_ref,
                    "registry_jurisdiction": registry_jurisdiction,
                    "registry_digest": registry_digest,
                }
            )
        )

    @staticmethod
    def _collective_external_registry_ack_quorum_digest(
        *,
        collective_id: str,
        submission_receipt_digest: str,
        ack_quorum_digest_set_digest: str,
        ack_quorum_authority_refs: Sequence[str],
        ack_quorum_jurisdictions: Sequence[str],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": COLLECTIVE_EXTERNAL_REGISTRY_ACK_QUORUM_PROFILE_ID,
                    "collective_id": collective_id,
                    "submission_receipt_digest": submission_receipt_digest,
                    "ack_quorum_digest_set_digest": ack_quorum_digest_set_digest,
                    "ack_quorum_authority_refs": list(ack_quorum_authority_refs),
                    "ack_quorum_jurisdictions": list(ack_quorum_jurisdictions),
                }
            )
        )

    @staticmethod
    def _transport_receipt_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            key: deepcopy(value)
            for key, value in receipt.items()
            if key not in {"kind", "schema_version", "digest"}
        }

    def _validate_packet_capture_export(
        self,
        packet_capture_export: Mapping[str, Any],
        *,
        recovery_route_trace_binding: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(packet_capture_export, Mapping):
            raise ValueError("packet_capture_export must be a mapping")
        if packet_capture_export.get("kind") != "distributed_transport_packet_capture_export":
            errors.append("packet_capture_export.kind mismatch")
        if packet_capture_export.get("schema_version") != "1.0.0":
            errors.append("packet_capture_export.schema_version mismatch")
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
            self._check_non_empty_string(
                packet_capture_export.get(field_name),
                field_name,
                errors,
            )
        for field_name in (
            "trace_digest",
            "authority_plane_digest",
            "envelope_digest",
            "artifact_digest",
            "readback_digest",
            "digest",
        ):
            if not self._looks_like_digest(packet_capture_export.get(field_name)):
                errors.append(f"{field_name} must be sha256 hex")
        if packet_capture_export.get("capture_profile") != COLLECTIVE_PACKET_CAPTURE_PROFILE:
            errors.append("packet_capture_export.capture_profile mismatch")
        if packet_capture_export.get("artifact_format") != COLLECTIVE_PACKET_CAPTURE_FORMAT:
            errors.append("packet_capture_export.artifact_format mismatch")
        if packet_capture_export.get("export_status") != "verified":
            errors.append("packet_capture_export.export_status must be verified")

        route_exports = packet_capture_export.get("route_exports")
        if not isinstance(route_exports, list) or not route_exports:
            errors.append("packet_capture_export.route_exports must be a non-empty list")
            route_exports = []
        route_binding_refs: List[str] = []
        route_export_errors = 0
        for index, route_export in enumerate(route_exports):
            if not isinstance(route_export, Mapping):
                errors.append(f"route_exports[{index}] must be an object")
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
                    if not self._looks_like_digest(value):
                        errors.append(f"route_exports[{index}].{field_name} must be sha256 hex")
                        route_export_errors += 1
                else:
                    self._check_non_empty_string(
                        value,
                        f"route_exports[{index}].{field_name}",
                        errors,
                    )
            route_binding_ref = route_export.get("route_binding_ref")
            if isinstance(route_binding_ref, str):
                route_binding_refs.append(route_binding_ref)
            if route_export.get("readback_verified") is not True:
                errors.append(f"route_exports[{index}].readback_verified must be true")
                route_export_errors += 1
            if route_export.get("readback_packet_count") != 2:
                errors.append(
                    f"route_exports[{index}].readback_packet_count must equal 2"
                )
                route_export_errors += 1
            if (
                packet_capture_export.get("os_native_readback_available") is True
                and route_export.get("os_native_readback_verified") is not True
            ):
                errors.append(
                    f"route_exports[{index}].os_native_readback_verified must be true"
                )
                route_export_errors += 1

        route_count = packet_capture_export.get("route_count")
        packet_count = packet_capture_export.get("packet_count")
        if not isinstance(route_count, int) or route_count != len(route_exports):
            errors.append("packet_capture_export.route_count must match route_exports")
            route_count = len(route_exports)
        if not isinstance(packet_count, int) or packet_count != route_count * 2:
            errors.append(
                "packet_capture_export.packet_count must equal two packets per route"
            )
        if (
            packet_capture_export.get("os_native_readback_available") is True
            and packet_capture_export.get("os_native_readback_ok") is not True
        ):
            errors.append("packet_capture_export.os_native_readback_ok must be true")
        if recovery_route_trace_binding is not None:
            expected_route_refs = list(
                recovery_route_trace_binding.get("route_binding_refs", [])
            )
            if packet_capture_export.get("trace_ref") != recovery_route_trace_binding.get(
                "authority_route_trace_ref"
            ):
                errors.append("packet_capture_export.trace_ref must match route trace")
            if packet_capture_export.get("trace_digest") != recovery_route_trace_binding.get(
                "authority_route_trace_digest"
            ):
                errors.append("packet_capture_export.trace_digest must match route trace")
            if route_binding_refs != expected_route_refs:
                errors.append("packet_capture_export route refs must match route trace")
            if route_count != recovery_route_trace_binding.get("route_count"):
                errors.append("packet_capture_export.route_count must match route trace")

        expected_digest = sha256_text(
            canonical_json(self._transport_receipt_digest_payload(packet_capture_export))
        )
        digest_bound = packet_capture_export.get("digest") == expected_digest
        if not digest_bound:
            errors.append("packet_capture_export.digest must bind payload")
        return {
            "ok": not errors,
            "errors": errors,
            "digest_bound": digest_bound,
            "route_binding_refs": route_binding_refs,
            "packet_capture_complete": route_export_errors == 0 and not errors,
        }

    def _validate_privileged_capture_acquisition(
        self,
        privileged_capture_acquisition: Mapping[str, Any],
        *,
        recovery_route_trace_binding: Mapping[str, Any] | None = None,
        packet_capture_export: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(privileged_capture_acquisition, Mapping):
            raise ValueError("privileged_capture_acquisition must be a mapping")
        if (
            privileged_capture_acquisition.get("kind")
            != "distributed_transport_privileged_capture_acquisition"
        ):
            errors.append("privileged_capture_acquisition.kind mismatch")
        if privileged_capture_acquisition.get("schema_version") != "1.0.0":
            errors.append("privileged_capture_acquisition.schema_version mismatch")
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
            if not self._looks_like_digest(privileged_capture_acquisition.get(field_name)):
                errors.append(f"{field_name} must be sha256 hex")
        if (
            privileged_capture_acquisition.get("acquisition_profile")
            != COLLECTIVE_PRIVILEGED_CAPTURE_PROFILE
        ):
            errors.append("privileged_capture_acquisition.acquisition_profile mismatch")
        if (
            privileged_capture_acquisition.get("privilege_mode")
            != COLLECTIVE_PRIVILEGED_CAPTURE_MODE
        ):
            errors.append("privileged_capture_acquisition.privilege_mode mismatch")
        if privileged_capture_acquisition.get("grant_status") != "granted":
            errors.append("privileged_capture_acquisition.grant_status must be granted")
        local_ips = privileged_capture_acquisition.get("local_ips")
        if not isinstance(local_ips, list) or not local_ips:
            errors.append("privileged_capture_acquisition.local_ips must be non-empty")
        route_binding_refs = privileged_capture_acquisition.get("route_binding_refs")
        if not isinstance(route_binding_refs, list) or not route_binding_refs:
            errors.append(
                "privileged_capture_acquisition.route_binding_refs must be non-empty"
            )
            route_binding_refs = []
        capture_command = privileged_capture_acquisition.get("capture_command")
        if not isinstance(capture_command, list) or not capture_command:
            errors.append("privileged_capture_acquisition.capture_command must be non-empty")
            capture_command = []
        else:
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
        if recovery_route_trace_binding is not None:
            if privileged_capture_acquisition.get(
                "trace_ref"
            ) != recovery_route_trace_binding.get("authority_route_trace_ref"):
                errors.append("privileged capture trace_ref must match route trace")
            if privileged_capture_acquisition.get(
                "trace_digest"
            ) != recovery_route_trace_binding.get("authority_route_trace_digest"):
                errors.append("privileged capture trace_digest must match route trace")
            if sorted(route_binding_refs) != sorted(
                recovery_route_trace_binding.get("route_binding_refs", [])
            ):
                errors.append("privileged capture route refs must match route trace")
        if packet_capture_export is not None:
            if privileged_capture_acquisition.get(
                "capture_ref"
            ) != packet_capture_export.get("capture_ref"):
                errors.append("privileged capture capture_ref must match packet capture")
            if privileged_capture_acquisition.get(
                "capture_digest"
            ) != packet_capture_export.get("digest"):
                errors.append(
                    "privileged capture capture_digest must match packet capture"
                )

        expected_digest = sha256_text(
            canonical_json(
                self._transport_receipt_digest_payload(privileged_capture_acquisition)
            )
        )
        digest_bound = privileged_capture_acquisition.get("digest") == expected_digest
        if not digest_bound:
            errors.append("privileged_capture_acquisition.digest must bind payload")
        return {
            "ok": not errors,
            "errors": errors,
            "digest_bound": digest_bound,
        }

    def _validate_authority_route_trace_contract(
        self,
        authority_route_trace: Mapping[str, Any],
    ) -> None:
        if not isinstance(authority_route_trace, Mapping):
            raise ValueError("authority_route_trace must be a mapping")
        expected_fields = {
            "kind": "distributed_transport_authority_route_trace",
            "schema_version": "1.0.0",
            "trace_status": "authenticated",
            "trace_profile": "non-loopback-mtls-authority-route-v1",
            "socket_trace_profile": "mtls-socket-trace-v1",
            "os_observer_profile": "os-native-tcp-observer-v1",
            "cross_host_binding_profile": "attested-cross-host-authority-binding-v1",
            "route_target_discovery_profile": "bounded-authority-route-target-discovery-v1",
        }
        for field_name, expected in expected_fields.items():
            if authority_route_trace.get(field_name) != expected:
                raise ValueError(f"authority_route_trace.{field_name} must equal {expected}")
        for flag_name in (
            "non_loopback_verified",
            "authority_plane_bound",
            "response_digest_bound",
            "socket_trace_complete",
            "os_observer_complete",
            "route_target_discovery_bound",
            "cross_host_verified",
        ):
            if authority_route_trace.get(flag_name) is not True:
                raise ValueError(f"authority_route_trace.{flag_name} must be true")
        if not self._looks_like_digest(authority_route_trace.get("digest")):
            raise ValueError("authority_route_trace.digest must be sha256 hex")
        if not self._looks_like_digest(authority_route_trace.get("authority_plane_digest")):
            raise ValueError("authority_route_trace.authority_plane_digest must be sha256 hex")
        if not self._looks_like_digest(
            authority_route_trace.get("route_target_discovery_digest")
        ):
            raise ValueError(
                "authority_route_trace.route_target_discovery_digest must be sha256 hex"
            )
        route_bindings = authority_route_trace.get("route_bindings")
        if not isinstance(route_bindings, list) or len(route_bindings) < 2:
            raise ValueError("authority_route_trace.route_bindings must contain at least 2 routes")
        if authority_route_trace.get("route_count") != len(route_bindings):
            raise ValueError("authority_route_trace.route_count must match route_bindings")
        if authority_route_trace.get("mtls_authenticated_count") < len(route_bindings):
            raise ValueError("authority_route_trace must authenticate every route binding")
        if authority_route_trace.get("distinct_remote_host_count") < 2:
            raise ValueError("authority_route_trace must bind at least 2 remote hosts")
        for index, route in enumerate(route_bindings):
            if not isinstance(route, Mapping):
                raise ValueError(f"authority_route_trace.route_bindings[{index}] must be an object")
            if route.get("mtls_status") != "authenticated":
                raise ValueError(
                    f"authority_route_trace.route_bindings[{index}].mtls_status must be authenticated"
                )
            socket_trace = route.get("socket_trace")
            if not isinstance(socket_trace, Mapping):
                raise ValueError(
                    f"authority_route_trace.route_bindings[{index}].socket_trace must be an object"
                )
            if socket_trace.get("non_loopback") is not True:
                raise ValueError(
                    f"authority_route_trace.route_bindings[{index}].socket_trace.non_loopback must be true"
                )
            if not self._looks_like_digest(socket_trace.get("response_digest")):
                raise ValueError(
                    f"authority_route_trace.route_bindings[{index}].socket_trace.response_digest must be sha256 hex"
                )
            os_observer = route.get("os_observer_receipt")
            if not isinstance(os_observer, Mapping):
                raise ValueError(
                    f"authority_route_trace.route_bindings[{index}].os_observer_receipt must be an object"
                )
            if os_observer.get("receipt_status") != "observed":
                raise ValueError(
                    f"authority_route_trace.route_bindings[{index}].os_observer_receipt.receipt_status must be observed"
                )
            if not self._looks_like_digest(os_observer.get("host_binding_digest")):
                raise ValueError(
                    f"authority_route_trace.route_bindings[{index}].os_observer_receipt.host_binding_digest must be sha256 hex"
                )

    def _require_record(self, collective_id: str) -> Dict[str, Any]:
        collective = self._normalize_non_empty_string(collective_id, "collective_id")
        try:
            return self.records[collective]
        except KeyError as exc:
            raise KeyError(f"unknown collective: {collective}") from exc

    def _require_merge_session(self, merge_session_id: str) -> Dict[str, Any]:
        merge_id = self._normalize_non_empty_string(merge_session_id, "merge_session_id")
        try:
            return self.merge_sessions[merge_id]
        except KeyError as exc:
            raise KeyError(f"unknown merge session: {merge_id}") from exc

    def _normalize_member_ids(self, member_ids: Sequence[str]) -> List[str]:
        if not isinstance(member_ids, Sequence) or isinstance(member_ids, (str, bytes)):
            raise ValueError("member_ids must be a sequence of identity ids")
        normalized = [
            self._normalize_non_empty_string(member_id, f"member_ids[{index}]")
            for index, member_id in enumerate(member_ids)
        ]
        deduped = _dedupe_preserve_order(normalized)
        if len(deduped) < COLLECTIVE_MIN_MEMBERS or len(deduped) > COLLECTIVE_MAX_MEMBERS:
            raise ValueError(
                f"collective must contain between {COLLECTIVE_MIN_MEMBERS} and {COLLECTIVE_MAX_MEMBERS} unique members"
            )
        return deduped

    @staticmethod
    def _normalize_non_empty_string(value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _normalize_duration(value: Any, field_name: str) -> float:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{field_name} must be a positive number")
        normalized = float(value)
        if normalized <= 0:
            raise ValueError(f"{field_name} must be > 0")
        return normalized

    @staticmethod
    def _looks_like_digest(value: Any) -> bool:
        return isinstance(value, str) and len(value) == 64 and all(
            char in "0123456789abcdef" for char in value
        )

    @classmethod
    def _normalize_digest(cls, value: Any, field_name: str) -> str:
        if not cls._looks_like_digest(value):
            raise ValueError(f"{field_name} must be a sha256 hex digest")
        return str(value)

    @staticmethod
    def _normalize_wms_mode(value: Any, field_name: str) -> str:
        if value not in COLLECTIVE_ALLOWED_WMS_MODES:
            raise ValueError(f"{field_name} must be one of {sorted(COLLECTIVE_ALLOWED_WMS_MODES)}")
        return str(value)

    def _normalize_confirmations(
        self,
        confirmations: Mapping[str, bool],
        required_member_ids: Sequence[str],
    ) -> Dict[str, bool]:
        if not isinstance(confirmations, Mapping):
            raise ValueError("identity confirmations must be a mapping")
        normalized: Dict[str, bool] = {}
        for member_id in required_member_ids:
            if member_id not in confirmations:
                raise ValueError(f"missing identity confirmation for {member_id}")
            normalized[member_id] = bool(confirmations[member_id])
        return normalized

    @staticmethod
    def _check_non_empty_string(value: Any, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty string")

    @staticmethod
    def _oversight_bound(oversight: Any) -> bool:
        return isinstance(oversight, Mapping) and all(
            oversight.get(field) is True
            for field in ("council_witnessed", "federation_attested", "guardian_observed")
        )

    def _require_oversight(
        self,
        *,
        council_witnessed: bool,
        federation_attested: bool,
        guardian_observed: bool,
    ) -> None:
        if not council_witnessed:
            raise PermissionError("collective operations require council witness")
        if not federation_attested:
            raise PermissionError("collective operations require federation attestation")
        if not guardian_observed:
            raise PermissionError("collective operations require guardian observation")
