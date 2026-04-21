"""Distributed council transport attestation reference model."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import shutil
import socket
import ssl
import struct
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Mapping
from urllib.parse import urlsplit
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
AUTHORITY_CHURN_PROFILE = "bounded-key-server-churn-window-v1"
AUTHORITY_ROUTE_TRACE_PROFILE = "non-loopback-mtls-authority-route-v1"
AUTHORITY_ROUTE_SOCKET_PROFILE = "mtls-socket-trace-v1"
AUTHORITY_ROUTE_OS_OBSERVER_PROFILE = "os-native-tcp-observer-v1"
AUTHORITY_ROUTE_CROSS_HOST_PROFILE = "attested-cross-host-authority-binding-v1"
AUTHORITY_ROUTE_PCAP_EXPORT_PROFILE = "trace-bound-pcap-export-v1"
AUTHORITY_ROUTE_PCAP_ARTIFACT_FORMAT = "pcap"
AUTHORITY_ROUTE_PCAP_READBACK_PROFILE = "pcap-readback-v1"
AUTHORITY_ROUTE_PCAP_OS_NATIVE_PROFILE = "tcpdump-readback-v1"
PRIVILEGED_CAPTURE_ACQUISITION_PROFILE = "bounded-live-interface-capture-acquisition-v1"
PRIVILEGED_CAPTURE_PRIVILEGE_MODE = "delegated-broker"
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
    churn_profile: str
    key_epoch: int
    directory_ref: str
    directory_digest: str
    quorum_requirement: int
    reachable_server_count: int
    active_server_count: int
    draining_server_count: int
    matched_root_count: int
    trusted_root_refs: List[str]
    root_coverage: List[Dict[str, Any]]
    churn_safe: bool
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
            "churn_profile": self.churn_profile,
            "key_epoch": self.key_epoch,
            "directory_ref": self.directory_ref,
            "directory_digest": self.directory_digest,
            "quorum_requirement": self.quorum_requirement,
            "reachable_server_count": self.reachable_server_count,
            "active_server_count": self.active_server_count,
            "draining_server_count": self.draining_server_count,
            "matched_root_count": self.matched_root_count,
            "trusted_root_refs": list(self.trusted_root_refs),
            "root_coverage": [dict(coverage) for coverage in self.root_coverage],
            "churn_safe": self.churn_safe,
            "key_servers": [dict(server) for server in self.key_servers],
            "proof_digest": self.proof_digest,
            "digest": self.digest,
        }


@dataclass
class DistributedTransportAuthorityChurnWindow:
    """Machine-checkable authority-plane churn window bound across two snapshots."""

    churn_window_ref: str
    checked_at: str
    council_tier: str
    transport_profile: str
    churn_profile: str
    key_epoch: int
    directory_ref: str
    directory_digest: str
    previous_authority_plane_ref: str
    next_authority_plane_ref: str
    quorum_requirement: int
    trusted_root_refs: List[str]
    retained_server_refs: List[str]
    added_server_refs: List[str]
    removed_server_refs: List[str]
    draining_server_refs: List[str]
    retained_root_refs: List[str]
    added_root_refs: List[str]
    removed_root_refs: List[str]
    server_transitions: List[Dict[str, Any]]
    continuity_guard: Dict[str, Any]
    proof_digest: str
    digest: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "distributed_transport_authority_churn_window",
            "schema_version": "1.0.0",
            "churn_window_ref": self.churn_window_ref,
            "checked_at": self.checked_at,
            "council_tier": self.council_tier,
            "transport_profile": self.transport_profile,
            "churn_profile": self.churn_profile,
            "key_epoch": self.key_epoch,
            "directory_ref": self.directory_ref,
            "directory_digest": self.directory_digest,
            "previous_authority_plane_ref": self.previous_authority_plane_ref,
            "next_authority_plane_ref": self.next_authority_plane_ref,
            "quorum_requirement": self.quorum_requirement,
            "trusted_root_refs": list(self.trusted_root_refs),
            "retained_server_refs": list(self.retained_server_refs),
            "added_server_refs": list(self.added_server_refs),
            "removed_server_refs": list(self.removed_server_refs),
            "draining_server_refs": list(self.draining_server_refs),
            "retained_root_refs": list(self.retained_root_refs),
            "added_root_refs": list(self.added_root_refs),
            "removed_root_refs": list(self.removed_root_refs),
            "server_transitions": [dict(transition) for transition in self.server_transitions],
            "continuity_guard": dict(self.continuity_guard),
            "proof_digest": self.proof_digest,
            "digest": self.digest,
        }


@dataclass
class DistributedTransportAuthorityRouteTrace:
    """Machine-checkable non-loopback mTLS route trace for authority-plane members."""

    trace_ref: str
    authority_plane_ref: str
    authority_plane_digest: str
    envelope_ref: str
    envelope_digest: str
    council_tier: str
    transport_profile: str
    trace_profile: str
    socket_trace_profile: str
    os_observer_profile: str
    cross_host_binding_profile: str
    ca_bundle_ref: str
    client_certificate_ref: str
    server_name: str
    authority_cluster_ref: str
    route_count: int
    distinct_remote_host_count: int
    mtls_authenticated_count: int
    trusted_root_refs: List[str]
    non_loopback_verified: bool
    authority_plane_bound: bool
    response_digest_bound: bool
    socket_trace_complete: bool
    os_observer_complete: bool
    cross_host_verified: bool
    route_bindings: List[Dict[str, Any]]
    trace_status: str
    recorded_at: str
    total_connect_latency_ms: float
    total_handshake_latency_ms: float
    total_round_trip_latency_ms: float
    digest: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "distributed_transport_authority_route_trace",
            "schema_version": "1.0.0",
            "trace_ref": self.trace_ref,
            "authority_plane_ref": self.authority_plane_ref,
            "authority_plane_digest": self.authority_plane_digest,
            "envelope_ref": self.envelope_ref,
            "envelope_digest": self.envelope_digest,
            "council_tier": self.council_tier,
            "transport_profile": self.transport_profile,
            "trace_profile": self.trace_profile,
            "socket_trace_profile": self.socket_trace_profile,
            "os_observer_profile": self.os_observer_profile,
            "cross_host_binding_profile": self.cross_host_binding_profile,
            "ca_bundle_ref": self.ca_bundle_ref,
            "client_certificate_ref": self.client_certificate_ref,
            "server_name": self.server_name,
            "authority_cluster_ref": self.authority_cluster_ref,
            "route_count": self.route_count,
            "distinct_remote_host_count": self.distinct_remote_host_count,
            "mtls_authenticated_count": self.mtls_authenticated_count,
            "trusted_root_refs": list(self.trusted_root_refs),
            "non_loopback_verified": self.non_loopback_verified,
            "authority_plane_bound": self.authority_plane_bound,
            "response_digest_bound": self.response_digest_bound,
            "socket_trace_complete": self.socket_trace_complete,
            "os_observer_complete": self.os_observer_complete,
            "cross_host_verified": self.cross_host_verified,
            "route_bindings": [dict(binding) for binding in self.route_bindings],
            "trace_status": self.trace_status,
            "recorded_at": self.recorded_at,
            "total_connect_latency_ms": self.total_connect_latency_ms,
            "total_handshake_latency_ms": self.total_handshake_latency_ms,
            "total_round_trip_latency_ms": self.total_round_trip_latency_ms,
            "digest": self.digest,
        }


@dataclass
class DistributedTransportPacketCaptureExport:
    """Trace-bound packet-capture artifact exported from an authenticated authority route trace."""

    capture_ref: str
    trace_ref: str
    trace_digest: str
    authority_plane_ref: str
    authority_plane_digest: str
    envelope_ref: str
    envelope_digest: str
    council_tier: str
    transport_profile: str
    capture_profile: str
    artifact_format: str
    readback_profile: str
    os_native_readback_profile: str
    route_count: int
    packet_count: int
    artifact_size_bytes: int
    artifact_digest: str
    readback_digest: str
    route_exports: List[Dict[str, Any]]
    os_native_readback_available: bool
    os_native_readback_ok: bool
    export_status: str
    recorded_at: str
    digest: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "distributed_transport_packet_capture_export",
            "schema_version": "1.0.0",
            "capture_ref": self.capture_ref,
            "trace_ref": self.trace_ref,
            "trace_digest": self.trace_digest,
            "authority_plane_ref": self.authority_plane_ref,
            "authority_plane_digest": self.authority_plane_digest,
            "envelope_ref": self.envelope_ref,
            "envelope_digest": self.envelope_digest,
            "council_tier": self.council_tier,
            "transport_profile": self.transport_profile,
            "capture_profile": self.capture_profile,
            "artifact_format": self.artifact_format,
            "readback_profile": self.readback_profile,
            "os_native_readback_profile": self.os_native_readback_profile,
            "route_count": self.route_count,
            "packet_count": self.packet_count,
            "artifact_size_bytes": self.artifact_size_bytes,
            "artifact_digest": self.artifact_digest,
            "readback_digest": self.readback_digest,
            "route_exports": [dict(route_export) for route_export in self.route_exports],
            "os_native_readback_available": self.os_native_readback_available,
            "os_native_readback_ok": self.os_native_readback_ok,
            "export_status": self.export_status,
            "recorded_at": self.recorded_at,
            "digest": self.digest,
        }


@dataclass
class DistributedTransportPrivilegedCaptureAcquisition:
    """Delegated privileged live-capture lease bound to an authority route trace."""

    acquisition_ref: str
    trace_ref: str
    trace_digest: str
    capture_ref: str
    capture_digest: str
    authority_plane_ref: str
    authority_plane_digest: str
    envelope_ref: str
    envelope_digest: str
    council_tier: str
    transport_profile: str
    acquisition_profile: str
    broker_profile: str
    privilege_mode: str
    lease_ref: str
    broker_attestation_ref: str
    interface_name: str
    local_ips: List[str]
    capture_filter: str
    filter_digest: str
    route_binding_refs: List[str]
    capture_command: List[str]
    lease_duration_s: int
    lease_expires_at: str
    grant_status: str
    recorded_at: str
    digest: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "distributed_transport_privileged_capture_acquisition",
            "schema_version": "1.0.0",
            "acquisition_ref": self.acquisition_ref,
            "trace_ref": self.trace_ref,
            "trace_digest": self.trace_digest,
            "capture_ref": self.capture_ref,
            "capture_digest": self.capture_digest,
            "authority_plane_ref": self.authority_plane_ref,
            "authority_plane_digest": self.authority_plane_digest,
            "envelope_ref": self.envelope_ref,
            "envelope_digest": self.envelope_digest,
            "council_tier": self.council_tier,
            "transport_profile": self.transport_profile,
            "acquisition_profile": self.acquisition_profile,
            "broker_profile": self.broker_profile,
            "privilege_mode": self.privilege_mode,
            "lease_ref": self.lease_ref,
            "broker_attestation_ref": self.broker_attestation_ref,
            "interface_name": self.interface_name,
            "local_ips": list(self.local_ips),
            "capture_filter": self.capture_filter,
            "filter_digest": self.filter_digest,
            "route_binding_refs": list(self.route_binding_refs),
            "capture_command": list(self.capture_command),
            "lease_duration_s": self.lease_duration_s,
            "lease_expires_at": self.lease_expires_at,
            "grant_status": self.grant_status,
            "recorded_at": self.recorded_at,
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
        active_server_count = sum(
            1 for server in key_servers if server["authority_status"] == "active"
        )
        draining_server_count = sum(
            1 for server in key_servers if server["authority_status"] == "draining"
        )
        root_coverage: List[Dict[str, Any]] = []
        for root_ref in trusted_root_refs:
            active_server_refs = sorted(
                server["key_server_ref"]
                for server in key_servers
                if server["authority_status"] == "active" and root_ref in server["matched_root_refs"]
            )
            draining_server_refs = sorted(
                server["key_server_ref"]
                for server in key_servers
                if server["authority_status"] == "draining" and root_ref in server["matched_root_refs"]
            )
            if not active_server_refs:
                raise ValueError(
                    "authority plane trusted root coverage must retain at least 1 active key server per root"
                )
            root_coverage.append(
                {
                    "root_ref": root_ref,
                    "active_server_refs": active_server_refs,
                    "draining_server_refs": draining_server_refs,
                    "coverage_status": "handoff-ready" if draining_server_refs else "stable",
                }
            )
        churn_safe = all(
            coverage["coverage_status"] in {"stable", "handoff-ready"} for coverage in root_coverage
        )
        proof_digest = sha256_text(
            canonical_json(
                {
                    "authority_plane_ref": f"authority-plane://{envelope.council_tier}/{envelope.route_nonce}",
                    "churn_profile": "overlap-safe-authority-handoff-v1",
                    "directory_digest": directory_digest,
                    "key_server_refs": [server["key_server_ref"] for server in key_servers],
                    "matched_root_refs": trusted_root_refs,
                    "root_coverage": root_coverage,
                    "quorum_requirement": envelope.trust_root_quorum,
                }
            )
        )
        payload = {
            "authority_plane_ref": f"authority-plane://{envelope.council_tier}/{envelope.route_nonce}",
            "authority_profile": AUTHORITY_PLANE_PROFILE,
            "checked_at": checked_at,
            "council_tier": envelope.council_tier,
            "churn_profile": "overlap-safe-authority-handoff-v1",
            "directory_digest": directory_digest,
            "directory_ref": root_directory.directory_ref,
            "key_epoch": root_directory.key_epoch,
            "key_servers": key_servers,
            "active_server_count": active_server_count,
            "draining_server_count": draining_server_count,
            "matched_root_count": len(trusted_root_refs),
            "proof_digest": proof_digest,
            "quorum_requirement": envelope.trust_root_quorum,
            "reachable_server_count": len(key_servers),
            "root_coverage": root_coverage,
            "churn_safe": churn_safe,
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
            churn_profile=payload["churn_profile"],
            key_epoch=root_directory.key_epoch,
            directory_ref=root_directory.directory_ref,
            directory_digest=directory_digest,
            quorum_requirement=envelope.trust_root_quorum,
            reachable_server_count=len(key_servers),
            active_server_count=active_server_count,
            draining_server_count=draining_server_count,
            matched_root_count=len(trusted_root_refs),
            trusted_root_refs=trusted_root_refs,
            root_coverage=root_coverage,
            churn_safe=churn_safe,
            key_servers=key_servers,
            proof_digest=proof_digest,
            digest=digest,
        )

    def reconcile_authority_churn(
        self,
        previous_authority_plane: DistributedTransportAuthorityPlane,
        next_authority_plane: DistributedTransportAuthorityPlane,
    ) -> DistributedTransportAuthorityChurnWindow:
        if previous_authority_plane.council_tier != next_authority_plane.council_tier:
            raise ValueError("authority churn council_tier must remain stable across snapshots")
        if previous_authority_plane.transport_profile != next_authority_plane.transport_profile:
            raise ValueError("authority churn transport_profile must remain stable across snapshots")
        if previous_authority_plane.directory_ref != next_authority_plane.directory_ref:
            raise ValueError("authority churn directory_ref must remain stable across snapshots")
        if previous_authority_plane.directory_digest != next_authority_plane.directory_digest:
            raise ValueError("authority churn directory_digest must remain stable across snapshots")
        if previous_authority_plane.key_epoch != next_authority_plane.key_epoch:
            raise ValueError("authority churn key_epoch must remain stable across snapshots")
        if previous_authority_plane.quorum_requirement != next_authority_plane.quorum_requirement:
            raise ValueError("authority churn quorum_requirement must remain stable across snapshots")

        previous_servers = {
            server["key_server_ref"]: dict(server) for server in previous_authority_plane.key_servers
        }
        next_servers = {server["key_server_ref"]: dict(server) for server in next_authority_plane.key_servers}
        previous_refs = set(previous_servers)
        next_refs = set(next_servers)
        retained_server_refs = sorted(previous_refs & next_refs)
        added_server_refs = sorted(next_refs - previous_refs)
        removed_server_refs = sorted(previous_refs - next_refs)
        draining_server_refs = sorted(
            {
                ref
                for ref, server in {**previous_servers, **next_servers}.items()
                if server.get("authority_status") == "draining"
            }
        )
        churn_detected = bool(added_server_refs or removed_server_refs)
        minimum_overlap_required = 1 if churn_detected else 0
        if len(retained_server_refs) < minimum_overlap_required:
            raise ValueError("authority churn must retain at least 1 overlapping key server")
        removed_servers_draining = all(
            previous_servers[ref].get("authority_status") == "draining" for ref in removed_server_refs
        )
        if not removed_servers_draining:
            raise ValueError("authority churn may remove only previously draining key servers")
        if len(next_authority_plane.trusted_root_refs) < next_authority_plane.quorum_requirement:
            raise ValueError("authority churn must preserve trust_root_quorum")

        retained_root_refs = sorted(
            set(previous_authority_plane.trusted_root_refs) & set(next_authority_plane.trusted_root_refs)
        )
        added_root_refs = sorted(
            set(next_authority_plane.trusted_root_refs) - set(previous_authority_plane.trusted_root_refs)
        )
        removed_root_refs = sorted(
            set(previous_authority_plane.trusted_root_refs) - set(next_authority_plane.trusted_root_refs)
        )
        server_transitions: List[Dict[str, Any]] = []
        for key_server_ref in sorted(previous_refs | next_refs):
            previous_server = previous_servers.get(key_server_ref)
            next_server = next_servers.get(key_server_ref)
            if previous_server and next_server:
                transition = "retained-draining" if next_server.get("authority_status") == "draining" else "retained"
            elif next_server:
                transition = "added"
            else:
                transition = "removed"
            server_transitions.append(
                {
                    "key_server_ref": key_server_ref,
                    "transition": transition,
                    "previous_status": previous_server.get("authority_status", "missing")
                    if previous_server
                    else "missing",
                    "current_status": next_server.get("authority_status", "missing")
                    if next_server
                    else "missing",
                    "matched_root_refs": list(
                        next_server.get("matched_root_refs", previous_server.get("matched_root_refs", []))
                        if previous_server and next_server
                        else (next_server or previous_server).get("matched_root_refs", [])
                    ),
                }
            )

        continuity_guard = {
            "minimum_overlap_required": minimum_overlap_required,
            "overlap_server_count": len(retained_server_refs),
            "overlap_satisfied": len(retained_server_refs) >= minimum_overlap_required,
            "removed_servers_require_draining": True,
            "removed_servers_draining": removed_servers_draining,
            "quorum_maintained": len(next_authority_plane.trusted_root_refs)
            >= next_authority_plane.quorum_requirement,
            "churn_detected": churn_detected,
            "status": "quorum-maintained",
        }
        checked_at = utc_now_iso()
        proof_digest = sha256_text(
            canonical_json(
                {
                    "previous_authority_plane_ref": previous_authority_plane.authority_plane_ref,
                    "next_authority_plane_ref": next_authority_plane.authority_plane_ref,
                    "retained_server_refs": retained_server_refs,
                    "added_server_refs": added_server_refs,
                    "removed_server_refs": removed_server_refs,
                    "retained_root_refs": retained_root_refs,
                    "trusted_root_refs": next_authority_plane.trusted_root_refs,
                    "continuity_guard": continuity_guard,
                }
            )
        )
        payload = {
            "churn_window_ref": (
                f"authority-churn://{next_authority_plane.council_tier}/"
                f"{sha256_text(f'{previous_authority_plane.authority_plane_ref}:{next_authority_plane.authority_plane_ref}')[:16]}"
            ),
            "checked_at": checked_at,
            "council_tier": next_authority_plane.council_tier,
            "transport_profile": next_authority_plane.transport_profile,
            "churn_profile": AUTHORITY_CHURN_PROFILE,
            "key_epoch": next_authority_plane.key_epoch,
            "directory_ref": next_authority_plane.directory_ref,
            "directory_digest": next_authority_plane.directory_digest,
            "previous_authority_plane_ref": previous_authority_plane.authority_plane_ref,
            "next_authority_plane_ref": next_authority_plane.authority_plane_ref,
            "quorum_requirement": next_authority_plane.quorum_requirement,
            "trusted_root_refs": list(next_authority_plane.trusted_root_refs),
            "retained_server_refs": retained_server_refs,
            "added_server_refs": added_server_refs,
            "removed_server_refs": removed_server_refs,
            "draining_server_refs": draining_server_refs,
            "retained_root_refs": retained_root_refs,
            "added_root_refs": added_root_refs,
            "removed_root_refs": removed_root_refs,
            "server_transitions": server_transitions,
            "continuity_guard": continuity_guard,
            "proof_digest": proof_digest,
        }
        digest = sha256_text(canonical_json(payload))
        return DistributedTransportAuthorityChurnWindow(
            churn_window_ref=payload["churn_window_ref"],
            checked_at=checked_at,
            council_tier=next_authority_plane.council_tier,
            transport_profile=next_authority_plane.transport_profile,
            churn_profile=AUTHORITY_CHURN_PROFILE,
            key_epoch=next_authority_plane.key_epoch,
            directory_ref=next_authority_plane.directory_ref,
            directory_digest=next_authority_plane.directory_digest,
            previous_authority_plane_ref=previous_authority_plane.authority_plane_ref,
            next_authority_plane_ref=next_authority_plane.authority_plane_ref,
            quorum_requirement=next_authority_plane.quorum_requirement,
            trusted_root_refs=list(next_authority_plane.trusted_root_refs),
            retained_server_refs=retained_server_refs,
            added_server_refs=added_server_refs,
            removed_server_refs=removed_server_refs,
            draining_server_refs=draining_server_refs,
            retained_root_refs=retained_root_refs,
            added_root_refs=added_root_refs,
            removed_root_refs=removed_root_refs,
            server_transitions=server_transitions,
            continuity_guard=continuity_guard,
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

    def trace_non_loopback_authority_routes(
        self,
        envelope: DistributedTransportEnvelope,
        authority_plane: DistributedTransportAuthorityPlane,
        *,
        route_targets: List[Dict[str, Any]],
        ca_cert_path: str,
        ca_bundle_ref: str,
        client_cert_path: str,
        client_key_path: str,
        client_certificate_ref: str,
        request_timeout_ms: int = 1_000,
    ) -> DistributedTransportAuthorityRouteTrace:
        if authority_plane.council_tier != envelope.council_tier:
            raise ValueError("authority route trace authority_plane council_tier must match envelope")
        if authority_plane.transport_profile != envelope.transport_profile:
            raise ValueError("authority route trace authority_plane transport_profile must match envelope")

        normalized_targets = self._normalize_route_targets(route_targets)
        authority_server_map = {
            server["key_server_ref"]: dict(server) for server in authority_plane.key_servers
        }
        if sorted(normalized_targets) != sorted(authority_server_map):
            raise ValueError("authority route trace must cover every reachable authority-plane key server")
        authority_cluster_refs = sorted(
            {target["authority_cluster_ref"] for target in normalized_targets.values()}
        )
        if len(authority_cluster_refs) != 1:
            raise ValueError(
                "authority route trace route_targets must belong to exactly 1 authority_cluster_ref"
            )
        authority_cluster_ref = authority_cluster_refs[0]

        timeout_ms = self._require_positive_int(request_timeout_ms, "request_timeout_ms")
        ca_path = self._require_non_empty_string(ca_cert_path, "ca_cert_path")
        client_cert = self._require_non_empty_string(client_cert_path, "client_cert_path")
        client_key = self._require_non_empty_string(client_key_path, "client_key_path")
        normalized_ca_ref = self._require_non_empty_string(ca_bundle_ref, "ca_bundle_ref")
        normalized_client_ref = self._require_non_empty_string(
            client_certificate_ref,
            "client_certificate_ref",
        )
        client_fingerprint = self._certificate_fingerprint_from_pem_file(client_cert)
        tls_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ca_path)
        tls_context.load_cert_chain(client_cert, client_key)

        route_bindings: List[Dict[str, Any]] = []
        connect_total = 0.0
        handshake_total = 0.0
        round_trip_total = 0.0

        for key_server_ref, target in normalized_targets.items():
            authority_server = authority_server_map[key_server_ref]
            server_endpoint = target["server_endpoint"]
            server_name = target["server_name"]
            remote_host_ref = target["remote_host_ref"]
            remote_host_attestation_ref = target["remote_host_attestation_ref"]
            remote_jurisdiction = target["remote_jurisdiction"]
            remote_network_zone = target["remote_network_zone"]
            parsed_endpoint = urlsplit(server_endpoint)
            if parsed_endpoint.scheme != "https":
                raise ValueError("authority route trace endpoints must use https://")
            if not parsed_endpoint.hostname or parsed_endpoint.port is None:
                raise ValueError("authority route trace endpoints must include host and port")
            path = parsed_endpoint.path or "/"
            if parsed_endpoint.query:
                path = f"{path}?{parsed_endpoint.query}"

            connect_started = time.monotonic()
            raw_socket = socket.create_connection(
                (parsed_endpoint.hostname, parsed_endpoint.port),
                timeout=timeout_ms / 1000.0,
            )
            local_ip, local_port = raw_socket.getsockname()
            remote_ip, remote_port = raw_socket.getpeername()
            connect_latency_ms = round((time.monotonic() - connect_started) * 1000.0, 3)

            handshake_started = time.monotonic()
            tls_socket = tls_context.wrap_socket(raw_socket, server_hostname=server_name)
            handshake_latency_ms = round((time.monotonic() - handshake_started) * 1000.0, 3)
            route_started = time.monotonic()
            request_bytes = f"GET {path} HTTP/1.1\r\nHost: {server_name}\r\nConnection: close\r\nAccept: application/json\r\n\r\n".encode(
                "utf-8"
            )
            tls_socket.sendall(request_bytes)
            os_observer_receipt = self._capture_os_observer_receipt(
                local_ip=local_ip,
                local_port=local_port,
                remote_ip=remote_ip,
                remote_port=remote_port,
                remote_host_ref=remote_host_ref,
                remote_host_attestation_ref=remote_host_attestation_ref,
                authority_cluster_ref=authority_cluster_ref,
            )
            response_bytes = b""
            while True:
                chunk = tls_socket.recv(4096)
                if not chunk:
                    break
                response_bytes += chunk
            round_trip_latency_ms = round((time.monotonic() - route_started) * 1000.0, 3)
            peer_cert = tls_socket.getpeercert(binary_form=True)
            cipher_suite = tls_socket.cipher()
            tls_version = tls_socket.version()
            tls_socket.close()

            http_status, payload = self._parse_http_json_response(response_bytes)
            response_digest = sha256_text(canonical_json(payload))
            response_digest_bound = response_digest == authority_server["response_digest"]
            non_loopback = (
                not ipaddress.ip_address(local_ip).is_loopback
                and not ipaddress.ip_address(remote_ip).is_loopback
            )
            mtls_status = (
                "authenticated"
                if http_status == 200 and response_digest_bound and peer_cert and non_loopback
                else "rejected"
            )
            route_binding_ref = (
                f"authority-route://{authority_plane.council_tier}/"
                f"{sha256_text(f'{authority_plane.authority_plane_ref}:{key_server_ref}:{server_endpoint}')[:16]}"
            )
            route_bindings.append(
                {
                    "key_server_ref": key_server_ref,
                    "server_role": authority_server["server_role"],
                    "authority_status": authority_server["authority_status"],
                    "server_endpoint": server_endpoint,
                    "server_name": server_name,
                    "remote_host_ref": remote_host_ref,
                    "remote_host_attestation_ref": remote_host_attestation_ref,
                    "authority_cluster_ref": authority_cluster_ref,
                    "remote_jurisdiction": remote_jurisdiction,
                    "remote_network_zone": remote_network_zone,
                    "route_binding_ref": route_binding_ref,
                    "matched_root_refs": list(authority_server["matched_root_refs"]),
                    "mtls_status": mtls_status,
                    "response_digest_bound": response_digest_bound,
                    "os_observer_receipt": os_observer_receipt,
                    "socket_trace": {
                        "local_ip": local_ip,
                        "local_port": local_port,
                        "remote_ip": remote_ip,
                        "remote_port": remote_port,
                        "non_loopback": non_loopback,
                        "transport_profile": AUTHORITY_ROUTE_SOCKET_PROFILE,
                        "tls_version": tls_version or "",
                        "cipher_suite": cipher_suite[0] if cipher_suite else "",
                        "peer_certificate_fingerprint": hashlib.sha256(peer_cert).hexdigest()
                        if peer_cert
                        else "",
                        "client_certificate_fingerprint": client_fingerprint,
                        "request_bytes": len(request_bytes),
                        "response_bytes": len(response_bytes),
                        "http_status": http_status,
                        "response_digest": response_digest,
                        "connect_latency_ms": connect_latency_ms,
                        "tls_handshake_latency_ms": handshake_latency_ms,
                        "round_trip_latency_ms": round_trip_latency_ms,
                    },
                }
            )
            connect_total += connect_latency_ms
            handshake_total += handshake_latency_ms
            round_trip_total += round_trip_latency_ms

        recorded_at = utc_now_iso()
        route_count = len(route_bindings)
        distinct_remote_host_count = len(
            {binding["remote_host_ref"] for binding in route_bindings}
        )
        mtls_authenticated_count = sum(
            1 for binding in route_bindings if binding["mtls_status"] == "authenticated"
        )
        non_loopback_verified = all(binding["socket_trace"]["non_loopback"] for binding in route_bindings)
        authority_plane_bound = all(
            binding["server_role"] == authority_server_map[binding["key_server_ref"]]["server_role"]
            and binding["authority_status"]
            == authority_server_map[binding["key_server_ref"]]["authority_status"]
            and binding["matched_root_refs"]
            == authority_server_map[binding["key_server_ref"]]["matched_root_refs"]
            for binding in route_bindings
        )
        response_digest_bound = all(binding["response_digest_bound"] for binding in route_bindings)
        socket_trace_complete = all(
            binding["socket_trace"]["tls_version"]
            and binding["socket_trace"]["cipher_suite"]
            and binding["socket_trace"]["peer_certificate_fingerprint"]
            and binding["socket_trace"]["client_certificate_fingerprint"]
            and binding["socket_trace"]["http_status"] == 200
            for binding in route_bindings
        )
        os_observer_complete = all(
            binding["os_observer_receipt"]["receipt_status"] == "observed"
            and binding["os_observer_receipt"]["observed_sources"]
            and binding["os_observer_receipt"]["connection_states"]
            and binding["os_observer_receipt"]["remote_host_ref"] == binding["remote_host_ref"]
            and binding["os_observer_receipt"]["remote_host_attestation_ref"]
            == binding["remote_host_attestation_ref"]
            and binding["os_observer_receipt"]["authority_cluster_ref"]
            == binding["authority_cluster_ref"]
            for binding in route_bindings
        )
        cross_host_verified = (
            distinct_remote_host_count == route_count
            and route_count >= 2
            and all(binding["remote_host_attestation_ref"] for binding in route_bindings)
        )
        trace_status = (
            "authenticated"
            if route_count == len(authority_plane.key_servers)
            and mtls_authenticated_count == route_count
            and non_loopback_verified
            and authority_plane_bound
            and response_digest_bound
            and socket_trace_complete
            and os_observer_complete
            else "rejected"
        )
        payload = {
            "trace_ref": f"authority-route-trace://{authority_plane.council_tier}/{authority_plane.authority_plane_ref.split('/')[-1]}",
            "authority_plane_ref": authority_plane.authority_plane_ref,
            "authority_plane_digest": authority_plane.digest,
            "envelope_ref": envelope.envelope_id,
            "envelope_digest": envelope.envelope_digest,
            "council_tier": envelope.council_tier,
            "transport_profile": envelope.transport_profile,
            "trace_profile": AUTHORITY_ROUTE_TRACE_PROFILE,
            "socket_trace_profile": AUTHORITY_ROUTE_SOCKET_PROFILE,
            "os_observer_profile": AUTHORITY_ROUTE_OS_OBSERVER_PROFILE,
            "cross_host_binding_profile": AUTHORITY_ROUTE_CROSS_HOST_PROFILE,
            "ca_bundle_ref": normalized_ca_ref,
            "client_certificate_ref": normalized_client_ref,
            "server_name": route_bindings[0]["server_name"],
            "authority_cluster_ref": authority_cluster_ref,
            "route_count": route_count,
            "distinct_remote_host_count": distinct_remote_host_count,
            "mtls_authenticated_count": mtls_authenticated_count,
            "trusted_root_refs": list(authority_plane.trusted_root_refs),
            "non_loopback_verified": non_loopback_verified,
            "authority_plane_bound": authority_plane_bound,
            "response_digest_bound": response_digest_bound,
            "socket_trace_complete": socket_trace_complete,
            "os_observer_complete": os_observer_complete,
            "cross_host_verified": cross_host_verified,
            "route_bindings": route_bindings,
            "trace_status": trace_status,
            "recorded_at": recorded_at,
            "total_connect_latency_ms": round(connect_total, 3),
            "total_handshake_latency_ms": round(handshake_total, 3),
            "total_round_trip_latency_ms": round(round_trip_total, 3),
        }
        digest = sha256_text(canonical_json(payload))
        return DistributedTransportAuthorityRouteTrace(
            trace_ref=payload["trace_ref"],
            authority_plane_ref=authority_plane.authority_plane_ref,
            authority_plane_digest=authority_plane.digest,
            envelope_ref=envelope.envelope_id,
            envelope_digest=envelope.envelope_digest,
            council_tier=envelope.council_tier,
            transport_profile=envelope.transport_profile,
            trace_profile=AUTHORITY_ROUTE_TRACE_PROFILE,
            socket_trace_profile=AUTHORITY_ROUTE_SOCKET_PROFILE,
            os_observer_profile=AUTHORITY_ROUTE_OS_OBSERVER_PROFILE,
            cross_host_binding_profile=AUTHORITY_ROUTE_CROSS_HOST_PROFILE,
            ca_bundle_ref=normalized_ca_ref,
            client_certificate_ref=normalized_client_ref,
            server_name=payload["server_name"],
            authority_cluster_ref=authority_cluster_ref,
            route_count=route_count,
            distinct_remote_host_count=distinct_remote_host_count,
            mtls_authenticated_count=mtls_authenticated_count,
            trusted_root_refs=list(authority_plane.trusted_root_refs),
            non_loopback_verified=non_loopback_verified,
            authority_plane_bound=authority_plane_bound,
            response_digest_bound=response_digest_bound,
            socket_trace_complete=socket_trace_complete,
            os_observer_complete=os_observer_complete,
            cross_host_verified=cross_host_verified,
            route_bindings=route_bindings,
            trace_status=trace_status,
            recorded_at=recorded_at,
            total_connect_latency_ms=payload["total_connect_latency_ms"],
            total_handshake_latency_ms=payload["total_handshake_latency_ms"],
            total_round_trip_latency_ms=payload["total_round_trip_latency_ms"],
            digest=digest,
        )

    def export_authority_route_packet_capture(
        self,
        authority_route_trace: DistributedTransportAuthorityRouteTrace,
    ) -> DistributedTransportPacketCaptureExport:
        if authority_route_trace.trace_status != "authenticated":
            raise ValueError("packet capture export requires an authenticated authority route trace")

        pcap_bytes, route_exports = self._build_authority_route_pcap(authority_route_trace)
        artifact_digest = hashlib.sha256(pcap_bytes).hexdigest()
        artifact_size_bytes = len(pcap_bytes)
        readback_packets = self._readback_authority_route_pcap(pcap_bytes)

        for route_export in route_exports:
            outbound = [
                packet
                for packet in readback_packets
                if packet["tuple_digest"] == route_export["outbound_tuple_digest"]
            ]
            inbound = [
                packet
                for packet in readback_packets
                if packet["tuple_digest"] == route_export["inbound_tuple_digest"]
            ]
            route_export["readback_packet_count"] = len(outbound) + len(inbound)
            route_export["readback_verified"] = (
                len(outbound) == 1
                and len(inbound) == 1
                and outbound[0]["payload_length"] == route_export["outbound_request_bytes"]
                and inbound[0]["payload_length"] == route_export["inbound_response_bytes"]
            )

        os_native_readback = self._run_tcpdump_readback(
            pcap_bytes=pcap_bytes,
            route_exports=route_exports,
        )
        os_native_readback_ok = os_native_readback["available"] and os_native_readback["verified"]
        readback_payload = {
            "packets": readback_packets,
            "route_exports": route_exports,
            "os_native_readback": os_native_readback,
        }
        readback_digest = sha256_text(canonical_json(readback_payload))
        export_status = (
            "verified"
            if all(route_export["readback_verified"] for route_export in route_exports)
            and (not os_native_readback["available"] or os_native_readback["verified"])
            else "rejected"
        )
        recorded_at = utc_now_iso()
        payload = {
            "capture_ref": (
                "authority-packet-capture://"
                f"{authority_route_trace.council_tier}/{authority_route_trace.trace_ref.split('/')[-1]}"
            ),
            "trace_ref": authority_route_trace.trace_ref,
            "trace_digest": authority_route_trace.digest,
            "authority_plane_ref": authority_route_trace.authority_plane_ref,
            "authority_plane_digest": authority_route_trace.authority_plane_digest,
            "envelope_ref": authority_route_trace.envelope_ref,
            "envelope_digest": authority_route_trace.envelope_digest,
            "council_tier": authority_route_trace.council_tier,
            "transport_profile": authority_route_trace.transport_profile,
            "capture_profile": AUTHORITY_ROUTE_PCAP_EXPORT_PROFILE,
            "artifact_format": AUTHORITY_ROUTE_PCAP_ARTIFACT_FORMAT,
            "readback_profile": AUTHORITY_ROUTE_PCAP_READBACK_PROFILE,
            "os_native_readback_profile": AUTHORITY_ROUTE_PCAP_OS_NATIVE_PROFILE,
            "route_count": authority_route_trace.route_count,
            "packet_count": len(readback_packets),
            "artifact_size_bytes": artifact_size_bytes,
            "artifact_digest": artifact_digest,
            "readback_digest": readback_digest,
            "route_exports": route_exports,
            "os_native_readback_available": os_native_readback["available"],
            "os_native_readback_ok": os_native_readback_ok,
            "export_status": export_status,
            "recorded_at": recorded_at,
        }
        digest = sha256_text(canonical_json(payload))
        return DistributedTransportPacketCaptureExport(
            capture_ref=payload["capture_ref"],
            trace_ref=authority_route_trace.trace_ref,
            trace_digest=authority_route_trace.digest,
            authority_plane_ref=authority_route_trace.authority_plane_ref,
            authority_plane_digest=authority_route_trace.authority_plane_digest,
            envelope_ref=authority_route_trace.envelope_ref,
            envelope_digest=authority_route_trace.envelope_digest,
            council_tier=authority_route_trace.council_tier,
            transport_profile=authority_route_trace.transport_profile,
            capture_profile=AUTHORITY_ROUTE_PCAP_EXPORT_PROFILE,
            artifact_format=AUTHORITY_ROUTE_PCAP_ARTIFACT_FORMAT,
            readback_profile=AUTHORITY_ROUTE_PCAP_READBACK_PROFILE,
            os_native_readback_profile=AUTHORITY_ROUTE_PCAP_OS_NATIVE_PROFILE,
            route_count=authority_route_trace.route_count,
            packet_count=payload["packet_count"],
            artifact_size_bytes=artifact_size_bytes,
            artifact_digest=artifact_digest,
            readback_digest=readback_digest,
            route_exports=route_exports,
            os_native_readback_available=os_native_readback["available"],
            os_native_readback_ok=os_native_readback_ok,
            export_status=export_status,
            recorded_at=recorded_at,
            digest=digest,
        )

    def acquire_privileged_interface_capture(
        self,
        authority_route_trace: DistributedTransportAuthorityRouteTrace,
        packet_capture_export: DistributedTransportPacketCaptureExport,
        *,
        broker_command: List[str],
        lease_duration_s: int = 300,
    ) -> DistributedTransportPrivilegedCaptureAcquisition:
        if authority_route_trace.trace_status != "authenticated":
            raise ValueError("privileged capture acquisition requires an authenticated authority route trace")
        if packet_capture_export.export_status != "verified":
            raise ValueError("privileged capture acquisition requires a verified packet capture export")
        if packet_capture_export.trace_ref != authority_route_trace.trace_ref:
            raise ValueError("privileged capture acquisition capture trace_ref must match authority route trace")
        if packet_capture_export.trace_digest != authority_route_trace.digest:
            raise ValueError("privileged capture acquisition capture trace_digest must match authority route trace")
        if packet_capture_export.authority_plane_ref != authority_route_trace.authority_plane_ref:
            raise ValueError(
                "privileged capture acquisition capture authority_plane_ref must match authority route trace"
            )
        if packet_capture_export.authority_plane_digest != authority_route_trace.authority_plane_digest:
            raise ValueError(
                "privileged capture acquisition capture authority_plane_digest must match authority route trace"
            )
        if packet_capture_export.envelope_ref != authority_route_trace.envelope_ref:
            raise ValueError("privileged capture acquisition capture envelope_ref must match authority route trace")
        if packet_capture_export.envelope_digest != authority_route_trace.envelope_digest:
            raise ValueError(
                "privileged capture acquisition capture envelope_digest must match authority route trace"
            )

        broker_argv = self._normalize_string_sequence(broker_command, "broker_command")
        lease_duration = self._require_positive_int(lease_duration_s, "lease_duration_s")
        local_ips = sorted(
            {
                self._require_non_empty_string(binding["socket_trace"].get("local_ip"), "local_ip")
                for binding in authority_route_trace.route_bindings
            }
        )
        interface_names = sorted({self._discover_interface_for_ip(local_ip) for local_ip in local_ips})
        if len(interface_names) != 1:
            raise ValueError(
                "privileged capture acquisition requires all traced local IPs to resolve to one interface"
            )
        interface_name = interface_names[0]
        capture_filter = self._build_authority_route_capture_filter(authority_route_trace)
        filter_digest = sha256_text(capture_filter)
        route_binding_refs = sorted(
            self._require_non_empty_string(binding.get("route_binding_ref"), "route_binding_ref")
            for binding in authority_route_trace.route_bindings
        )
        tcpdump_path = shutil.which("tcpdump")
        if not tcpdump_path:
            raise ValueError("privileged capture acquisition requires tcpdump on PATH")
        request_payload = {
            "trace_ref": authority_route_trace.trace_ref,
            "trace_digest": authority_route_trace.digest,
            "capture_ref": packet_capture_export.capture_ref,
            "capture_digest": packet_capture_export.digest,
            "authority_plane_ref": authority_route_trace.authority_plane_ref,
            "authority_plane_digest": authority_route_trace.authority_plane_digest,
            "envelope_ref": authority_route_trace.envelope_ref,
            "envelope_digest": authority_route_trace.envelope_digest,
            "council_tier": authority_route_trace.council_tier,
            "transport_profile": authority_route_trace.transport_profile,
            "tcpdump_path": tcpdump_path,
            "requested_interface": interface_name,
            "local_ips": local_ips,
            "capture_filter": capture_filter,
            "filter_digest": filter_digest,
            "route_binding_refs": route_binding_refs,
            "lease_duration_s": lease_duration,
        }
        broker_result = subprocess.run(
            broker_argv,
            input=canonical_json(request_payload),
            capture_output=True,
            text=True,
            check=False,
            errors="replace",
        )
        if broker_result.returncode != 0:
            raise ValueError("privileged capture acquisition broker command failed")
        try:
            broker_payload = json.loads(broker_result.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError("privileged capture acquisition broker must return JSON") from exc
        if not isinstance(broker_payload, Mapping):
            raise ValueError("privileged capture acquisition broker payload must be a mapping")

        broker_profile = self._require_non_empty_string(
            broker_payload.get("broker_profile"),
            "broker_profile",
        )
        privilege_mode = self._require_non_empty_string(
            broker_payload.get("privilege_mode"),
            "privilege_mode",
        )
        lease_ref = self._require_non_empty_string(broker_payload.get("lease_ref"), "lease_ref")
        broker_attestation_ref = self._require_non_empty_string(
            broker_payload.get("broker_attestation_ref"),
            "broker_attestation_ref",
        )
        approved_interface = self._require_non_empty_string(
            broker_payload.get("approved_interface"),
            "approved_interface",
        )
        if approved_interface != interface_name:
            raise ValueError("privileged capture acquisition broker must echo the resolved interface")
        approved_filter_digest = self._require_sha256_hex(
            broker_payload.get("approved_filter_digest"),
            "approved_filter_digest",
        )
        if approved_filter_digest != filter_digest:
            raise ValueError("privileged capture acquisition broker must echo the capture filter digest")
        approved_route_binding_refs = sorted(
            self._normalize_string_list(
                broker_payload.get("route_binding_refs"),
                "route_binding_refs",
            )
        )
        if approved_route_binding_refs != route_binding_refs:
            raise ValueError("privileged capture acquisition broker must bind every traced route")
        capture_command = self._normalize_string_sequence(
            broker_payload.get("capture_command"),
            "capture_command",
        )
        if capture_command[0] != tcpdump_path:
            raise ValueError("privileged capture acquisition capture_command must start with tcpdump")
        if interface_name not in capture_command:
            raise ValueError("privileged capture acquisition capture_command must bind the resolved interface")
        if capture_filter not in capture_command:
            raise ValueError("privileged capture acquisition capture_command must bind the capture filter")
        grant_status = self._require_non_empty_string(broker_payload.get("grant_status"), "grant_status")
        if grant_status not in {"granted", "rejected"}:
            raise ValueError("grant_status must be granted or rejected")
        lease_expires_at = self._require_non_empty_string(
            broker_payload.get("lease_expires_at"),
            "lease_expires_at",
        )

        recorded_at = utc_now_iso()
        payload = {
            "acquisition_ref": (
                "authority-live-capture://"
                f"{authority_route_trace.council_tier}/{authority_route_trace.trace_ref.split('/')[-1]}"
            ),
            "trace_ref": authority_route_trace.trace_ref,
            "trace_digest": authority_route_trace.digest,
            "capture_ref": packet_capture_export.capture_ref,
            "capture_digest": packet_capture_export.digest,
            "authority_plane_ref": authority_route_trace.authority_plane_ref,
            "authority_plane_digest": authority_route_trace.authority_plane_digest,
            "envelope_ref": authority_route_trace.envelope_ref,
            "envelope_digest": authority_route_trace.envelope_digest,
            "council_tier": authority_route_trace.council_tier,
            "transport_profile": authority_route_trace.transport_profile,
            "acquisition_profile": PRIVILEGED_CAPTURE_ACQUISITION_PROFILE,
            "broker_profile": broker_profile,
            "privilege_mode": privilege_mode,
            "lease_ref": lease_ref,
            "broker_attestation_ref": broker_attestation_ref,
            "interface_name": interface_name,
            "local_ips": local_ips,
            "capture_filter": capture_filter,
            "filter_digest": filter_digest,
            "route_binding_refs": route_binding_refs,
            "capture_command": capture_command,
            "lease_duration_s": lease_duration,
            "lease_expires_at": lease_expires_at,
            "grant_status": grant_status,
            "recorded_at": recorded_at,
        }
        digest = sha256_text(canonical_json(payload))
        return DistributedTransportPrivilegedCaptureAcquisition(
            acquisition_ref=payload["acquisition_ref"],
            trace_ref=authority_route_trace.trace_ref,
            trace_digest=authority_route_trace.digest,
            capture_ref=packet_capture_export.capture_ref,
            capture_digest=packet_capture_export.digest,
            authority_plane_ref=authority_route_trace.authority_plane_ref,
            authority_plane_digest=authority_route_trace.authority_plane_digest,
            envelope_ref=authority_route_trace.envelope_ref,
            envelope_digest=authority_route_trace.envelope_digest,
            council_tier=authority_route_trace.council_tier,
            transport_profile=authority_route_trace.transport_profile,
            acquisition_profile=PRIVILEGED_CAPTURE_ACQUISITION_PROFILE,
            broker_profile=broker_profile,
            privilege_mode=privilege_mode,
            lease_ref=lease_ref,
            broker_attestation_ref=broker_attestation_ref,
            interface_name=interface_name,
            local_ips=local_ips,
            capture_filter=capture_filter,
            filter_digest=filter_digest,
            route_binding_refs=route_binding_refs,
            capture_command=capture_command,
            lease_duration_s=lease_duration,
            lease_expires_at=lease_expires_at,
            grant_status=grant_status,
            recorded_at=recorded_at,
            digest=digest,
        )

    def _capture_os_observer_receipt(
        self,
        *,
        local_ip: str,
        local_port: int,
        remote_ip: str,
        remote_port: int,
        remote_host_ref: str,
        remote_host_attestation_ref: str,
        authority_cluster_ref: str,
    ) -> Dict[str, Any]:
        observed_sources: set[str] = set()
        connection_states: set[str] = set()
        local_netstat = f"{local_ip}.{local_port}"
        remote_netstat = f"{remote_ip}.{remote_port}"
        local_lsof = f"{local_ip}:{local_port}"
        remote_lsof = f"{remote_ip}:{remote_port}"
        owning_pid = os.getpid()

        netstat_path = shutil.which("netstat")
        if netstat_path:
            observed, states = self._capture_netstat_observer(
                netstat_path=netstat_path,
                local_endpoint=local_netstat,
                remote_endpoint=remote_netstat,
            )
            if observed:
                observed_sources.add("netstat")
                connection_states.update(states)

        lsof_path = shutil.which("lsof")
        if lsof_path:
            observed, states = self._capture_lsof_observer(
                lsof_path=lsof_path,
                local_endpoint=local_lsof,
                remote_endpoint=remote_lsof,
                owning_pid=owning_pid,
            )
            if observed:
                observed_sources.add("lsof")
                connection_states.update(states)

        receipt_status = "observed" if observed_sources else "missing"
        tuple_payload = f"{local_ip}:{local_port}->{remote_ip}:{remote_port}"
        host_binding_digest = sha256_text(
            canonical_json(
                {
                    "authority_cluster_ref": authority_cluster_ref,
                    "remote_host_ref": remote_host_ref,
                    "remote_host_attestation_ref": remote_host_attestation_ref,
                    "tuple_digest": sha256_text(tuple_payload),
                }
            )
        )
        return {
            "kind": "distributed_transport_os_observer_receipt",
            "schema_version": "1.0.0",
            "receipt_id": (
                "authority-os-observer://"
                f"{sha256_text(tuple_payload)[:16]}"
            ),
            "observer_profile": AUTHORITY_ROUTE_OS_OBSERVER_PROFILE,
            "observed_at": utc_now_iso(),
            "local_ip": local_ip,
            "local_port": local_port,
            "remote_ip": remote_ip,
            "remote_port": remote_port,
            "remote_host_ref": remote_host_ref,
            "remote_host_attestation_ref": remote_host_attestation_ref,
            "authority_cluster_ref": authority_cluster_ref,
            "owning_pid": owning_pid,
            "observed_sources": sorted(observed_sources),
            "connection_states": sorted(connection_states),
            "tuple_digest": sha256_text(tuple_payload),
            "host_binding_digest": host_binding_digest,
            "receipt_status": receipt_status,
        }

    def _build_authority_route_pcap(
        self,
        authority_route_trace: DistributedTransportAuthorityRouteTrace,
    ) -> tuple[bytes, List[Dict[str, Any]]]:
        packet_records: List[bytes] = []
        route_exports: List[Dict[str, Any]] = []
        ts_sec = int(time.time())
        ts_usec = 0
        packet_index = 0

        for binding in authority_route_trace.route_bindings:
            socket_trace = dict(binding["socket_trace"])
            local_ip = self._require_non_empty_string(socket_trace.get("local_ip"), "local_ip")
            remote_ip = self._require_non_empty_string(socket_trace.get("remote_ip"), "remote_ip")
            local_port = self._require_positive_int(socket_trace.get("local_port"), "local_port")
            remote_port = self._require_positive_int(socket_trace.get("remote_port"), "remote_port")
            request_length = self._require_positive_int(
                socket_trace.get("request_bytes"),
                "request_bytes",
            )
            response_length = self._require_positive_int(
                socket_trace.get("response_bytes"),
                "response_bytes",
            )
            route_binding_ref = self._require_non_empty_string(
                binding.get("route_binding_ref"),
                "route_binding_ref",
            )
            response_digest = self._require_sha256_hex(
                socket_trace.get("response_digest"),
                "response_digest",
            )
            outbound_tuple_digest = sha256_text(f"{local_ip}:{local_port}->{remote_ip}:{remote_port}")
            inbound_tuple_digest = sha256_text(f"{remote_ip}:{remote_port}->{local_ip}:{local_port}")
            outbound_payload = self._deterministic_packet_payload(
                seed=f"{route_binding_ref}:request",
                length=request_length,
            )
            inbound_payload = self._deterministic_packet_payload(
                seed=f"{response_digest}:response",
                length=response_length,
            )
            outbound_packet = self._build_ipv4_tcp_packet(
                src_ip=local_ip,
                dst_ip=remote_ip,
                src_port=local_port,
                dst_port=remote_port,
                payload=outbound_payload,
                sequence_number=1,
                acknowledgement_number=1,
                packet_id=packet_index + 1,
            )
            packet_records.append(
                self._build_pcap_record(
                    packet=outbound_packet,
                    ts_sec=ts_sec,
                    ts_usec=ts_usec,
                )
            )
            packet_index += 1
            ts_usec += 1
            inbound_packet = self._build_ipv4_tcp_packet(
                src_ip=remote_ip,
                dst_ip=local_ip,
                src_port=remote_port,
                dst_port=local_port,
                payload=inbound_payload,
                sequence_number=1,
                acknowledgement_number=request_length + 1,
                packet_id=packet_index + 1,
            )
            packet_records.append(
                self._build_pcap_record(
                    packet=inbound_packet,
                    ts_sec=ts_sec,
                    ts_usec=ts_usec,
                )
            )
            packet_index += 1
            ts_usec += 1
            route_exports.append(
                {
                    "key_server_ref": binding["key_server_ref"],
                    "route_binding_ref": route_binding_ref,
                    "local_ip": local_ip,
                    "local_port": local_port,
                    "remote_ip": remote_ip,
                    "remote_port": remote_port,
                    "outbound_tuple_digest": outbound_tuple_digest,
                    "inbound_tuple_digest": inbound_tuple_digest,
                    "packet_order": ["outbound-request", "inbound-response"],
                    "outbound_request_bytes": request_length,
                    "inbound_response_bytes": response_length,
                    "outbound_payload_digest": hashlib.sha256(outbound_payload).hexdigest(),
                    "inbound_payload_digest": hashlib.sha256(inbound_payload).hexdigest(),
                    "readback_packet_count": 0,
                    "readback_verified": False,
                }
            )

        global_header = struct.pack(
            "<IHHIIII",
            0xA1B2C3D4,
            2,
            4,
            0,
            0,
            65535,
            101,
        )
        return global_header + b"".join(packet_records), route_exports

    @staticmethod
    def _deterministic_packet_payload(*, seed: str, length: int) -> bytes:
        digest = hashlib.sha256(seed.encode("utf-8")).digest()
        repeats = (length // len(digest)) + 1
        return (digest * repeats)[:length]

    @staticmethod
    def _build_pcap_record(*, packet: bytes, ts_sec: int, ts_usec: int) -> bytes:
        header = struct.pack("<IIII", ts_sec, ts_usec, len(packet), len(packet))
        return header + packet

    @classmethod
    def _build_ipv4_tcp_packet(
        cls,
        *,
        src_ip: str,
        dst_ip: str,
        src_port: int,
        dst_port: int,
        payload: bytes,
        sequence_number: int,
        acknowledgement_number: int,
        packet_id: int,
    ) -> bytes:
        src_ip_bytes = socket.inet_aton(src_ip)
        dst_ip_bytes = socket.inet_aton(dst_ip)
        tcp_header = cls._build_tcp_header(
            src_ip_bytes=src_ip_bytes,
            dst_ip_bytes=dst_ip_bytes,
            src_port=src_port,
            dst_port=dst_port,
            sequence_number=sequence_number,
            acknowledgement_number=acknowledgement_number,
            payload=payload,
        )
        total_length = 20 + len(tcp_header) + len(payload)
        version_ihl = (4 << 4) | 5
        ip_header_without_checksum = struct.pack(
            "!BBHHHBBH4s4s",
            version_ihl,
            0,
            total_length,
            packet_id & 0xFFFF,
            0,
            64,
            socket.IPPROTO_TCP,
            0,
            src_ip_bytes,
            dst_ip_bytes,
        )
        ip_checksum = cls._internet_checksum(ip_header_without_checksum)
        ip_header = struct.pack(
            "!BBHHHBBH4s4s",
            version_ihl,
            0,
            total_length,
            packet_id & 0xFFFF,
            0,
            64,
            socket.IPPROTO_TCP,
            ip_checksum,
            src_ip_bytes,
            dst_ip_bytes,
        )
        return ip_header + tcp_header + payload

    @classmethod
    def _build_tcp_header(
        cls,
        *,
        src_ip_bytes: bytes,
        dst_ip_bytes: bytes,
        src_port: int,
        dst_port: int,
        sequence_number: int,
        acknowledgement_number: int,
        payload: bytes,
    ) -> bytes:
        data_offset = 5
        offset_reserved_flags = (data_offset << 12) | 0x018
        window_size = 65535
        urgent_pointer = 0
        tcp_header_without_checksum = struct.pack(
            "!HHIIHHHH",
            src_port,
            dst_port,
            sequence_number,
            acknowledgement_number,
            offset_reserved_flags,
            window_size,
            0,
            urgent_pointer,
        )
        tcp_length = len(tcp_header_without_checksum) + len(payload)
        pseudo_header = struct.pack(
            "!4s4sBBH",
            src_ip_bytes,
            dst_ip_bytes,
            0,
            socket.IPPROTO_TCP,
            tcp_length,
        )
        checksum = cls._internet_checksum(pseudo_header + tcp_header_without_checksum + payload)
        return struct.pack(
            "!HHIIHHHH",
            src_port,
            dst_port,
            sequence_number,
            acknowledgement_number,
            offset_reserved_flags,
            window_size,
            checksum,
            urgent_pointer,
        )

    @staticmethod
    def _internet_checksum(data: bytes) -> int:
        if len(data) % 2 == 1:
            data += b"\x00"
        total = 0
        for index in range(0, len(data), 2):
            total += (data[index] << 8) + data[index + 1]
        while total > 0xFFFF:
            total = (total & 0xFFFF) + (total >> 16)
        return (~total) & 0xFFFF

    @classmethod
    def _readback_authority_route_pcap(cls, pcap_bytes: bytes) -> List[Dict[str, Any]]:
        if len(pcap_bytes) < 24:
            raise ValueError("pcap export must include a global header")
        magic_number = struct.unpack_from("<I", pcap_bytes, 0)[0]
        if magic_number != 0xA1B2C3D4:
            raise ValueError("pcap export must use little-endian libpcap format")
        linktype = struct.unpack_from("<I", pcap_bytes, 20)[0]
        if linktype != 101:
            raise ValueError("pcap export must use raw IPv4 linktype")

        packets: List[Dict[str, Any]] = []
        offset = 24
        while offset < len(pcap_bytes):
            if offset + 16 > len(pcap_bytes):
                raise ValueError("pcap record header is truncated")
            _, _, included_length, original_length = struct.unpack_from("<IIII", pcap_bytes, offset)
            offset += 16
            packet_bytes = pcap_bytes[offset : offset + included_length]
            if len(packet_bytes) != included_length or included_length != original_length:
                raise ValueError("pcap packet payload is truncated")
            packets.append(cls._parse_ipv4_tcp_packet(packet_bytes))
            offset += included_length
        return packets

    @staticmethod
    def _parse_ipv4_tcp_packet(packet: bytes) -> Dict[str, Any]:
        if len(packet) < 40:
            raise ValueError("pcap packet must contain IPv4 and TCP headers")
        version_ihl = packet[0]
        version = version_ihl >> 4
        ihl = (version_ihl & 0x0F) * 4
        if version != 4 or ihl < 20:
            raise ValueError("pcap packet must be IPv4")
        total_length = struct.unpack("!H", packet[2:4])[0]
        protocol = packet[9]
        if protocol != socket.IPPROTO_TCP:
            raise ValueError("pcap packet must use TCP")
        src_ip = socket.inet_ntoa(packet[12:16])
        dst_ip = socket.inet_ntoa(packet[16:20])
        tcp_offset = ihl
        src_port, dst_port, _, _, offset_reserved_flags = struct.unpack(
            "!HHIIH",
            packet[tcp_offset : tcp_offset + 14],
        )
        data_offset = ((offset_reserved_flags >> 12) & 0xF) * 4
        payload_start = tcp_offset + data_offset
        payload_length = max(total_length - payload_start, 0)
        tuple_digest = sha256_text(f"{src_ip}:{src_port}->{dst_ip}:{dst_port}")
        return {
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port,
            "payload_length": payload_length,
            "tuple_digest": tuple_digest,
        }

    @classmethod
    def _run_tcpdump_readback(
        cls,
        *,
        pcap_bytes: bytes,
        route_exports: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        tcpdump_path = shutil.which("tcpdump")
        if not tcpdump_path:
            return {
                "available": False,
                "verified": False,
                "output_digest": sha256_text(""),
                "matched_line_count": 0,
            }

        with tempfile.NamedTemporaryFile(prefix="omoikane-route-capture-", suffix=".pcap") as handle:
            handle.write(pcap_bytes)
            handle.flush()
            result = subprocess.run(
                [tcpdump_path, "-nn", "-r", handle.name],
                capture_output=True,
                text=True,
                check=False,
                errors="replace",
            )
        if result.returncode != 0:
            return {
                "available": True,
                "verified": False,
                "output_digest": sha256_text(result.stdout + result.stderr),
                "matched_line_count": 0,
            }

        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        matched_line_count = 0
        for route_export in route_exports:
            outbound_pattern = (
                f"{route_export['local_ip']}.{route_export['local_port']} > "
                f"{route_export['remote_ip']}.{route_export['remote_port']}"
            )
            inbound_pattern = (
                f"{route_export['remote_ip']}.{route_export['remote_port']} > "
                f"{route_export['local_ip']}.{route_export['local_port']}"
            )
            outbound_length = route_export["outbound_request_bytes"]
            inbound_length = route_export["inbound_response_bytes"]
            outbound_matches = [
                line
                for line in lines
                if outbound_pattern in line and f"length {outbound_length}" in line
            ]
            inbound_matches = [
                line
                for line in lines
                if inbound_pattern in line and f"length {inbound_length}" in line
            ]
            route_export["os_native_readback_verified"] = (
                len(outbound_matches) == 1 and len(inbound_matches) == 1
            )
            if route_export["os_native_readback_verified"]:
                matched_line_count += 2
        return {
            "available": True,
            "verified": all(
                route_export.get("os_native_readback_verified", False)
                for route_export in route_exports
            ),
            "output_digest": sha256_text("\n".join(lines)),
            "matched_line_count": matched_line_count,
        }

    def _capture_netstat_observer(
        self,
        *,
        netstat_path: str,
        local_endpoint: str,
        remote_endpoint: str,
    ) -> tuple[bool, List[str]]:
        result = subprocess.run(
            [netstat_path, "-anv", "-p", "tcp"],
            capture_output=True,
            text=True,
            check=False,
            errors="replace",
        )
        if result.returncode != 0:
            return False, []
        states = {
            parts[-1]
            for line in result.stdout.splitlines()
            if local_endpoint in line
            and remote_endpoint in line
            and (parts := line.split())
            and parts[-1].isupper()
        }
        return bool(states), sorted(states)

    def _capture_lsof_observer(
        self,
        *,
        lsof_path: str,
        local_endpoint: str,
        remote_endpoint: str,
        owning_pid: int,
    ) -> tuple[bool, List[str]]:
        result = subprocess.run(
            [lsof_path, "-nP", "-iTCP"],
            capture_output=True,
            text=True,
            check=False,
            errors="replace",
        )
        if result.returncode not in {0, 1}:
            return False, []
        states: set[str] = set()
        for line in result.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) < 9 or parts[1] != str(owning_pid):
                continue
            name_field = " ".join(parts[8:])
            if local_endpoint not in name_field or remote_endpoint not in name_field:
                continue
            if "(" in name_field and name_field.endswith(")"):
                states.add(name_field.rsplit("(", 1)[-1][:-1])
        return bool(states), sorted(states)

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

    @classmethod
    def _normalize_string_sequence(cls, values: Any, field_name: str) -> List[str]:
        if not isinstance(values, list) or not values:
            raise ValueError(f"{field_name} must be a non-empty list")
        return [
            cls._require_non_empty_string(value, f"{field_name}[{index}]")
            for index, value in enumerate(values)
        ]

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

    @classmethod
    def _normalize_route_targets(cls, values: Any) -> Dict[str, Dict[str, str]]:
        if not isinstance(values, list) or not values:
            raise ValueError("route_targets must be a non-empty list")
        normalized: Dict[str, Dict[str, str]] = {}
        for index, value in enumerate(values):
            if not isinstance(value, Mapping):
                raise ValueError("route_targets entries must be mappings")
            key_server_ref = cls._require_non_empty_string(
                value.get("key_server_ref"),
                f"route_targets[{index}].key_server_ref",
            )
            if key_server_ref in normalized:
                raise ValueError("route_targets key_server_ref values must be unique")
            normalized[key_server_ref] = {
                "server_endpoint": cls._require_non_empty_string(
                    value.get("server_endpoint"),
                    f"route_targets[{index}].server_endpoint",
                ),
                "server_name": cls._require_non_empty_string(
                    value.get("server_name"),
                    f"route_targets[{index}].server_name",
                ),
                "remote_host_ref": cls._require_non_empty_string(
                    value.get("remote_host_ref"),
                    f"route_targets[{index}].remote_host_ref",
                ),
                "remote_host_attestation_ref": cls._require_non_empty_string(
                    value.get("remote_host_attestation_ref"),
                    f"route_targets[{index}].remote_host_attestation_ref",
                ),
                "authority_cluster_ref": cls._require_non_empty_string(
                    value.get("authority_cluster_ref"),
                    f"route_targets[{index}].authority_cluster_ref",
                ),
                "remote_jurisdiction": cls._require_non_empty_string(
                    value.get("remote_jurisdiction"),
                    f"route_targets[{index}].remote_jurisdiction",
                ),
                "remote_network_zone": cls._require_non_empty_string(
                    value.get("remote_network_zone"),
                    f"route_targets[{index}].remote_network_zone",
                ),
            }
        return normalized

    @staticmethod
    def _certificate_fingerprint_from_pem_file(path: str) -> str:
        pem_text = Path(path).read_text(encoding="utf-8")
        der_bytes = ssl.PEM_cert_to_DER_cert(pem_text)
        return hashlib.sha256(der_bytes).hexdigest()

    @classmethod
    def _parse_http_json_response(cls, response_bytes: bytes) -> tuple[int, Dict[str, Any]]:
        header_bytes, separator, body_bytes = response_bytes.partition(b"\r\n\r\n")
        if not separator:
            raise ValueError("authority route trace response must be valid HTTP")
        header_lines = header_bytes.decode("utf-8").splitlines()
        if not header_lines:
            raise ValueError("authority route trace response must include a status line")
        status_parts = header_lines[0].split()
        if len(status_parts) < 2:
            raise ValueError("authority route trace response status line is invalid")
        try:
            http_status = int(status_parts[1])
        except ValueError as exc:
            raise ValueError("authority route trace response status must be numeric") from exc
        try:
            payload = json.loads(body_bytes.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("authority route trace response body must be JSON") from exc
        if not isinstance(payload, Mapping):
            raise ValueError("authority route trace response payload must be a mapping")
        return http_status, dict(payload)

    @classmethod
    def _build_authority_route_capture_filter(
        cls,
        authority_route_trace: DistributedTransportAuthorityRouteTrace,
    ) -> str:
        clauses: List[str] = []
        for binding in authority_route_trace.route_bindings:
            socket_trace = binding.get("socket_trace")
            if not isinstance(socket_trace, Mapping):
                raise ValueError("authority route trace socket_trace must be a mapping")
            local_ip = cls._require_non_empty_string(socket_trace.get("local_ip"), "local_ip")
            remote_ip = cls._require_non_empty_string(socket_trace.get("remote_ip"), "remote_ip")
            local_port = cls._require_positive_int(socket_trace.get("local_port"), "local_port")
            remote_port = cls._require_positive_int(socket_trace.get("remote_port"), "remote_port")
            clauses.append(
                "("
                f"src host {local_ip} and src port {local_port} and "
                f"dst host {remote_ip} and dst port {remote_port}"
                ")"
            )
            clauses.append(
                "("
                f"src host {remote_ip} and src port {remote_port} and "
                f"dst host {local_ip} and dst port {local_port}"
                ")"
            )
        if not clauses:
            raise ValueError("authority route capture filter requires at least 1 traced route")
        return "tcp and (" + " or ".join(clauses) + ")"

    @classmethod
    def _discover_interface_for_ip(cls, local_ip: str) -> str:
        normalized_ip = cls._require_non_empty_string(local_ip, "local_ip")
        for _, interface_name in socket.if_nameindex():
            if cls._interface_has_ipv4(interface_name, normalized_ip):
                return interface_name
        raise ValueError(f"could not resolve a network interface for local_ip {normalized_ip}")

    @staticmethod
    def _interface_has_ipv4(interface_name: str, local_ip: str) -> bool:
        ipconfig_path = shutil.which("ipconfig")
        if ipconfig_path:
            result = subprocess.run(
                [ipconfig_path, "getifaddr", interface_name],
                capture_output=True,
                text=True,
                check=False,
                errors="replace",
            )
            if result.returncode == 0 and result.stdout.strip() == local_ip:
                return True
        ifconfig_path = shutil.which("ifconfig")
        if ifconfig_path:
            result = subprocess.run(
                [ifconfig_path, interface_name],
                capture_output=True,
                text=True,
                check=False,
                errors="replace",
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    parts = line.strip().split()
                    if len(parts) >= 2 and parts[0] == "inet" and parts[1] == local_ip:
                        return True
        ip_path = shutil.which("ip")
        if ip_path:
            result = subprocess.run(
                [ip_path, "-o", "-4", "addr", "show", "dev", interface_name],
                capture_output=True,
                text=True,
                check=False,
                errors="replace",
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if " inet " not in line:
                        continue
                    inet_part = line.split(" inet ", 1)[1].split("/", 1)[0].strip()
                    if inet_part == local_ip:
                        return True
        return False
