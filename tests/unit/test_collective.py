from __future__ import annotations

from contextlib import contextmanager
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import unittest

from omoikane.common import canonical_json, sha256_text
from omoikane.interface.collective import CollectiveIdentityService


@contextmanager
def live_ack_endpoint(payload: dict[str, object]):
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
        yield f"http://127.0.0.1:{server.server_address[1]}/registry-ack"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1.0)


class CollectiveIdentityServiceTests(unittest.TestCase):
    @staticmethod
    def _identity_confirmation_profile(member_id: str, digest_seed: str = "a") -> dict:
        digest = digest_seed * 64
        consistency_digest = "b" * 64 if digest_seed != "b" else "c" * 64
        return {
            "confirmation_id": f"identity-confirmation-{digest_seed * 12}",
            "profile_id": "multidimensional-identity-confirmation-v1",
            "identity_id": member_id,
            "required_dimensions": [
                "episodic_recall",
                "self_model_alignment",
                "subjective_self_report",
                "third_party_witness_alignment",
            ],
            "result": "passed",
            "active_transition_allowed": True,
            "confirmation_digest": digest,
            "witness_quorum": {"status": "met"},
            "self_report_witness_consistency": {
                "policy_id": "identity-self-report-witness-consistency-v1",
                "status": "bound",
                "consistency_digest": consistency_digest,
            },
        }

    @staticmethod
    def _authority_route_trace() -> dict:
        def route_binding(index: int, digest_seed: str) -> dict:
            suffix = f"{index}" * 16
            return {
                "key_server_ref": f"keyserver://federation/notary-{index}",
                "server_role": "quorum-notary" if index == 1 else "directory-mirror",
                "authority_status": "active",
                "server_endpoint": f"https://10.0.0.{index}:443/authority-route-{index}",
                "server_name": "authority.local",
                "remote_host_ref": f"host://federation/authority-edge-{index}",
                "remote_host_attestation_ref": (
                    f"host-attestation://federation/authority-edge-{index}/2026-04-26"
                ),
                "authority_cluster_ref": "authority-cluster://federation/review-window",
                "remote_jurisdiction": "JP-13" if index == 1 else "US-CA",
                "remote_network_zone": "apne1" if index == 1 else "usw2",
                "route_binding_ref": f"authority-route://federation/{suffix}",
                "matched_root_refs": [f"root://federation/pki-{index}"],
                "mtls_status": "authenticated",
                "response_digest_bound": True,
                "os_observer_receipt": {
                    "receipt_id": f"authority-os-observer://{suffix}",
                    "receipt_status": "observed",
                    "host_binding_digest": digest_seed * 64,
                },
                "socket_trace": {
                    "non_loopback": True,
                    "response_digest": digest_seed * 64,
                },
            }

        return {
            "kind": "distributed_transport_authority_route_trace",
            "schema_version": "1.0.0",
            "trace_ref": "authority-route-trace://federation/test",
            "authority_plane_ref": "authority-plane://federation/test",
            "authority_plane_digest": "d" * 64,
            "route_target_discovery_ref": "authority-route-targets://federation/test",
            "route_target_discovery_digest": "e" * 64,
            "council_tier": "federation",
            "transport_profile": "federation-mtls-quorum-v1",
            "trace_profile": "non-loopback-mtls-authority-route-v1",
            "socket_trace_profile": "mtls-socket-trace-v1",
            "os_observer_profile": "os-native-tcp-observer-v1",
            "cross_host_binding_profile": "attested-cross-host-authority-binding-v1",
            "route_target_discovery_profile": "bounded-authority-route-target-discovery-v1",
            "route_count": 2,
            "mtls_authenticated_count": 2,
            "distinct_remote_host_count": 2,
            "non_loopback_verified": True,
            "authority_plane_bound": True,
            "response_digest_bound": True,
            "socket_trace_complete": True,
            "os_observer_complete": True,
            "route_target_discovery_bound": True,
            "cross_host_verified": True,
            "route_bindings": [
                route_binding(1, "4"),
                route_binding(2, "5"),
            ],
            "trace_status": "authenticated",
            "digest": "f" * 64,
        }

    @staticmethod
    def _packet_capture_export(route_trace: dict) -> dict:
        route_exports = []
        for index, route in enumerate(route_trace["route_bindings"], start=1):
            socket = route["socket_trace"]
            route_exports.append(
                {
                    "key_server_ref": route["key_server_ref"],
                    "route_binding_ref": route["route_binding_ref"],
                    "local_ip": f"192.0.2.{index}",
                    "local_port": 51000 + index,
                    "remote_ip": f"198.51.100.{index}",
                    "remote_port": 443,
                    "outbound_tuple_digest": sha256_text(f"outbound-{index}"),
                    "inbound_tuple_digest": sha256_text(f"inbound-{index}"),
                    "packet_order": ["outbound-request", "inbound-response"],
                    "outbound_request_bytes": 96 + index,
                    "inbound_response_bytes": 320 + index,
                    "outbound_payload_digest": sha256_text(f"request-{index}"),
                    "inbound_payload_digest": socket["response_digest"],
                    "readback_packet_count": 2,
                    "readback_verified": True,
                    "os_native_readback_verified": True,
                }
            )
        receipt = {
            "kind": "distributed_transport_packet_capture_export",
            "schema_version": "1.0.0",
            "capture_ref": "authority-packet-capture://federation/test",
            "trace_ref": route_trace["trace_ref"],
            "trace_digest": route_trace["digest"],
            "authority_plane_ref": route_trace["authority_plane_ref"],
            "authority_plane_digest": route_trace["authority_plane_digest"],
            "envelope_ref": "distributed-envelope-test",
            "envelope_digest": "6" * 64,
            "council_tier": route_trace["council_tier"],
            "transport_profile": route_trace["transport_profile"],
            "capture_profile": "trace-bound-pcap-export-v1",
            "artifact_format": "pcap",
            "readback_profile": "pcap-readback-v1",
            "os_native_readback_profile": "tcpdump-readback-v1",
            "route_count": len(route_exports),
            "packet_count": len(route_exports) * 2,
            "artifact_size_bytes": 512,
            "artifact_digest": sha256_text("collective-pcap-artifact"),
            "readback_digest": sha256_text("collective-pcap-readback"),
            "route_exports": route_exports,
            "os_native_readback_available": True,
            "os_native_readback_ok": True,
            "export_status": "verified",
            "recorded_at": "2026-04-26T00:00:00Z",
        }
        receipt["digest"] = sha256_text(
            canonical_json(
                {
                    key: value
                    for key, value in receipt.items()
                    if key not in {"kind", "schema_version", "digest"}
                }
            )
        )
        return receipt

    @staticmethod
    def _privileged_capture_acquisition(route_trace: dict, capture_export: dict) -> dict:
        route_refs = [route["route_binding_ref"] for route in route_trace["route_bindings"]]
        capture_filter = "tcp and host 192.0.2.1"
        receipt = {
            "kind": "distributed_transport_privileged_capture_acquisition",
            "schema_version": "1.0.0",
            "acquisition_ref": "authority-live-capture://federation/test",
            "trace_ref": route_trace["trace_ref"],
            "trace_digest": route_trace["digest"],
            "capture_ref": capture_export["capture_ref"],
            "capture_digest": capture_export["digest"],
            "authority_plane_ref": route_trace["authority_plane_ref"],
            "authority_plane_digest": route_trace["authority_plane_digest"],
            "envelope_ref": "distributed-envelope-test",
            "envelope_digest": "6" * 64,
            "council_tier": route_trace["council_tier"],
            "transport_profile": route_trace["transport_profile"],
            "acquisition_profile": "bounded-live-interface-capture-acquisition-v1",
            "broker_profile": "delegated-privileged-capture-broker-v1",
            "privilege_mode": "delegated-broker",
            "lease_ref": "capture-lease://federation/test",
            "broker_attestation_ref": "broker://authority-capture/test",
            "interface_name": "en0",
            "local_ips": ["192.0.2.1"],
            "capture_filter": capture_filter,
            "filter_digest": sha256_text(capture_filter),
            "route_binding_refs": route_refs,
            "capture_command": [
                "/usr/sbin/tcpdump",
                "-i",
                "en0",
                "-w",
                "{capture_output_path}",
                capture_filter,
            ],
            "lease_duration_s": 300,
            "lease_expires_at": "2026-04-26T00:05:00Z",
            "grant_status": "granted",
            "recorded_at": "2026-04-26T00:00:00Z",
        }
        receipt["digest"] = sha256_text(
            canonical_json(
                {
                    key: value
                    for key, value in receipt.items()
                    if key not in {"kind", "schema_version", "digest"}
                }
            )
        )
        return receipt

    def test_register_open_close_and_dissolve_collective(self) -> None:
        service = CollectiveIdentityService()
        record = service.register_collective(
            collective_identity_id="collective://meridian",
            member_ids=["identity://origin", "identity://peer"],
            purpose="bounded merge for shared planning",
            proposed_name="Collective Meridian",
            council_witnessed=True,
            federation_attested=True,
            guardian_observed=True,
        )
        session = service.open_merge_session(
            collective_id=record["collective_id"],
            imc_session_id="imc://merge-session",
            wms_session_id="wms://shared-session",
            requested_duration_seconds=8.0,
            council_witnessed=True,
            federation_attested=True,
            guardian_observed=True,
            shared_world_mode="shared_reality",
        )
        closed = service.close_merge_session(
            session["merge_session_id"],
            disconnect_reason="bounded merge completed",
            time_in_merge_seconds=7.8,
            resulting_wms_mode="private_reality",
            identity_confirmations={
                "identity://origin": True,
                "identity://peer": True,
            },
        )
        dissolved = service.dissolve_collective(
            record["collective_id"],
            requested_by="identity://origin",
            member_confirmations={
                "identity://origin": True,
                "identity://peer": True,
            },
            identity_confirmation_profiles={
                "identity://origin": self._identity_confirmation_profile(
                    "identity://origin",
                    "a",
                ),
                "identity://peer": self._identity_confirmation_profile(
                    "identity://peer",
                    "c",
                ),
            },
            reason="members returned to independent subjectivity",
        )
        final_record = service.snapshot(record["collective_id"])
        record_validation = service.validate_record(final_record)
        session_validation = service.validate_merge_session(closed)
        dissolution_validation = service.validate_dissolution_receipt(dissolved)
        transport_binding = service.bind_recovery_verifier_transport(dissolved)
        transport_validation = service.validate_recovery_verifier_transport_binding(
            transport_binding,
            dissolved,
        )
        route_trace_binding = service.bind_recovery_verifier_route_trace(
            transport_binding,
            self._authority_route_trace(),
        )
        route_trace_validation = service.validate_recovery_verifier_route_trace_binding(
            route_trace_binding,
            transport_binding,
            self._authority_route_trace(),
        )
        route_trace = self._authority_route_trace()
        packet_capture = self._packet_capture_export(route_trace)
        privileged_capture = self._privileged_capture_acquisition(
            route_trace,
            packet_capture,
        )
        capture_binding = service.bind_recovery_route_trace_capture_export(
            route_trace_binding,
            packet_capture,
            privileged_capture,
        )
        capture_validation = service.validate_recovery_route_trace_capture_export_binding(
            capture_binding,
            route_trace_binding,
            packet_capture,
            privileged_capture,
        )
        registry_sync = service.sync_dissolution_external_registry(
            capture_binding,
            registry_ack_authority_route_trace=route_trace,
            registry_ack_packet_capture_export=packet_capture,
            registry_ack_privileged_capture_acquisition=privileged_capture,
        )
        ack_endpoint_probes = []
        for index, ack_receipt in enumerate(registry_sync["ack_quorum_receipts"]):
            payload = service.external_registry_ack_endpoint_payload(
                registry_sync,
                ack_receipt,
                checked_at=f"2026-04-26T11:10:0{index}Z",
            )
            with live_ack_endpoint(payload) as endpoint:
                ack_endpoint_probes.append(
                    service.probe_external_registry_ack_endpoint(
                        registry_ack_endpoint=endpoint,
                        external_registry_sync=registry_sync,
                        ack_receipt=ack_receipt,
                    )
                )
        registry_sync = service.bind_external_registry_ack_endpoint_probes(
            registry_sync,
            ack_endpoint_probes,
        )
        registry_validation = service.validate_collective_external_registry_sync(
            registry_sync,
            capture_binding,
            route_trace,
            packet_capture,
            privileged_capture,
        )
        tampered_registry_sync = dict(registry_sync)
        tampered_registry_sync["ack_quorum_digest_set"] = [
            registry_sync["ack_quorum_digest_set"][0],
            "0" * 64,
        ]
        tampered_registry_validation = service.validate_collective_external_registry_sync(
            tampered_registry_sync,
            capture_binding,
            route_trace,
            packet_capture,
            privileged_capture,
        )
        tampered_route_trace_registry_sync = dict(registry_sync)
        tampered_route_trace_registry_sync["ack_route_trace_binding_digest_set"] = [
            registry_sync["ack_route_trace_binding_digest_set"][0],
            "0" * 64,
        ]
        tampered_route_trace_registry_validation = (
            service.validate_collective_external_registry_sync(
                tampered_route_trace_registry_sync,
                capture_binding,
                route_trace,
                packet_capture,
                privileged_capture,
            )
        )
        tampered_ack_capture_registry_sync = dict(registry_sync)
        tampered_ack_capture_registry_sync["ack_route_capture_binding_digest_set"] = [
            registry_sync["ack_route_capture_binding_digest_set"][0],
            "0" * 64,
        ]
        tampered_ack_capture_registry_validation = (
            service.validate_collective_external_registry_sync(
                tampered_ack_capture_registry_sync,
                capture_binding,
                route_trace,
                packet_capture,
                privileged_capture,
            )
        )
        tampered_live_probe_registry_sync = dict(registry_sync)
        tampered_live_probe_registry_sync["ack_live_endpoint_probe_digests"] = [
            registry_sync["ack_live_endpoint_probe_digests"][0],
            "0" * 64,
        ]
        tampered_live_probe_registry_validation = (
            service.validate_collective_external_registry_sync(
                tampered_live_probe_registry_sync,
                capture_binding,
                route_trace,
                packet_capture,
                privileged_capture,
            )
        )
        tampered_signed_response_registry_sync = dict(registry_sync)
        tampered_signed_response_registry_sync[
            "ack_live_endpoint_response_signature_digests"
        ] = [
            registry_sync["ack_live_endpoint_response_signature_digests"][0],
            "0" * 64,
        ]
        tampered_signed_response_registry_validation = (
            service.validate_collective_external_registry_sync(
                tampered_signed_response_registry_sync,
                capture_binding,
                route_trace,
                packet_capture,
                privileged_capture,
            )
        )

        self.assertEqual("Collective Meridian", record["display_name"])
        self.assertEqual("completed", closed["status"])
        self.assertTrue(closed["within_budget"])
        self.assertTrue(closed["private_escape_honored"])
        self.assertEqual("1.0", dissolved["schema_version"])
        self.assertEqual("dissolved", dissolved["status"])
        self.assertEqual("dissolved", final_record["status"])
        self.assertTrue(record_validation["ok"])
        self.assertTrue(session_validation["ok"])
        self.assertTrue(session_validation["identity_confirmation_complete"])
        self.assertTrue(dissolution_validation["ok"])
        self.assertTrue(dissolution_validation["schema_version_bound"])
        self.assertTrue(dissolution_validation["member_confirmation_complete"])
        self.assertTrue(dissolution_validation["member_recovery_proofs_bound"])
        self.assertTrue(dissolution_validation["member_recovery_digest_set_bound"])
        self.assertTrue(dissolution_validation["member_recovery_binding_digest_bound"])
        self.assertFalse(dissolution_validation["raw_identity_confirmation_profiles_stored"])
        self.assertTrue(dissolution_validation["audit_bound"])
        self.assertEqual(
            "collective-dissolution-identity-confirmation-binding-v1",
            dissolved["member_recovery_binding_profile"],
        )
        self.assertEqual(
            ["a" * 64, "c" * 64],
            dissolved["member_recovery_confirmation_digest_set"],
        )
        self.assertTrue(transport_validation["ok"])
        self.assertTrue(transport_validation["dissolution_receipt_digest_bound"])
        self.assertTrue(transport_validation["verifier_transport_receipts_bound"])
        self.assertTrue(transport_validation["verifier_transport_binding_digest_bound"])
        self.assertFalse(transport_validation["raw_verifier_payload_stored"])
        self.assertEqual(
            "collective-dissolution-recovery-verifier-transport-v1",
            transport_binding["profile_id"],
        )
        self.assertEqual(2, transport_binding["verifier_transport_receipt_count"])
        self.assertTrue(route_trace_validation["ok"])
        self.assertTrue(route_trace_validation["recovery_transport_bound"])
        self.assertTrue(route_trace_validation["authority_route_trace_bound"])
        self.assertTrue(route_trace_validation["member_route_bindings_bound"])
        self.assertFalse(route_trace_validation["raw_route_payload_stored"])
        self.assertEqual(
            "collective-recovery-non-loopback-route-trace-binding-v1",
            route_trace_binding["profile_id"],
        )
        self.assertEqual(2, route_trace_binding["member_route_binding_count"])
        self.assertTrue(capture_validation["ok"])
        self.assertTrue(capture_validation["recovery_route_trace_bound"])
        self.assertTrue(capture_validation["packet_capture_bound"])
        self.assertTrue(capture_validation["privileged_capture_bound"])
        self.assertTrue(capture_validation["member_capture_bindings_bound"])
        self.assertFalse(capture_validation["raw_packet_body_stored"])
        self.assertEqual(
            "collective-recovery-route-trace-capture-export-v1",
            capture_binding["profile_id"],
        )
        self.assertEqual(2, capture_binding["member_capture_binding_count"])
        self.assertTrue(registry_validation["ok"])
        self.assertTrue(registry_validation["capture_export_bound"])
        self.assertTrue(registry_validation["submission_ack_bound"])
        self.assertTrue(registry_validation["ack_quorum_bound"])
        self.assertTrue(registry_validation["ack_route_trace_bound"])
        self.assertTrue(registry_validation["ack_route_packet_capture_bound"])
        self.assertTrue(registry_validation["ack_route_privileged_capture_bound"])
        self.assertTrue(registry_validation["ack_route_capture_bindings_bound"])
        self.assertTrue(registry_validation["ack_route_capture_route_binding_set_bound"])
        self.assertTrue(registry_validation["ack_route_capture_export_bound"])
        self.assertTrue(registry_validation["ack_live_endpoint_probe_bound"])
        self.assertTrue(
            registry_validation["ack_live_endpoint_signed_response_envelope_bound"]
        )
        self.assertFalse(registry_validation["raw_registry_payload_stored"])
        self.assertFalse(registry_validation["raw_ack_payload_stored"])
        self.assertFalse(registry_validation["raw_ack_route_payload_stored"])
        self.assertFalse(registry_validation["raw_ack_endpoint_payload_stored"])
        self.assertFalse(registry_validation["raw_response_signature_payload_stored"])
        self.assertFalse(registry_validation["raw_packet_body_stored"])
        self.assertEqual(
            "collective-external-registry-ack-quorum-v1",
            registry_sync["ack_quorum_profile_id"],
        )
        self.assertEqual(
            "collective-external-registry-ack-route-trace-v1",
            registry_sync["ack_route_trace_profile_id"],
        )
        self.assertEqual(2, registry_sync["ack_quorum_required_authority_count"])
        self.assertEqual(2, registry_sync["ack_quorum_required_jurisdiction_count"])
        self.assertEqual(["JP-13", "FEDERATION"], registry_sync["ack_quorum_jurisdictions"])
        self.assertEqual(2, len(registry_sync["ack_quorum_receipts"]))
        self.assertEqual("complete", registry_sync["ack_quorum_status"])
        self.assertEqual(2, registry_sync["ack_route_trace_binding_count"])
        self.assertTrue(registry_sync["ack_route_trace_bound"])
        self.assertEqual(
            "collective-external-registry-ack-route-capture-export-v1",
            registry_sync["ack_route_capture_export_profile_id"],
        )
        self.assertEqual(2, registry_sync["ack_route_capture_binding_count"])
        self.assertTrue(registry_sync["ack_route_capture_export_bound"])
        self.assertEqual(
            "collective-external-registry-ack-live-endpoint-probe-v1",
            registry_sync["ack_live_endpoint_probe_profile_id"],
        )
        self.assertEqual(2, registry_sync["ack_live_endpoint_probe_count"])
        self.assertTrue(registry_sync["ack_live_endpoint_probe_bound"])
        self.assertEqual(
            "collective-external-registry-ack-signed-response-envelope-v1",
            registry_sync["ack_live_endpoint_probe_receipts"][0][
                "response_envelope_profile"
            ],
        )
        self.assertEqual(
            2,
            len(registry_sync["ack_live_endpoint_response_signature_digests"]),
        )
        self.assertTrue(registry_sync["ack_live_endpoint_signed_response_envelope_bound"])
        self.assertFalse(tampered_registry_validation["ok"])
        self.assertFalse(tampered_registry_validation["ack_quorum_bound"])
        self.assertFalse(tampered_route_trace_registry_validation["ok"])
        self.assertFalse(tampered_route_trace_registry_validation["ack_route_trace_bound"])
        self.assertFalse(tampered_ack_capture_registry_validation["ok"])
        self.assertFalse(
            tampered_ack_capture_registry_validation["ack_route_capture_bindings_bound"]
        )
        self.assertFalse(tampered_live_probe_registry_validation["ok"])
        self.assertFalse(tampered_live_probe_registry_validation["ack_live_endpoint_probe_bound"])
        self.assertFalse(tampered_signed_response_registry_validation["ok"])
        self.assertFalse(
            tampered_signed_response_registry_validation[
                "ack_live_endpoint_signed_response_envelope_bound"
            ]
        )

    def test_dissolve_rejects_missing_identity_confirmation_profile(self) -> None:
        service = CollectiveIdentityService()
        record = service.register_collective(
            collective_identity_id="collective://meridian",
            member_ids=["identity://origin", "identity://peer"],
            purpose="bounded merge for shared planning",
            proposed_name="Collective Meridian",
            council_witnessed=True,
            federation_attested=True,
            guardian_observed=True,
        )

        with self.assertRaisesRegex(ValueError, "missing identity confirmation profile"):
            service.dissolve_collective(
                record["collective_id"],
                requested_by="identity://origin",
                member_confirmations={
                    "identity://origin": True,
                    "identity://peer": True,
                },
                identity_confirmation_profiles={
                    "identity://origin": self._identity_confirmation_profile(
                        "identity://origin",
                        "a",
                    ),
                },
                reason="members returned to independent subjectivity",
            )

    def test_open_requires_full_oversight(self) -> None:
        service = CollectiveIdentityService()
        record = service.register_collective(
            collective_identity_id="collective://meridian",
            member_ids=["identity://origin", "identity://peer"],
            purpose="bounded merge for shared planning",
            proposed_name="Collective Meridian",
            council_witnessed=True,
            federation_attested=True,
            guardian_observed=True,
        )

        with self.assertRaisesRegex(PermissionError, "federation attestation"):
            service.open_merge_session(
                collective_id=record["collective_id"],
                imc_session_id="imc://merge-session",
                wms_session_id="wms://shared-session",
                requested_duration_seconds=8.0,
                council_witnessed=True,
                federation_attested=False,
                guardian_observed=True,
                shared_world_mode="shared_reality",
            )


if __name__ == "__main__":
    unittest.main()
