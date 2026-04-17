from __future__ import annotations

import unittest

from omoikane.mind.qualia import QualiaBuffer
from omoikane.mind.self_model import SelfModelMonitor, SelfModelSnapshot


class QualiaBufferTests(unittest.TestCase):
    def test_append_rejects_out_of_range_values(self) -> None:
        buffer = QualiaBuffer()

        with self.assertRaises(ValueError):
            buffer.append("過負荷", 0.2, 0.1, 1.2)

    def test_recent_requires_positive_count(self) -> None:
        buffer = QualiaBuffer()
        buffer.append("静穏", 0.1, 0.2, 0.9)

        with self.assertRaises(ValueError):
            buffer.recent(0)

    def test_recent_returns_latest_ticks_in_order(self) -> None:
        buffer = QualiaBuffer()
        buffer.append("起動", 0.1, 0.2, 0.9)
        buffer.append("合議", 0.2, 0.3, 0.8)
        buffer.append("記録", 0.0, 0.1, 0.95)

        recent = buffer.recent(2)

        self.assertEqual([1, 2], [tick["tick_id"] for tick in recent])


class SelfModelMonitorTests(unittest.TestCase):
    def test_abrupt_change_is_flagged(self) -> None:
        monitor = SelfModelMonitor(abrupt_change_threshold=0.35)
        monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["continuity", "consent", "reversibility"],
                goals=["safe-self-construction", "identity-preservation"],
                traits={"curiosity": 0.71, "caution": 0.84, "agency": 0.62},
            )
        )

        result = monitor.update(
            SelfModelSnapshot(
                identity_id="id-1",
                values=["expedience"],
                goals=["unbounded-self-modification"],
                traits={"curiosity": 0.05, "caution": 0.10, "agency": 0.99},
            )
        )

        self.assertTrue(result["abrupt_change"])
        self.assertGreaterEqual(result["divergence"], 0.35)


if __name__ == "__main__":
    unittest.main()
