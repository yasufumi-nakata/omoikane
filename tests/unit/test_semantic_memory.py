from __future__ import annotations

import unittest

from omoikane.mind.connectome import ConnectomeModel
from omoikane.mind.memory import MemoryCrystalStore, SemanticMemoryProjector


class SemanticMemoryProjectorTests(unittest.TestCase):
    def test_reference_snapshot_validates(self) -> None:
        projector = SemanticMemoryProjector()

        snapshot = projector.build_reference_snapshot("identity-demo")
        validation = projector.validate(snapshot)

        self.assertTrue(validation["ok"])
        self.assertEqual(2, validation["concept_count"])
        self.assertEqual(
            ["council-review", "migration-check"],
            validation["labels"],
        )
        self.assertEqual(["procedural-memory"], validation["deferred_surfaces"])

    def test_project_rejects_invalid_manifest(self) -> None:
        projector = SemanticMemoryProjector()
        manifest = MemoryCrystalStore().build_reference_manifest("identity-demo")
        manifest["segments"][0]["digest"] = "0" * 64

        with self.assertRaisesRegex(ValueError, "valid MemoryCrystal manifest"):
            projector.project("identity-demo", manifest)

    def test_validate_rejects_concept_count_mismatch(self) -> None:
        projector = SemanticMemoryProjector()
        snapshot = projector.build_reference_snapshot("identity-demo")
        snapshot["concept_count"] = 1

        validation = projector.validate(snapshot)

        self.assertFalse(validation["ok"])
        self.assertTrue(
            any("concept_count" in error for error in validation["errors"])
        )

    def test_prepare_procedural_handoff_returns_ready_bridge(self) -> None:
        projector = SemanticMemoryProjector()
        snapshot = projector.build_reference_snapshot("identity-demo")
        connectome_document = ConnectomeModel().build_reference_snapshot("identity-demo")

        handoff = projector.prepare_procedural_handoff(
            "identity-demo",
            snapshot,
            connectome_document,
        )
        validation = projector.validate_procedural_handoff(
            handoff,
            semantic_snapshot=snapshot,
            connectome_document=connectome_document,
        )

        self.assertTrue(validation["ok"])
        self.assertEqual(2, validation["concept_count"])
        self.assertEqual(
            ["council-review", "migration-check"],
            validation["canonical_labels"],
        )
        self.assertEqual("mind.procedural.v0", validation["target_namespace"])
        self.assertEqual("ready", validation["status"])

    def test_validate_procedural_handoff_rejects_manifest_digest_mismatch(self) -> None:
        projector = SemanticMemoryProjector()
        snapshot = projector.build_reference_snapshot("identity-demo")
        manifest = MemoryCrystalStore().build_reference_manifest("identity-demo")
        connectome_document = ConnectomeModel().build_reference_snapshot("identity-demo")
        handoff = projector.prepare_procedural_handoff(
            "identity-demo",
            snapshot,
            connectome_document,
        )
        handoff["source_manifest_digest"] = "0" * 64

        validation = projector.validate_procedural_handoff(
            handoff,
            semantic_snapshot=snapshot,
            manifest=manifest,
            connectome_document=connectome_document,
        )

        self.assertFalse(validation["ok"])
        self.assertTrue(
            any("source_manifest_digest" in error for error in validation["errors"])
        )


if __name__ == "__main__":
    unittest.main()
