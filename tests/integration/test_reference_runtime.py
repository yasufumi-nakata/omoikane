from __future__ import annotations

import unittest
from pathlib import Path

from omoikane.reference_os import OmoikaneReferenceOS


class ReferenceRuntimeTests(unittest.TestCase):
    def test_reference_scenario_runs(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_reference_scenario()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["qualia"]["monotonic"])
        self.assertEqual("Approval", result["safe_patch"]["ethics"]["status"])
        self.assertEqual("Veto", result["blocked_patch"]["ethics"]["status"])

    def test_gap_report_reads_repo(self) -> None:
        runtime = OmoikaneReferenceOS()
        repo_root = Path(__file__).resolve().parents[2]

        report = runtime.generate_gap_report(repo_root)

        self.assertIn("open_question_count", report)
        self.assertGreaterEqual(report["open_question_count"], 1)
        self.assertEqual(0, report["missing_expected_file_count"])


if __name__ == "__main__":
    unittest.main()
