from __future__ import annotations

import unittest

from omoikane.mind.connectome import ConnectomeModel
from omoikane.mind.memory import (
    MemoryCrystalStore,
    ProceduralMemoryProjector,
    ProceduralMemoryWritebackGate,
)


class ProceduralMemoryProjectorTests(unittest.TestCase):
    def test_reference_snapshot_validates(self) -> None:
        projector = ProceduralMemoryProjector()

        snapshot = projector.build_reference_snapshot("identity-demo")
        validation = projector.validate(snapshot)

        self.assertTrue(validation["ok"])
        self.assertEqual(2, validation["recommendation_count"])
        self.assertEqual(
            ["continuity_integrator->ethics_gate", "sensory_ingress->continuity_integrator"],
            sorted(validation["target_paths"]),
        )
        self.assertEqual(
            ["weight-application", "skill-execution"],
            validation["deferred_surfaces"],
        )

    def test_project_rejects_invalid_connectome_document(self) -> None:
        projector = ProceduralMemoryProjector()
        manifest = MemoryCrystalStore().build_reference_manifest("identity-demo")
        connectome_document = ConnectomeModel().build_reference_snapshot("identity-demo")
        connectome_document["edges"][0]["target"] = connectome_document["edges"][0]["id"]

        with self.assertRaisesRegex(ValueError, "unknown node"):
            projector.project("identity-demo", manifest, connectome_document)

    def test_validate_rejects_recommendation_count_mismatch(self) -> None:
        projector = ProceduralMemoryProjector()
        snapshot = projector.build_reference_snapshot("identity-demo")
        snapshot["recommendation_count"] = 1

        validation = projector.validate(snapshot)

        self.assertFalse(validation["ok"])
        self.assertTrue(
            any("recommendation_count" in error for error in validation["errors"])
        )


class ProceduralMemoryWritebackGateTests(unittest.TestCase):
    def test_apply_returns_valid_receipt_and_updated_connectome(self) -> None:
        projector = ProceduralMemoryProjector()
        gate = ProceduralMemoryWritebackGate()
        manifest = MemoryCrystalStore().build_reference_manifest("identity-demo")
        connectome_document = ConnectomeModel().build_reference_snapshot("identity-demo")
        preview_snapshot = projector.project("identity-demo", manifest, connectome_document)

        result = gate.apply(
            "identity-demo",
            preview_snapshot,
            connectome_document,
            self_attestation_id="self://procedural-writeback/test-001",
            council_attestation_id="council://procedural-writeback/test-001",
            guardian_attestation_id="guardian://procedural-writeback/test-001",
            human_reviewers=["human://reviewers/alice", "human://reviewers/bob"],
            approval_reason="bounded preview を writeback として適用する",
        )
        validation = gate.validate(
            result["receipt"],
            result["updated_connectome_document"],
            preview_snapshot,
        )

        self.assertTrue(validation["ok"])
        self.assertEqual(2, validation["applied_recommendation_count"])
        self.assertEqual(
            ["human://reviewers/alice", "human://reviewers/bob"],
            validation["human_reviewers"],
        )
        self.assertNotEqual(
            connectome_document["snapshot_id"],
            result["updated_connectome_document"]["snapshot_id"],
        )
        self.assertEqual("approved", result["receipt"]["status"])

    def test_apply_rejects_missing_human_quorum(self) -> None:
        projector = ProceduralMemoryProjector()
        gate = ProceduralMemoryWritebackGate()
        manifest = MemoryCrystalStore().build_reference_manifest("identity-demo")
        connectome_document = ConnectomeModel().build_reference_snapshot("identity-demo")
        preview_snapshot = projector.project("identity-demo", manifest, connectome_document)

        with self.assertRaisesRegex(PermissionError, "at least 2 human reviewers"):
            gate.apply(
                "identity-demo",
                preview_snapshot,
                connectome_document,
                self_attestation_id="self://procedural-writeback/test-001",
                council_attestation_id="council://procedural-writeback/test-001",
                guardian_attestation_id="guardian://procedural-writeback/test-001",
                human_reviewers=["human://reviewers/alice"],
                approval_reason="reviewer quorum 不足",
            )


if __name__ == "__main__":
    unittest.main()
