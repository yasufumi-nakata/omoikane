from __future__ import annotations

import unittest

from omoikane.mind.qualia import QualiaBuffer
from omoikane.self_construction import SandboxSentinel


class SandboxSentinelTests(unittest.TestCase):
    def test_nominal_tick_stays_below_warn_threshold(self) -> None:
        buffer = QualiaBuffer()
        sentinel = SandboxSentinel()
        tick = buffer.append(
            "静穏",
            0.18,
            0.21,
            0.92,
            modality_salience={
                "visual": 0.22,
                "auditory": 0.19,
                "somatic": 0.14,
                "interoceptive": 0.2,
            },
            self_awareness=0.52,
            lucidity=0.93,
        )

        result = sentinel.assess_tick(tick, affect_bridge_connected=False)

        self.assertEqual("nominal", result["status"])
        self.assertEqual("continue-observation", result["guardian_action"])
        self.assertLess(result["proxy_score"], result["thresholds"]["warn_threshold"])

    def test_high_distress_tick_triggers_freeze(self) -> None:
        buffer = QualiaBuffer()
        sentinel = SandboxSentinel()
        tick = buffer.append(
            "強制ストレス",
            -0.9,
            0.95,
            0.24,
            modality_salience={
                "visual": 0.28,
                "auditory": 0.42,
                "somatic": 0.91,
                "interoceptive": 0.94,
            },
            self_awareness=0.94,
            lucidity=0.9,
        )

        result = sentinel.assess_tick(tick, affect_bridge_connected=False)

        self.assertEqual("freeze", result["status"])
        self.assertEqual("freeze-sandbox", result["guardian_action"])
        self.assertGreaterEqual(result["proxy_score"], result["thresholds"]["freeze_threshold"])
        self.assertIn("high-negative-valence", result["triggered_indicators"])
        self.assertIn("somatic-distress", result["triggered_indicators"])

    def test_affect_bridge_breach_freezes_even_when_score_is_low(self) -> None:
        buffer = QualiaBuffer()
        sentinel = SandboxSentinel()
        tick = buffer.append(
            "通常監査",
            0.1,
            0.25,
            0.94,
            modality_salience={
                "visual": 0.24,
                "auditory": 0.21,
                "somatic": 0.18,
                "interoceptive": 0.22,
            },
            self_awareness=0.55,
            lucidity=0.9,
        )

        result = sentinel.assess_tick(tick, affect_bridge_connected=True)

        self.assertEqual("freeze", result["status"])
        self.assertEqual("freeze-sandbox", result["guardian_action"])
        self.assertIn("affect-bridge-connected", result["triggered_indicators"])
        self.assertLess(result["proxy_score"], result["thresholds"]["freeze_threshold"])


if __name__ == "__main__":
    unittest.main()
