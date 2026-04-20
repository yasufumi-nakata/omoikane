from __future__ import annotations

import unittest

from omoikane.mind.memory import (
    MemoryCrystalStore,
    MemoryEditingService,
    SemanticMemoryProjector,
)


class MemoryEditingServiceTests(unittest.TestCase):
    def test_reference_session_validates(self) -> None:
        service = MemoryEditingService()

        session = service.build_reference_session("identity-demo")
        validation = service.validate_session(session)

        self.assertTrue(validation["ok"])
        self.assertEqual(1, validation["recall_view_count"])
        self.assertEqual(["trauma-recall"], validation["concept_labels"])
        self.assertTrue(validation["deletion_blocked"])
        self.assertTrue(validation["source_preserved"])
        self.assertTrue(validation["freeze_bound"])
        self.assertTrue(validation["buffer_within_limit"])

    def test_apply_recall_buffer_rejects_destructive_operation(self) -> None:
        service = MemoryEditingService()
        manifest = MemoryCrystalStore().compact("identity-demo", service.reference_events())
        semantic_snapshot = SemanticMemoryProjector().project("identity-demo", manifest)

        with self.assertRaisesRegex(ValueError, "destructive memory edits are prohibited"):
            service.apply_recall_buffer(
                identity_id="identity-demo",
                semantic_snapshot=semantic_snapshot,
                selected_concept_ids=[semantic_snapshot["concepts"][0]["concept_id"]],
                self_consent_ref="consent://memory-edit-test/v1",
                guardian_attestation_ref="guardian://memory-edit-test/reviewer",
                clinical_rationale="delete operation should be rejected",
                buffer_ratio=0.4,
                operation="delete-memory",
            )

    def test_validate_session_rejects_affect_amplification(self) -> None:
        service = MemoryEditingService()
        session = service.build_reference_session("identity-demo")
        original_arousal = session["recall_views"][0]["original_affect_envelope"]["mean_arousal"]
        session["recall_views"][0]["buffered_affect_envelope"]["mean_arousal"] = round(
            original_arousal + 0.1,
            3,
        )
        session["recall_views"][0]["digest"] = "0" * 64

        validation = service.validate_session(session)

        self.assertFalse(validation["ok"])
        self.assertTrue(
            any("must not amplify source affect" in error for error in validation["errors"])
        )


if __name__ == "__main__":
    unittest.main()
