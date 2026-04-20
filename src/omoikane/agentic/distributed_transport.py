"""Distributed council transport attestation reference model."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
import time
from typing import Any, Dict, List, Mapping
import urllib.request

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

FEDERATION_GUARDIAN_ID = "guardian://neutral-federation"
HERITAGE_PARTICIPANTS = (
    "heritage://culture-a",
    "heritage://culture-b",
    "heritage://legal-advisor",
    "heritage://ethics-committee",
)
ROLE_TRUST_SCORES = {
    "self-liaison": 0.74,
    "guardian": 0.91,
    "cultural-representative": 0.73,
    "legal-advisor": 0.78,
    "ethics-committee": 0.88,
}
FEDERATION_ROOTS = (
    "root://federation/pki-a",
    "root://federation/pki-b",
)
HERITAGE_ROOTS = (
    "root://heritage/pki-a",
    "root://heritage/pki-b",
    "root://heritage/pki-c",
)
RELAY_TELEMETRY_PROFILE = "bounded-relay-observability-v1"
LIVE_ROOT_DIRECTORY_TRANSPORT_PROFILE = "live-http-json-rootdir-v1"
LIVE_KEY_SERVER_TRANSPORT_PROFILE = "live-http-json-keyserver-v1"
AUTHORITY_PLANE_PROFILE = "bounded-key-server-fleet-v1"
RELAY_TRANSPORT_LAYER_BY_PROFILE = {
    "federation-mtls-quorum-v1": "mtls",
    "heritage-attested-review-v1": "attested-bridge",
}


@dataclass
class DistributedParticipantAttestation:
    """One remote participant attestation bound to a transport envelope."""

    attestation_id: str
    participant_id: str
    council_tier: str
    role: str
    credential_ref: str
    proof_ref: str
    transport_key_ref: str
    trust_root_ref: str
    key_epoch: int
    trust_score: float
    issued_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "distributed_participant_attestation",
            "schema_version": "1.0.0",
            "attestation_id": self.attestation_id,
            "participant_id": self.participant_id,
            "council_tier": self.council_tier,
            "role": self.role,
            "credential_ref": self.credential_ref,
            "proof_ref": self.proof_ref,
            "transport_key_ref": self.transport_key_ref,
            "trust_root_ref": self.trust_root_ref,
            "key_epoch": self.key_epoch,
            "trust_score": self.trust_score,
            "issued_at": self.issued_at,
        }


@dataclass
class DistributedTransportEnvelope:
    """Bounded remote handoff bundle for a distributed council review."""

    envelope_id: str
    topology_ref: str
    proposal_ref: str
    council_tier: str
    transport_profile: str
    recipient_endpoint: str
    payload_ref: str
    payload_digest: str
    route_nonce: str
    freshness_window_s: int
    quorum: int
    required_roles: List[str]
    key_epoch: int
    accepted_key_epochs: List[int]
    trust_root_refs: List[str]
    trust_root_quorum: int
    max_hops: int
    previous_envelope_ref: str | None
    channel_binding_ref: str
    participant_attestations: List[DistributedParticipantAttestation]
    attestation_digest: str
    issued_at: str
    envelope_digest: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "distributed_transport_envelope",
            "schema_version": "1.0.0",
            "envelope_id": self.envelope_id,
            "topology_ref": self.topology_ref,
            "proposal_ref": self.proposal_ref,
            "council_tier": self.council_tier,
            "transport_profile": self.transport_profile,
            "recipient_endpoint": self.recipient_endpoint,
            "payload_ref": self.payload_ref,
            "payload_digest": self.payload_digest,
            "route_nonce": self.route_nonce,
            "freshness_window_s": self.freshness_window_s,
            "quorum": self.quorum,
            "required_roles": list(self.required_roles),
            "key_epoch": self.key_epoch,
            "accepted_key_epochs": list(self.accepted_key_epochs),
            "trust_root_refs": list(self.trust_root_refs),
            "trust_root_quorum": self.trust_root_quorum,
            "max_hops": self.max_hops,
            "previous_envelope_ref": self.previous_envelope_ref,
            "channel_binding_ref": self.channel_binding_ref,
            "participant_attestations": [
                attestation.to_dict() for attestation in self.participant_attestations
            ],
            "attestation_digest": self.attestation_digest,
            "issued_at": self.issued_at,
            "envelope_digest": self.envelope_digest,
        }


@dataclass
class DistributedTransportReceipt:
    """Receipt recorded after one remote distributed review attempt."""

    receipt_id: str
    envelope_ref: str
    envelope_digest: str
    council_tier: str
    transport_profile: str
    result_ref: str
    result_digest: str
    route_nonce: str
    key_epoch: int
    verified_root_refs: List[str]
    hop_nonce_chain: List[str]
    receipt_status: str
    authenticity_checks: Dict[str, Any]
    participant_bindings: List[Dict[str, Any]]
    recorded_at: str
    digest: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "distributed_transport_receipt",
            "schema_version": "1.0.0",
            "receipt_id": self.receipt_id,
            "envelope_ref": self.envelope_ref,
            "envelope_digest": self.envelope_digest,
            "council_tier": self.council_tier,
            "transport_profile": self.transport_profile,
            "result_ref": self.result_ref,
            "result_digest": self.result_digest,
            "route_nonce": self.route_nonce,
            "key_epoch": self.key_epoch,
            "verified_root_refs": list(self.verified_root_refs),
            "hop_nonce_chain": list(self.hop_nonce_chain),
            "receipt_status": self.receipt_status,
            "authenticity_checks": dict(self.authenticity_checks),
            "participant_bindings": [dict(binding) for binding in self.participant_bindings],
            "recorded_at": self.recorded_at,
            "digest": self.digest,
        }


@dataclass
class DistributedRelayHopTelemetry:
    """One observed relay hop bound to a distributed transport receipt."""

    hop_index: int
    relay_id: str
    relay_endpoint: str
    jurisdiction: str
    network_zone: str
    transport_layer: str
    hop_nonce: str
    observed_latency_ms: float
    root_refs_seen: List[str]
    route_binding_ref: str
    attested_participant_count: int
    delivery_status: str
    observed_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hop_index": self.hop_index,
            "relay_id": self.relay_id,
            "relay_endpoint": self.relay_endpoint,
            "jurisdiction": self.jurisdiction,
            "network_zone": self.network_zone,
            "transport_layer": self.transport_layer,
            "hop_nonce": self.hop_nonce,
            "observed_latency_ms": self.observed_latency_ms,
            "root_refs_seen": list(self.root_refs_seen),
            "route_binding_ref": self.route_binding_ref,
            "attested_participant_count": self.attested_participant_count,
            "delivery_status": self.delivery_status,
            "observed_at": self.observed_at,
        }


@dataclass
class DistributedTransportRelayTelemetry:
    """Machine-checkable multi-hop relay telemetry for one distributed receipt."""

    telemetry_id: str
    envelope_ref: str
    envelope_digest: str
    receipt_ref: str
    receipt_digest: str
    council_tier: str
    transport_profile: str
    path_profile: str
    route_nonce: str
    hop_count: int
    max_hops: int
    hop_chain_digest: str
    relay_hops: List[DistributedRelayHopTelemetry]
    total_latency_ms: float
    anti_replay_status: str
    replay_guard_status: str
    root_quorum_met: bool
    end_to_end_status: str
    recorded_at: str
    digest: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "distributed_transport_relay_telemetry",
            "schema_version": "1.0.0",
            "telemetry_id": self.telemetry_id,
            "envelope_ref": self.envelope_ref,
            "envelope_digest": self.envelope_digest,
            "receipt_ref": self.receipt_ref,
            "receipt_digest": self.receipt_digest,
            "council_tier": self.council_tier,
            "transport_profile": self.transport_profile,
            "path_profile": self.path_profile,
            "route_nonce": self.route_nonce,
            "hop_count": self.hop_count,
            "max_hops": self.max_hops,
            "hop_chain_digest": self.hop_chain_digest,
            "relay_hops": [hop.to_dict() for hop in self.relay_hops],
            "total_latency_ms": self.total_latency_ms,
            "anti_replay_status": self.anti_replay_status,
            "replay_guard_status": self.replay_guard_status,
            "root_quorum_met": self.root_quorum_met,
            "end_to_end_status": self.end_to_end_status,
            "recorded_at": self.recorded_at,
            "digest": self.digest,
        }


@dataclass
class DistributedTransportRootConnectivityReceipt:
    """Connectivity receipt for one live remote root-directory probe."""

    receipt_id: str
    directory_ref: str
    directory_endpoint: str
    transport_profile: str
    recorded_at: str
    request_timeout_ms: int
    observed_latency_ms: float
    http_status: int
    response_digest: str
    receipt_status: str
    matched_root_count: int
    quorum_satisfied: bool
    trusted_root_refs: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "distributed_transport_root_connectivity_receipt",
            "schema_version": "1.0.0",
            "receipt_id": self.receipt_id,
            "directory_ref": self.directory_ref,
            "directory_endpoint": self.directory_endpoint,
            "transport_profile": self.transport_profile,
            "recorded_at": self.recorded_at,
            "request_timeout_ms": self.request_timeout_ms,
            "observed_latency_ms": self.observed_latency_ms,
            "http_status": self.http_status,
            "response_digest": self.response_digest,
            "receipt_status": self.receipt_status,
            "matched_root_count": self.matched_root_count,
            "quorum_satisfied": self.quorum_satisfied,
            "trusted_root_refs": list(self.trusted_root_refs),
        }


@dataclass
class DistributedTransportRootDirectory:
    """Normalized live root-directory report bound to one transport envelope."""

    directory_ref: str
    checked_at: str
    council_tier: str
    transport_profile: str
    key_epoch: int
    active_root_ref: str
    accepted_roots: List[Dict[str, Any]]
    quorum_requirement: int
    proof_digest: str
    trusted_root_refs: List[str]
    connectivity_receipt: DistributedTransportRootConnectivityReceipt

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "distributed_transport_root_directory",
            "schema_version": "1.0.0",
            "directory_ref": self.directory_ref,
            "checked_at": self.checked_at,
            "council_tier": self.council_tier,
            "transport_profile": self.transport_profile,
            "key_epoch": self.key_epoch,
            "active_root_ref": self.active_root_ref,
            "accepted_roots": [dict(root) for root in self.accepted_roots],
            "quorum_requirement": self.quorum_requirement,
            "proof_digest": self.proof_digest,
            "trusted_root_refs": list(self.trusted_root_refs),
            "connectivity_receipt": self.connectivity_receipt.to_dict(),
        }


@dataclass
class DistributedTransportAuthorityPlane:
    """Bounded authority-plane snapshot for external key-server fleets."""

    authority_plane_ref: str
    checked_at: str
    council_tier: str
    transport_profile: str
    authority_profile: str
    key_epoch: int
    directory_ref: str
    directory_digest: str
    quorum_requirement: int
    reachable_server_count: int
    matched_root_count: int
    trusted_root_refs: List[str]
    key_servers: List[Dict[str, Any]]
    proof_digest: str
    digest: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "distributed_transport_authority_plane",
            "schema_version": "1.0.0",
            "authority_plane_ref": self.authority_plane_ref,
            "checked_at": self.checked_at,
            "council_tier": self.council_tier,
            "transport_profile": self.transport_profile,
            "authority_profile": self.authority_profile,
            "key_epoch": self.key_epoch,
            "directory_ref": self.directory_ref,
            "directory_digest": self.directory_digest,
            "quorum_requirement": self.quorum_requirement,
            "reachable_server_count": self.reachable_server_count,
            "matched_root_count": self.matched_root_count,
            "trusted_root_refs": list(self.trusted_root_refs),
            "key_servers": [dict(server) for server in self.key_servers],
            "proof_digest": self.proof_digest,
            "digest": self.digest,
        }


class DistributedTransportService:
    """Issue transport-attested remote handoff bundles and verify receipts."""

    def __init__(self) -> None:
        self._consumed_route_nonces: set[str] = set()
        self._consumed_hop_chain_digests: set[str] = set()

    def issue_federation_handoff(
        self,
        *,
        topology_ref: str,
        proposal_ref: str,
        payload_ref: str,
        payload_digest: str,
        participant_identity_ids: List[str],
    ) -> DistributedTransportEnvelope:
        participants = sorted(set(participant_identity_ids))
        if len(participants) < 2:
            raise ValueError("federation handoff requires at least 2 identity participants")
        participants.append(FEDERATION_GUARDIAN_ID)
        return self._build_envelope(
            topology_ref=topology_ref,
            proposal_ref=proposal_ref,
            council_tier="federation",
            transport_profile="federation-mtls-quorum-v1",
            recipient_endpoint="federation://shared-reality-review",
            payload_ref=payload_ref,
            payload_digest=payload_digest,
            participant_ids=participants,
            quorum=3,
            required_roles=["self-liaison", "self-liaison", "guardian"],
            freshness_window_s=900,
            key_epoch=1,
            accepted_key_epochs=[1],
            trust_root_refs=[FEDERATION_ROOTS[0]],
            trust_root_quorum=1,
            max_hops=2,
            previous_envelope_ref=None,
        )

    def issue_heritage_handoff(
        self,
        *,
        topology_ref: str,
        proposal_ref: str,
        payload_ref: str,
        payload_digest: str,
        referenced_clauses: List[str],
    ) -> DistributedTransportEnvelope:
        if not referenced_clauses:
            raise ValueError("heritage handoff requires at least 1 referenced clause")
        return self._build_envelope(
            topology_ref=topology_ref,
            proposal_ref=proposal_ref,
            council_tier="heritage",
            transport_profile="heritage-attested-review-v1",
            recipient_endpoint="heritage://interpretive-review",
            payload_ref=payload_ref,
            payload_digest=payload_digest,
            participant_ids=list(HERITAGE_PARTICIPANTS),
            quorum=4,
            required_roles=[
                "cultural-representative",
                "cultural-representative",
                "legal-advisor",
                "ethics-committee",
            ],
            freshness_window_s=1800,
            key_epoch=1,
            accepted_key_epochs=[1],
            trust_root_refs=[HERITAGE_ROOTS[0], HERITAGE_ROOTS[1]],
            trust_root_quorum=2,
            max_hops=3,
            previous_envelope_ref=None,
        )

    def rotate_transport_keys(
        self,
        envelope: DistributedTransportEnvelope,
        *,
        next_key_epoch: int,
        trust_root_refs: List[str],
        trust_root_quorum: int,
    ) -> DistributedTransportEnvelope:
        if next_key_epoch <= envelope.key_epoch:
            raise ValueError("next_key_epoch must be greater than the current key_epoch")
        normalized_roots = sorted(set(trust_root_refs))
        if not normalized_roots:
            raise ValueError("trust_root_refs must not be empty")
        if trust_root_quorum < 1 or trust_root_quorum > len(normalized_roots):
            raise ValueError("trust_root_quorum must be between 1 and the number of trust roots")

        return self._build_envelope(
            topology_ref=envelope.topology_ref,
            proposal_ref=envelope.proposal_ref,
            council_tier=envelope.council_tier,
            transport_profile=envelope.transport_profile,
            recipient_endpoint=envelope.recipient_endpoint,
            payload_ref=envelope.payload_ref,
            payload_digest=envelope.payload_digest,
            participant_ids=[attestation.participant_id for attestation in envelope.participant_attestations],
            quorum=envelope.quorum,
            required_roles=list(envelope.required_roles),
            freshness_window_s=envelope.freshness_window_s,
            key_epoch=next_key_epoch,
            accepted_key_epochs=sorted(set(envelope.accepted_key_epochs + [next_key_epoch])),
            trust_root_refs=normalized_roots,
            trust_root_quorum=trust_root_quorum,
            max_hops=envelope.max_hops,
            previous_envelope_ref=envelope.envelope_id,
        )

    def probe_live_root_directory(
        self,
        envelope: DistributedTransportEnvelope,
        *,
        directory_endpoint: str,
        request_timeout_ms: int = 1_000,
    ) -> DistributedTransportRootDirectory:
        normalized_endpoint = self._require_non_empty_string(directory_endpoint, "directory_endpoint")
        timeout_ms = self._require_positive_int(request_timeout_ms, "request_timeout_ms")
        request_started = time.monotonic()
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(normalized_endpoint, timeout=timeout_ms / 1000.0) as response:
            http_status = int(getattr(response, "status", response.getcode()))
            payload_text = response.read().decode("utf-8")
        observed_latency_ms = round((time.monotonic() - request_started) * 1000.0, 1)
        if http_status != 200:
            raise ValueError(f"live root directory endpoint returned unexpected status {http_status}")
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise ValueError("live root directory endpoint must return JSON") from exc
        if not isinstance(payload, Mapping):
            raise ValueError("live root directory payload must be a mapping")
        return self._normalize_root_directory_report(
            payload,
            envelope,
            directory_endpoint=normalized_endpoint,
            request_timeout_ms=timeout_ms,
            observed_latency_ms=observed_latency_ms,
            http_status=http_status,
            response_digest=sha256_text(canonical_json(payload)),
        )

    def probe_authority_plane(
        self,
        envelope: DistributedTransportEnvelope,
        root_directory: DistributedTransportRootDirectory,
        *,
        authority_endpoints: List[str],
        request_timeout_ms: int = 1_000,
    ) -> DistributedTransportAuthorityPlane:
        if root_directory.council_tier != envelope.council_tier:
            raise ValueError("authority plane root_directory council_tier must match envelope")
        if root_directory.transport_profile != envelope.transport_profile:
            raise ValueError("authority plane root_directory transport_profile must match envelope")
        if root_directory.key_epoch not in envelope.accepted_key_epochs:
            raise ValueError("authority plane root_directory key_epoch must be accepted by envelope")

        normalized_endpoints = self._normalize_string_list(authority_endpoints, "authority_endpoints")
        timeout_ms = self._require_positive_int(request_timeout_ms, "request_timeout_ms")
        directory_digest = sha256_text(canonical_json(root_directory.to_dict()))
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        checked_at = utc_now_iso()
        key_servers: List[Dict[str, Any]] = []
        matched_root_refs: List[str] = []
        for endpoint in normalized_endpoints:
            request_started = time.monotonic()
            with opener.open(endpoint, timeout=timeout_ms / 1000.0) as response:
                http_status = int(getattr(response, "status", response.getcode()))
                payload_text = response.read().decode("utf-8")
            observed_latency_ms = round((time.monotonic() - request_started) * 1000.0, 1)
            if http_status != 200:
                raise ValueError(
                    f"authority plane key server endpoint returned unexpected status {http_status}"
                )
            try:
                payload = json.loads(payload_text)
            except json.JSONDecodeError as exc:
                raise ValueError("authority plane key server endpoint must return JSON") from exc
            if not isinstance(payload, Mapping):
                raise ValueError("authority plane key server payload must be a mapping")
            normalized_server = self._normalize_key_server_report(
                payload,
                envelope,
                root_directory,
                server_endpoint=endpoint,
                request_timeout_ms=timeout_ms,
                observed_latency_ms=observed_latency_ms,
                http_status=http_status,
                response_digest=sha256_text(canonical_json(payload)),
            )
            key_servers.append(normalized_server)
            matched_root_refs.extend(normalized_server["matched_root_refs"])

        trusted_root_refs = sorted(set(matched_root_refs))
        if len(trusted_root_refs) < envelope.trust_root_quorum:
            raise ValueError("authority plane must satisfy envelope trust_root_quorum")
        proof_digest = sha256_text(
            canonical_json(
                {
                    "authority_plane_ref": f"authority-plane://{envelope.council_tier}/{envelope.route_nonce}",
                    "directory_digest": directory_digest,
                    "key_server_refs": [server["key_server_ref"] for server in key_servers],
                    "matched_root_refs": trusted_root_refs,
                    "quorum_requirement": envelope.trust_root_quorum,
                }
            )
        )
        payload = {
            "authority_plane_ref": f"authority-plane://{envelope.council_tier}/{envelope.route_nonce}",
            "authority_profile": AUTHORITY_PLANE_PROFILE,
            "checked_at": checked_at,
            "council_tier": envelope.council_tier,
            "directory_digest": directory_digest,
            "directory_ref": root_directory.directory_ref,
            "key_epoch": root_directory.key_epoch,
            "key_servers": key_servers,
            "matched_root_count": len(trusted_root_refs),
            "proof_digest": proof_digest,
            "quorum_requirement": envelope.trust_root_quorum,
            "reachable_server_count": len(key_servers),
            "transport_profile": envelope.transport_profile,
            "trusted_root_refs": trusted_root_refs,
        }
        digest = sha256_text(canonical_json(payload))
        return DistributedTransportAuthorityPlane(
            authority_plane_ref=payload["authority_plane_ref"],
            checked_at=checked_at,
            council_tier=envelope.council_tier,
            transport_profile=envelope.transport_profile,
            authority_profile=AUTHORITY_PLANE_PROFILE,
            key_epoch=root_directory.key_epoch,
            directory_ref=root_directory.directory_ref,
            directory_digest=directory_digest,
            quorum_requirement=envelope.trust_root_quorum,
            reachable_server_count=len(key_servers),
            matched_root_count=len(trusted_root_refs),
            trusted_root_refs=trusted_root_refs,
            key_servers=key_servers,
            proof_digest=proof_digest,
            digest=digest,
        )

    def record_receipt(
        self,
        envelope: DistributedTransportEnvelope,
        *,
        result_ref: str,
        result_digest: str,
        participant_ids: List[str],
        channel_binding_ref: str,
        verified_root_refs: List[str] | None = None,
        key_epoch: int | None = None,
        hop_nonce_chain: List[str] | None = None,
    ) -> DistributedTransportReceipt:
        attestation_map = {
            attestation.participant_id: attestation for attestation in envelope.participant_attestations
        }
        if verified_root_refs is None:
            verified_root_refs = list(envelope.trust_root_refs[: envelope.trust_root_quorum])
        if key_epoch is None:
            key_epoch = envelope.key_epoch
        if hop_nonce_chain is None:
            hop_nonce_chain = [f"hop://{envelope.council_tier}/{envelope.route_nonce}"]

        bindings: List[Dict[str, Any]] = []
        accepted_role_counts: Counter[str] = Counter()
        accepted_count = 0
        for participant_id in participant_ids:
            attestation = attestation_map.get(participant_id)
            accepted = attestation is not None
            binding = {
                "participant_id": participant_id,
                "role": attestation.role if attestation else "unbound",
                "attestation_ref": attestation.attestation_id if attestation else "",
                "proof_ref": attestation.proof_ref if attestation else "",
                "accepted": accepted,
            }
            bindings.append(binding)
            if accepted and attestation is not None:
                accepted_count += 1
                accepted_role_counts[attestation.role] += 1

        required_role_counts = Counter(envelope.required_roles)
        required_roles_satisfied = all(
            accepted_role_counts[role] >= count for role, count in required_role_counts.items()
        )
        quorum_attested = accepted_count >= envelope.quorum
        channel_authenticated = channel_binding_ref == envelope.channel_binding_ref
        normalized_root_refs = sorted(set(verified_root_refs))
        federated_roots_verified = sum(
            1 for root_ref in normalized_root_refs if root_ref in envelope.trust_root_refs
        ) >= envelope.trust_root_quorum
        key_epoch_accepted = key_epoch in envelope.accepted_key_epochs
        normalized_hop_nonce_chain = [hop_nonce for hop_nonce in hop_nonce_chain if hop_nonce]
        hop_chain_digest = sha256_text(canonical_json(normalized_hop_nonce_chain))
        multi_hop_replay_status = "accepted"
        if (
            not normalized_hop_nonce_chain
            or len(normalized_hop_nonce_chain) > envelope.max_hops
            or len(set(normalized_hop_nonce_chain)) != len(normalized_hop_nonce_chain)
            or hop_chain_digest in self._consumed_hop_chain_digests
        ):
            multi_hop_replay_status = "blocked"
        replay_guard_status = (
            "blocked" if envelope.route_nonce in self._consumed_route_nonces else "accepted"
        )

        if replay_guard_status == "blocked" or multi_hop_replay_status == "blocked":
            receipt_status = "replay-blocked"
        elif (
            channel_authenticated
            and required_roles_satisfied
            and quorum_attested
            and federated_roots_verified
            and key_epoch_accepted
        ):
            receipt_status = "authenticated"
            self._consumed_route_nonces.add(envelope.route_nonce)
            self._consumed_hop_chain_digests.add(hop_chain_digest)
        else:
            receipt_status = "rejected"

        authenticity_checks = {
            "channel_authenticated": channel_authenticated,
            "required_roles_satisfied": required_roles_satisfied,
            "quorum_attested": quorum_attested,
            "federated_roots_verified": federated_roots_verified,
            "key_epoch_accepted": key_epoch_accepted,
            "replay_guard_status": replay_guard_status,
            "multi_hop_replay_status": multi_hop_replay_status,
        }
        payload = {
            "authenticity_checks": authenticity_checks,
            "council_tier": envelope.council_tier,
            "envelope_digest": envelope.envelope_digest,
            "envelope_ref": envelope.envelope_id,
            "hop_nonce_chain": normalized_hop_nonce_chain,
            "key_epoch": key_epoch,
            "participant_bindings": bindings,
            "receipt_id": new_id("distributed-receipt"),
            "receipt_status": receipt_status,
            "recorded_at": utc_now_iso(),
            "result_digest": result_digest,
            "result_ref": result_ref,
            "route_nonce": envelope.route_nonce,
            "transport_profile": envelope.transport_profile,
            "verified_root_refs": normalized_root_refs,
        }
        digest = sha256_text(canonical_json(payload))
        return DistributedTransportReceipt(
            receipt_id=payload["receipt_id"],
            envelope_ref=envelope.envelope_id,
            envelope_digest=envelope.envelope_digest,
            council_tier=envelope.council_tier,
            transport_profile=envelope.transport_profile,
            result_ref=result_ref,
            result_digest=result_digest,
            route_nonce=envelope.route_nonce,
            key_epoch=key_epoch,
            verified_root_refs=normalized_root_refs,
            hop_nonce_chain=normalized_hop_nonce_chain,
            receipt_status=receipt_status,
            authenticity_checks=authenticity_checks,
            participant_bindings=bindings,
            recorded_at=payload["recorded_at"],
            digest=digest,
        )

    def capture_relay_telemetry(
        self,
        envelope: DistributedTransportEnvelope,
        receipt: DistributedTransportReceipt,
        *,
        relay_path: List[Dict[str, Any]],
    ) -> DistributedTransportRelayTelemetry:
        if receipt.envelope_ref != envelope.envelope_id:
            raise ValueError("receipt must reference the provided envelope")
        if not relay_path:
            raise ValueError("relay_path must contain at least 1 hop")
        if len(relay_path) != len(receipt.hop_nonce_chain):
            raise ValueError("relay_path must align with receipt hop_nonce_chain length")
        if len(relay_path) > envelope.max_hops:
            raise ValueError("relay_path must not exceed envelope.max_hops")

        accepted_count = sum(
            1 for binding in receipt.participant_bindings if binding.get("accepted") is True
        )
        relay_hops: List[DistributedRelayHopTelemetry] = []
        total_latency_ms = 0.0
        for index, (hop_nonce, hop_data) in enumerate(zip(receipt.hop_nonce_chain, relay_path), start=1):
            relay_id = self._require_non_empty_string(hop_data.get("relay_id"), "relay_id")
            relay_endpoint = self._require_non_empty_string(
                hop_data.get("relay_endpoint"),
                "relay_endpoint",
            )
            jurisdiction = self._require_non_empty_string(
                hop_data.get("jurisdiction"),
                "jurisdiction",
            )
            network_zone = self._require_non_empty_string(
                hop_data.get("network_zone"),
                "network_zone",
            )
            transport_layer = self._require_non_empty_string(
                hop_data.get(
                    "transport_layer",
                    RELAY_TRANSPORT_LAYER_BY_PROFILE[envelope.transport_profile],
                ),
                "transport_layer",
            )
            observed_latency_ms = self._require_positive_float(
                hop_data.get("observed_latency_ms"),
                "observed_latency_ms",
            )
            root_refs_seen = self._normalize_string_list(
                hop_data.get("root_refs_seen", receipt.verified_root_refs),
                "root_refs_seen",
            )
            observed_at = self._require_non_empty_string(
                hop_data.get("observed_at", receipt.recorded_at),
                "observed_at",
            )
            delivery_status = "forwarded"
            if index == len(receipt.hop_nonce_chain):
                delivery_status = receipt.receipt_status
            route_binding_ref = (
                f"relay-binding://{envelope.council_tier}/"
                f"{sha256_text(f'{envelope.channel_binding_ref}:{relay_id}:{hop_nonce}')[:16]}"
            )
            relay_hops.append(
                DistributedRelayHopTelemetry(
                    hop_index=index,
                    relay_id=relay_id,
                    relay_endpoint=relay_endpoint,
                    jurisdiction=jurisdiction,
                    network_zone=network_zone,
                    transport_layer=transport_layer,
                    hop_nonce=hop_nonce,
                    observed_latency_ms=observed_latency_ms,
                    root_refs_seen=root_refs_seen,
                    route_binding_ref=route_binding_ref,
                    attested_participant_count=accepted_count,
                    delivery_status=delivery_status,
                    observed_at=observed_at,
                )
            )
            total_latency_ms += observed_latency_ms

        hop_chain_digest = sha256_text(canonical_json(receipt.hop_nonce_chain))
        recorded_at = receipt.recorded_at
        payload = {
            "council_tier": envelope.council_tier,
            "end_to_end_status": receipt.receipt_status,
            "envelope_digest": envelope.envelope_digest,
            "envelope_ref": envelope.envelope_id,
            "hop_chain_digest": hop_chain_digest,
            "hop_count": len(receipt.hop_nonce_chain),
            "max_hops": envelope.max_hops,
            "path_profile": RELAY_TELEMETRY_PROFILE,
            "receipt_digest": receipt.digest,
            "receipt_ref": receipt.receipt_id,
            "recorded_at": recorded_at,
            "relay_hops": [hop.to_dict() for hop in relay_hops],
            "route_nonce": envelope.route_nonce,
            "root_quorum_met": receipt.authenticity_checks["federated_roots_verified"],
            "transport_profile": envelope.transport_profile,
            "anti_replay_status": receipt.authenticity_checks["multi_hop_replay_status"],
            "replay_guard_status": receipt.authenticity_checks["replay_guard_status"],
            "total_latency_ms": round(total_latency_ms, 3),
            "telemetry_id": new_id("distributed-telemetry"),
        }
        digest = sha256_text(canonical_json(payload))
        return DistributedTransportRelayTelemetry(
            telemetry_id=payload["telemetry_id"],
            envelope_ref=envelope.envelope_id,
            envelope_digest=envelope.envelope_digest,
            receipt_ref=receipt.receipt_id,
            receipt_digest=receipt.digest,
            council_tier=envelope.council_tier,
            transport_profile=envelope.transport_profile,
            path_profile=RELAY_TELEMETRY_PROFILE,
            route_nonce=envelope.route_nonce,
            hop_count=len(receipt.hop_nonce_chain),
            max_hops=envelope.max_hops,
            hop_chain_digest=hop_chain_digest,
            relay_hops=relay_hops,
            total_latency_ms=round(total_latency_ms, 3),
            anti_replay_status=receipt.authenticity_checks["multi_hop_replay_status"],
            replay_guard_status=receipt.authenticity_checks["replay_guard_status"],
            root_quorum_met=receipt.authenticity_checks["federated_roots_verified"],
            end_to_end_status=receipt.receipt_status,
            recorded_at=recorded_at,
            digest=digest,
        )

    def _normalize_key_server_report(
        self,
        payload: Mapping[str, Any],
        envelope: DistributedTransportEnvelope,
        root_directory: DistributedTransportRootDirectory,
        *,
        server_endpoint: str,
        request_timeout_ms: int,
        observed_latency_ms: float,
        http_status: int,
        response_digest: str,
    ) -> Dict[str, Any]:
        if payload.get("kind") != "distributed_transport_key_server":
            raise ValueError("authority plane key server kind must equal distributed_transport_key_server")
        if payload.get("schema_version") != "1.0.0":
            raise ValueError("authority plane key server schema_version must equal 1.0.0")
        key_server_ref = self._require_non_empty_string(payload.get("key_server_ref"), "key_server_ref")
        if not key_server_ref.startswith("keyserver://"):
            raise ValueError("key_server_ref must start with keyserver://")
        checked_at = self._require_non_empty_string(payload.get("checked_at"), "checked_at")
        council_tier = self._require_non_empty_string(payload.get("council_tier"), "council_tier")
        if council_tier != envelope.council_tier:
            raise ValueError("authority plane key server council_tier must match envelope")
        served_transport_profile = self._require_non_empty_string(
            payload.get("served_transport_profile"),
            "served_transport_profile",
        )
        if served_transport_profile != envelope.transport_profile:
            raise ValueError("authority plane key server served_transport_profile must match envelope")
        server_role = self._require_non_empty_string(payload.get("server_role"), "server_role")
        if server_role not in {"directory-mirror", "quorum-notary"}:
            raise ValueError("authority plane key server role must be directory-mirror or quorum-notary")
        authority_status = self._require_non_empty_string(
            payload.get("authority_status"),
            "authority_status",
        )
        if authority_status not in {"active", "draining"}:
            raise ValueError("authority plane key server authority_status must be active or draining")
        key_epoch = self._require_positive_int(payload.get("key_epoch"), "key_epoch")
        if key_epoch != root_directory.key_epoch or key_epoch not in envelope.accepted_key_epochs:
            raise ValueError("authority plane key server key_epoch must match accepted root directory epoch")
        proof_digest = self._require_sha256_hex(payload.get("proof_digest"), "proof_digest")
        advertised_root_refs = self._normalize_string_list(
            payload.get("advertised_root_refs"),
            "advertised_root_refs",
        )
        matched_root_refs = sorted(
            {
                root_ref
                for root_ref in advertised_root_refs
                if root_ref in root_directory.trusted_root_refs
            }
        )
        if not matched_root_refs:
            raise ValueError("authority plane key server must advertise at least 1 trusted root")
        return {
            "kind": "distributed_transport_key_server",
            "schema_version": "1.0.0",
            "key_server_ref": key_server_ref,
            "checked_at": checked_at,
            "council_tier": council_tier,
            "served_transport_profile": served_transport_profile,
            "server_role": server_role,
            "authority_status": authority_status,
            "key_epoch": key_epoch,
            "advertised_root_refs": advertised_root_refs,
            "matched_root_refs": matched_root_refs,
            "server_endpoint": server_endpoint,
            "transport_profile": LIVE_KEY_SERVER_TRANSPORT_PROFILE,
            "request_timeout_ms": request_timeout_ms,
            "observed_latency_ms": observed_latency_ms,
            "http_status": http_status,
            "response_digest": response_digest,
            "receipt_status": "reachable",
            "proof_digest": proof_digest,
            "recorded_at": utc_now_iso(),
        }

    def _normalize_root_directory_report(
        self,
        payload: Mapping[str, Any],
        envelope: DistributedTransportEnvelope,
        *,
        directory_endpoint: str,
        request_timeout_ms: int,
        observed_latency_ms: float,
        http_status: int,
        response_digest: str,
    ) -> DistributedTransportRootDirectory:
        if payload.get("kind") != "distributed_transport_root_directory":
            raise ValueError("live root directory kind must equal distributed_transport_root_directory")
        if payload.get("schema_version") != "1.0.0":
            raise ValueError("live root directory schema_version must equal 1.0.0")

        directory_ref = self._require_non_empty_string(payload.get("directory_ref"), "directory_ref")
        if not directory_ref.startswith("rootdir://"):
            raise ValueError("directory_ref must start with rootdir://")
        checked_at = self._require_non_empty_string(payload.get("checked_at"), "checked_at")
        council_tier = self._require_non_empty_string(payload.get("council_tier"), "council_tier")
        if council_tier != envelope.council_tier:
            raise ValueError("live root directory council_tier must match envelope")
        transport_profile = self._require_non_empty_string(
            payload.get("transport_profile"),
            "transport_profile",
        )
        if transport_profile != envelope.transport_profile:
            raise ValueError("live root directory transport_profile must match envelope")
        key_epoch = self._require_positive_int(payload.get("key_epoch"), "key_epoch")
        if key_epoch not in envelope.accepted_key_epochs:
            raise ValueError("live root directory key_epoch must be accepted by envelope")
        quorum_requirement = self._require_positive_int(
            payload.get("quorum_requirement"),
            "quorum_requirement",
        )
        if quorum_requirement != envelope.trust_root_quorum:
            raise ValueError("live root directory quorum_requirement must match envelope trust_root_quorum")
        proof_digest = self._require_sha256_hex(payload.get("proof_digest"), "proof_digest")

        accepted_roots_raw = payload.get("accepted_roots")
        if not isinstance(accepted_roots_raw, list) or not accepted_roots_raw:
            raise ValueError("accepted_roots must be a non-empty list")
        accepted_roots: List[Dict[str, Any]] = []
        trusted_root_refs: List[str] = []
        active_root_ref = self._require_non_empty_string(payload.get("active_root_ref"), "active_root_ref")
        allowed_statuses = {"active", "candidate", "retired"}
        for index, root in enumerate(accepted_roots_raw):
            if not isinstance(root, Mapping):
                raise ValueError("accepted_roots entries must be mappings")
            root_ref = self._require_non_empty_string(root.get("root_ref"), f"accepted_roots[{index}].root_ref")
            fingerprint = self._require_sha256_hex(
                root.get("fingerprint"),
                f"accepted_roots[{index}].fingerprint",
            )
            status = self._require_non_empty_string(root.get("status"), f"accepted_roots[{index}].status")
            if status not in allowed_statuses:
                raise ValueError("accepted_roots status must be active, candidate, or retired")
            root_key_epoch = self._require_positive_int(
                root.get("key_epoch"),
                f"accepted_roots[{index}].key_epoch",
            )
            if root_key_epoch not in envelope.accepted_key_epochs:
                raise ValueError("accepted_roots key_epoch must stay within envelope accepted_key_epochs")
            normalized_root = {
                "root_ref": root_ref,
                "fingerprint": fingerprint,
                "status": status,
                "key_epoch": root_key_epoch,
            }
            accepted_roots.append(normalized_root)
            if root_ref in envelope.trust_root_refs and status in {"active", "candidate"}:
                trusted_root_refs.append(root_ref)
        if active_root_ref not in {root["root_ref"] for root in accepted_roots}:
            raise ValueError("active_root_ref must reference one accepted root")
        if len(sorted(set(trusted_root_refs))) < envelope.trust_root_quorum:
            raise ValueError("live root directory must satisfy envelope trust_root_quorum")

        trusted_root_refs = sorted(set(trusted_root_refs))
        connectivity_receipt = DistributedTransportRootConnectivityReceipt(
            receipt_id=new_id("distributed-root-connectivity"),
            directory_ref=directory_ref,
            directory_endpoint=directory_endpoint,
            transport_profile=LIVE_ROOT_DIRECTORY_TRANSPORT_PROFILE,
            recorded_at=utc_now_iso(),
            request_timeout_ms=request_timeout_ms,
            observed_latency_ms=observed_latency_ms,
            http_status=http_status,
            response_digest=response_digest,
            receipt_status="reachable",
            matched_root_count=len(trusted_root_refs),
            quorum_satisfied=len(trusted_root_refs) >= envelope.trust_root_quorum,
            trusted_root_refs=trusted_root_refs,
        )
        return DistributedTransportRootDirectory(
            directory_ref=directory_ref,
            checked_at=checked_at,
            council_tier=council_tier,
            transport_profile=transport_profile,
            key_epoch=key_epoch,
            active_root_ref=active_root_ref,
            accepted_roots=accepted_roots,
            quorum_requirement=quorum_requirement,
            proof_digest=proof_digest,
            trusted_root_refs=trusted_root_refs,
            connectivity_receipt=connectivity_receipt,
        )

    def _build_envelope(
        self,
        *,
        topology_ref: str,
        proposal_ref: str,
        council_tier: str,
        transport_profile: str,
        recipient_endpoint: str,
        payload_ref: str,
        payload_digest: str,
        participant_ids: List[str],
        quorum: int,
        required_roles: List[str],
        freshness_window_s: int,
        key_epoch: int,
        accepted_key_epochs: List[int],
        trust_root_refs: List[str],
        trust_root_quorum: int,
        max_hops: int,
        previous_envelope_ref: str | None,
    ) -> DistributedTransportEnvelope:
        attestations = self._build_attestations(
            council_tier,
            participant_ids,
            key_epoch=key_epoch,
            trust_root_refs=trust_root_refs,
        )
        route_nonce = new_id("route-nonce")
        issued_at = utc_now_iso()
        attestation_digest = sha256_text(
            canonical_json(
                {
                    "attestation_ids": [attestation.attestation_id for attestation in attestations],
                    "accepted_key_epochs": accepted_key_epochs,
                    "roles": [attestation.role for attestation in attestations],
                    "trust_root_refs": trust_root_refs,
                    "transport_profile": transport_profile,
                }
            )
        )
        envelope_payload = {
            "attestation_digest": attestation_digest,
            "channel_binding_ref": f"channel-binding://{council_tier}/{sha256_text(f'{topology_ref}:{payload_digest}:{route_nonce}')[:16]}",
            "council_tier": council_tier,
            "envelope_id": new_id("distributed-envelope"),
            "freshness_window_s": freshness_window_s,
            "issued_at": issued_at,
            "key_epoch": key_epoch,
            "accepted_key_epochs": accepted_key_epochs,
            "trust_root_refs": trust_root_refs,
            "trust_root_quorum": trust_root_quorum,
            "max_hops": max_hops,
            "previous_envelope_ref": previous_envelope_ref,
            "participant_attestations": [attestation.to_dict() for attestation in attestations],
            "payload_digest": payload_digest,
            "payload_ref": payload_ref,
            "proposal_ref": proposal_ref,
            "quorum": quorum,
            "recipient_endpoint": recipient_endpoint,
            "required_roles": required_roles,
            "route_nonce": route_nonce,
            "topology_ref": topology_ref,
            "transport_profile": transport_profile,
        }
        envelope_digest = sha256_text(canonical_json(envelope_payload))
        return DistributedTransportEnvelope(
            envelope_id=envelope_payload["envelope_id"],
            topology_ref=topology_ref,
            proposal_ref=proposal_ref,
            council_tier=council_tier,
            transport_profile=transport_profile,
            recipient_endpoint=recipient_endpoint,
            payload_ref=payload_ref,
            payload_digest=payload_digest,
            route_nonce=route_nonce,
            freshness_window_s=freshness_window_s,
            quorum=quorum,
            required_roles=list(required_roles),
            key_epoch=key_epoch,
            accepted_key_epochs=list(accepted_key_epochs),
            trust_root_refs=list(trust_root_refs),
            trust_root_quorum=trust_root_quorum,
            max_hops=max_hops,
            previous_envelope_ref=previous_envelope_ref,
            channel_binding_ref=envelope_payload["channel_binding_ref"],
            participant_attestations=attestations,
            attestation_digest=attestation_digest,
            issued_at=issued_at,
            envelope_digest=envelope_digest,
        )

    def _build_attestations(
        self,
        council_tier: str,
        participant_ids: List[str],
        *,
        key_epoch: int,
        trust_root_refs: List[str],
    ) -> List[DistributedParticipantAttestation]:
        attestations: List[DistributedParticipantAttestation] = []
        for index, participant_id in enumerate(participant_ids):
            role = self._role_for_participant(council_tier, participant_id)
            digest_seed = sha256_text(f"{council_tier}:{participant_id}:{role}:epoch-{key_epoch}")
            trust_root_ref = trust_root_refs[index % len(trust_root_refs)]
            attestations.append(
                DistributedParticipantAttestation(
                    attestation_id=new_id("distributed-attestation"),
                    participant_id=participant_id,
                    council_tier=council_tier,
                    role=role,
                    credential_ref=f"credential://{council_tier}/{digest_seed[:12]}",
                    proof_ref=f"proof://{council_tier}/{digest_seed[12:24]}",
                    transport_key_ref=f"transport-key://{council_tier}/epoch-{key_epoch}/{digest_seed[24:36]}",
                    trust_root_ref=trust_root_ref,
                    key_epoch=key_epoch,
                    trust_score=ROLE_TRUST_SCORES[role],
                    issued_at=utc_now_iso(),
                )
            )
        return attestations

    @staticmethod
    def _role_for_participant(council_tier: str, participant_id: str) -> str:
        if council_tier == "federation":
            if participant_id == FEDERATION_GUARDIAN_ID:
                return "guardian"
            return "self-liaison"
        if council_tier == "heritage":
            if participant_id in {"heritage://culture-a", "heritage://culture-b"}:
                return "cultural-representative"
            if participant_id == "heritage://legal-advisor":
                return "legal-advisor"
            if participant_id == "heritage://ethics-committee":
                return "ethics-committee"
        raise ValueError(f"unsupported participant for {council_tier}: {participant_id}")

    @staticmethod
    def _require_non_empty_string(value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value.strip()

    @classmethod
    def _normalize_string_list(cls, values: Any, field_name: str) -> List[str]:
        if not isinstance(values, list) or not values:
            raise ValueError(f"{field_name} must be a non-empty list")
        normalized: List[str] = []
        for value in values:
            text = cls._require_non_empty_string(value, field_name)
            if text not in normalized:
                normalized.append(text)
        return normalized

    @staticmethod
    def _require_positive_float(value: Any, field_name: str) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} must be numeric") from exc
        if number <= 0:
            raise ValueError(f"{field_name} must be greater than 0")
        return number

    @staticmethod
    def _require_positive_int(value: Any, field_name: str) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} must be an integer") from exc
        if number <= 0:
            raise ValueError(f"{field_name} must be greater than 0")
        return number

    @staticmethod
    def _require_sha256_hex(value: Any, field_name: str) -> str:
        text = DistributedTransportService._require_non_empty_string(value, field_name)
        if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
            raise ValueError(f"{field_name} must be a sha256 hex digest")
        return text
