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
        self.assertEqual(32, result["qualia"]["profile"]["embedding_dimensions"])
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

    def test_memory_demo_returns_valid_manifest(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_memory_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["append_only"])
        self.assertEqual(5, result["validation"]["source_event_count"])
        self.assertEqual(2, result["validation"]["segment_count"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["crystal-commit"])

    def test_cognitive_failover_demo_records_fallback(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_cognitive_failover_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["reasoning"]["degraded"])
        self.assertEqual("narrative_v1", result["reasoning"]["selected_backend"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["cognitive-failover"])

    def test_qualia_demo_reports_reference_sampling_profile(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_qualia_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual(250, result["qualia"]["profile"]["sampling_window_ms"])
        self.assertEqual(
            ["visual", "auditory", "somatic", "interoceptive"],
            result["qualia"]["profile"]["modalities"],
        )
        self.assertEqual(32, len(result["qualia"]["recent"][0]["sensory_embeddings"]["visual"]))
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["qualia-checkpoint"])

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

    def test_task_graph_demo_reports_bounded_complexity(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_task_graph_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual("reference-v0", result["graph"]["complexity_policy"]["policy_id"])
        self.assertEqual(5, result["validation"]["node_count"])
        self.assertEqual(4, result["validation"]["edge_count"])
        self.assertEqual(3, result["dispatch"]["dispatched_count"])
        self.assertEqual(3, result["synthesis"]["accepted_result_count"])

    def test_trust_demo_reports_update_policy_and_human_pin(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_trust_demo()

        self.assertEqual("reference-v0", result["policy"]["policy_id"])
        self.assertEqual(0.99, result["agents"]["integrity-guardian"]["global_score"])
        self.assertFalse(result["events"][-1]["applied"])
        self.assertEqual(0.62, result["agents"]["design-architect"]["global_score"])
        self.assertTrue(result["agents"]["codex-builder"]["eligibility"]["apply_to_runtime"])

    def test_ethics_demo_reports_rule_language_and_recorded_events(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_ethics_demo()

        self.assertEqual("deterministic-rule-tree-v0", result["language"]["language_id"])
        self.assertEqual("Veto", result["decisions"]["immutable_boundary"]["status"])
        self.assertEqual("Escalate", result["decisions"]["sandbox_escalation"]["status"])
        self.assertEqual("Approval", result["decisions"]["approved_fork"]["status"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["ethics-veto"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["ethics-escalate"])


if __name__ == "__main__":
    unittest.main()
