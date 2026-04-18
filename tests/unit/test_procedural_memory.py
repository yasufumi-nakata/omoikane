from __future__ import annotations

import unittest

from omoikane.mind.connectome import ConnectomeModel
from omoikane.mind.memory import MemoryCrystalStore, ProceduralMemoryProjector


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


if __name__ == "__main__":
    unittest.main()
