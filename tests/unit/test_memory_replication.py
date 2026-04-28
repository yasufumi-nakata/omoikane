from __future__ import annotations

import unittest

from omoikane.mind.memory import MemoryCrystalStore, MemoryReplicationService


class MemoryReplicationServiceTests(unittest.TestCase):
    def test_reference_session_validates_with_quorum_and_council_escalation(self) -> None:
        service = MemoryReplicationService()

        session = service.build_reference_session("identity-demo")
        validation = service.validate_session(session)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["quorum_ok"])
        self.assertTrue(validation["council_escalated"])
        self.assertTrue(validation["resync_required"])
        self.assertTrue(validation["key_succession_bound"])
        self.assertTrue(validation["key_succession_guardian_quorum_ok"])
        self.assertTrue(validation["key_succession_threshold_ok"])
        self.assertTrue(validation["key_succession_signer_roster_policy_bound"])
        self.assertTrue(validation["key_succession_signer_roster_quorum_ok"])
        self.assertTrue(
            validation[
                "key_succession_multi_jurisdiction_signer_roster_quorum_bound"
            ]
        )
        self.assertTrue(
            validation[
                "key_succession_multi_jurisdiction_signer_roster_quorum_ok"
            ]
        )
        self.assertTrue(validation["key_succession_quorum_threshold_policy_bound"])
        self.assertTrue(validation["key_succession_quorum_threshold_policy_ok"])
        self.assertTrue(validation["long_term_media_renewal_bound"])
        self.assertEqual(
            ["coldstore", "trustee"],
            validation["long_term_media_renewal_targets"],
        )
        self.assertTrue(validation["long_term_media_renewal_readback_ok"])
        self.assertEqual(3650, validation["long_term_media_renewal_refresh_interval_days"])
        self.assertEqual(1000, validation["long_term_media_renewal_target_horizon_years"])
        self.assertTrue(validation["long_term_media_renewal_refresh_window_bound"])
        self.assertTrue(validation["long_term_media_renewal_source_proof_current"])
        self.assertTrue(validation["long_term_media_renewal_revocation_check_ok"])
        self.assertEqual(90, validation["long_term_media_renewal_revocation_check_window_days"])
        self.assertTrue(validation["long_term_media_renewal_registry_verifier_bound"])
        self.assertTrue(validation["long_term_media_renewal_registry_verifier_quorum_ok"])
        self.assertFalse(validation["raw_key_material_stored"])
        self.assertFalse(validation["raw_shard_material_stored"])
        self.assertFalse(validation["raw_signer_roster_payload_stored"])
        self.assertFalse(validation["raw_jurisdiction_policy_payload_stored"])
        self.assertFalse(validation["raw_quorum_threshold_policy_payload_stored"])
        self.assertFalse(validation["raw_media_payload_stored"])
        self.assertFalse(validation["raw_media_readback_payload_stored"])
        self.assertFalse(validation["raw_media_revocation_payload_stored"])
        self.assertFalse(validation["raw_media_refresh_payload_stored"])
        self.assertFalse(validation["raw_media_registry_payload_stored"])
        self.assertFalse(validation["raw_media_registry_response_payload_stored"])
        media_renewal = session["long_term_media_renewal"]
        self.assertEqual("long-term-media-renewal-proof-v1", media_renewal["policy_id"])
        self.assertEqual(["coldstore", "trustee"], media_renewal["renewal_target_ids"])
        self.assertEqual(2, len(media_renewal["proof_digest_set"]))
        self.assertEqual(2, len(media_renewal["readback_digest_set"]))
        refresh_window = media_renewal["refresh_window"]
        self.assertEqual(
            "long-term-media-renewal-refresh-window-v1",
            refresh_window["policy_id"],
        )
        self.assertEqual("current-not-revoked", refresh_window["source_proof_status"])
        self.assertEqual("within-window", refresh_window["refresh_status"])
        self.assertEqual(90, refresh_window["revocation_check_window_days"])
        self.assertTrue(refresh_window["stale_source_fail_closed"])
        self.assertTrue(refresh_window["revoked_source_fail_closed"])
        self.assertFalse(refresh_window["raw_revocation_payload_stored"])
        self.assertFalse(refresh_window["raw_refresh_payload_stored"])
        registry_verifier = refresh_window["registry_verifier"]
        self.assertEqual(
            "long-term-media-renewal-registry-verifier-v1",
            registry_verifier["policy_id"],
        )
        self.assertEqual(["JP-13", "SG-01"], registry_verifier["registry_jurisdictions"])
        self.assertEqual("complete", registry_verifier["quorum_status"])
        self.assertEqual("current-not-revoked", registry_verifier["registry_status"])
        self.assertEqual(2, len(registry_verifier["response_digest_set"]))
        self.assertEqual(250, registry_verifier["response_timeout_ms"])
        self.assertFalse(registry_verifier["raw_registry_payload_stored"])
        self.assertFalse(registry_verifier["raw_response_payload_stored"])
        signer_roster_quorum = session["key_succession"]["signer_roster_quorum"]
        self.assertEqual(
            ["JP-13", "SG-01"],
            signer_roster_quorum["accepted_jurisdictions"],
        )
        self.assertEqual(2, len(signer_roster_quorum["jurisdiction_policy_digests"]))
        self.assertEqual(4, len(signer_roster_quorum["signature_digest_set"]))
        self.assertEqual(
            "key-succession-multi-jurisdiction-quorum-threshold-policy-v1",
            signer_roster_quorum["threshold_policy_authority"]["policy_id"],
        )
        self.assertEqual(["primary", "mirror"], validation["immediate_target_ids"])
        self.assertEqual(["coldstore", "trustee"], validation["delayed_target_ids"])
        self.assertEqual(["coldstore", "mirror", "primary"], validation["consensus_target_ids"])
        self.assertEqual(["trustee"], validation["mismatch_target_ids"])

    def test_replicate_rejects_manifest_identity_mismatch(self) -> None:
        service = MemoryReplicationService()
        manifest = MemoryCrystalStore().build_reference_manifest("identity-demo")

        with self.assertRaisesRegex(ValueError, "manifest.identity_id"):
            service.replicate("other-identity", manifest)

    def test_validate_session_rejects_lost_consensus_quorum(self) -> None:
        service = MemoryReplicationService()

        session = service.build_reference_session("identity-demo")
        session["verification_audit"]["consensus_target_ids"] = ["primary", "mirror"]
        session["reconciliation"]["consensus_target_ids"] = ["primary", "mirror"]
        session["digest"] = "0" * 64

        validation = service.validate_session(session)

        self.assertFalse(validation["ok"])
        self.assertTrue(
            any("minimum_consensus_targets" in error for error in validation["errors"])
        )

    def test_validate_session_rejects_raw_key_material_storage(self) -> None:
        service = MemoryReplicationService()

        session = service.build_reference_session("identity-demo")
        session["key_succession"]["raw_key_material_stored"] = True
        session["digest"] = "0" * 64

        validation = service.validate_session(session)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["key_succession_bound"])
        self.assertTrue(validation["raw_key_material_stored"])
        self.assertTrue(
            any("raw_key_material_stored" in error for error in validation["errors"])
        )

    def test_validate_session_rejects_raw_signer_roster_payload_storage(self) -> None:
        service = MemoryReplicationService()

        session = service.build_reference_session("identity-demo")
        session["key_succession"]["signer_roster_policy"][
            "raw_signer_roster_payload_stored"
        ] = True
        session["key_succession"]["digest"] = "0" * 64
        session["digest"] = "0" * 64

        validation = service.validate_session(session)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["key_succession_bound"])
        self.assertFalse(validation["key_succession_signer_roster_policy_bound"])
        self.assertTrue(validation["raw_signer_roster_payload_stored"])
        self.assertTrue(
            any(
                "raw_signer_roster_payload_stored" in error
                for error in validation["errors"]
            )
        )

    def test_validate_session_rejects_signer_roster_signature_drift(self) -> None:
        service = MemoryReplicationService()

        session = service.build_reference_session("identity-demo")
        session["key_succession"]["signer_roster_policy"]["accepted_signers"][0][
            "signature_digest"
        ] = "f" * 64
        session["key_succession"]["signer_roster_policy"]["digest"] = "0" * 64
        session["key_succession"]["digest"] = "0" * 64
        session["digest"] = "0" * 64

        validation = service.validate_session(session)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["key_succession_signer_roster_policy_bound"])
        self.assertFalse(validation["key_succession_signer_roster_quorum_ok"])
        self.assertTrue(
            any("signature_digest mismatch" in error for error in validation["errors"])
        )

    def test_validate_session_rejects_missing_multi_jurisdiction_signer_quorum(self) -> None:
        service = MemoryReplicationService()

        session = service.build_reference_session("identity-demo")
        session["key_succession"]["signer_roster_quorum"]["accepted_jurisdictions"] = [
            "JP-13"
        ]
        session["key_succession"]["signer_roster_quorum"]["jurisdiction_policies"] = [
            session["key_succession"]["signer_roster_quorum"]["jurisdiction_policies"][0]
        ]
        session["key_succession"]["signer_roster_quorum"]["digest"] = "0" * 64
        session["key_succession"]["digest"] = "0" * 64
        session["digest"] = "0" * 64

        validation = service.validate_session(session)

        self.assertFalse(validation["ok"])
        self.assertFalse(
            validation[
                "key_succession_multi_jurisdiction_signer_roster_quorum_bound"
            ]
        )
        self.assertFalse(
            validation[
                "key_succession_multi_jurisdiction_signer_roster_quorum_ok"
            ]
        )
        self.assertTrue(
            any("multi-jurisdiction" in error for error in validation["errors"])
        )

    def test_validate_session_rejects_raw_jurisdiction_policy_payload_storage(self) -> None:
        service = MemoryReplicationService()

        session = service.build_reference_session("identity-demo")
        session["key_succession"]["signer_roster_quorum"][
            "raw_jurisdiction_policy_payload_stored"
        ] = True
        session["key_succession"]["signer_roster_quorum"]["digest"] = "0" * 64
        session["key_succession"]["digest"] = "0" * 64
        session["digest"] = "0" * 64

        validation = service.validate_session(session)

        self.assertFalse(validation["ok"])
        self.assertFalse(
            validation[
                "key_succession_multi_jurisdiction_signer_roster_quorum_bound"
            ]
        )
        self.assertTrue(validation["raw_jurisdiction_policy_payload_stored"])
        self.assertTrue(
            any(
                "raw_jurisdiction_policy_payload_stored" in error
                for error in validation["errors"]
            )
        )

    def test_validate_session_rejects_quorum_threshold_policy_drift(self) -> None:
        service = MemoryReplicationService()

        session = service.build_reference_session("identity-demo")
        threshold_authority = session["key_succession"]["signer_roster_quorum"][
            "threshold_policy_authority"
        ]
        threshold_authority["quorum_threshold"] = 1
        threshold_authority["digest"] = "0" * 64
        session["key_succession"]["signer_roster_quorum"]["digest"] = "0" * 64
        session["key_succession"]["digest"] = "0" * 64
        session["digest"] = "0" * 64

        validation = service.validate_session(session)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["key_succession_quorum_threshold_policy_bound"])
        self.assertFalse(validation["key_succession_quorum_threshold_policy_ok"])
        self.assertTrue(
            any(
                "threshold_policy_authority.quorum_threshold" in error
                for error in validation["errors"]
            )
        )

    def test_validate_session_rejects_raw_quorum_threshold_policy_payload_storage(self) -> None:
        service = MemoryReplicationService()

        session = service.build_reference_session("identity-demo")
        threshold_authority = session["key_succession"]["signer_roster_quorum"][
            "threshold_policy_authority"
        ]
        threshold_authority["raw_threshold_policy_payload_stored"] = True
        threshold_authority["digest"] = "0" * 64
        session["key_succession"]["signer_roster_quorum"]["digest"] = "0" * 64
        session["key_succession"]["digest"] = "0" * 64
        session["digest"] = "0" * 64

        validation = service.validate_session(session)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["key_succession_quorum_threshold_policy_bound"])
        self.assertTrue(validation["raw_quorum_threshold_policy_payload_stored"])
        self.assertTrue(
            any(
                "raw_threshold_policy_payload_stored" in error
                for error in validation["errors"]
            )
        )

    def test_validate_session_rejects_stale_media_renewal_refresh_window(self) -> None:
        service = MemoryReplicationService()

        session = service.build_reference_session("identity-demo")
        refresh_window = session["long_term_media_renewal"]["refresh_window"]
        refresh_window["source_proof_status"] = "stale"
        refresh_window["refresh_commit_digest"] = "0" * 64
        session["long_term_media_renewal"]["digest"] = "0" * 64
        session["digest"] = "0" * 64

        validation = service.validate_session(session)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["long_term_media_renewal_refresh_window_bound"])
        self.assertFalse(validation["long_term_media_renewal_source_proof_current"])
        self.assertTrue(
            any("source_proof_status" in error for error in validation["errors"])
        )

    def test_validate_session_rejects_raw_media_revocation_payload_storage(self) -> None:
        service = MemoryReplicationService()

        session = service.build_reference_session("identity-demo")
        refresh_window = session["long_term_media_renewal"]["refresh_window"]
        refresh_window["raw_revocation_payload_stored"] = True
        refresh_window["refresh_commit_digest"] = "0" * 64
        session["long_term_media_renewal"]["digest"] = "0" * 64
        session["digest"] = "0" * 64

        validation = service.validate_session(session)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["long_term_media_renewal_revocation_check_ok"])
        self.assertTrue(validation["raw_media_revocation_payload_stored"])
        self.assertTrue(
            any(
                "raw_revocation_payload_stored" in error
                for error in validation["errors"]
            )
        )

    def test_validate_session_rejects_media_registry_verifier_drift(self) -> None:
        service = MemoryReplicationService()

        session = service.build_reference_session("identity-demo")
        registry_verifier = session["long_term_media_renewal"]["refresh_window"][
            "registry_verifier"
        ]
        registry_verifier["registry_status"] = "stale"
        registry_verifier["digest"] = "0" * 64
        session["long_term_media_renewal"]["refresh_window"][
            "refresh_commit_digest"
        ] = "0" * 64
        session["long_term_media_renewal"]["digest"] = "0" * 64
        session["digest"] = "0" * 64

        validation = service.validate_session(session)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["long_term_media_renewal_registry_verifier_bound"])
        self.assertFalse(
            validation["long_term_media_renewal_registry_verifier_quorum_ok"]
        )
        self.assertTrue(
            any("registry_status" in error for error in validation["errors"])
        )

    def test_validate_session_rejects_raw_media_registry_payload_storage(self) -> None:
        service = MemoryReplicationService()

        session = service.build_reference_session("identity-demo")
        registry_verifier = session["long_term_media_renewal"]["refresh_window"][
            "registry_verifier"
        ]
        registry_verifier["raw_response_payload_stored"] = True
        registry_verifier["digest"] = "0" * 64
        session["long_term_media_renewal"]["refresh_window"][
            "refresh_commit_digest"
        ] = "0" * 64
        session["long_term_media_renewal"]["digest"] = "0" * 64
        session["digest"] = "0" * 64

        validation = service.validate_session(session)

        self.assertFalse(validation["ok"])
        self.assertFalse(
            validation["long_term_media_renewal_registry_verifier_quorum_ok"]
        )
        self.assertTrue(validation["raw_media_registry_response_payload_stored"])
        self.assertTrue(
            any(
                "raw_response_payload_stored" in error
                for error in validation["errors"]
            )
        )

    def test_validate_session_rejects_long_term_media_readback_drift(self) -> None:
        service = MemoryReplicationService()

        session = service.build_reference_session("identity-demo")
        session["long_term_media_renewal"]["media_proofs"][0]["readback_digest"] = "f" * 64
        session["long_term_media_renewal"]["media_proofs"][0]["proof_digest"] = "0" * 64
        session["long_term_media_renewal"]["digest"] = "0" * 64
        session["digest"] = "0" * 64

        validation = service.validate_session(session)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["long_term_media_renewal_bound"])
        self.assertFalse(validation["long_term_media_renewal_readback_ok"])
        self.assertTrue(
            any("readback_digest mismatch" in error for error in validation["errors"])
        )

    def test_validate_session_rejects_raw_long_term_media_payload_storage(self) -> None:
        service = MemoryReplicationService()

        session = service.build_reference_session("identity-demo")
        session["long_term_media_renewal"]["media_proofs"][1][
            "raw_media_payload_stored"
        ] = True
        session["long_term_media_renewal"]["digest"] = "0" * 64
        session["digest"] = "0" * 64

        validation = service.validate_session(session)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["long_term_media_renewal_bound"])
        self.assertTrue(validation["raw_media_payload_stored"])
        self.assertTrue(
            any("raw_media_payload_stored" in error for error in validation["errors"])
        )


if __name__ == "__main__":
    unittest.main()
