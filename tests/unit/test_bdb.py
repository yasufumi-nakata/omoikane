from __future__ import annotations

import unittest

from omoikane.interface.bdb import BiologicalDigitalBridge


class BiologicalDigitalBridgeTests(unittest.TestCase):
    def test_reference_session_is_viable_and_reversible(self) -> None:
        bridge = BiologicalDigitalBridge()
        session = bridge.open_session("identity-bdb-1", replacement_ratio=0.35)

        cycle = bridge.transduce_cycle(
            session["session_id"],
            spike_channels=["motor_cortex", "somatic_feedback", "autonomic_state"],
            neuromodulators={
                "acetylcholine": 0.42,
                "dopamine": 0.31,
                "serotonin": 0.28,
            },
            stimulus_targets=["motor_cortex", "somatic_feedback"],
        )
        increase = bridge.adjust_replacement_ratio(
            session["session_id"],
            new_ratio=0.50,
            rationale="stress test higher replacement load",
        )
        decrease = bridge.adjust_replacement_ratio(
            session["session_id"],
            new_ratio=0.20,
            rationale="verify reversibility toward biological-only operation",
        )
        fallback = bridge.fail_safe_fallback(
            session["session_id"],
            reason="codec watchdog triggered fail-safe",
        )
        snapshot = bridge.snapshot(session["session_id"])
        validation = bridge.validate_session(snapshot)

        self.assertTrue(cycle["within_budget"])
        self.assertEqual("increase", increase["direction"])
        self.assertEqual("decrease", decrease["direction"])
        self.assertEqual("bio-autonomous-fallback", fallback["status"])
        self.assertEqual(0.0, snapshot["effective_replacement_ratio"])
        self.assertFalse(snapshot["fallback_policy"]["stim_output_enabled"])
        self.assertTrue(validation["ok"])
        self.assertTrue(validation["reversibility_verified"])
        self.assertTrue(validation["bio_autonomy_retained"])

    def test_rejects_ratio_outside_step_grid(self) -> None:
        bridge = BiologicalDigitalBridge()

        with self.assertRaisesRegex(ValueError, "align to 0.05 steps"):
            bridge.open_session("identity-bdb-2", replacement_ratio=0.33)


if __name__ == "__main__":
    unittest.main()
