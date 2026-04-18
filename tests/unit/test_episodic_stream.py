from __future__ import annotations

import unittest

from omoikane.mind.memory import EpisodicStream, MemoryCrystalStore


class EpisodicStreamTests(unittest.TestCase):
    def test_reference_snapshot_validates_and_is_ready_for_compaction(self) -> None:
        stream = EpisodicStream()

        snapshot = stream.build_reference_snapshot("identity-demo")
        validation = stream.validate_snapshot(snapshot)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["ready_for_compaction"])
        self.assertEqual(5, validation["event_count"])
        self.assertEqual(5, validation["compaction_candidate_count"])
        self.assertEqual("deliberation", validation["narrative_roles"][0])
        self.assertEqual("handoff", validation["narrative_roles"][-1])

    def test_append_rejects_unknown_narrative_role(self) -> None:
        stream = EpisodicStream()

        with self.assertRaisesRegex(ValueError, "narrative_role"):
            stream.append(
                summary="invalid event",
                tags=["invalid"],
                salience=0.2,
                valence=0.0,
                arousal=0.1,
                source_refs=["ledger://entry/invalid"],
                attention_target="invalid.target",
                narrative_role="rewrite",
                self_coherence=0.7,
                continuity_ref="ledger://entry/invalid",
            )

    def test_memory_compaction_accepts_episodic_handoff_window(self) -> None:
        stream = EpisodicStream()
        store = MemoryCrystalStore()

        snapshot = stream.build_reference_snapshot("identity-demo")
        manifest = store.compact("identity-demo", snapshot["events"])
        validation = store.validate(manifest)

        self.assertTrue(validation["ok"])
        self.assertEqual(snapshot["event_count"], validation["source_event_count"])


if __name__ == "__main__":
    unittest.main()
