from __future__ import annotations

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import unittest

from omoikane.agentic.distributed_transport import DistributedTransportService
from omoikane.common import canonical_json, sha256_text
from omoikane.interface.imc import InterMindChannel
from omoikane.interface.wms import WorldModelSync


@contextmanager
def live_slo_endpoint(payload: dict[str, object]):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def do_GET(self) -> None:  # noqa: N802
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()
            self.close_connection = True

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/authority-slo"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1.0)


class WorldModelSyncTests(unittest.TestCase):
    def _time_rate_attestation_receipts(
        self,
        sync: WorldModelSync,
        session: dict,
        *,
        proposer_id: str,
        requested_time_rate: float,
    ) -> tuple[dict, list[dict]]:
        participants = session["current_state"]["participants"]
        subject = sync.build_time_rate_attestation_subject(
            session["session_id"],
            proposer_id=proposer_id,
            requested_time_rate=requested_time_rate,
        )
        imc = InterMindChannel()
        template = {
            "public_fields": [
                "time_rate_attestation_subject_digest",
                "participant_id",
                "baseline_time_rate",
                "requested_time_rate",
                "attestation_decision",
            ],
            "intimate_fields": [],
            "sealed_fields": [],
        }
        receipts = []
        for participant_id in participants:
            counterparty = participants[1] if participant_id == participants[0] else participants[0]
            imc_session = imc.open_session(
                initiator_id=counterparty,
                peer_id=participant_id,
                mode="text",
                initiator_template=template,
                peer_template=template,
                peer_attested=True,
                forward_secrecy=True,
                council_witnessed=True,
            )
            message = imc.send(
                imc_session["session_id"],
                sender_id=participant_id,
                summary="subjective time-rate attestation for WMS private escape",
                payload={
                    "time_rate_attestation_subject_digest": subject["digest"],
                    "participant_id": participant_id,
                    "baseline_time_rate": subject["baseline_time_rate"],
                    "requested_time_rate": subject["requested_time_rate"],
                    "attestation_decision": "attest",
                },
            )
            receipts.append(
                sync.build_time_rate_attestation_receipt(
                    session["session_id"],
                    participant_id=participant_id,
                    time_rate_attestation_subject_digest=subject["digest"],
                    baseline_time_rate=subject["baseline_time_rate"],
                    requested_time_rate=subject["requested_time_rate"],
                    imc_session=imc_session,
                    imc_message=message,
                )
            )
        return subject, receipts

    def _approval_transport_receipts(
        self,
        sync: WorldModelSync,
        session: dict,
        *,
        requested_by: str,
        proposed_physics_rules_ref: str,
        rationale: str,
    ) -> list[dict]:
        participants = session["current_state"]["participants"]
        subject = sync.build_physics_rules_approval_subject(
            session["session_id"],
            requested_by=requested_by,
            proposed_physics_rules_ref=proposed_physics_rules_ref,
            rationale=rationale,
        )
        imc = InterMindChannel()
        template = {
            "public_fields": [
                "approval_subject_digest",
                "participant_id",
                "approval_decision",
            ],
            "intimate_fields": [],
            "sealed_fields": [],
        }
        receipts = []
        for participant_id in participants:
            counterparty = participants[1] if participant_id == participants[0] else participants[0]
            imc_session = imc.open_session(
                initiator_id=counterparty,
                peer_id=participant_id,
                mode="text",
                initiator_template=template,
                peer_template=template,
                peer_attested=True,
                forward_secrecy=True,
                council_witnessed=True,
            )
            message = imc.send(
                imc_session["session_id"],
                sender_id=participant_id,
                summary="approval for reversible WMS physics rules change",
                payload={
                    "approval_subject_digest": subject["digest"],
                    "participant_id": participant_id,
                    "approval_decision": "approve",
                },
            )
            receipts.append(
                sync.build_participant_approval_transport_receipt(
                    session["session_id"],
                    participant_id=participant_id,
                    approval_subject_digest=subject["digest"],
                    imc_session=imc_session,
                    imc_message=message,
                )
            )
        return receipts

    def _authority_route_trace(self, *, trace_ref: str = "authority-route-trace://federation/test") -> dict:
        route_bindings = []
        for index, remote_host_ref in enumerate(
            [
                "host://federation/wms-engine-edge-a",
                "host://federation/wms-engine-edge-b",
            ],
            start=1,
        ):
            remote_ip = "192.0.2.10" if index == 1 else "198.51.100.20"
            route_binding_ref = f"authority-route://federation/test-{index}"
            tuple_digest = sha256_text(
                canonical_json(
                    {
                        "local_ip": "203.0.113.5",
                        "local_port": 53000 + index,
                        "remote_ip": remote_ip,
                        "remote_port": 44300 + index,
                    }
                )
            )
            host_binding_digest = sha256_text(
                canonical_json(
                    {
                        "tuple_digest": tuple_digest,
                        "remote_host_ref": remote_host_ref,
                        "remote_host_attestation_ref": (
                            f"host-attestation://federation/wms-engine-edge-{index}"
                        ),
                        "authority_cluster_ref": "authority-cluster://federation/wms-engine",
                    }
                )
            )
            route_bindings.append(
                {
                    "key_server_ref": f"keyserver://federation/wms-engine-{index}",
                    "server_role": "quorum-notary" if index == 1 else "directory-mirror",
                    "authority_status": "active",
                    "server_endpoint": f"https://{remote_ip}:4430{index}/route",
                    "server_name": "authority.local",
                    "remote_host_ref": remote_host_ref,
                    "remote_host_attestation_ref": (
                        f"host-attestation://federation/wms-engine-edge-{index}"
                    ),
                    "authority_cluster_ref": "authority-cluster://federation/wms-engine",
                    "remote_jurisdiction": "JP-13" if index == 1 else "US-CA",
                    "remote_network_zone": "apne1" if index == 1 else "usw2",
                    "route_binding_ref": route_binding_ref,
                    "matched_root_refs": [f"root://federation/pki-{index}"],
                    "mtls_status": "authenticated",
                    "response_digest_bound": True,
                    "os_observer_receipt": {
                        "kind": "distributed_transport_os_observer_receipt",
                        "schema_version": "1.0.0",
                        "receipt_id": f"authority-os-observer://test-{index}",
                        "observer_profile": "os-native-tcp-observer-v1",
                        "observed_at": "2026-04-25T02:30:00Z",
                        "local_ip": "203.0.113.5",
                        "local_port": 53000 + index,
                        "remote_ip": remote_ip,
                        "remote_port": 44300 + index,
                        "remote_host_ref": remote_host_ref,
                        "remote_host_attestation_ref": (
                            f"host-attestation://federation/wms-engine-edge-{index}"
                        ),
                        "authority_cluster_ref": "authority-cluster://federation/wms-engine",
                        "owning_pid": 1000 + index,
                        "observed_sources": ["lsof", "netstat"],
                        "connection_states": ["ESTABLISHED"],
                        "tuple_digest": tuple_digest,
                        "host_binding_digest": host_binding_digest,
                        "receipt_status": "observed",
                    },
                    "socket_trace": {
                        "local_ip": "203.0.113.5",
                        "local_port": 53000 + index,
                        "remote_ip": remote_ip,
                        "remote_port": 44300 + index,
                        "non_loopback": True,
                        "transport_profile": "mtls-socket-trace-v1",
                        "tls_version": "TLSv1.3",
                        "cipher_suite": "TLS_AES_256_GCM_SHA384",
                        "peer_certificate_fingerprint": sha256_text(f"peer-{index}"),
                        "client_certificate_fingerprint": sha256_text("client"),
                        "request_bytes": 128,
                        "response_bytes": 512,
                        "http_status": 200,
                        "response_digest": sha256_text(f"response-{index}"),
                        "connect_latency_ms": 4.0,
                        "tls_handshake_latency_ms": 9.0,
                        "round_trip_latency_ms": 13.0,
                    },
                }
            )
        trace = {
            "kind": "distributed_transport_authority_route_trace",
            "schema_version": "1.0.0",
            "trace_ref": trace_ref,
            "authority_plane_ref": "authority-plane://federation/test",
            "authority_plane_digest": sha256_text("authority-plane://federation/test"),
            "route_target_discovery_ref": "authority-route-targets://federation/test",
            "route_target_discovery_digest": sha256_text(
                "authority-route-targets://federation/test"
            ),
            "envelope_ref": "distributed-envelope-test00000000",
            "envelope_digest": sha256_text("distributed-envelope-test"),
            "council_tier": "federation",
            "transport_profile": "federation-mtls-quorum-v1",
            "trace_profile": "non-loopback-mtls-authority-route-v1",
            "socket_trace_profile": "mtls-socket-trace-v1",
            "os_observer_profile": "os-native-tcp-observer-v1",
            "cross_host_binding_profile": "attested-cross-host-authority-binding-v1",
            "route_target_discovery_profile": "bounded-authority-route-target-discovery-v1",
            "ca_bundle_ref": "cert://authority-ca",
            "client_certificate_ref": "cert://authority-client",
            "server_name": "authority.local",
            "authority_cluster_ref": "authority-cluster://federation/wms-engine",
            "route_count": 2,
            "distinct_remote_host_count": 2,
            "mtls_authenticated_count": 2,
            "trusted_root_refs": ["root://federation/pki-1", "root://federation/pki-2"],
            "non_loopback_verified": True,
            "authority_plane_bound": True,
            "response_digest_bound": True,
            "socket_trace_complete": True,
            "os_observer_complete": True,
            "route_target_discovery_bound": True,
            "cross_host_verified": True,
            "route_bindings": route_bindings,
            "trace_status": "authenticated",
            "recorded_at": "2026-04-25T02:30:00Z",
            "total_connect_latency_ms": 8.0,
            "total_handshake_latency_ms": 18.0,
            "total_round_trip_latency_ms": 26.0,
        }
        trace["digest"] = sha256_text(canonical_json(trace))
        return trace

    def _packet_capture_export(self, route_trace: dict) -> dict:
        route_exports = []
        for binding in route_trace["route_bindings"]:
            socket_trace = binding["socket_trace"]
            route_exports.append(
                {
                    "key_server_ref": binding["key_server_ref"],
                    "route_binding_ref": binding["route_binding_ref"],
                    "local_ip": socket_trace["local_ip"],
                    "local_port": socket_trace["local_port"],
                    "remote_ip": socket_trace["remote_ip"],
                    "remote_port": socket_trace["remote_port"],
                    "outbound_tuple_digest": sha256_text(
                        canonical_json(
                            {
                                "direction": "outbound-request",
                                "local_ip": socket_trace["local_ip"],
                                "local_port": socket_trace["local_port"],
                                "remote_ip": socket_trace["remote_ip"],
                                "remote_port": socket_trace["remote_port"],
                            }
                        )
                    ),
                    "inbound_tuple_digest": sha256_text(
                        canonical_json(
                            {
                                "direction": "inbound-response",
                                "local_ip": socket_trace["local_ip"],
                                "local_port": socket_trace["local_port"],
                                "remote_ip": socket_trace["remote_ip"],
                                "remote_port": socket_trace["remote_port"],
                            }
                        )
                    ),
                    "packet_order": ["outbound-request", "inbound-response"],
                    "outbound_request_bytes": socket_trace["request_bytes"],
                    "inbound_response_bytes": socket_trace["response_bytes"],
                    "outbound_payload_digest": sha256_text(
                        f"{binding['route_binding_ref']}:outbound"
                    ),
                    "inbound_payload_digest": sha256_text(
                        f"{binding['route_binding_ref']}:inbound"
                    ),
                    "readback_packet_count": 2,
                    "readback_verified": True,
                    "os_native_readback_verified": True,
                }
            )
        payload = {
            "capture_ref": "authority-packet-capture://federation/test",
            "trace_ref": route_trace["trace_ref"],
            "trace_digest": route_trace["digest"],
            "authority_plane_ref": route_trace["authority_plane_ref"],
            "authority_plane_digest": route_trace["authority_plane_digest"],
            "envelope_ref": route_trace["envelope_ref"],
            "envelope_digest": route_trace["envelope_digest"],
            "council_tier": route_trace["council_tier"],
            "transport_profile": route_trace["transport_profile"],
            "capture_profile": "trace-bound-pcap-export-v1",
            "artifact_format": "pcap",
            "readback_profile": "pcap-readback-v1",
            "os_native_readback_profile": "tcpdump-readback-v1",
            "route_count": route_trace["route_count"],
            "packet_count": route_trace["route_count"] * 2,
            "artifact_size_bytes": 768,
            "artifact_digest": sha256_text(canonical_json(route_exports)),
            "readback_digest": sha256_text(canonical_json({"route_exports": route_exports})),
            "route_exports": route_exports,
            "os_native_readback_available": True,
            "os_native_readback_ok": True,
            "export_status": "verified",
            "recorded_at": "2026-04-25T02:31:00Z",
        }
        payload["digest"] = sha256_text(canonical_json(payload))
        return {
            "kind": "distributed_transport_packet_capture_export",
            "schema_version": "1.0.0",
            **payload,
        }

    def _privileged_capture_acquisition(self, route_trace: dict, capture_export: dict) -> dict:
        route_binding_refs = [
            binding["route_binding_ref"] for binding in route_trace["route_bindings"]
        ]
        capture_filter = (
            "tcp and ("
            + " or ".join(
                [
                    (
                        f"host {binding['socket_trace']['remote_ip']} and "
                        f"port {binding['socket_trace']['remote_port']}"
                    )
                    for binding in route_trace["route_bindings"]
                ]
            )
            + ")"
        )
        capture_command = [
            "/usr/sbin/tcpdump",
            "-i",
            "en0",
            "-w",
            "{capture_output_path}",
            capture_filter,
        ]
        payload = {
            "acquisition_ref": "authority-live-capture://federation/test",
            "trace_ref": route_trace["trace_ref"],
            "trace_digest": route_trace["digest"],
            "capture_ref": capture_export["capture_ref"],
            "capture_digest": capture_export["digest"],
            "authority_plane_ref": route_trace["authority_plane_ref"],
            "authority_plane_digest": route_trace["authority_plane_digest"],
            "envelope_ref": route_trace["envelope_ref"],
            "envelope_digest": route_trace["envelope_digest"],
            "council_tier": route_trace["council_tier"],
            "transport_profile": route_trace["transport_profile"],
            "acquisition_profile": "bounded-live-interface-capture-acquisition-v1",
            "broker_profile": "delegated-privileged-capture-broker-v1",
            "privilege_mode": "delegated-broker",
            "lease_ref": "capture-lease://federation/test",
            "broker_attestation_ref": "broker://authority-capture/test",
            "interface_name": "en0",
            "local_ips": ["203.0.113.5"],
            "capture_filter": capture_filter,
            "filter_digest": sha256_text(capture_filter),
            "route_binding_refs": route_binding_refs,
            "capture_command": capture_command,
            "lease_duration_s": 300,
            "lease_expires_at": "2026-04-25T02:36:00Z",
            "grant_status": "granted",
            "recorded_at": "2026-04-25T02:31:00Z",
        }
        payload["digest"] = sha256_text(canonical_json(payload))
        return {
            "kind": "distributed_transport_privileged_capture_acquisition",
            "schema_version": "1.0.0",
            **payload,
        }

    def test_minor_diff_reconciles_via_consensus_round(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )

        outcome = sync.propose_diff(
            session["session_id"],
            proposer_id="identity://peer",
            candidate_objects=["atrium", "council-table", "shared-lantern"],
            affected_object_ratio=0.03,
            attested=True,
        )
        snapshot = sync.snapshot(session["session_id"])

        self.assertEqual("minor_diff", outcome["classification"])
        self.assertEqual("consensus-round", outcome["decision"])
        self.assertFalse(outcome["escape_offered"])
        self.assertIn("shared-lantern", snapshot["objects"])

    def test_major_diff_offers_private_reality_escape(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )

        outcome = sync.propose_diff(
            session["session_id"],
            proposer_id="identity://peer",
            candidate_objects=["atrium", "council-table", "gravity-well"],
            affected_object_ratio=0.22,
            attested=True,
        )
        switched = sync.switch_mode(
            session["session_id"],
            mode="private_reality",
            requested_by="identity://primary",
            reason="major shared-world divergence",
        )
        snapshot = sync.snapshot(session["session_id"])

        self.assertEqual("major_diff", outcome["classification"])
        self.assertTrue(outcome["escape_offered"])
        self.assertTrue(switched["private_escape_honored"])
        self.assertEqual("local", snapshot["authority"])

    def test_time_rate_deviation_offers_escape_without_mutating_state(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )
        subject, attestations = self._time_rate_attestation_receipts(
            sync,
            session,
            proposer_id="identity://peer",
            requested_time_rate=1.25,
        )

        outcome = sync.propose_diff(
            session["session_id"],
            proposer_id="identity://peer",
            candidate_objects=["atrium", "council-table"],
            affected_object_ratio=0.01,
            attested=True,
            requested_time_rate=1.25,
            time_rate_attestation_receipts=attestations,
        )
        snapshot = sync.snapshot(session["session_id"])

        self.assertEqual("major_diff", outcome["classification"])
        self.assertEqual("offer-private-reality", outcome["decision"])
        self.assertTrue(outcome["escape_offered"])
        self.assertEqual("fixed-time-rate-private-escape-v1", outcome["time_rate_policy_id"])
        self.assertEqual(1.0, outcome["baseline_time_rate"])
        self.assertEqual(1.25, outcome["requested_time_rate"])
        self.assertEqual(0.25, outcome["time_rate_delta"])
        self.assertTrue(outcome["time_rate_deviation_detected"])
        self.assertTrue(outcome["time_rate_escape_required"])
        self.assertTrue(outcome["time_rate_state_locked"])
        self.assertEqual("baseline-requested-time-rate-delta-v1", outcome["time_rate_deviation_digest_profile"])
        self.assertEqual(64, len(outcome["time_rate_deviation_digest"]))
        self.assertEqual("subjective-time-attestation-transport-v1", outcome["time_rate_attestation_policy_id"])
        self.assertEqual(subject["digest"], outcome["time_rate_attestation_subject_digest"])
        self.assertTrue(outcome["time_rate_attestation_required"])
        self.assertTrue(outcome["time_rate_attestation_quorum_met"])
        self.assertTrue(outcome["time_rate_attestation_participant_order_bound"])
        self.assertEqual(2, len(outcome["time_rate_attestation_receipts"]))
        self.assertTrue(
            all(
                sync.validate_time_rate_attestation_receipt(
                    receipt,
                    time_rate_attestation_subject_digest=subject["digest"],
                )["ok"]
                for receipt in outcome["time_rate_attestation_receipts"]
            )
        )
        self.assertEqual(1.0, snapshot["time_rate"])

    def test_time_rate_deviation_without_transport_attestation_fails_quorum(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )

        outcome = sync.propose_diff(
            session["session_id"],
            proposer_id="identity://peer",
            candidate_objects=["atrium", "council-table"],
            affected_object_ratio=0.01,
            attested=True,
            requested_time_rate=1.25,
        )

        self.assertTrue(outcome["time_rate_attestation_required"])
        self.assertFalse(outcome["time_rate_attestation_quorum_met"])
        self.assertEqual(
            ["identity://primary", "identity://peer"],
            outcome["time_rate_attestation_missing_participants"],
        )

    def test_unauthorized_diff_isolated_as_malicious_inject(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )

        outcome = sync.propose_diff(
            session["session_id"],
            proposer_id="identity://spoof",
            candidate_objects=["atrium", "spoofed-object"],
            affected_object_ratio=0.4,
            attested=False,
        )
        violation = sync.observe_violation(session["session_id"])

        self.assertEqual("malicious_inject", outcome["classification"])
        self.assertEqual("guardian-veto", outcome["decision"])
        self.assertEqual("isolate-session", violation["guardian_action"])
        self.assertTrue(violation["violation_detected"])

    def test_physics_rules_change_requires_unanimous_reversible_receipt(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )
        baseline = sync.snapshot(session["session_id"])
        proposed_ref = "physics://shared-atrium/low-gravity-v1"
        rationale = "bounded rehearsal"
        approval_transport_receipts = self._approval_transport_receipts(
            sync,
            session,
            requested_by="identity://primary",
            proposed_physics_rules_ref=proposed_ref,
            rationale=rationale,
        )

        receipt = sync.propose_physics_rules_change(
            session["session_id"],
            requested_by="identity://primary",
            proposed_physics_rules_ref=proposed_ref,
            rationale=rationale,
            participant_approvals=["identity://primary", "identity://peer"],
            guardian_attested=True,
            approval_transport_receipts=approval_transport_receipts,
        )
        changed = sync.snapshot(session["session_id"])
        validation = sync.validate_physics_rules_change(receipt)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["approval_quorum_met"])
        self.assertTrue(validation["approval_transport_quorum_met"])
        self.assertTrue(validation["approval_transport_digest_bound"])
        self.assertTrue(validation["approval_collection_complete"])
        self.assertTrue(validation["approval_collection_digest_bound"])
        self.assertTrue(validation["revert_bound"])
        self.assertTrue(validation["digest_bound"])
        self.assertEqual("applied", receipt["decision"])
        self.assertEqual(
            "physics://shared-atrium/low-gravity-v1",
            changed["physics_rules_ref"],
        )
        self.assertEqual(baseline["physics_rules_ref"], receipt["rollback_physics_rules_ref"])

        reverted = sync.revert_physics_rules_change(
            session["session_id"],
            change_id=receipt["change_id"],
            requested_by="identity://primary",
            reason="rehearsal complete",
            guardian_attested=True,
        )
        reverted_state = sync.snapshot(session["session_id"])
        revert_validation = sync.validate_physics_rules_change(reverted)

        self.assertTrue(revert_validation["ok"])
        self.assertEqual("reverted", reverted["decision"])
        self.assertEqual(receipt["change_id"], reverted["revert_of_change_id"])
        self.assertEqual(baseline["physics_rules_ref"], reverted_state["physics_rules_ref"])
        self.assertEqual(receipt["rollback_token_ref"], reverted["rollback_token_ref"])

    def test_approval_collection_batches_participant_receipts(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer", "identity://observer"],
            objects=["atrium", "council-table"],
        )
        proposed_ref = "physics://shared-atrium/low-gravity-v1"
        rationale = "bounded rehearsal"
        receipts = self._approval_transport_receipts(
            sync,
            session,
            requested_by="identity://primary",
            proposed_physics_rules_ref=proposed_ref,
            rationale=rationale,
        )
        subject = sync.build_physics_rules_approval_subject(
            session["session_id"],
            requested_by="identity://primary",
            proposed_physics_rules_ref=proposed_ref,
            rationale=rationale,
        )

        collection = sync.build_approval_collection_receipt(
            session["session_id"],
            approval_subject_digest=subject["digest"],
            approval_transport_receipts=receipts,
            max_batch_size=2,
        )
        validation = sync.validate_approval_collection_receipt(
            collection,
            required_participants=session["current_state"]["participants"],
            approval_subject_digest=subject["digest"],
            approval_transport_receipts=receipts,
        )

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["collection_complete"])
        self.assertTrue(validation["participant_order_bound"])
        self.assertTrue(validation["receipt_set_digest_bound"])
        self.assertTrue(validation["batches_within_limit"])
        self.assertEqual(2, collection["batch_count"])
        self.assertEqual(
            ["identity://primary", "identity://peer", "identity://observer"],
            collection["covered_participants"],
        )

    def test_distributed_approval_fanout_binds_transport_results(self) -> None:
        sync = WorldModelSync()
        transport = DistributedTransportService()
        session = sync.create_session(
            ["identity://primary", "identity://peer", "identity://observer"],
            objects=["atrium", "council-table"],
        )
        proposed_ref = "physics://shared-atrium/low-gravity-v1"
        rationale = "bounded rehearsal"
        receipts = self._approval_transport_receipts(
            sync,
            session,
            requested_by="identity://primary",
            proposed_physics_rules_ref=proposed_ref,
            rationale=rationale,
        )
        subject = sync.build_physics_rules_approval_subject(
            session["session_id"],
            requested_by="identity://primary",
            proposed_physics_rules_ref=proposed_ref,
            rationale=rationale,
        )
        collection = sync.build_approval_collection_receipt(
            session["session_id"],
            approval_subject_digest=subject["digest"],
            approval_transport_receipts=receipts,
            max_batch_size=2,
        )
        fanout_results = []
        for index, participant_id in enumerate(session["current_state"]["participants"], start=1):
            participant_pair = (
                ["identity://primary", "identity://peer"]
                if participant_id == "identity://primary"
                else ["identity://primary", participant_id]
            )
            result_digest = sync.build_distributed_approval_result_digest(
                approval_subject_digest=subject["digest"],
                participant_id=participant_id,
                approval_collection_digest=collection["digest"],
            )
            envelope = transport.issue_federation_handoff(
                topology_ref=f"topology://wms-test/{index}",
                proposal_ref=f"wms-approval://{index}",
                payload_ref=f"cas://sha256/{subject['digest']}",
                payload_digest=subject["digest"],
                participant_identity_ids=participant_pair,
            )
            transport_receipt = transport.record_receipt(
                envelope,
                result_ref=f"resolution://wms-test/{index}",
                result_digest=result_digest,
                participant_ids=[
                    attestation.participant_id
                    for attestation in envelope.participant_attestations
                ],
                channel_binding_ref=envelope.channel_binding_ref,
                verified_root_refs=["root://federation/pki-a"],
                key_epoch=1,
                hop_nonce_chain=[f"hop://wms-test/{index}/relay-a"],
            )
            fanout_results.append(
                {
                    "participant_id": participant_id,
                    "approval_result_ref": f"resolution://wms-test/{index}",
                    "approval_result_digest": result_digest,
                    "transport_envelope": envelope.to_dict(),
                    "transport_receipt": transport_receipt.to_dict(),
                }
            )

        retry_attempts = [
            {
                "participant_id": session["current_state"]["participants"][-1],
                "attempt_index": 1,
                "outage_kind": "timeout",
                "retry_after_ms": 250,
                "retry_decision": "retry",
                "recovery_result_digest": fanout_results[-1]["approval_result_digest"],
                "recovery_transport_receipt_digest": fanout_results[-1][
                    "transport_receipt"
                ]["digest"],
            }
        ]
        fanout = sync.build_distributed_approval_fanout_receipt(
            session["session_id"],
            approval_subject_digest=subject["digest"],
            approval_collection_receipt=collection,
            participant_fanout_results=fanout_results,
            fanout_retry_attempts=retry_attempts,
        )
        validation = sync.validate_distributed_approval_fanout_receipt(
            fanout,
            required_participants=session["current_state"]["participants"],
            approval_subject_digest=subject["digest"],
            approval_collection_digest=collection["digest"],
        )
        tampered_fanout = dict(fanout)
        tampered_fanout["partial_outage_status"] = "not-required"
        rejected_with_tampered_fanout = sync.propose_physics_rules_change(
            session["session_id"],
            requested_by="identity://primary",
            proposed_physics_rules_ref=proposed_ref,
            rationale=rationale,
            participant_approvals=session["current_state"]["participants"],
            guardian_attested=True,
            approval_transport_receipts=receipts,
            approval_collection_receipt=collection,
            approval_fanout_receipt=tampered_fanout,
        )
        physics_change = sync.propose_physics_rules_change(
            session["session_id"],
            requested_by="identity://primary",
            proposed_physics_rules_ref=proposed_ref,
            rationale=rationale,
            participant_approvals=session["current_state"]["participants"],
            guardian_attested=True,
            approval_transport_receipts=receipts,
            approval_collection_receipt=collection,
            approval_fanout_receipt=fanout,
        )
        physics_validation = sync.validate_physics_rules_change(physics_change)
        state_digest = sha256_text(canonical_json(sync.snapshot(session["session_id"])))
        engine_session_ref = f"engine-session://test/{session['session_id']}"
        engine_entry = sync.build_engine_transaction_entry(
            transaction_id=f"engine-txn://test/{session['session_id']}/fanout",
            transaction_index=1,
            operation="approval_fanout_bound",
            source_artifact_kind="wms_distributed_approval_fanout_receipt",
            source_artifact_ref=f"wms-approval-fanout://{fanout['digest'][:16]}",
            source_artifact_digest=fanout["digest"],
            engine_session_ref=engine_session_ref,
            engine_state_before_digest=state_digest,
            engine_state_after_digest=state_digest,
            participant_ids=session["current_state"]["participants"],
        )
        engine_log = sync.build_engine_transaction_log_receipt(
            session["session_id"],
            engine_adapter_ref="engine-adapter://test/wms",
            engine_session_ref=engine_session_ref,
            transaction_log_ref=f"engine-log://test/{session['session_id']}",
            transaction_entries=[engine_entry],
            required_operations=["approval_fanout_bound"],
            source_artifact_digests={"approval_fanout_bound": fanout["digest"]},
        )
        route_trace = self._authority_route_trace()
        route_health_observation = {
            "authority_ref": "authority://test/federation",
            "route_ref": route_trace["route_bindings"][0]["route_binding_ref"],
            "participant_id": session["current_state"]["participants"][-1],
            "outage_kind": "timeout",
            "route_status": "partial-outage",
            "remote_jurisdiction": "JP-13",
            "jurisdiction_policy_registry_ref": (
                "policy-registry://jp-13/test-wms-authority-retry"
            ),
            "jurisdiction_rate_limit_ref": "rate-limit://jp-13/test-wms-retry",
            "jurisdiction_retry_limit_ms": 500,
            "authority_slo_snapshot_ref": (
                "authority-slo://test/federation/observer-timeout"
            ),
            "authority_slo_retry_limit_ms": 500,
            "signer_key_ref": "key://test/jp-13/wms-retry-signer",
            "observed_latency_ms": 830,
            "success_ratio": 0.667,
            "consecutive_failures": 1,
        }
        jurisdiction_policy_registry_digest = sha256_text(
            canonical_json(
                {
                    "registry_policy_id": "registry-bound-authority-retry-slo-v1",
                    "registry_profile": "jurisdiction-policy-registry-bound-retry-v1",
                    "jurisdiction_policy_registry_ref": route_health_observation[
                        "jurisdiction_policy_registry_ref"
                    ],
                    "remote_jurisdiction": route_health_observation[
                        "remote_jurisdiction"
                    ],
                    "jurisdiction_rate_limit_ref": route_health_observation[
                        "jurisdiction_rate_limit_ref"
                    ],
                    "jurisdiction_retry_limit_ms": route_health_observation[
                        "jurisdiction_retry_limit_ms"
                    ],
                    "signer_key_ref": route_health_observation["signer_key_ref"],
                }
            )
        )
        slo_payload = {
            "checked_at": "2026-04-26T00:20:00Z",
            "authority_ref": route_health_observation["authority_ref"],
            "route_ref": route_health_observation["route_ref"],
            "route_status": route_health_observation["route_status"],
            "remote_jurisdiction": route_health_observation["remote_jurisdiction"],
            "jurisdiction_policy_registry_ref": route_health_observation[
                "jurisdiction_policy_registry_ref"
            ],
            "jurisdiction_policy_registry_digest": jurisdiction_policy_registry_digest,
            "authority_slo_snapshot_profile": "authority-slo-snapshot-retry-window-v1",
            "authority_slo_snapshot_ref": route_health_observation[
                "authority_slo_snapshot_ref"
            ],
            "authority_slo_retry_limit_ms": route_health_observation[
                "authority_slo_retry_limit_ms"
            ],
            "observed_latency_ms": route_health_observation["observed_latency_ms"],
            "success_ratio": route_health_observation["success_ratio"],
            "consecutive_failures": route_health_observation["consecutive_failures"],
        }
        with live_slo_endpoint(slo_payload) as endpoint:
            slo_probe = sync.probe_remote_authority_slo_snapshot_endpoint(
                slo_endpoint=endpoint,
                authority_ref=route_health_observation["authority_ref"],
                route_ref=route_health_observation["route_ref"],
                route_status=route_health_observation["route_status"],
                remote_jurisdiction=route_health_observation["remote_jurisdiction"],
                jurisdiction_policy_registry_ref=route_health_observation[
                    "jurisdiction_policy_registry_ref"
                ],
                jurisdiction_policy_registry_digest=jurisdiction_policy_registry_digest,
                authority_slo_snapshot_ref=route_health_observation[
                    "authority_slo_snapshot_ref"
                ],
                authority_slo_retry_limit_ms=route_health_observation[
                    "authority_slo_retry_limit_ms"
                ],
                observed_latency_ms=route_health_observation["observed_latency_ms"],
                success_ratio=route_health_observation["success_ratio"],
                consecutive_failures=route_health_observation["consecutive_failures"],
                request_timeout_ms=500,
            )
        backup_route_health_observation = {
            "authority_ref": "authority://test/heritage",
            "route_ref": route_trace["route_bindings"][1]["route_binding_ref"],
            "participant_id": session["current_state"]["participants"][-1],
            "outage_kind": "timeout",
            "route_status": "recovered",
            "remote_jurisdiction": "US-CA",
            "jurisdiction_policy_registry_ref": (
                "policy-registry://us-ca/test-wms-authority-retry"
            ),
            "jurisdiction_rate_limit_ref": "rate-limit://us-ca/test-wms-retry",
            "jurisdiction_retry_limit_ms": 750,
            "authority_slo_snapshot_ref": (
                "authority-slo://test/heritage/observer-timeout"
            ),
            "authority_slo_retry_limit_ms": 750,
            "signer_key_ref": "key://test/us-ca/wms-retry-signer",
            "observed_latency_ms": 410,
            "success_ratio": 0.91,
            "consecutive_failures": 0,
        }
        backup_registry_digest = sha256_text(
            canonical_json(
                {
                    "registry_policy_id": "registry-bound-authority-retry-slo-v1",
                    "registry_profile": "jurisdiction-policy-registry-bound-retry-v1",
                    "jurisdiction_policy_registry_ref": backup_route_health_observation[
                        "jurisdiction_policy_registry_ref"
                    ],
                    "remote_jurisdiction": backup_route_health_observation[
                        "remote_jurisdiction"
                    ],
                    "jurisdiction_rate_limit_ref": backup_route_health_observation[
                        "jurisdiction_rate_limit_ref"
                    ],
                    "jurisdiction_retry_limit_ms": backup_route_health_observation[
                        "jurisdiction_retry_limit_ms"
                    ],
                    "signer_key_ref": backup_route_health_observation[
                        "signer_key_ref"
                    ],
                }
            )
        )
        backup_slo_payload = {
            "checked_at": "2026-04-26T00:20:05Z",
            "authority_ref": backup_route_health_observation["authority_ref"],
            "route_ref": backup_route_health_observation["route_ref"],
            "route_status": backup_route_health_observation["route_status"],
            "remote_jurisdiction": backup_route_health_observation[
                "remote_jurisdiction"
            ],
            "jurisdiction_policy_registry_ref": backup_route_health_observation[
                "jurisdiction_policy_registry_ref"
            ],
            "jurisdiction_policy_registry_digest": backup_registry_digest,
            "authority_slo_snapshot_profile": "authority-slo-snapshot-retry-window-v1",
            "authority_slo_snapshot_ref": backup_route_health_observation[
                "authority_slo_snapshot_ref"
            ],
            "authority_slo_retry_limit_ms": backup_route_health_observation[
                "authority_slo_retry_limit_ms"
            ],
            "observed_latency_ms": backup_route_health_observation[
                "observed_latency_ms"
            ],
            "success_ratio": backup_route_health_observation["success_ratio"],
            "consecutive_failures": backup_route_health_observation[
                "consecutive_failures"
            ],
        }
        with live_slo_endpoint(backup_slo_payload) as backup_endpoint:
            backup_slo_probe = sync.probe_remote_authority_slo_snapshot_endpoint(
                slo_endpoint=backup_endpoint,
                authority_ref=backup_route_health_observation["authority_ref"],
                route_ref=backup_route_health_observation["route_ref"],
                route_status=backup_route_health_observation["route_status"],
                remote_jurisdiction=backup_route_health_observation[
                    "remote_jurisdiction"
                ],
                jurisdiction_policy_registry_ref=backup_route_health_observation[
                    "jurisdiction_policy_registry_ref"
                ],
                jurisdiction_policy_registry_digest=backup_registry_digest,
                authority_slo_snapshot_ref=backup_route_health_observation[
                    "authority_slo_snapshot_ref"
                ],
                authority_slo_retry_limit_ms=backup_route_health_observation[
                    "authority_slo_retry_limit_ms"
                ],
                observed_latency_ms=backup_route_health_observation[
                    "observed_latency_ms"
                ],
                success_ratio=backup_route_health_observation["success_ratio"],
                consecutive_failures=backup_route_health_observation[
                    "consecutive_failures"
                ],
                request_timeout_ms=500,
            )
        slo_quorum_threshold_policy = (
            sync.build_authority_slo_quorum_threshold_policy_receipt(
                policy_ref="policy://test/wms-authority-slo-quorum-threshold",
                jurisdiction_policy_registry_refs=[
                    route_health_observation["jurisdiction_policy_registry_ref"],
                    backup_route_health_observation[
                        "jurisdiction_policy_registry_ref"
                    ],
                ],
                jurisdiction_policy_registry_digests=[
                    jurisdiction_policy_registry_digest,
                    backup_registry_digest,
                ],
                remote_jurisdictions=[
                    route_health_observation["remote_jurisdiction"],
                    backup_route_health_observation["remote_jurisdiction"],
                ],
                signer_key_ref="key://test/wms-slo-quorum-threshold-signer",
                required_authority_count=2,
                required_jurisdiction_count=2,
                effective_at="2026-04-26T00:20:06Z",
            )
        )
        slo_quorum = sync.build_authority_slo_probe_quorum_receipt(
            [slo_probe, backup_slo_probe],
            authority_route_trace=route_trace,
            primary_probe_digest=slo_probe["digest"],
            threshold_policy_receipt=slo_quorum_threshold_policy,
        )
        slo_probe_validation = sync.validate_authority_slo_probe_receipt(slo_probe)
        slo_quorum_threshold_policy_validation = (
            sync.validate_authority_slo_quorum_threshold_policy_receipt(
                slo_quorum_threshold_policy
            )
        )
        slo_quorum_validation = sync.validate_authority_slo_probe_quorum_receipt(
            slo_quorum,
            authority_route_trace=route_trace,
        )
        retry_budget = sync.build_remote_authority_retry_budget_receipt(
            session["session_id"],
            authority_profile_ref="authority-profile://test/wms-approval-retry",
            approval_fanout_receipt=fanout,
            engine_transaction_log_receipt=engine_log,
            route_health_observations=[route_health_observation],
            authority_slo_probe_receipts=[slo_probe],
            authority_slo_probe_quorum_receipt=slo_quorum,
            authority_route_trace=route_trace,
        )
        retry_budget_validation = sync.validate_remote_authority_retry_budget_receipt(
            retry_budget,
            approval_fanout_receipt=fanout,
            engine_transaction_log_receipt=engine_log,
            required_participants=session["current_state"]["participants"],
            authority_route_trace=route_trace,
        )
        tampered_budget = dict(retry_budget)
        tampered_budget["engine_log_fanout_bound"] = False
        tampered_budget_validation = sync.validate_remote_authority_retry_budget_receipt(
            tampered_budget,
            approval_fanout_receipt=fanout,
            engine_transaction_log_receipt=engine_log,
            required_participants=session["current_state"]["participants"],
            authority_route_trace=route_trace,
        )
        tampered_signature_budget = dict(retry_budget)
        tampered_signature_budget["authority_signature_digests"] = [
            sha256_text("tampered-signature")
        ]
        tampered_signature_validation = sync.validate_remote_authority_retry_budget_receipt(
            tampered_signature_budget,
            approval_fanout_receipt=fanout,
            engine_transaction_log_receipt=engine_log,
            required_participants=session["current_state"]["participants"],
            authority_route_trace=route_trace,
        )
        tampered_registry_budget = dict(retry_budget)
        tampered_registry_budget["jurisdiction_policy_registry_digests"] = [
            sha256_text("tampered-registry")
        ]
        tampered_registry_validation = sync.validate_remote_authority_retry_budget_receipt(
            tampered_registry_budget,
            approval_fanout_receipt=fanout,
            engine_transaction_log_receipt=engine_log,
            required_participants=session["current_state"]["participants"],
            authority_route_trace=route_trace,
        )
        tampered_slo_probe_budget = dict(retry_budget)
        tampered_slo_probe_budget["authority_slo_probe_digests"] = [
            sha256_text("tampered-slo-probe")
        ]
        tampered_slo_probe_validation = sync.validate_remote_authority_retry_budget_receipt(
            tampered_slo_probe_budget,
            approval_fanout_receipt=fanout,
            engine_transaction_log_receipt=engine_log,
            required_participants=session["current_state"]["participants"],
            authority_route_trace=route_trace,
        )
        tampered_slo_quorum_budget = dict(retry_budget)
        tampered_slo_quorum_budget["authority_slo_probe_quorum_digest"] = sha256_text(
            "tampered-slo-quorum"
        )
        tampered_slo_quorum_budget_validation = (
            sync.validate_remote_authority_retry_budget_receipt(
                tampered_slo_quorum_budget,
                approval_fanout_receipt=fanout,
                engine_transaction_log_receipt=engine_log,
                required_participants=session["current_state"]["participants"],
                authority_route_trace=route_trace,
            )
        )
        tampered_retry_transport_budget = dict(retry_budget)
        tampered_retry_transport_budget["transport_route_binding_refs"] = [
            "authority-route://tampered"
        ]
        tampered_retry_transport_validation = (
            sync.validate_remote_authority_retry_budget_receipt(
                tampered_retry_transport_budget,
                approval_fanout_receipt=fanout,
                engine_transaction_log_receipt=engine_log,
                required_participants=session["current_state"]["participants"],
                authority_route_trace=route_trace,
            )
        )
        tampered_slo_quorum = dict(slo_quorum)
        tampered_slo_quorum["authority_slo_probe_receipts"] = [slo_probe]
        tampered_slo_quorum_validation = sync.validate_authority_slo_probe_quorum_receipt(
            tampered_slo_quorum,
            authority_route_trace=route_trace,
        )
        tampered_route_trace = dict(route_trace)
        tampered_route_trace["digest"] = sha256_text("tampered-slo-route-trace")
        tampered_slo_route_validation = sync.validate_authority_slo_probe_quorum_receipt(
            slo_quorum,
            authority_route_trace=tampered_route_trace,
        )
        tampered_threshold_policy = dict(slo_quorum_threshold_policy)
        tampered_threshold_policy["required_authority_count"] = 3
        tampered_threshold_policy_validation = (
            sync.validate_authority_slo_quorum_threshold_policy_receipt(
                tampered_threshold_policy
            )
        )

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["fanout_complete"])
        self.assertTrue(validation["transport_receipt_set_authenticated"])
        self.assertTrue(validation["result_digest_bound"])
        self.assertTrue(validation["retry_policy_bound"])
        self.assertTrue(validation["partial_outage_recovered"])
        self.assertEqual("rejected", rejected_with_tampered_fanout["decision"])
        self.assertFalse(rejected_with_tampered_fanout["approval_fanout_complete"])
        self.assertTrue(physics_validation["ok"])
        self.assertTrue(physics_validation["approval_fanout_complete"])
        self.assertTrue(physics_validation["approval_fanout_digest_bound"])
        self.assertEqual("complete", fanout["fanout_status"])
        self.assertEqual("recovered", fanout["partial_outage_status"])
        self.assertEqual(1, fanout["retry_attempt_count"])
        self.assertEqual(
            [session["current_state"]["participants"][-1]],
            fanout["outage_participants"],
        )
        self.assertEqual(3, fanout["result_count"])
        self.assertTrue(slo_probe_validation["ok"])
        self.assertTrue(slo_probe_validation["authority_slo_live_probe_bound"])
        self.assertTrue(slo_probe["slo_endpoint_ref"].startswith("http://"))
        self.assertEqual(64, len(slo_probe["network_response_digest"]))
        self.assertFalse(slo_probe["raw_slo_payload_stored"])
        self.assertTrue(slo_quorum_threshold_policy_validation["ok"])
        self.assertTrue(
            slo_quorum_threshold_policy_validation["threshold_source_bound"]
        )
        self.assertTrue(slo_quorum_threshold_policy_validation["signature_bound"])
        self.assertTrue(slo_quorum_threshold_policy_validation["signer_roster_bound"])
        self.assertTrue(
            slo_quorum_threshold_policy_validation[
                "signer_roster_verifier_quorum_bound"
            ]
        )
        self.assertTrue(
            slo_quorum_threshold_policy_validation["revocation_registry_bound"]
        )
        self.assertEqual(2, slo_quorum_threshold_policy["required_authority_count"])
        self.assertEqual(2, slo_quorum_threshold_policy["required_jurisdiction_count"])
        self.assertTrue(slo_quorum_threshold_policy["signer_roster_bound"])
        self.assertTrue(
            slo_quorum_threshold_policy["signer_roster_verifier_quorum_bound"]
        )
        self.assertTrue(slo_quorum_threshold_policy["revocation_registry_bound"])
        self.assertEqual(
            "verified",
            slo_quorum_threshold_policy["threshold_authority_binding_status"],
        )
        self.assertFalse(
            slo_quorum_threshold_policy["raw_threshold_policy_payload_stored"]
        )
        self.assertFalse(
            slo_quorum_threshold_policy["raw_signer_roster_payload_stored"]
        )
        self.assertFalse(
            slo_quorum_threshold_policy["raw_revocation_registry_payload_stored"]
        )
        self.assertFalse(slo_quorum_threshold_policy["raw_authority_payload_stored"])
        self.assertTrue(slo_quorum_validation["ok"])
        self.assertTrue(slo_quorum_validation["quorum_bound"])
        self.assertTrue(slo_quorum_validation["multi_authority_bound"])
        self.assertTrue(slo_quorum_validation["multi_jurisdiction_bound"])
        self.assertTrue(slo_quorum_validation["threshold_policy_source_bound"])
        self.assertTrue(slo_quorum_validation["threshold_policy_signature_bound"])
        self.assertTrue(slo_quorum_validation["threshold_signer_roster_bound"])
        self.assertTrue(
            slo_quorum_validation["threshold_signer_roster_verifier_quorum_bound"]
        )
        self.assertTrue(slo_quorum_validation["threshold_revocation_registry_bound"])
        self.assertTrue(slo_quorum_validation["authority_slo_transport_trace_bound"])
        self.assertTrue(
            slo_quorum_validation["authority_slo_transport_cross_host_bound"]
        )
        self.assertTrue(slo_quorum_validation["raw_transport_payload_redacted"])
        self.assertEqual(2, slo_quorum["accepted_probe_count"])
        self.assertEqual(2, slo_quorum["accepted_authority_count"])
        self.assertEqual(2, slo_quorum["accepted_jurisdiction_count"])
        self.assertEqual(2, slo_quorum["required_jurisdiction_count"])
        self.assertEqual(slo_probe["digest"], slo_quorum["primary_probe_digest"])
        self.assertEqual(route_trace["digest"], slo_quorum["authority_route_trace_digest"])
        self.assertEqual(
            [binding["route_binding_ref"] for binding in route_trace["route_bindings"]],
            slo_quorum["transport_route_binding_refs"],
        )
        self.assertEqual(slo_quorum["route_refs"], slo_quorum["transport_route_binding_refs"])
        self.assertEqual(
            slo_quorum_threshold_policy["digest"],
            slo_quorum["threshold_policy_digest"],
        )
        self.assertEqual(
            slo_quorum_threshold_policy["policy_signature_digest"],
            slo_quorum["threshold_policy_signature_digest"],
        )
        self.assertEqual(
            slo_quorum_threshold_policy["signer_roster_digest"],
            slo_quorum["threshold_signer_roster_digest"],
        )
        self.assertEqual(
            slo_quorum_threshold_policy[
                "signer_roster_verifier_response_set_digest"
            ],
            slo_quorum["threshold_signer_roster_verifier_response_set_digest"],
        )
        self.assertTrue(slo_quorum["threshold_signer_roster_verifier_quorum_bound"])
        self.assertEqual(
            slo_quorum_threshold_policy["revocation_registry_digest"],
            slo_quorum["threshold_revocation_registry_digest"],
        )
        self.assertTrue(slo_quorum["threshold_revocation_registry_bound"])
        self.assertEqual("verified", slo_quorum["threshold_authority_binding_status"])
        self.assertEqual(
            [slo_probe["digest"], backup_slo_probe["digest"]],
            slo_quorum["accepted_probe_digests"],
        )
        self.assertFalse(slo_quorum["raw_slo_payload_stored"])
        self.assertFalse(slo_quorum["raw_threshold_policy_payload_stored"])
        self.assertFalse(slo_quorum["raw_threshold_signer_roster_payload_stored"])
        self.assertFalse(slo_quorum["raw_threshold_revocation_registry_payload_stored"])
        self.assertFalse(slo_quorum["raw_threshold_authority_payload_stored"])
        self.assertFalse(slo_quorum["raw_transport_payload_stored"])
        self.assertTrue(retry_budget_validation["ok"])
        self.assertTrue(retry_budget_validation["adaptive_retry_budget_bound"])
        self.assertTrue(retry_budget_validation["engine_log_fanout_bound"])
        self.assertTrue(retry_budget_validation["route_health_bound"])
        self.assertTrue(retry_budget_validation["jurisdiction_rate_limit_bound"])
        self.assertTrue(retry_budget_validation["jurisdiction_policy_registry_bound"])
        self.assertTrue(retry_budget_validation["authority_slo_snapshot_bound"])
        self.assertTrue(retry_budget_validation["authority_slo_live_probe_bound"])
        self.assertTrue(retry_budget_validation["authority_slo_probe_quorum_bound"])
        self.assertTrue(retry_budget_validation["retry_budget_transport_trace_bound"])
        self.assertTrue(retry_budget_validation["registry_slo_schedule_bound"])
        self.assertTrue(retry_budget_validation["authority_signature_bound"])
        self.assertTrue(retry_budget_validation["signed_jurisdiction_retry_budget_bound"])
        self.assertTrue(retry_budget_validation["registry_bound_retry_budget_bound"])
        self.assertTrue(retry_budget_validation["schedule_bound"])
        self.assertEqual("complete", retry_budget["budget_status"])
        self.assertEqual(250, retry_budget["total_scheduled_delay_ms"])
        self.assertEqual(["JP-13"], retry_budget["remote_jurisdictions"])
        self.assertTrue(retry_budget["jurisdiction_rate_limit_bound"])
        self.assertTrue(retry_budget["jurisdiction_policy_registry_bound"])
        self.assertTrue(retry_budget["authority_slo_snapshot_bound"])
        self.assertTrue(retry_budget["authority_slo_live_probe_bound"])
        self.assertEqual([slo_probe["digest"]], retry_budget["authority_slo_probe_digests"])
        self.assertTrue(retry_budget["authority_slo_probe_quorum_bound"])
        self.assertTrue(retry_budget["retry_budget_transport_trace_bound"])
        self.assertEqual(
            slo_quorum["digest"],
            retry_budget["authority_slo_probe_quorum_digest"],
        )
        self.assertEqual(
            slo_probe["digest"],
            retry_budget["authority_slo_probe_quorum_primary_probe_digest"],
        )
        self.assertEqual(
            route_trace["digest"],
            retry_budget["authority_route_trace_digest"],
        )
        self.assertEqual(
            slo_quorum["transport_route_binding_refs"],
            retry_budget["transport_route_binding_refs"],
        )
        self.assertEqual(64, len(retry_budget["retry_transport_binding_digest"]))
        self.assertTrue(retry_budget["registry_slo_schedule_bound"])
        self.assertTrue(retry_budget["registry_bound_retry_budget_bound"])
        self.assertTrue(retry_budget["authority_signature_bound"])
        self.assertEqual(
            ["policy-registry://jp-13/test-wms-authority-retry"],
            retry_budget["jurisdiction_policy_registry_refs"],
        )
        self.assertEqual(
            ["authority-slo://test/federation/observer-timeout"],
            retry_budget["authority_slo_snapshot_refs"],
        )
        self.assertEqual(
            500,
            retry_budget["schedule_entries"][0]["registry_slo_retry_limit_ms"],
        )
        self.assertFalse(retry_budget["raw_remote_transcript_stored"])
        self.assertFalse(tampered_budget_validation["ok"])
        self.assertFalse(tampered_budget_validation["digest_bound"])
        self.assertFalse(tampered_signature_validation["ok"])
        self.assertFalse(tampered_signature_validation["authority_signature_bound"])
        self.assertFalse(tampered_registry_validation["ok"])
        self.assertFalse(tampered_registry_validation["jurisdiction_policy_registry_bound"])
        self.assertFalse(tampered_slo_probe_validation["ok"])
        self.assertFalse(tampered_slo_probe_validation["authority_slo_live_probe_bound"])
        self.assertFalse(tampered_slo_quorum_budget_validation["ok"])
        self.assertFalse(
            tampered_slo_quorum_budget_validation[
                "retry_budget_transport_trace_bound"
            ]
        )
        self.assertFalse(tampered_retry_transport_validation["ok"])
        self.assertFalse(
            tampered_retry_transport_validation[
                "retry_budget_transport_trace_bound"
            ]
        )
        self.assertFalse(tampered_slo_quorum_validation["ok"])
        self.assertFalse(tampered_slo_quorum_validation["multi_jurisdiction_bound"])
        self.assertFalse(tampered_slo_route_validation["ok"])
        self.assertFalse(
            tampered_slo_route_validation["authority_slo_transport_trace_bound"]
        )
        self.assertFalse(tampered_threshold_policy_validation["ok"])
        self.assertFalse(tampered_threshold_policy_validation["policy_body_bound"])
        tampered_roster_policy = dict(slo_quorum_threshold_policy)
        tampered_roster_policy["signer_roster_digest"] = sha256_text(
            "tampered-threshold-signer-roster"
        )
        tampered_roster_validation = (
            sync.validate_authority_slo_quorum_threshold_policy_receipt(
                tampered_roster_policy
            )
        )
        self.assertFalse(tampered_roster_validation["ok"])
        self.assertFalse(tampered_roster_validation["signer_roster_bound"])
        tampered_revocation_policy = dict(slo_quorum_threshold_policy)
        tampered_revocation_policy["revocation_registry_digest"] = sha256_text(
            "tampered-threshold-revocation-registry"
        )
        tampered_revocation_validation = (
            sync.validate_authority_slo_quorum_threshold_policy_receipt(
                tampered_revocation_policy
            )
        )
        self.assertFalse(tampered_revocation_validation["ok"])
        self.assertFalse(tampered_revocation_validation["revocation_registry_bound"])

    def test_engine_transaction_log_binds_ordered_digest_only_entries(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )
        state_digest = sha256_text(canonical_json(sync.snapshot(session["session_id"])))
        engine_session_ref = f"engine-session://test/{session['session_id']}"
        source_digests = {
            "time_rate_escape_evidence": sha256_text("time-rate-evidence"),
            "approval_collection_bound": sha256_text("approval-collection"),
            "approval_fanout_bound": sha256_text("approval-fanout"),
            "physics_rules_apply": sha256_text("physics-apply"),
            "physics_rules_revert": sha256_text("physics-revert"),
        }
        entries = [
            sync.build_engine_transaction_entry(
                transaction_id=f"engine-txn://test/{index}",
                transaction_index=index,
                operation=operation,
                source_artifact_kind=(
                    "wms_reconcile"
                    if operation == "time_rate_escape_evidence"
                    else "wms_physics_rules_change_receipt"
                ),
                source_artifact_ref=f"artifact://{operation}",
                source_artifact_digest=source_digests[operation],
                engine_session_ref=engine_session_ref,
                engine_state_before_digest=state_digest,
                engine_state_after_digest=state_digest,
                participant_ids=session["current_state"]["participants"],
            )
            for index, operation in enumerate(source_digests, start=1)
        ]

        receipt = sync.build_engine_transaction_log_receipt(
            session["session_id"],
            engine_adapter_ref="engine-adapter://test/reference",
            engine_adapter_key_ref="engine-key://test/reference/signer",
            engine_session_ref=engine_session_ref,
            transaction_log_ref=f"engine-log://test/{session['session_id']}",
            transaction_entries=entries,
            source_artifact_digests=source_digests,
        )
        validation = sync.validate_engine_transaction_log_receipt(
            receipt,
            source_artifact_digests=source_digests,
        )
        tampered = dict(receipt)
        tampered["transaction_entries"] = [dict(entry) for entry in receipt["transaction_entries"]]
        tampered["transaction_entries"][0]["source_artifact_digest"] = sha256_text("tampered")
        tampered_validation = sync.validate_engine_transaction_log_receipt(
            tampered,
            source_artifact_digests=source_digests,
        )
        tampered_signature = dict(receipt)
        tampered_signature["engine_adapter_signature_digest"] = sha256_text(
            "tampered-adapter-signature"
        )
        tampered_signature_validation = sync.validate_engine_transaction_log_receipt(
            tampered_signature,
            source_artifact_digests=source_digests,
        )

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["engine_binding_complete"])
        self.assertTrue(validation["entry_order_bound"])
        self.assertTrue(validation["source_artifacts_bound"])
        self.assertTrue(validation["redaction_complete"])
        self.assertTrue(validation["engine_adapter_signature_bound"])
        self.assertTrue(validation["signature_digest_bound"])
        self.assertTrue(validation["raw_adapter_signature_excluded"])
        self.assertEqual("complete", receipt["engine_binding_status"])
        self.assertEqual(
            "signed-wms-engine-adapter-log-v1",
            receipt["engine_adapter_signature_profile"],
        )
        self.assertEqual(
            "wms-engine-adapter-signature-digest-v1",
            receipt["engine_adapter_signature_digest_profile"],
        )
        self.assertEqual(
            "engine-key://test/reference/signer",
            receipt["engine_adapter_key_ref"],
        )
        self.assertTrue(receipt["engine_adapter_signature_bound"])
        self.assertFalse(receipt["raw_adapter_signature_stored"])
        self.assertEqual(receipt["required_operations"], receipt["covered_operations"])
        self.assertFalse(tampered_validation["ok"])
        self.assertFalse(tampered_validation["source_artifacts_bound"])
        self.assertFalse(tampered_signature_validation["ok"])
        self.assertFalse(tampered_signature_validation["signature_digest_bound"])
        self.assertFalse(
            tampered_signature_validation["engine_adapter_signature_bound"]
        )

    def test_engine_route_binding_binds_transaction_log_to_authority_trace(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )
        state_digest = sha256_text(canonical_json(sync.snapshot(session["session_id"])))
        engine_session_ref = f"engine-session://test/{session['session_id']}"
        source_digest = sha256_text("approval-fanout")
        entry = sync.build_engine_transaction_entry(
            transaction_id="engine-txn://test/route-binding/001",
            transaction_index=1,
            operation="approval_fanout_bound",
            source_artifact_kind="wms_distributed_approval_fanout_receipt",
            source_artifact_ref="artifact://approval-fanout",
            source_artifact_digest=source_digest,
            engine_session_ref=engine_session_ref,
            engine_state_before_digest=state_digest,
            engine_state_after_digest=state_digest,
            participant_ids=session["current_state"]["participants"],
        )
        engine_log = sync.build_engine_transaction_log_receipt(
            session["session_id"],
            engine_adapter_ref="engine-adapter://test/reference",
            engine_session_ref=engine_session_ref,
            transaction_log_ref=f"engine-log://test/{session['session_id']}",
            transaction_entries=[entry],
            required_operations=["approval_fanout_bound"],
            source_artifact_digests={"approval_fanout_bound": source_digest},
        )
        route_trace = self._authority_route_trace()

        receipt = sync.build_engine_route_binding_receipt(
            session["session_id"],
            engine_transaction_log_receipt=engine_log,
            authority_route_trace=route_trace,
        )
        validation = sync.validate_engine_route_binding_receipt(
            receipt,
            engine_transaction_log_receipt=engine_log,
            authority_route_trace=route_trace,
        )
        tampered_trace = dict(route_trace)
        tampered_trace["digest"] = sha256_text("tampered-route-trace")
        tampered_validation = sync.validate_engine_route_binding_receipt(
            receipt,
            engine_transaction_log_receipt=engine_log,
            authority_route_trace=tampered_trace,
        )

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["engine_log_bound"])
        self.assertTrue(validation["authority_route_trace_bound"])
        self.assertTrue(validation["cross_host_route_bound"])
        self.assertTrue(validation["engine_route_binding_complete"])
        self.assertEqual("complete", receipt["engine_route_binding_status"])
        self.assertFalse(receipt["raw_engine_payload_stored"])
        self.assertFalse(receipt["raw_route_payload_stored"])
        self.assertEqual(route_trace["digest"], receipt["authority_route_trace_digest"])
        self.assertEqual(engine_log["digest"], receipt["engine_transaction_log_digest"])
        self.assertFalse(tampered_validation["ok"])
        self.assertFalse(tampered_validation["authority_route_trace_bound"])

    def test_engine_capture_binding_binds_route_to_capture_evidence(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )
        state_digest = sha256_text(canonical_json(sync.snapshot(session["session_id"])))
        engine_session_ref = f"engine-session://test/{session['session_id']}"
        source_digest = sha256_text("approval-fanout")
        entry = sync.build_engine_transaction_entry(
            transaction_id="engine-txn://test/capture-binding/001",
            transaction_index=1,
            operation="approval_fanout_bound",
            source_artifact_kind="wms_distributed_approval_fanout_receipt",
            source_artifact_ref="artifact://approval-fanout",
            source_artifact_digest=source_digest,
            engine_session_ref=engine_session_ref,
            engine_state_before_digest=state_digest,
            engine_state_after_digest=state_digest,
            participant_ids=session["current_state"]["participants"],
        )
        engine_log = sync.build_engine_transaction_log_receipt(
            session["session_id"],
            engine_adapter_ref="engine-adapter://test/reference",
            engine_session_ref=engine_session_ref,
            transaction_log_ref=f"engine-log://test/{session['session_id']}",
            transaction_entries=[entry],
            required_operations=["approval_fanout_bound"],
            source_artifact_digests={"approval_fanout_bound": source_digest},
        )
        route_trace = self._authority_route_trace()
        route_binding = sync.build_engine_route_binding_receipt(
            session["session_id"],
            engine_transaction_log_receipt=engine_log,
            authority_route_trace=route_trace,
        )
        packet_capture = self._packet_capture_export(route_trace)
        acquisition = self._privileged_capture_acquisition(route_trace, packet_capture)

        receipt = sync.build_engine_capture_binding_receipt(
            session["session_id"],
            engine_route_binding_receipt=route_binding,
            packet_capture_export=packet_capture,
            privileged_capture_acquisition=acquisition,
        )
        validation = sync.validate_engine_capture_binding_receipt(
            receipt,
            engine_route_binding_receipt=route_binding,
            packet_capture_export=packet_capture,
            privileged_capture_acquisition=acquisition,
        )
        tampered_acquisition = dict(acquisition)
        tampered_acquisition["filter_digest"] = sha256_text("tampered-filter")
        tampered_validation = sync.validate_engine_capture_binding_receipt(
            receipt,
            engine_route_binding_receipt=route_binding,
            packet_capture_export=packet_capture,
            privileged_capture_acquisition=tampered_acquisition,
        )

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["engine_route_binding_bound"])
        self.assertTrue(validation["packet_capture_bound"])
        self.assertTrue(validation["privileged_capture_bound"])
        self.assertTrue(validation["route_binding_set_bound"])
        self.assertTrue(validation["engine_capture_binding_complete"])
        self.assertEqual("complete", receipt["engine_capture_binding_status"])
        self.assertEqual(route_binding["digest"], receipt["engine_route_binding_digest"])
        self.assertEqual(packet_capture["digest"], receipt["packet_capture_digest"])
        self.assertEqual(acquisition["digest"], receipt["privileged_capture_digest"])
        self.assertEqual(4, receipt["packet_count"])
        self.assertFalse(receipt["raw_engine_payload_stored"])
        self.assertFalse(receipt["raw_route_payload_stored"])
        self.assertFalse(receipt["raw_packet_body_stored"])
        self.assertFalse(tampered_validation["ok"])
        self.assertFalse(tampered_validation["privileged_capture_bound"])

    def test_physics_rules_change_rejects_missing_peer_approval(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )
        baseline = sync.snapshot(session["session_id"])

        receipt = sync.propose_physics_rules_change(
            session["session_id"],
            requested_by="identity://primary",
            proposed_physics_rules_ref="physics://shared-atrium/low-gravity-v1",
            rationale="bounded rehearsal",
            participant_approvals=["identity://primary"],
            guardian_attested=True,
        )
        unchanged = sync.snapshot(session["session_id"])

        self.assertEqual("rejected", receipt["decision"])
        self.assertFalse(receipt["approval_quorum_met"])
        self.assertFalse(receipt["approval_transport_quorum_met"])
        self.assertEqual(baseline["physics_rules_ref"], unchanged["physics_rules_ref"])

    def test_physics_rules_change_rejects_static_approval_without_transport(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )
        baseline = sync.snapshot(session["session_id"])

        receipt = sync.propose_physics_rules_change(
            session["session_id"],
            requested_by="identity://primary",
            proposed_physics_rules_ref="physics://shared-atrium/low-gravity-v1",
            rationale="bounded rehearsal",
            participant_approvals=["identity://primary", "identity://peer"],
            guardian_attested=True,
        )
        unchanged = sync.snapshot(session["session_id"])

        self.assertEqual("rejected", receipt["decision"])
        self.assertTrue(receipt["approval_quorum_met"])
        self.assertFalse(receipt["approval_transport_quorum_met"])
        self.assertEqual(baseline["physics_rules_ref"], unchanged["physics_rules_ref"])


if __name__ == "__main__":
    unittest.main()
