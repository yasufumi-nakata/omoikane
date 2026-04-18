from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from omoikane.cli import main


class CliIntegrationTests(unittest.TestCase):
    def test_connectome_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "connectome-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual(3, result["validation"]["node_count"])

    def test_memory_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "memory-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["append_only"])
        self.assertEqual(5, result["validation"]["source_event_count"])
        self.assertEqual(2, result["validation"]["segment_count"])

    def test_substrate_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "substrate-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual("released", result["substrate"]["allocation"]["status"])
        self.assertEqual("warm-standby", result["substrate"]["transfer"]["continuity_mode"])

    def test_qualia_demo_emits_reference_profile(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "qualia-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual(32, result["qualia"]["profile"]["embedding_dimensions"])
        self.assertEqual(250, result["qualia"]["profile"]["sampling_window_ms"])
        self.assertEqual(32, len(result["qualia"]["recent"][0]["sensory_embeddings"]["visual"]))

    def test_continuity_demo_emits_profile_and_snapshot(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "continuity-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual("sha256", result["ledger_profile"]["chain_algorithm"])
        self.assertEqual(3, len(result["ledger_snapshot"]))

    def test_council_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "council-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual(1_000, result["policies"]["expedited"]["hard_timeout_ms"])
        self.assertEqual("soft-timeout", result["sessions"]["standard_soft_timeout"]["timeout_status"]["status"])

    def test_task_graph_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "task-graph-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual(5, result["validation"]["node_count"])
        self.assertEqual(3, result["dispatch"]["dispatched_count"])
        self.assertEqual(3, result["synthesis"]["accepted_result_count"])

    def test_trust_demo_emits_threshold_and_pin_state(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "trust-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertEqual("reference-v0", result["policy"]["policy_id"])
        self.assertEqual(0.99, result["agents"]["integrity-guardian"]["global_score"])
        self.assertFalse(result["events"][-1]["applied"])
        self.assertTrue(result["agents"]["design-architect"]["eligibility"]["count_for_weighted_vote"])


if __name__ == "__main__":
    unittest.main()
