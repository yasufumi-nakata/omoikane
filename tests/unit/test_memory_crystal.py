from __future__ import annotations

import unittest

from omoikane.mind.memory import MemoryCrystalStore


class MemoryCrystalStoreTests(unittest.TestCase):
    def test_reference_manifest_validates(self) -> None:
        store = MemoryCrystalStore()

        manifest = store.build_reference_manifest("identity-demo")
        validation = store.validate(manifest)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["append_only"])
        self.assertEqual(5, validation["source_event_count"])
        self.assertEqual(2, validation["segment_count"])
        self.assertEqual(
            ["council-review", "migration-check"],
            validation["themes"],
        )

    def test_validate_rejects_too_many_events_in_segment(self) -> None:
        store = MemoryCrystalStore()
        manifest = store.build_reference_manifest("identity-demo")
        manifest["segments"][0]["source_event_ids"].append("episode-overflow")
        manifest["source_event_count"] += 1
        manifest["segments"][0]["digest"] = "0" * 64

        validation = store.validate(manifest)

        self.assertFalse(validation["ok"])
        self.assertTrue(
            any("max_source_events_per_segment" in error for error in validation["errors"])
        )

    def test_compact_rejects_empty_source_refs(self) -> None:
        store = MemoryCrystalStore()
        events = store.reference_events()
        events[0]["source_refs"] = []

        with self.assertRaisesRegex(ValueError, "source_refs"):
            store.compact("identity-demo", events)


if __name__ == "__main__":
    unittest.main()
