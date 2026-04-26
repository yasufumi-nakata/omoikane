from __future__ import annotations

import unittest

from omoikane.interface.collective import CollectiveIdentityService


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
