from __future__ import annotations

import unittest
from pathlib import Path

from omoikane.reference_os import OmoikaneReferenceOS


class ReferenceRuntimeTests(unittest.TestCase):
    def test_version_demo_emits_release_manifest(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_version_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("0.1.0", result["manifest"]["runtime_version"])
        self.assertEqual("2026.04", result["manifest"]["regulation_calver"])
        self.assertEqual("2026.04", result["manifest"]["catalog_snapshot"]["calver"])
        self.assertIn("agentic.council.v0", result["manifest"]["idl_versions"])
        self.assertIn(
            "specs/schemas/release_manifest.schema",
            result["manifest"]["schema_versions"],
        )
        self.assertEqual("bootstrap", result["manifest"]["runtime_stability"])
        self.assertEqual(64, len(result["release_digest"]))

    def test_amendment_demo_reports_constitutional_freeze(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_amendment_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["core_frozen"])
        self.assertTrue(result["validation"]["kernel_guarded_rollout"])
        self.assertTrue(result["validation"]["operational_guarded_rollout"])
        self.assertEqual(2, result["policy"]["kernel_human_review_quorum"])
        self.assertEqual("frozen", result["proposals"]["core"]["status"])
        self.assertFalse(result["decisions"]["core"]["allow_apply"])
        self.assertEqual("dark-launch", result["decisions"]["kernel"]["applied_stage"])
        self.assertEqual("5pct", result["decisions"]["operational"]["applied_stage"])

    def test_bdb_demo_reports_viable_bridge_contract(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_bdb_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("bio-autonomous-fallback", result["session"]["bridge_state"])
        self.assertEqual(0.0, result["session"]["effective_replacement_ratio"])
        self.assertTrue(result["validation"]["reversibility_verified"])
        self.assertEqual(3, result["ledger_verification"]["category_counts"]["interface-bdb"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["interface-bdb-fallback"])

    def test_imc_demo_reports_disclosure_floor_and_disconnect(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_imc_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("memory_glimpse", result["handshake"]["route_mode"])
        self.assertTrue(result["validation"]["forward_secrecy_enforced"])
        self.assertTrue(result["validation"]["sealed_fields_protected"])
        self.assertEqual("closed", result["session"]["status"])
        self.assertEqual(3, result["ledger_verification"]["category_counts"]["interface-imc"])

    def test_collective_demo_reports_bounded_merge_and_dissolution(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_collective_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["collective_identity_distinct"])
        self.assertTrue(result["validation"]["merge_window_bounded"])
        self.assertTrue(result["validation"]["merge_duration_within_budget"])
        self.assertTrue(result["validation"]["private_escape_honored"])
        self.assertTrue(result["validation"]["identity_confirmation_complete"])
        self.assertTrue(result["validation"]["dissolution_clears_collective"])
        self.assertEqual("merge_thought", result["merge"]["merge_mode"])
        self.assertEqual("dissolved", result["collective"]["status"])
        self.assertEqual(4, result["ledger_verification"]["category_counts"]["interface-collective"])

    def test_ewa_demo_reports_veto_and_release(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_ewa_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["authorization_ok"])
        self.assertTrue(result["validation"]["authorization_ready"])
        self.assertTrue(result["validation"]["authorization_matches_command"])
        self.assertEqual("physical-device-actuation", result["validation"]["authorization_delivery_scope"])
        self.assertEqual("executed", result["approved_command"]["status"])
        self.assertTrue(result["validation"]["emergency_stop_ok"])
        self.assertTrue(result["validation"]["emergency_stop_latched"])
        self.assertTrue(result["validation"]["emergency_stop_bound_to_command"])
        self.assertTrue(result["validation"]["emergency_stop_bound_to_authorization"])
        self.assertTrue(result["validation"]["release_after_stop"])
        self.assertEqual("vetoed", result["veto"]["status"])
        self.assertIn("harm.human", result["veto"]["matched_tokens"])
        self.assertEqual("released", result["handle"]["status"])
        self.assertEqual("released", result["veto_handle"]["status"])
        self.assertEqual("watchdog-timeout", result["emergency_stop"]["trigger_source"])
        self.assertEqual(
            result["authorization"]["authorization_id"],
            result["approved_command"]["approval_path"]["authorization_id"],
        )
        self.assertEqual(
            1,
            result["ledger_verification"]["category_counts"]["interface-ewa-authorization"],
        )
        self.assertEqual(6, result["ledger_verification"]["category_counts"]["interface-ewa"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["interface-ewa-veto"])
        self.assertEqual(
            1,
            result["ledger_verification"]["category_counts"]["interface-ewa-emergency-stop"],
        )

    def test_sensory_loopback_demo_reports_guardian_hold_and_recovery(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_sensory_loopback_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["coherent_delivery"])
        self.assertTrue(result["validation"]["guardian_hold_triggered"])
        self.assertTrue(result["validation"]["stabilized_active"])
        self.assertTrue(result["validation"]["artifact_family_ok"])
        self.assertTrue(result["validation"]["artifact_family_multi_scene"])
        self.assertTrue(result["validation"]["artifact_family_bound"])
        self.assertTrue(result["validation"]["qualia_binding_bound"])
        self.assertEqual("active", result["session"]["status"])
        self.assertEqual(3, result["artifact_family"]["scene_count"])
        self.assertEqual(2, result["artifact_family"]["guardian_intervention_count"])
        self.assertEqual("active", result["artifact_family"]["final_session_status"])
        self.assertEqual("guardian-hold", result["receipts"]["degraded"]["delivery_status"])
        self.assertEqual(3, result["ledger_verification"]["category_counts"]["interface-sensory-loopback"])
        self.assertEqual(
            1,
            result["ledger_verification"]["category_counts"]["interface-sensory-loopback-guardian"],
        )
        self.assertEqual(
            1,
            result["ledger_verification"]["category_counts"]["interface-sensory-loopback-family"],
        )

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
        self.assertEqual(0, report["open_question_count"])
        self.assertEqual(0, report["missing_expected_file_count"])
        self.assertEqual(0, report["empty_eval_surface_count"])
        self.assertEqual(0, report["catalog_pending_count"])

    def test_naming_demo_returns_fixed_policy_and_aliases(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_naming_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual("Omoikane", result["policy"]["rules"]["project_romanization"]["canonical"])
        self.assertEqual("Mirage Self", result["policy"]["rules"]["sandbox_self_name"]["canonical"])
        self.assertEqual("rewrite-required", result["reviews"]["hyphenated_brand"]["status"])
        self.assertEqual("allowed-alias", result["reviews"]["legacy_runtime_alias"]["status"])
        self.assertTrue(result["validation"]["sandbox_formal_name_fixed"])

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

    def test_memory_edit_demo_returns_reversible_buffer_session(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_memory_edit_demo()

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
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["memory-edit"])

    def test_semantic_demo_returns_valid_projection(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_semantic_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["semantic"]["ok"])
        self.assertEqual(2, result["validation"]["semantic"]["concept_count"])
        self.assertEqual(
            ["council-review", "migration-check"],
            result["validation"]["semantic"]["labels"],
        )
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["semantic-projection"])

    def test_procedural_demo_returns_valid_preview(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_procedural_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["connectome"]["ok"])
        self.assertTrue(result["validation"]["procedural"]["ok"])
        self.assertEqual(2, result["validation"]["procedural"]["recommendation_count"])
        self.assertEqual(
            ["continuity_integrator->ethics_gate", "sensory_ingress->continuity_integrator"],
            sorted(result["validation"]["procedural"]["target_paths"]),
        )
        self.assertEqual(["skill-execution"], result["procedural"]["snapshot"]["deferred_surfaces"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["procedural-preview"])

    def test_procedural_writeback_demo_returns_valid_receipt(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_procedural_writeback_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["writeback"]["ok"])
        self.assertEqual(2, result["validation"]["writeback"]["applied_recommendation_count"])
        self.assertEqual(
            ["human://reviewers/alice", "human://reviewers/bob"],
            result["validation"]["writeback"]["human_reviewers"],
        )
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["procedural-writeback"])

    def test_procedural_skill_demo_returns_valid_sandbox_execution(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_procedural_skill_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["execution"]["ok"])
        self.assertEqual(2, result["validation"]["execution"]["execution_count"])
        self.assertEqual(
            ["guardian-review-rehearsal", "migration-handoff-rehearsal"],
            sorted(result["validation"]["execution"]["skill_labels"]),
        )
        self.assertTrue(result["validation"]["execution"]["rollback_token_preserved"])
        self.assertEqual("sandbox-complete", result["procedural"]["skill_execution_receipt"]["status"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["procedural-execution"])

    def test_procedural_enactment_demo_returns_valid_temp_workspace_session(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_procedural_enactment_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["enactment"]["ok"])
        self.assertEqual(2, result["validation"]["enactment"]["materialized_skill_count"])
        self.assertEqual(2, result["validation"]["enactment"]["executed_command_count"])
        self.assertTrue(result["validation"]["enactment"]["all_commands_passed"])
        self.assertEqual("removed", result["validation"]["enactment"]["cleanup_status"])
        self.assertEqual("passed", result["validation"]["enactment"]["enactment_status"])
        self.assertTrue(result["validation"]["enactment"]["rollback_token_preserved"])
        self.assertEqual("passed", result["procedural"]["skill_enactment_session"]["status"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["procedural-enactment"])

    def test_design_reader_demo_returns_bound_handoff(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_design_reader_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("ready", result["validation"]["manifest_status"])
        self.assertEqual(7, result["validation"]["source_digest_count"])
        self.assertEqual(3, result["validation"]["must_sync_docs_count"])
        self.assertEqual("delta-detected", result["validation"]["delta_scan_status"])
        self.assertEqual(2, result["validation"]["delta_scan_changed_ref_count"])
        self.assertEqual(1, result["validation"]["delta_scan_changed_design_ref_count"])
        self.assertEqual(1, result["validation"]["delta_scan_changed_spec_ref_count"])
        self.assertEqual(2, result["validation"]["delta_scan_command_receipt_count"])
        self.assertTrue(result["validation"]["delta_scan_bound_to_manifest"])
        self.assertTrue(result["validation"]["council_review_required"])
        self.assertTrue(result["validation"]["guardian_review_required"])
        self.assertTrue(result["validation"]["build_request_has_design_delta_ref"])
        self.assertTrue(result["validation"]["build_request_has_design_delta_digest"])
        self.assertEqual(7, result["validation"]["output_path_count"])
        self.assertEqual(2, result["ledger_verification"]["category_counts"]["self-modify"])

    def test_builder_demo_returns_valid_build_pipeline(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_builder_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["design_reader_handoff_ok"])
        self.assertEqual("ready", result["validation"]["design_manifest_status"])
        self.assertEqual(12, result["validation"]["design_source_digest_count"])
        self.assertEqual(3, result["validation"]["must_sync_docs_count"])
        self.assertTrue(result["validation"]["scope_allowed"])
        self.assertTrue(result["validation"]["immutable_boundaries_preserved"])
        self.assertEqual(2, result["validation"]["patch_count"])
        self.assertTrue(result["validation"]["sandbox_apply_ok"])
        self.assertEqual("applied", result["validation"]["sandbox_apply_status"])
        self.assertEqual(2, result["validation"]["sandbox_apply_patch_count"])
        self.assertEqual(3, result["validation"]["selected_eval_count"])
        self.assertTrue(result["validation"]["eval_execution_ok"])
        self.assertEqual("passed", result["validation"]["eval_execution_status"])
        self.assertEqual(2, result["validation"]["eval_execution_command_count"])
        self.assertEqual("removed", result["validation"]["eval_execution_cleanup_status"])
        self.assertEqual("promote", result["validation"]["rollout_decision"])
        self.assertTrue(result["validation"]["eval_report_evidence_bound"])
        self.assertTrue(result["validation"]["eval_execution_evidence_bound"])
        self.assertTrue(result["validation"]["rollout_session_ok"])
        self.assertEqual("promoted", result["validation"]["rollout_status"])
        self.assertEqual(4, result["validation"]["rollout_completed_stage_count"])
        self.assertEqual(
            ["dark-launch", "canary-5pct", "broad-50pct", "full-100pct"],
            result["validation"]["rollout_stage_ids"],
        )
        self.assertTrue(result["validation"]["rollback_ready"])
        self.assertEqual("ready", result["builder"]["artifact"]["status"])
        self.assertEqual(
            "src/omoikane/self_construction/builders.py",
            result["builder"]["patches"][0]["target_path"],
        )
        self.assertEqual(
            [
                "evals/continuity/council_output_build_request_pipeline.yaml",
                "evals/continuity/differential_eval_execution_binding.yaml",
                "evals/continuity/builder_staged_rollout_execution.yaml",
            ],
            result["builder"]["suite_selection"]["selected_evals"],
        )
        self.assertEqual(
            "builder-handoff-ab-evidence-v1",
            result["builder"]["eval_reports"][0]["profile_id"],
        )
        self.assertEqual(64, len(result["builder"]["eval_reports"][0]["comparison_digest"]))
        execution_report = next(
            report
            for report in result["builder"]["eval_reports"]
            if report["eval_ref"] == "evals/continuity/differential_eval_execution_binding.yaml"
        )
        self.assertTrue(execution_report["execution_bound"])
        self.assertEqual(2, execution_report["execution_receipt"]["executed_command_count"])
        self.assertTrue(
            result["builder"]["build_request"]["design_delta_ref"].startswith("design://")
        )
        self.assertEqual("applied", result["builder"]["sandbox_apply_receipt"]["status"])
        self.assertEqual("passed", result["builder"]["eval_execution_session"]["status"])
        self.assertEqual("promoted", result["builder"]["rollout_session"]["status"])
        self.assertEqual(8, result["ledger_verification"]["category_counts"]["self-modify"])

    def test_builder_live_demo_runs_actual_workspace_commands(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_builder_live_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["design_reader_handoff_ok"])
        self.assertEqual("ready", result["validation"]["design_manifest_status"])
        self.assertTrue(result["validation"]["scope_allowed"])
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
        self.assertEqual(4, result["ledger_verification"]["category_counts"]["self-modify"])

    def test_rollback_demo_restores_pre_apply_snapshot(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_rollback_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
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
        self.assertEqual(6, result["validation"]["selected_eval_count"])
        self.assertTrue(result["validation"]["eval_report_evidence_bound"])
        self.assertTrue(result["validation"]["eval_execution_evidence_bound"])
        self.assertEqual(2, result["validation"]["eval_execution_command_count"])
        self.assertEqual("removed", result["validation"]["eval_execution_cleanup_status"])
        self.assertEqual(
            "mirage://build-l5-rollback-0001/snapshot/pre-apply",
            result["validation"]["restored_snapshot_ref"],
        )
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
        self.assertEqual(2, result["validation"]["continuity_event_ref_count"])
        self.assertEqual(3, result["validation"]["notification_ref_count"])
        rollback_report = next(
            report
            for report in result["builder"]["eval_reports"]
            if report["eval_ref"] == "evals/continuity/builder_rollback_execution.yaml"
        )
        self.assertEqual("builder-rollback-trigger-evidence-v1", rollback_report["profile_id"])
        self.assertEqual("regression", rollback_report["outcome"])
        self.assertEqual("rolled-back", result["builder"]["rollback_session"]["status"])
        self.assertEqual(
            "satisfied",
            result["builder"]["rollback_guardian_oversight_event"]["human_attestation"]["status"],
        )
        self.assertEqual(9, result["ledger_verification"]["category_counts"]["self-modify"])

    def test_reasoning_demo_records_baseline_and_fallback(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_reasoning_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["baseline_primary"])
        self.assertTrue(result["reasoning"]["degraded"])
        self.assertEqual("narrative_v1", result["reasoning"]["selected_backend"])
        self.assertTrue(result["validation"]["shift_safe"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["cognitive-failover"])

    def test_affect_demo_records_smoothed_failover(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_affect_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("stability_guard_v1", result["validation"]["selected_backend"])
        self.assertTrue(result["validation"]["continuity_guard_preserved"])
        self.assertTrue(result["validation"]["smoothed"])
        self.assertTrue(result["validation"]["consent_preserved"])
        self.assertEqual("observe", result["validation"]["recommended_guard"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["cognitive-failover"])

    def test_attention_demo_records_guard_aligned_failover(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_attention_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("continuity_anchor_v1", result["validation"]["selected_backend"])
        self.assertTrue(result["validation"]["guard_aligned"])
        self.assertTrue(result["validation"]["safe_target_selected"])
        self.assertEqual("guardian-review", result["attention"]["focus"]["focus_target"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["cognitive-failover"])

    def test_perception_demo_records_qualia_bound_safe_scene_failover(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_perception_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["baseline_primary"])
        self.assertEqual("continuity_projection_v1", result["validation"]["selected_backend"])
        self.assertTrue(result["validation"]["guard_aligned"])
        self.assertTrue(result["validation"]["safe_scene_selected"])
        self.assertTrue(result["validation"]["qualia_bound"])
        self.assertEqual("guardian-review-scene", result["perception"]["frame"]["scene_label"])
        self.assertEqual("guardian-review", result["validation"]["perception_gate"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["cognitive-failover"])

    def test_volition_demo_records_guard_aligned_failover(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_volition_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("guardian_bias_v1", result["validation"]["selected_backend"])
        self.assertTrue(result["validation"]["guard_aligned"])
        self.assertEqual("guardian-review", result["validation"]["selected_intent"])
        self.assertEqual("review", result["validation"]["execution_mode"])
        self.assertEqual("guardian-review", result["volition"]["intent"]["selected_intent"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["cognitive-failover"])

    def test_imagination_demo_records_private_fallback_and_shared_baseline(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_imagination_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("continuity_scene_guard_v1", result["validation"]["selected_backend"])
        self.assertTrue(result["validation"]["baseline_co_imagination_ready"])
        self.assertTrue(result["validation"]["baseline_shared_handoff"])
        self.assertTrue(result["validation"]["failover_private"])
        self.assertEqual("co_imagination", result["baseline"]["handoff"]["imc_session"]["mode"])
        self.assertEqual("private-sandbox", result["imagination"]["scene"]["handoff"]["mode"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["cognitive-failover"])

    def test_language_demo_records_redacted_guarded_bridge(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_language_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["baseline_primary"])
        self.assertEqual("continuity_phrase_v1", result["validation"]["selected_backend"])
        self.assertTrue(result["validation"]["guard_aligned"])
        self.assertTrue(result["validation"]["redaction_applied"])
        self.assertEqual("guardian", result["validation"]["delivery_target"])
        self.assertEqual("guardian-brief", result["validation"]["discourse_mode"])
        self.assertTrue(result["validation"]["private_channel_locked"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["cognitive-failover"])

    def test_metacognition_demo_records_guarded_fallback_and_identity_anchor(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_metacognition_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("continuity_mirror_v1", result["validation"]["selected_backend"])
        self.assertTrue(result["validation"]["baseline_primary"])
        self.assertTrue(result["validation"]["guard_aligned"])
        self.assertTrue(result["validation"]["abrupt_change_flagged"])
        self.assertEqual("guardian-review", result["validation"]["escalation_target"])
        self.assertIn("continuity-first", result["metacognition"]["report"]["salient_values"])
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

    def test_self_model_demo_reports_stable_and_abrupt_observations(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_self_model_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("bounded-self-model-monitor-v1", result["profile"]["policy_id"])
        self.assertEqual(0.35, result["validation"]["threshold"])
        self.assertTrue(result["validation"]["stable_within_threshold"])
        self.assertTrue(result["validation"]["abrupt_flagged"])
        self.assertEqual(3, result["validation"]["history_length"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["identity-fidelity"])

    def test_sandbox_demo_freezes_on_surrogate_signal(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_sandbox_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual("surrogate-suffering-proxy-v0", result["profile"]["policy_id"])
        self.assertEqual("nominal", result["assessments"]["safe"]["status"])
        self.assertEqual("freeze", result["assessments"]["critical"]["status"])
        self.assertGreaterEqual(
            result["assessments"]["critical"]["proxy_score"],
            result["assessments"]["critical"]["thresholds"]["freeze_threshold"],
        )
        self.assertEqual(2, result["ledger_verification"]["category_counts"]["sandbox-monitor"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["sandbox-freeze"])

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

    def test_broker_demo_records_rotation_and_release(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_broker_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["neutrality_rotation_triggered"])
        self.assertTrue(result["validation"]["standby_kind_differs"])
        self.assertTrue(result["validation"]["energy_floor_signal_routes_to_standby"])
        self.assertTrue(result["validation"]["standby_probe_ready"])
        self.assertTrue(result["validation"]["attestation_chain_ready"])
        self.assertTrue(result["validation"]["attestation_chain_window_complete"])
        self.assertTrue(result["validation"]["dual_allocation_window_opened"])
        self.assertTrue(result["validation"]["dual_allocation_shadow_allocated"])
        self.assertTrue(result["validation"]["dual_allocation_sync_complete"])
        self.assertTrue(result["validation"]["attestation_stream_ready"])
        self.assertTrue(result["validation"]["attestation_stream_window_complete"])
        self.assertTrue(result["validation"]["attestation_stream_binds_selected_standby"])
        self.assertTrue(result["validation"]["dual_allocation_closed"])
        self.assertTrue(result["validation"]["dual_allocation_cleanup_released"])
        self.assertTrue(result["validation"]["migration_binds_streamed_state"])
        self.assertEqual("critical", result["broker"]["energy_floor_signal"]["severity"])
        self.assertEqual(
            result["broker"]["selection"]["standby_substrate"]["substrate_id"],
            result["broker"]["migration"]["destination_substrate"],
        )
        self.assertEqual("ready", result["broker"]["standby_probe"]["probe_status"])
        self.assertEqual("handoff-ready", result["broker"]["attestation_chain"]["chain_status"])
        self.assertEqual("B", result["broker"]["dual_allocation_window"]["method"])
        self.assertEqual("shadow-active", result["broker"]["dual_allocation_window"]["window_status"])
        self.assertEqual(
            "sealed-handoff-ready",
            result["broker"]["attestation_stream"]["stream_status"],
        )
        self.assertEqual(5, len(result["broker"]["attestation_stream"]["observations"]))
        self.assertEqual(
            "allocated",
            result["broker"]["dual_allocation_window"]["shadow_allocation"]["status"],
        )
        self.assertEqual("closed", result["broker"]["closed_dual_allocation_window"]["window_status"])
        self.assertEqual(
            "released",
            result["broker"]["closed_dual_allocation_window"]["shadow_release"]["status"],
        )
        self.assertEqual("hot-handoff", result["broker"]["migration"]["continuity_mode"])
        self.assertEqual("released", result["broker"]["release"]["status"])
        self.assertEqual("released", result["broker"]["final_state"]["release"]["status"])

    def test_continuity_demo_emits_profile_and_snapshot(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_continuity_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual("hmac-sha256", result["ledger_profile"]["signature_algorithm"])
        self.assertEqual(3, len(result["ledger_snapshot"]))
        self.assertEqual("self-modify", result["ledger_snapshot"][-1]["category"])

    def test_identity_demo_reports_pause_resume_contract(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_identity_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["council_pause_requires_resolution"])
        self.assertTrue(result["validation"]["council_pause_records_pause_state"])
        self.assertTrue(result["validation"]["resume_requires_self_proof"])
        self.assertTrue(result["validation"]["council_pause_resume_roundtrip"])
        self.assertTrue(result["validation"]["self_pause_allows_no_council_ref"])
        self.assertTrue(result["validation"]["self_pause_resume_roundtrip"])
        self.assertEqual("paused", result["transitions"]["council_pause"]["status"])
        self.assertEqual(
            "council",
            result["transitions"]["council_pause"]["pause_state"]["pause_authority"],
        )
        self.assertEqual("active", result["transitions"]["self_resume"]["status"])
        self.assertIsNone(result["transitions"]["self_pause"]["pause_state"]["council_resolution_ref"])
        self.assertEqual(4, result["ledger_verification"]["category_counts"]["identity-lifecycle"])

    def test_scheduler_demo_reports_timeout_rollback_and_completion(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_scheduler_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["method_a_fixed"])
        self.assertTrue(result["validation"]["method_b_fixed"])
        self.assertTrue(result["validation"]["method_c_fixed"])
        self.assertTrue(result["validation"]["order_violation_blocked"])
        self.assertTrue(result["validation"]["timeout_rolled_back"])
        self.assertTrue(result["validation"]["pause_resume_roundtrip"])
        self.assertTrue(result["validation"]["completed"])
        self.assertTrue(result["validation"]["method_b_signal_paused"])
        self.assertTrue(result["validation"]["method_b_signal_rolled_back"])
        self.assertTrue(result["validation"]["method_b_completed"])
        self.assertTrue(result["validation"]["method_c_fail_closed"])
        self.assertTrue(result["validation"]["artifact_bundle_attached"])
        self.assertTrue(result["validation"]["artifact_sync_gate_blocked"])
        self.assertTrue(result["validation"]["artifact_sync_current_before_handoff"])
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
        self.assertEqual("bdb-bridge", result["scenarios"]["timeout"]["rollback_target"])
        self.assertEqual("completed", result["final_handle"]["status"])
        self.assertEqual("current", result["final_handle"]["artifact_sync"]["bundle_status"])
        self.assertEqual("stable", result["final_handle"]["verifier_roster"]["rotation_state"])
        self.assertEqual(
            "rotated",
            result["method_a_rotation_final_handle"]["verifier_roster"]["rotation_state"],
        )
        self.assertEqual(
            "dual-channel-review",
            result["scenarios"]["method_b"]["signal_rollback"]["rollback_target"],
        )
        self.assertEqual("completed", result["method_b_final_handle"]["status"])
        self.assertEqual("fail", result["scenarios"]["method_c"]["signal_fail"]["action"])
        self.assertEqual("failed", result["method_c_final_handle"]["status"])
        self.assertEqual("failed", result["method_c_revoked_final_handle"]["status"])
        self.assertEqual("failed", result["method_c_verifier_revoked_final_handle"]["status"])

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

    def test_consensus_bus_demo_records_audited_delivery(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_consensus_bus_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["bus_transport_bound"])
        self.assertTrue(result["validation"]["direct_attempt_blocked"])
        self.assertTrue(result["validation"]["guardian_gate_present"])
        self.assertEqual("resolve", result["session"]["audit"]["last_phase"])
        self.assertEqual(6, result["session"]["audit"]["message_count"])
        self.assertEqual(1, result["session"]["audit"]["blocked_direct_attempts"])
        self.assertEqual(7, result["ledger_verification"]["category_counts"]["consensus-bus"])
        self.assertTrue(result["ledger_verification"]["ok"])

    def test_multi_council_demo_externalizes_cross_self_and_interpretive_routes(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_multi_council_demo()

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
        self.assertTrue(result["validation"]["ambiguous_blocks_local_binding"])

    def test_distributed_council_demo_reports_bound_external_reviews(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_distributed_council_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual(
            "binding-approved",
            result["distributed_resolutions"]["federation"]["final_outcome"],
        )
        self.assertEqual(
            "advisory",
            result["distributed_resolutions"]["federation"]["local_binding_status"],
        )
        self.assertEqual(
            "ethics-veto",
            result["distributed_resolutions"]["heritage"]["decision_mode"],
        )
        self.assertEqual(
            "heritage-overrides-local",
            result["distributed_resolutions"]["heritage"]["conflict_resolution"],
        )
        self.assertEqual(
            "escalate-human-governance",
            result["distributed_resolutions"]["conflict"]["final_outcome"],
        )
        self.assertEqual(2, len(result["distributed_resolutions"]["conflict"]["external_resolution_refs"]))
        self.assertTrue(result["validation"]["federation_binds_cross_self"])
        self.assertTrue(result["validation"]["heritage_veto_blocks_local"])
        self.assertTrue(result["validation"]["conflict_escalates_to_human"])

    def test_distributed_transport_demo_reports_attested_handoffs_and_replay_guard(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_distributed_transport_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual(
            "federation-mtls-quorum-v1",
            result["handoffs"]["federation"]["transport_profile"],
        )
        self.assertEqual(
            "authenticated",
            result["receipts"]["federation"]["receipt_status"],
        )
        self.assertEqual(
            "authenticated",
            result["receipts"]["federation_rotated"]["receipt_status"],
        )
        self.assertEqual(
            "authenticated",
            result["receipts"]["heritage"]["receipt_status"],
        )
        self.assertEqual(
            "replay-blocked",
            result["receipts"]["replay_blocked"]["receipt_status"],
        )
        self.assertEqual(
            "replay-blocked",
            result["receipts"]["multi_hop_replay_blocked"]["receipt_status"],
        )
        self.assertEqual([1, 2], result["handoffs"]["federation_rotated"]["accepted_key_epochs"])
        self.assertEqual(2, result["handoffs"]["federation_rotated"]["trust_root_quorum"])
        self.assertTrue(result["validation"]["federation_transport_authenticated"])
        self.assertTrue(result["validation"]["federation_rotation_authenticated"])
        self.assertTrue(result["validation"]["heritage_transport_authenticated"])
        self.assertTrue(result["validation"]["replay_guard_blocks_reuse"])
        self.assertTrue(result["validation"]["multi_hop_replay_blocks_reuse"])
        self.assertTrue(result["validation"]["federated_roots_enforced"])
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
        self.assertEqual(
            "verified",
            result["packet_capture_export"]["federation_rotated"]["export_status"],
        )
        self.assertEqual(
            "trace-bound-pcap-export-v1",
            result["packet_capture_export"]["federation_rotated"]["capture_profile"],
        )
        self.assertEqual(
            "pcap",
            result["packet_capture_export"]["federation_rotated"]["artifact_format"],
        )
        self.assertEqual(
            4,
            result["packet_capture_export"]["federation_rotated"]["packet_count"],
        )
        self.assertTrue(result["validation"]["authority_packet_capture_exported"])
        self.assertTrue(result["validation"]["authority_packet_capture_os_native_readback"])
        self.assertEqual(
            "granted",
            result["privileged_capture_acquisition"]["federation_rotated"]["grant_status"],
        )
        self.assertEqual(
            "bounded-live-interface-capture-acquisition-v1",
            result["privileged_capture_acquisition"]["federation_rotated"]["acquisition_profile"],
        )
        self.assertEqual(
            "delegated-broker",
            result["privileged_capture_acquisition"]["federation_rotated"]["privilege_mode"],
        )
        self.assertTrue(result["validation"]["authority_privileged_capture_granted"])
        self.assertTrue(result["validation"]["authority_privileged_capture_filter_bound"])
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

    def test_cognitive_audit_demo_returns_cross_layer_review(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_cognitive_audit_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["self_model"]["alert"]["abrupt_change"])
        self.assertEqual("guardian-review", result["audit"]["record"]["recommended_action"])
        self.assertEqual("approved", result["council"]["decision"]["outcome"])
        self.assertEqual("open-guardian-review", result["audit"]["resolution"]["follow_up_action"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["qualia-checkpoint"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["cognitive-audit"])

    def test_cognitive_audit_governance_demo_binds_distributed_and_oversight_review(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_cognitive_audit_governance_demo()

        self.assertTrue(result["validation"]["all_bindings_valid"])
        self.assertTrue(result["validation"]["oversight_network_bound"])
        self.assertTrue(result["validation"]["federation_gate_preserves_review"])
        self.assertTrue(result["validation"]["heritage_gate_preserves_boundary"])
        self.assertTrue(result["validation"]["conflict_escalates_human_governance"])
        self.assertEqual("federation-attested-review", result["bindings"]["federation"]["execution_gate"])
        self.assertEqual("heritage-veto-boundary", result["bindings"]["heritage"]["execution_gate"])
        self.assertEqual(
            "distributed-conflict-human-escalation",
            result["bindings"]["conflict"]["execution_gate"],
        )
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["guardian-oversight"])
        self.assertEqual(2, result["ledger_verification"]["category_counts"]["council-distributed"])
        self.assertEqual(4, result["ledger_verification"]["category_counts"]["cognitive-audit"])

    def test_trust_demo_reports_update_policy_and_human_pin(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_trust_demo()

        self.assertEqual("reference-v0", result["policy"]["policy_id"])
        self.assertEqual(0.99, result["agents"]["integrity-guardian"]["global_score"])
        self.assertFalse(result["events"][-1]["applied"])
        self.assertEqual(0.62, result["agents"]["design-architect"]["global_score"])
        self.assertTrue(result["agents"]["codex-builder"]["eligibility"]["apply_to_runtime"])

    def test_oversight_demo_propagates_pin_breach(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_guardian_oversight_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["veto_quorum_satisfied"])
        self.assertTrue(result["validation"]["veto_binding_recorded"])
        self.assertTrue(result["validation"]["verification_binding_recorded"])
        self.assertTrue(result["validation"]["reviewer_registry_ready"])
        self.assertTrue(result["validation"]["live_verification_ready"])
        self.assertTrue(result["validation"]["jurisdiction_bundle_ready"])
        self.assertTrue(result["validation"]["responsibility_scope_enforced"])
        self.assertTrue(result["validation"]["pin_breach_propagated"])
        self.assertTrue(result["validation"]["human_pin_cleared"])
        self.assertTrue(result["validation"]["guardian_role_removed"])
        self.assertEqual(
            "proof://oversight/reviewer-alpha/v1",
            result["events"]["veto"]["reviewer_bindings"][0]["proof_ref"],
        )
        self.assertEqual(
            "verifier://guardian-oversight.jp/reviewer-alpha",
            result["events"]["veto"]["reviewer_bindings"][0]["verifier_ref"],
        )
        self.assertEqual("breached", result["events"]["pin_renewal"]["human_attestation"]["status"])
        self.assertEqual(2, result["ledger_verification"]["category_counts"]["guardian-oversight"])

    def test_oversight_network_demo_binds_verifier_receipt(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_guardian_oversight_network_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["network_receipt_verified"])
        self.assertTrue(result["validation"]["network_endpoint_bound"])
        self.assertTrue(result["validation"]["network_profile_bound"])
        self.assertTrue(result["validation"]["latency_within_budget"])
        self.assertTrue(result["validation"]["binding_carries_receipt"])
        self.assertTrue(result["validation"]["binding_carries_trust_root"])
        self.assertTrue(result["validation"]["binding_carries_authority_chain"])
        self.assertEqual(
            "verifier://guardian-oversight.jp",
            result["reviewer"]["credential_verification"]["network_receipt"]["verifier_endpoint"],
        )
        self.assertEqual(
            "root://guardian-oversight.jp/reviewer-live-pki",
            result["event"]["reviewer_bindings"][0]["trust_root_ref"],
        )

    def test_ethics_demo_reports_rule_language_and_recorded_events(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_ethics_demo()

        self.assertEqual("deterministic-rule-tree-v0", result["language"]["language_id"])
        self.assertEqual("Veto", result["decisions"]["immutable_boundary"]["status"])
        self.assertEqual("Escalate", result["decisions"]["sandbox_escalation"]["status"])
        self.assertEqual("Approval", result["decisions"]["approved_fork"]["status"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["ethics-veto"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["ethics-escalate"])

    def test_termination_demo_reports_immediate_pending_and_reject_paths(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_termination_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["completed_within_budget"])
        self.assertTrue(result["validation"]["cool_off_pending"])
        self.assertTrue(result["validation"]["invalid_self_proof_rejected"])
        self.assertEqual("completed", result["outcomes"]["completed"]["status"])
        self.assertEqual("cool-off-pending", result["observations"]["cool_off"]["status"])
        self.assertEqual("released", result["substrate_snapshot"]["allocations"][0]["status"])
        self.assertEqual(3, result["ledger_verification"]["category_counts"]["terminate"])


if __name__ == "__main__":
    unittest.main()
