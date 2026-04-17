from __future__ import annotations

import unittest
from pathlib import Path

from omoikane.reference_os import OmoikaneReferenceOS


class ReferenceRuntimeTests(unittest.TestCase):
    def test_reference_scenario_runs(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_reference_scenario()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual("sha256", result["ledger_profile"]["chain_algorithm"])
        self.assertTrue(result["qualia"]["monotonic"])
        self.assertEqual("Approval", result["safe_patch"]["ethics"]["status"])
        self.assertEqual("Veto", result["blocked_patch"]["ethics"]["status"])
        self.assertGreaterEqual(len(result["ledger_snapshot"]), 4)

    def test_gap_report_reads_repo(self) -> None:
        runtime = OmoikaneReferenceOS()
        repo_root = Path(__file__).resolve().parents[2]

        report = runtime.generate_gap_report(repo_root)

        self.assertIn("open_question_count", report)
        self.assertGreaterEqual(report["open_question_count"], 1)
        self.assertEqual(0, report["missing_expected_file_count"])
        self.assertEqual(0, report["empty_eval_surface_count"])
        self.assertEqual(0, report["catalog_pending_count"])

    def test_connectome_demo_returns_valid_document(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_connectome_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertEqual(3, result["validation"]["node_count"])
        self.assertEqual(2, result["validation"]["edge_count"])
        self.assertTrue(result["ledger_verification"]["ok"])

    def test_cognitive_failover_demo_records_fallback(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_cognitive_failover_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["reasoning"]["degraded"])
        self.assertEqual("narrative_v1", result["reasoning"]["selected_backend"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["cognitive-failover"])

    def test_substrate_demo_records_migration_and_release(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_substrate_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual("released", result["substrate"]["allocation"]["status"])
        self.assertEqual(
            "classical_silicon.redundant",
            result["substrate"]["transfer"]["destination_substrate"],
        )
        self.assertEqual("released", result["substrate"]["release"]["status"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["substrate-migrate"])

    def test_continuity_demo_emits_profile_and_snapshot(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_continuity_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual("hmac-sha256", result["ledger_profile"]["signature_algorithm"])
        self.assertEqual(3, len(result["ledger_snapshot"]))
        self.assertEqual("self-modify", result["ledger_snapshot"][-1]["category"])

    def test_council_demo_reports_timeout_policy(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_council_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual(45_000, result["policies"]["standard"]["soft_timeout_ms"])
        self.assertEqual(
            "timeout-fallback",
            result["sessions"]["standard_soft_timeout"]["decision_mode"],
        )
        self.assertEqual(
            "deferred",
            result["sessions"]["expedited_hard_timeout"]["outcome"],
        )


if __name__ == "__main__":
    unittest.main()
