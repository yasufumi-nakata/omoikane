from __future__ import annotations

import unittest

from omoikane.interface.wms import WorldModelSync


class WorldModelSyncTests(unittest.TestCase):
    def test_minor_diff_reconciles_via_consensus_round(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )

        outcome = sync.propose_diff(
            session["session_id"],
            proposer_id="identity://peer",
            candidate_objects=["atrium", "council-table", "shared-lantern"],
            affected_object_ratio=0.03,
            attested=True,
        )
        snapshot = sync.snapshot(session["session_id"])

        self.assertEqual("minor_diff", outcome["classification"])
        self.assertEqual("consensus-round", outcome["decision"])
        self.assertFalse(outcome["escape_offered"])
        self.assertIn("shared-lantern", snapshot["objects"])

    def test_major_diff_offers_private_reality_escape(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )

        outcome = sync.propose_diff(
            session["session_id"],
            proposer_id="identity://peer",
            candidate_objects=["atrium", "council-table", "gravity-well"],
            affected_object_ratio=0.22,
            attested=True,
        )
        switched = sync.switch_mode(
            session["session_id"],
            mode="private_reality",
            requested_by="identity://primary",
            reason="major shared-world divergence",
        )
        snapshot = sync.snapshot(session["session_id"])

        self.assertEqual("major_diff", outcome["classification"])
        self.assertTrue(outcome["escape_offered"])
        self.assertTrue(switched["private_escape_honored"])
        self.assertEqual("local", snapshot["authority"])

    def test_unauthorized_diff_isolated_as_malicious_inject(self) -> None:
        sync = WorldModelSync()
        session = sync.create_session(
            ["identity://primary", "identity://peer"],
            objects=["atrium", "council-table"],
        )

        outcome = sync.propose_diff(
            session["session_id"],
            proposer_id="identity://spoof",
            candidate_objects=["atrium", "spoofed-object"],
            affected_object_ratio=0.4,
            attested=False,
        )
        violation = sync.observe_violation(session["session_id"])

        self.assertEqual("malicious_inject", outcome["classification"])
        self.assertEqual("guardian-veto", outcome["decision"])
        self.assertEqual("isolate-session", violation["guardian_action"])
        self.assertTrue(violation["violation_detected"])


if __name__ == "__main__":
    unittest.main()
