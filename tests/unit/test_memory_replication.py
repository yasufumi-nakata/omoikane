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


if __name__ == "__main__":
    unittest.main()
