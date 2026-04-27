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
        self.assertFalse(validation["raw_key_material_stored"])
        self.assertFalse(validation["raw_shard_material_stored"])
        self.assertFalse(validation["raw_signer_roster_payload_stored"])
        self.assertFalse(validation["raw_jurisdiction_policy_payload_stored"])
        self.assertFalse(validation["raw_quorum_threshold_policy_payload_stored"])
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


if __name__ == "__main__":
    unittest.main()
