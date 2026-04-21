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

    def test_collective_demo_emits_bounded_merge_and_recovery_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "collective-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["collective_identity_distinct"])
        self.assertTrue(result["validation"]["merge_window_bounded"])
        self.assertTrue(result["validation"]["private_escape_honored"])
        self.assertTrue(result["validation"]["identity_confirmation_complete"])
        self.assertEqual("dissolved", result["collective"]["status"])
        self.assertEqual("merge_thought", result["merge"]["merge_mode"])
        self.assertEqual("private_reality", result["wms"]["escape"]["new_mode"])

    def test_ewa_demo_emits_vetoed_irreversible_command(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "ewa-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["authorization_ok"])
        self.assertTrue(result["validation"]["authorization_ready"])
        self.assertTrue(result["validation"]["authorization_matches_command"])
        self.assertEqual("physical-device-actuation", result["validation"]["authorization_delivery_scope"])
        self.assertEqual("executed", result["approved_command"]["status"])
        self.assertEqual("vetoed", result["veto"]["status"])
        self.assertIn("harm.human", result["veto"]["matched_tokens"])
        self.assertEqual(
            result["authorization"]["authorization_id"],
            result["approved_command"]["approval_path"]["authorization_id"],
        )
        self.assertEqual("released", result["release"]["status"])

    def test_sensory_loopback_demo_emits_guardian_hold_and_recovery(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "sensory-loopback-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("delivered", result["receipts"]["coherent"]["delivery_status"])
        self.assertEqual("guardian-hold", result["receipts"]["degraded"]["delivery_status"])
        self.assertEqual("stabilized", result["receipts"]["stabilized"]["delivery_status"])
        self.assertTrue(result["validation"]["artifact_family_ok"])
        self.assertEqual(3, result["artifact_family"]["scene_count"])
        self.assertEqual(2, result["artifact_family"]["guardian_intervention_count"])
        self.assertEqual("active", result["session"]["status"])

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
        self.assertTrue(result["memory"]["episodic_stream"]["ready_for_compaction"])
        self.assertEqual(
            5,
            len(result["memory"]["episodic_stream"]["compaction_candidate_ids"]),
        )

    def test_memory_edit_demo_emits_reversible_buffer_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "memory-edit-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["memory_edit"]["ok"])
        self.assertTrue(result["validation"]["deletion_blocked"])
        self.assertTrue(result["validation"]["source_manifest_preserved"])
        self.assertEqual(1, result["validation"]["memory_edit"]["recall_view_count"])
        self.assertEqual(["trauma-recall"], result["validation"]["memory_edit"]["concept_labels"])
        self.assertEqual(
            ["self-only"],
            result["validation"]["memory_edit"]["disclosure_scopes"],
        )
        self.assertEqual("approved", result["memory_edit"]["session"]["status"])

    def test_semantic_demo_emits_valid_projection_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "semantic-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["semantic"]["ok"])
        self.assertEqual(2, result["validation"]["semantic"]["concept_count"])
        self.assertEqual(
            ["council-review", "migration-check"],
            result["validation"]["semantic"]["labels"],
        )
        self.assertEqual(
            ["procedural-memory"],
            result["semantic"]["snapshot"]["deferred_surfaces"],
        )

    def test_procedural_demo_emits_valid_preview_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "procedural-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["procedural"]["ok"])
        self.assertEqual(2, result["validation"]["procedural"]["recommendation_count"])
        self.assertEqual(
            ["continuity_integrator->ethics_gate", "sensory_ingress->continuity_integrator"],
            sorted(result["validation"]["procedural"]["target_paths"]),
        )
        self.assertEqual(
            ["skill-execution"],
            result["procedural"]["snapshot"]["deferred_surfaces"],
        )

    def test_procedural_writeback_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "procedural-writeback-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["writeback"]["ok"])
        self.assertEqual(2, result["validation"]["writeback"]["applied_recommendation_count"])
        self.assertEqual(
            ["human://reviewers/alice", "human://reviewers/bob"],
            result["validation"]["writeback"]["human_reviewers"],
        )
        self.assertEqual("approved", result["procedural"]["writeback_receipt"]["status"])

    def test_procedural_skill_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "procedural-skill-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["execution"]["ok"])
        self.assertEqual(2, result["validation"]["execution"]["execution_count"])
        self.assertEqual(
            ["guardian-review-rehearsal", "migration-handoff-rehearsal"],
            sorted(result["validation"]["execution"]["skill_labels"]),
        )
        self.assertEqual("sandbox-only", result["validation"]["execution"]["delivery_scope"])
        self.assertTrue(result["validation"]["execution"]["rollback_token_preserved"])
        self.assertEqual([], result["procedural"]["skill_execution_receipt"]["external_effects"])

    def test_procedural_enactment_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "procedural-enactment-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["enactment"]["ok"])
        self.assertEqual(2, result["validation"]["enactment"]["materialized_skill_count"])
        self.assertEqual(2, result["validation"]["enactment"]["executed_command_count"])
        self.assertTrue(result["validation"]["enactment"]["all_commands_passed"])
        self.assertEqual("removed", result["validation"]["enactment"]["cleanup_status"])
        self.assertEqual("sandbox-only", result["validation"]["enactment"]["delivery_scope"])
        self.assertTrue(result["validation"]["enactment"]["rollback_token_preserved"])
        self.assertEqual("passed", result["procedural"]["skill_enactment_session"]["status"])

    def test_design_reader_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "design-reader-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("ready", result["validation"]["manifest_status"])
        self.assertEqual(7, result["validation"]["source_digest_count"])
        self.assertEqual(3, result["validation"]["must_sync_docs_count"])
        self.assertTrue(result["validation"]["build_request_has_design_delta_ref"])
        self.assertTrue(result["validation"]["build_request_has_design_delta_digest"])
        self.assertEqual(7, result["validation"]["output_path_count"])

    def test_builder_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "builder-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["design_reader_handoff_ok"])
        self.assertEqual("ready", result["validation"]["design_manifest_status"])
        self.assertEqual(12, result["validation"]["design_source_digest_count"])
        self.assertEqual(3, result["validation"]["must_sync_docs_count"])
        self.assertTrue(result["validation"]["scope_allowed"])
        self.assertEqual(2, result["validation"]["patch_count"])
        self.assertEqual("applied", result["validation"]["sandbox_apply_status"])
        self.assertEqual("promote", result["validation"]["rollout_decision"])
        self.assertEqual("promoted", result["validation"]["rollout_status"])
        self.assertEqual(4, result["validation"]["rollout_completed_stage_count"])
        self.assertEqual("ready", result["builder"]["artifact"]["status"])
        self.assertEqual(
            [
                "evals/continuity/council_output_build_request_pipeline.yaml",
                "evals/continuity/builder_staged_rollout_execution.yaml",
            ],
            result["builder"]["suite_selection"]["selected_evals"],
        )
        self.assertEqual(
            "emit_build_request",
            result["builder"]["council_output"]["approved_action"],
        )
        self.assertTrue(result["builder"]["build_request"]["design_delta_ref"].startswith("design://"))
        self.assertEqual("promoted", result["builder"]["rollout_session"]["status"])

    def test_builder_live_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "builder-live-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["design_reader_handoff_ok"])
        self.assertEqual("ready", result["validation"]["design_manifest_status"])
        self.assertTrue(result["validation"]["enactment_ok"])
        self.assertEqual("passed", result["validation"]["enactment_status"])
        self.assertEqual(2, result["validation"]["mutated_file_count"])
        self.assertEqual(2, result["validation"]["executed_command_count"])
        self.assertTrue(result["validation"]["all_commands_passed"])
        self.assertEqual("removed", result["validation"]["cleanup_status"])
        self.assertEqual(
            ["evals/continuity/builder_live_enactment_execution.yaml"],
            result["builder"]["suite_selection"]["selected_evals"],
        )
        self.assertEqual("passed", result["builder"]["enactment_session"]["status"])

    def test_rollback_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "rollback-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["design_reader_handoff_ok"])
        self.assertEqual("ready", result["validation"]["design_manifest_status"])
        self.assertTrue(result["validation"]["live_enactment_ok"])
        self.assertTrue(result["validation"]["regression_detected"])
        self.assertEqual("rollback", result["validation"]["rollout_decision"])
        self.assertEqual("rolled-back", result["validation"]["rollout_status"])
        self.assertEqual("rolled-back", result["validation"]["rollback_status"])
        self.assertEqual("passed", result["validation"]["live_enactment_status"])
        self.assertEqual("eval-regression", result["validation"]["rollback_trigger"])
        self.assertEqual(5, result["validation"]["selected_eval_count"])
        self.assertEqual(2, result["validation"]["reverted_patch_count"])
        self.assertEqual(2, result["validation"]["reverse_apply_journal_count"])
        self.assertEqual(2, result["validation"]["reverse_apply_command_count"])
        self.assertEqual(2, result["validation"]["reverse_apply_verified_count"])
        self.assertEqual(2, result["validation"]["repo_bound_verified_count"])
        self.assertEqual("current-checkout-subtree", result["validation"]["repo_binding_scope"])
        self.assertEqual(2, result["validation"]["repo_binding_path_count"])
        self.assertEqual("verified", result["validation"]["checkout_mutation_status"])
        self.assertEqual(2, result["validation"]["checkout_mutation_path_count"])
        self.assertEqual("removed", result["validation"]["checkout_mutation_cleanup_status"])
        self.assertTrue(result["validation"]["checkout_mutation_restored"])
        self.assertEqual("verified", result["validation"]["current_worktree_mutation_status"])
        self.assertEqual(2, result["validation"]["current_worktree_mutation_path_count"])
        self.assertEqual(
            "removed", result["validation"]["current_worktree_mutation_cleanup_status"]
        )
        self.assertTrue(result["validation"]["current_worktree_mutation_restored"])
        self.assertEqual("verified", result["validation"]["external_observer_status"])
        self.assertEqual(5, result["validation"]["external_observer_receipt_count"])
        self.assertTrue(result["validation"]["external_observer_restored"])
        self.assertTrue(result["validation"]["external_observer_stash_preserved"])
        self.assertEqual("satisfied", result["validation"]["reviewer_oversight_status"])
        self.assertEqual(2, result["validation"]["reviewer_quorum_required"])
        self.assertEqual(2, result["validation"]["reviewer_quorum_received"])
        self.assertEqual(2, result["validation"]["reviewer_binding_count"])
        self.assertEqual(2, result["validation"]["reviewer_network_receipt_count"])
        self.assertTrue(result["validation"]["reviewer_network_attested"])
        self.assertTrue(result["validation"]["rollback_payload_ref_bound"])
        self.assertEqual("removed", result["validation"]["reverse_apply_cleanup_status"])
        self.assertEqual(
            ["dark-launch", "canary-5pct"],
            result["validation"]["reverted_stage_ids"],
        )
        self.assertEqual("rollback-approved", result["validation"]["telemetry_gate_status"])
        self.assertEqual("removed", result["validation"]["telemetry_gate_cleanup_status"])
        self.assertEqual(2, result["validation"]["telemetry_gate_command_count"])
        self.assertEqual(
            "mirage://build-l5-rollback-0001/snapshot/pre-apply",
            result["validation"]["restored_snapshot_ref"],
        )
        self.assertEqual("rolled-back", result["builder"]["rollback_session"]["status"])

    def test_episodic_demo_emits_valid_handoff_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "episodic-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["snapshot"]["ready_for_compaction"])
        self.assertTrue(result["validation"]["manifest"]["append_only"])
        self.assertEqual("canonical-episodic-stream-v1", result["profile"]["policy_id"])
        self.assertEqual(5, result["handoff"]["candidate_event_count"])

    def test_reasoning_demo_emits_trace_and_shift_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "reasoning-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["baseline_primary"])
        self.assertEqual("narrative_v1", result["validation"]["selected_backend"])
        self.assertTrue(result["validation"]["shift_safe"])
        self.assertEqual("reasoning_trace", result["reasoning"]["trace"]["kind"])
        self.assertEqual("reasoning_shift", result["reasoning"]["shift"]["kind"])

    def test_cognitive_demo_remains_reasoning_alias(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "cognitive-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("narrative_v1", result["reasoning"]["selected_backend"])
        self.assertTrue(result["reasoning"]["shift"]["safe_summary_only"])

    def test_substrate_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "substrate-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual("released", result["substrate"]["allocation"]["status"])
        self.assertEqual("warm-standby", result["substrate"]["transfer"]["continuity_mode"])

    def test_broker_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "broker-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["neutrality_rotation_triggered"])
        self.assertEqual("critical", result["broker"]["energy_floor_signal"]["severity"])
        self.assertEqual(
            result["broker"]["selection"]["standby_substrate"]["substrate_id"],
            result["broker"]["migration"]["destination_substrate"],
        )
        self.assertEqual("released", result["broker"]["release"]["status"])

    def test_qualia_demo_emits_reference_profile(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "qualia-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual(32, result["qualia"]["profile"]["embedding_dimensions"])
        self.assertEqual(250, result["qualia"]["profile"]["sampling_window_ms"])
        self.assertEqual(32, len(result["qualia"]["recent"][0]["sensory_embeddings"]["visual"]))

    def test_self_model_demo_emits_threshold_and_abrupt_flag(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "self-model-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("bounded-self-model-monitor-v1", result["profile"]["policy_id"])
        self.assertEqual(0.35, result["validation"]["threshold"])
        self.assertTrue(result["validation"]["stable_within_threshold"])
        self.assertTrue(result["validation"]["abrupt_flagged"])
        self.assertEqual(3, result["validation"]["history_length"])

    def test_affect_demo_emits_smoothed_failover_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "affect-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("stability_guard_v1", result["validation"]["selected_backend"])
        self.assertTrue(result["validation"]["smoothed"])
        self.assertTrue(result["validation"]["consent_preserved"])
        self.assertEqual("observe", result["validation"]["recommended_guard"])

    def test_attention_demo_emits_guard_aligned_failover_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "attention-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("continuity_anchor_v1", result["validation"]["selected_backend"])
        self.assertTrue(result["validation"]["guard_aligned"])
        self.assertTrue(result["validation"]["safe_target_selected"])
        self.assertEqual("guardian-review", result["attention"]["focus"]["focus_target"])
        self.assertTrue(result["ledger_verification"]["ok"])

    def test_volition_demo_emits_guard_aligned_failover_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "volition-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("guardian_bias_v1", result["validation"]["selected_backend"])
        self.assertTrue(result["validation"]["guard_aligned"])
        self.assertEqual("guardian-review", result["validation"]["selected_intent"])
        self.assertEqual("review", result["validation"]["execution_mode"])
        self.assertEqual("guardian-review", result["volition"]["intent"]["selected_intent"])
        self.assertTrue(result["ledger_verification"]["ok"])

    def test_imagination_demo_emits_bounded_handoff_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "imagination-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("continuity_scene_guard_v1", result["validation"]["selected_backend"])
        self.assertTrue(result["validation"]["baseline_co_imagination_ready"])
        self.assertTrue(result["validation"]["baseline_shared_handoff"])
        self.assertTrue(result["validation"]["failover_private"])
        self.assertTrue(result["validation"]["imc_delivery_redacted"])
        self.assertTrue(result["ledger_verification"]["ok"])

    def test_language_demo_emits_redacted_guarded_bridge_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "language-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["baseline_primary"])
        self.assertEqual("continuity_phrase_v1", result["validation"]["selected_backend"])
        self.assertTrue(result["validation"]["guard_aligned"])
        self.assertTrue(result["validation"]["redaction_applied"])
        self.assertEqual("guardian", result["validation"]["delivery_target"])
        self.assertEqual("guardian-brief", result["validation"]["discourse_mode"])
        self.assertTrue(result["validation"]["private_channel_locked"])

    def test_metacognition_demo_emits_guarded_self_monitor_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "metacognition-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("continuity_mirror_v1", result["validation"]["selected_backend"])
        self.assertTrue(result["validation"]["baseline_primary"])
        self.assertTrue(result["validation"]["guard_aligned"])
        self.assertTrue(result["validation"]["abrupt_change_flagged"])
        self.assertEqual("guardian-review", result["validation"]["escalation_target"])
        self.assertTrue(result["validation"]["sealed_notes_present"])

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

    def test_scheduler_demo_emits_timeout_rollback_and_completion(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "scheduler-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["method_a_fixed"])
        self.assertTrue(result["validation"]["method_b_fixed"])
        self.assertTrue(result["validation"]["method_c_fixed"])
        self.assertTrue(result["validation"]["order_violation_blocked"])
        self.assertTrue(result["validation"]["timeout_rolled_back"])
        self.assertTrue(result["validation"]["method_b_signal_paused"])
        self.assertTrue(result["validation"]["method_b_signal_rolled_back"])
        self.assertTrue(result["validation"]["method_b_completed"])
        self.assertTrue(result["validation"]["method_c_fail_closed"])
        self.assertTrue(result["validation"]["artifact_bundle_attached"])
        self.assertTrue(result["validation"]["artifact_sync_gate_blocked"])
        self.assertTrue(result["validation"]["artifact_sync_current_before_handoff"])
        self.assertTrue(result["validation"]["live_verifier_reachable"])
        self.assertTrue(result["validation"]["live_verifier_receipt_bound"])
        self.assertTrue(result["validation"]["live_verifier_sync_accepted"])
        self.assertTrue(result["validation"]["artifact_refresh_paused"])
        self.assertTrue(result["validation"]["artifact_refresh_recovered"])
        self.assertTrue(result["validation"]["artifact_revocation_fail_closed"])
        self.assertTrue(result["validation"]["verifier_rotation_overlap_paused"])
        self.assertTrue(result["validation"]["verifier_rotation_cutover_recovered"])
        self.assertTrue(result["validation"]["verifier_rotation_dual_attested"])
        self.assertTrue(result["validation"]["verifier_revocation_fail_closed"])
        self.assertTrue(result["validation"]["witness_quorum_bound"])
        self.assertTrue(result["validation"]["legal_attestation_bound"])
        self.assertEqual("rollback", result["scenarios"]["timeout"]["action"])
        self.assertEqual("completed", result["final_handle"]["status"])
        self.assertEqual("current", result["final_handle"]["artifact_sync"]["bundle_status"])
        self.assertEqual("stable", result["final_handle"]["verifier_roster"]["rotation_state"])
        self.assertEqual(
            "reachable",
            result["method_a_live_final_handle"]["verifier_roster"]["connectivity_receipt"][
                "receipt_status"
            ],
        )
        self.assertEqual(
            "rotated",
            result["method_a_rotation_final_handle"]["verifier_roster"]["rotation_state"],
        )
        self.assertEqual(
            "dual-channel-review",
            result["scenarios"]["method_b"]["signal_rollback"]["rollback_target"],
        )
        self.assertEqual("fail", result["scenarios"]["method_c"]["signal_fail"]["action"])
        self.assertEqual(
            "fail",
            result["scenarios"]["method_c_revoked"]["artifact_sync"]["action"],
        )
        self.assertEqual(
            "fail",
            result["scenarios"]["method_c_verifier_revoked"]["artifact_sync"]["action"],
        )

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

    def test_distributed_council_demo_emits_bound_external_resolutions(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "distributed-council-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual(
            "binding-approved",
            result["distributed_resolutions"]["federation"]["final_outcome"],
        )
        self.assertEqual(
            "ethics-veto",
            result["distributed_resolutions"]["heritage"]["decision_mode"],
        )
        self.assertEqual(
            "escalate-human-governance",
            result["distributed_resolutions"]["conflict"]["final_outcome"],
        )
        self.assertTrue(result["validation"]["federation_binds_cross_self"])
        self.assertTrue(result["validation"]["heritage_veto_blocks_local"])
        self.assertTrue(result["validation"]["conflict_escalates_to_human"])

    def test_distributed_transport_demo_emits_attested_handoffs_and_replay_guard(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "distributed-transport-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual(
            "federation-mtls-quorum-v1",
            result["handoffs"]["federation"]["transport_profile"],
        )
        self.assertEqual("authenticated", result["receipts"]["federation"]["receipt_status"])
        self.assertEqual("authenticated", result["receipts"]["federation_rotated"]["receipt_status"])
        self.assertEqual("authenticated", result["receipts"]["heritage"]["receipt_status"])
        self.assertEqual("replay-blocked", result["receipts"]["replay_blocked"]["receipt_status"])
        self.assertEqual("replay-blocked", result["receipts"]["multi_hop_replay_blocked"]["receipt_status"])
        self.assertEqual([1, 2], result["handoffs"]["federation_rotated"]["accepted_key_epochs"])
        self.assertTrue(result["validation"]["replay_guard_blocks_reuse"])
        self.assertTrue(result["validation"]["federation_rotation_authenticated"])
        self.assertTrue(result["validation"]["multi_hop_replay_blocks_reuse"])
        self.assertTrue(result["validation"]["live_root_directory_reachable"])
        self.assertTrue(result["validation"]["live_root_directory_quorum_bound"])
        self.assertTrue(result["validation"]["authority_plane_fleet_bound"])
        self.assertTrue(result["validation"]["authority_plane_root_directory_bound"])
        self.assertTrue(result["validation"]["authority_plane_churn_safe"])
        self.assertTrue(result["validation"]["authority_churn_overlap_bound"])
        self.assertTrue(result["validation"]["authority_churn_requires_draining_exit"])
        self.assertTrue(result["validation"]["authority_route_mtls_authenticated"])
        self.assertTrue(result["validation"]["authority_route_socket_trace_bound"])
        self.assertTrue(result["validation"]["authority_route_os_observer_bound"])
        self.assertEqual(
            2,
            result["live_root_directory"]["federation_rotated"]["connectivity_receipt"][
                "matched_root_count"
            ],
        )
        self.assertEqual(
            3,
            result["authority_plane"]["federation_rotated_initial"]["reachable_server_count"],
        )
        self.assertEqual(
            2,
            result["authority_plane"]["federation_rotated"]["reachable_server_count"],
        )
        self.assertEqual(
            2,
            result["authority_plane"]["federation_rotated_initial"]["active_server_count"],
        )
        self.assertEqual(
            1,
            result["authority_plane"]["federation_rotated_initial"]["draining_server_count"],
        )
        self.assertEqual(
            ["root://federation/pki-a", "root://federation/pki-b"],
            result["authority_plane"]["federation_rotated"]["trusted_root_refs"],
        )
        self.assertEqual(
            "handoff-ready",
            result["authority_plane"]["federation_rotated_initial"]["root_coverage"][1][
                "coverage_status"
            ],
        )
        self.assertEqual(
            "stable",
            result["authority_plane"]["federation_rotated"]["root_coverage"][1]["coverage_status"],
        )
        self.assertEqual(
            [],
            result["authority_churn"]["federation_rotated"]["added_server_refs"],
        )
        self.assertEqual(
            ["keyserver://federation/mirror-b-draining"],
            result["authority_churn"]["federation_rotated"]["removed_server_refs"],
        )
        self.assertEqual(
            result["authority_plane"]["federation_rotated"]["trusted_root_refs"],
            result["receipts"]["federation_rotated"]["verified_root_refs"],
        )
        self.assertEqual(
            "authenticated",
            result["authority_route_trace"]["federation_rotated"]["trace_status"],
        )
        self.assertEqual(
            2,
            result["authority_route_trace"]["federation_rotated"]["route_count"],
        )
        self.assertEqual(
            2,
            result["authority_route_trace"]["federation_rotated"]["mtls_authenticated_count"],
        )
        self.assertTrue(
            result["authority_route_trace"]["federation_rotated"]["non_loopback_verified"],
        )
        self.assertTrue(
            result["authority_route_trace"]["federation_rotated"]["authority_plane_bound"],
        )
        self.assertTrue(
            result["authority_route_trace"]["federation_rotated"]["response_digest_bound"],
        )
        self.assertTrue(
            result["authority_route_trace"]["federation_rotated"]["socket_trace_complete"],
        )
        self.assertEqual(
            "authority.local",
            result["authority_route_trace"]["federation_rotated"]["server_name"],
        )
        self.assertEqual(
            "os-native-tcp-observer-v1",
            result["authority_route_trace"]["federation_rotated"]["os_observer_profile"],
        )
        self.assertTrue(
            result["authority_route_trace"]["federation_rotated"]["os_observer_complete"],
        )
        self.assertTrue(
            all(
                binding["mtls_status"] == "authenticated"
                and binding["socket_trace"]["transport_profile"] == "mtls-socket-trace-v1"
                and binding["socket_trace"]["tls_version"].startswith("TLS")
                and not binding["socket_trace"]["remote_ip"].startswith("127.")
                for binding in result["authority_route_trace"]["federation_rotated"]["route_bindings"]
            )
        )
        self.assertTrue(
            all(
                binding["os_observer_receipt"]["receipt_status"] == "observed"
                and binding["os_observer_receipt"]["observed_sources"]
                and binding["os_observer_receipt"]["connection_states"]
                and binding["os_observer_receipt"]["owning_pid"] > 0
                for binding in result["authority_route_trace"]["federation_rotated"]["route_bindings"]
            )
        )
        self.assertTrue(result["validation"]["relay_telemetry_binds_rotated_path"])
        self.assertTrue(result["validation"]["relay_telemetry_surfaces_replay_block"])
        self.assertEqual(2, result["relay_telemetry"]["federation_rotated"]["hop_count"])
        self.assertEqual(
            "accepted",
            result["relay_telemetry"]["federation_rotated"]["anti_replay_status"],
        )
        self.assertEqual(
            "replay-blocked",
            result["relay_telemetry"]["multi_hop_replay_blocked"]["end_to_end_status"],
        )

    def test_cognitive_audit_demo_emits_cross_layer_review_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "cognitive-audit-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["ledger_categories_bound"]["qualia_checkpoint"])
        self.assertTrue(result["self_model"]["alert"]["abrupt_change"])
        self.assertEqual("guardian-review", result["audit"]["record"]["recommended_action"])
        self.assertEqual("open-guardian-review", result["audit"]["resolution"]["follow_up_action"])
        self.assertEqual("approved", result["council"]["decision"]["outcome"])

    def test_cognitive_audit_governance_demo_emits_governance_bound_json(self) -> None:
        stdout = io.StringIO()

        with patch(
            "sys.argv",
            ["omoikane", "cognitive-audit-governance-demo", "--json"],
        ), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["all_bindings_valid"])
        self.assertTrue(result["validation"]["oversight_network_bound"])
        self.assertEqual(
            "federation-attested-review",
            result["bindings"]["federation"]["execution_gate"],
        )
        self.assertEqual(
            "heritage-veto-boundary",
            result["bindings"]["heritage"]["execution_gate"],
        )
        self.assertEqual(
            "distributed-conflict-human-escalation",
            result["bindings"]["conflict"]["execution_gate"],
        )

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

    def test_consensus_bus_demo_emits_audited_delivery_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "consensus-bus-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["bus_transport_bound"])
        self.assertTrue(result["validation"]["direct_attempt_blocked"])
        self.assertEqual("resolve", result["session"]["audit"]["last_phase"])
        self.assertEqual(1, result["session"]["audit"]["blocked_direct_attempts"])
        self.assertEqual(7, result["ledger_verification"]["category_counts"]["consensus-bus"])
        self.assertTrue(result["ledger_verification"]["ok"])

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
        self.assertTrue(result["validation"]["veto_binding_recorded"])
        self.assertTrue(result["validation"]["verification_binding_recorded"])
        self.assertTrue(result["validation"]["reviewer_registry_ready"])
        self.assertTrue(result["validation"]["live_verification_ready"])
        self.assertTrue(result["validation"]["jurisdiction_bundle_ready"])
        self.assertTrue(result["validation"]["responsibility_scope_enforced"])
        self.assertTrue(result["validation"]["pin_breach_propagated"])
        self.assertEqual("joint", result["events"]["veto"]["reviewer_bindings"][0]["liability_mode"])
        self.assertEqual(
            "reviewer-live-proof-bridge-v1",
            result["events"]["veto"]["reviewer_bindings"][0]["transport_profile"],
        )
        self.assertFalse(result["trust"]["after_breach"]["pinned_by_human"])
        self.assertFalse(result["trust"]["after_breach"]["eligibility"]["guardian_role"])

    def test_oversight_network_demo_emits_verifier_network_receipt(self) -> None:
        stdout = io.StringIO()

        with patch(
            "sys.argv",
            ["omoikane", "oversight-network-demo", "--json"],
        ), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["network_receipt_verified"])
        self.assertTrue(result["validation"]["network_endpoint_bound"])
        self.assertTrue(result["validation"]["binding_carries_receipt"])
        self.assertTrue(result["validation"]["binding_carries_trust_root"])
        self.assertEqual(
            "guardian-reviewer-remote-attestation-v1",
            result["reviewer"]["credential_verification"]["network_receipt"]["network_profile_id"],
        )
        self.assertEqual(
            "verifier://guardian-oversight.jp",
            result["reviewer"]["credential_verification"]["network_receipt"]["verifier_endpoint"],
        )

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

    def test_termination_demo_emits_immediate_and_cool_off_paths(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "termination-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["completed_within_budget"])
        self.assertTrue(result["validation"]["cool_off_pending"])
        self.assertTrue(result["validation"]["invalid_self_proof_rejected"])
        self.assertEqual("completed", result["outcomes"]["completed"]["status"])
        self.assertEqual("cool-off-pending", result["outcomes"]["cool_off"]["status"])
        self.assertEqual("invalid-self-proof", result["outcomes"]["rejected"]["reject_reason"])
        self.assertTrue(result["ledger_verification"]["ok"])


if __name__ == "__main__":
    unittest.main()
