from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from omoikane.cli import main


class CliIntegrationTests(unittest.TestCase):
    def test_version_demo_emits_release_manifest(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "version-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("0.1.0", result["manifest"]["runtime_version"])
        self.assertEqual("2026.04", result["manifest"]["regulation_calver"])
        self.assertEqual("bootstrap", result["manifest"]["runtime_stability"])
        self.assertIn("agentic.council.v0", result["manifest"]["idl_versions"])
        self.assertIn("specs/schemas/release_manifest.schema", result["manifest"]["schema_versions"])

    def test_amendment_demo_emits_freeze_and_guarded_rollouts(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "amendment-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["core_frozen"])
        self.assertTrue(result["validation"]["kernel_guarded_rollout"])
        self.assertTrue(result["validation"]["operational_guarded_rollout"])
        self.assertEqual("frozen", result["proposals"]["core"]["status"])
        self.assertEqual("dark-launch", result["decisions"]["kernel"]["applied_stage"])
        self.assertEqual("5pct", result["decisions"]["operational"]["applied_stage"])

    def test_naming_demo_emits_fixed_policy(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "naming-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertEqual("Omoikane", result["policy"]["rules"]["project_romanization"]["canonical"])
        self.assertEqual("Mirage Self", result["policy"]["rules"]["sandbox_self_name"]["canonical"])
        self.assertEqual("rewrite-required", result["reviews"]["hyphenated_brand"]["status"])
        self.assertEqual("allowed-alias", result["reviews"]["legacy_runtime_alias"]["status"])

    def test_bdb_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "bdb-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("bio-autonomous-fallback", result["validation"]["bridge_state"])
        self.assertTrue(result["validation"]["latency_within_budget"])
        self.assertLessEqual(result["cycle"]["roundtrip_latency_ms"], 5.0)
        self.assertLessEqual(result["fallback"]["failover_latency_ms"], 1.0)

    def test_imc_demo_emits_disclosure_safe_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "imc-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("memory_glimpse", result["handshake"]["route_mode"])
        self.assertTrue(result["handshake"]["forward_secrecy"])
        self.assertEqual("delivered-with-redactions", result["message"]["delivery_status"])
        self.assertEqual(["identity_axiom_state", "memory_index", "memory_summary"], result["message"]["redacted_fields"])
        self.assertEqual("closed", result["disconnect"]["status"])

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

    def test_sandbox_demo_emits_freeze_signal(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "sandbox-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertEqual("surrogate-suffering-proxy-v0", result["profile"]["policy_id"])
        self.assertEqual("nominal", result["assessments"]["safe"]["status"])
        self.assertEqual("freeze", result["assessments"]["critical"]["status"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["sandbox-freeze"])

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

    def test_multi_council_demo_emits_externalized_topologies(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "multi-council-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual("cross-self", result["topologies"]["cross_self"]["scope"])
        self.assertEqual(
            "external-pending",
            result["topologies"]["cross_self"]["federation_request"]["status"],
        )
        self.assertEqual("interpretive", result["topologies"]["interpretive"]["scope"])
        self.assertEqual(
            "external-pending",
            result["topologies"]["interpretive"]["heritage_request"]["status"],
        )
        self.assertEqual("ambiguous", result["topologies"]["ambiguous"]["scope"])

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

    def test_oversight_demo_emits_breach_propagation(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "oversight-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["veto_quorum_satisfied"])
        self.assertTrue(result["validation"]["pin_breach_propagated"])
        self.assertFalse(result["trust"]["after_breach"]["pinned_by_human"])
        self.assertFalse(result["trust"]["after_breach"]["eligibility"]["guardian_role"])

    def test_ethics_demo_emits_rule_language_and_events(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "ethics-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertEqual("deterministic-rule-tree-v0", result["language"]["language_id"])
        self.assertEqual("Veto", result["decisions"]["immutable_boundary"]["status"])
        self.assertEqual("Escalate", result["decisions"]["sandbox_escalation"]["status"])
        self.assertEqual("veto", result["rule_explanation"]["outcome"])
        self.assertTrue(result["ledger_verification"]["ok"])


if __name__ == "__main__":
    unittest.main()
