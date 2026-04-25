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

    def test_wms_demo_reports_reversible_physics_rules_change(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_wms_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["minor_reconciled"])
        self.assertTrue(result["validation"]["major_escape_offered"])
        self.assertTrue(result["validation"]["time_rate_deviation_escape_bound"])
        self.assertTrue(result["validation"]["time_rate_attestation_transport_bound"])
        self.assertTrue(result["validation"]["malicious_isolated"])
        self.assertTrue(result["validation"]["private_escape_honored"])
        self.assertTrue(result["validation"]["physics_change_reversible"])
        self.assertTrue(result["validation"]["physics_approval_transport_bound"])
        self.assertTrue(result["validation"]["approval_collection_scaling_bound"])
        self.assertTrue(result["validation"]["distributed_approval_fanout_bound"])
        self.assertTrue(result["validation"]["distributed_approval_fanout_retry_bound"])
        self.assertTrue(result["validation"]["engine_transaction_log_bound"])
        self.assertTrue(result["validation"]["engine_route_binding_bound"])
        self.assertTrue(result["validation"]["engine_capture_binding_bound"])
        self.assertTrue(result["validation"]["remote_authority_retry_budget_bound"])
        self.assertTrue(result["validation"]["static_approval_without_transport_rejected"])
        self.assertTrue(result["validation"]["physics_change"]["revert_bound"])
        self.assertTrue(result["validation"]["physics_change"]["approval_transport_quorum_met"])
        self.assertTrue(result["validation"]["physics_change"]["approval_collection_complete"])
        self.assertTrue(result["validation"]["physics_change"]["approval_fanout_complete"])
        self.assertTrue(result["validation"]["engine_transaction_log"]["engine_binding_complete"])
        self.assertTrue(result["validation"]["engine_route_binding"]["engine_route_binding_complete"])
        self.assertTrue(result["validation"]["engine_capture_binding"]["engine_capture_binding_complete"])
        self.assertTrue(result["validation"]["physics_revert"]["revert_bound"])
        self.assertEqual("applied", result["scenarios"]["physics_change"]["decision"])
        self.assertEqual(3, len(result["scenarios"]["approval_transport_receipts"]))
        self.assertEqual(2, result["scenarios"]["approval_collection_receipt"]["batch_count"])
        self.assertEqual("complete", result["scenarios"]["approval_fanout_receipt"]["fanout_status"])
        self.assertEqual("recovered", result["scenarios"]["approval_fanout_receipt"]["partial_outage_status"])
        self.assertEqual(1, result["scenarios"]["approval_fanout_receipt"]["retry_attempt_count"])
        self.assertEqual(
            "complete",
            result["scenarios"]["engine_transaction_log"]["engine_binding_status"],
        )
        self.assertEqual(
            "complete",
            result["scenarios"]["engine_route_binding"]["engine_route_binding_status"],
        )
        self.assertEqual(
            "complete",
            result["scenarios"]["engine_capture_binding"]["engine_capture_binding_status"],
        )
        self.assertEqual(
            "complete",
            result["scenarios"]["remote_authority_retry_budget"]["budget_status"],
        )
        self.assertEqual(
            result["scenarios"]["approval_fanout_receipt"]["digest"],
            result["scenarios"]["remote_authority_retry_budget"]["approval_fanout_digest"],
        )
        self.assertTrue(
            result["scenarios"]["remote_authority_retry_budget"]["engine_log_fanout_bound"]
        )
        self.assertEqual(5, result["scenarios"]["engine_transaction_log"]["transaction_entry_count"])
        self.assertEqual(2, result["scenarios"]["engine_route_binding"]["route_count"])
        self.assertEqual(4, result["scenarios"]["engine_capture_binding"]["packet_count"])
        self.assertFalse(result["scenarios"]["engine_capture_binding"]["raw_packet_body_stored"])
        self.assertEqual("major_diff", result["scenarios"]["time_rate_deviation"]["classification"])
        self.assertEqual(1.25, result["scenarios"]["time_rate_deviation"]["requested_time_rate"])
        self.assertTrue(result["scenarios"]["time_rate_deviation"]["time_rate_state_locked"])
        self.assertTrue(
            result["scenarios"]["time_rate_deviation"]["time_rate_attestation_quorum_met"]
        )
        self.assertEqual(3, len(result["scenarios"]["time_rate_attestation_receipts"]))
        self.assertEqual("reverted", result["scenarios"]["physics_revert"]["decision"])
        self.assertEqual(2, result["ledger_verification"]["category_counts"]["interface-wms-physics"])
        self.assertEqual(3, result["ledger_verification"]["category_counts"]["interface-wms-engine"])

    def test_ewa_demo_reports_veto_and_release(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_ewa_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["motor_plan_ok"])
        self.assertTrue(result["validation"]["motor_plan_bound"])
        self.assertTrue(result["validation"]["stop_signal_path_ok"])
        self.assertTrue(result["validation"]["stop_signal_path_bound"])
        self.assertTrue(result["validation"]["stop_signal_adapter_receipt_ok"])
        self.assertTrue(result["validation"]["stop_signal_adapter_receipt_bound"])
        self.assertTrue(result["validation"]["legal_execution_ok"])
        self.assertTrue(result["validation"]["legal_execution_bound"])
        self.assertTrue(result["validation"]["guardian_oversight_gate_ok"])
        self.assertTrue(result["validation"]["guardian_oversight_gate_bound"])
        self.assertTrue(result["validation"]["reviewer_network_attested"])
        self.assertTrue(result["validation"]["authorization_ok"])
        self.assertTrue(result["validation"]["authorization_ready"])
        self.assertTrue(result["validation"]["authorization_matches_command"])
        self.assertTrue(result["validation"]["authorization_stop_signal_path_ready"])
        self.assertTrue(result["validation"]["authorization_stop_signal_adapter_receipt_ready"])
        self.assertTrue(result["validation"]["authorization_guardian_oversight_gate_ready"])
        self.assertEqual("physical-device-actuation", result["validation"]["authorization_delivery_scope"])
        self.assertEqual("executed", result["approved_command"]["status"])
        self.assertEqual(
            result["motor_plan"]["plan_id"],
            result["approved_command"]["motor_plan_id"],
        )
        self.assertEqual(
            result["stop_signal_path"]["path_id"],
            result["approved_command"]["stop_signal_path_id"],
        )
        self.assertEqual(
            result["legal_execution"]["execution_id"],
            result["approved_command"]["legal_execution_id"],
        )
        self.assertEqual(
            result["guardian_oversight_gate"]["gate_id"],
            result["authorization"]["guardian_oversight_gate_id"],
        )
        self.assertEqual(
            result["guardian_oversight_event"]["event_id"],
            result["authorization"]["guardian_oversight_event_id"],
        )
        self.assertEqual(
            "human-reviewer-ewa-001",
            result["guardian_oversight_gate"]["matched_reviewer_id"],
        )
        self.assertTrue(result["validation"]["approved_command_motor_plan_bound"])
        self.assertTrue(result["validation"]["approved_command_stop_signal_path_bound"])
        self.assertTrue(result["validation"]["approved_command_stop_signal_adapter_receipt_bound"])
        self.assertTrue(result["validation"]["approved_command_legal_execution_bound"])
        self.assertTrue(result["validation"]["emergency_stop_ok"])
        self.assertTrue(result["validation"]["emergency_stop_latched"])
        self.assertTrue(result["validation"]["emergency_stop_bus_delivery_latched"])
        self.assertTrue(result["validation"]["emergency_stop_bound_to_command"])
        self.assertTrue(result["validation"]["emergency_stop_bound_to_authorization"])
        self.assertTrue(result["validation"]["emergency_stop_bound_to_stop_signal_path"])
        self.assertTrue(result["validation"]["emergency_stop_bound_to_stop_signal_adapter_receipt"])
        self.assertTrue(result["validation"]["release_after_stop"])
        self.assertEqual("vetoed", result["veto"]["status"])
        self.assertIn("harm.human", result["veto"]["matched_tokens"])
        self.assertEqual("released", result["handle"]["status"])
        self.assertEqual("released", result["veto_handle"]["status"])
        self.assertEqual("watchdog-timeout", result["emergency_stop"]["trigger_source"])
        self.assertEqual(
            result["stop_signal_path"]["path_id"],
            result["emergency_stop"]["stop_signal_path_id"],
        )
        self.assertEqual(
            result["authorization"]["authorization_id"],
            result["approved_command"]["approval_path"]["authorization_id"],
        )
        self.assertEqual(
            1,
            result["ledger_verification"]["category_counts"]["interface-ewa-authorization"],
        )
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["interface-ewa-plan"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["interface-ewa-legal"])
        self.assertEqual(
            1,
            result["ledger_verification"]["category_counts"]["interface-ewa-stop-signal-adapter"],
        )
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["guardian-oversight"])
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
        self.assertTrue(result["validation"]["body_map_bound"])
        self.assertTrue(result["validation"]["proprioceptive_calibration_bound"])
        self.assertTrue(result["validation"]["alignment_ref_bound"])
        self.assertTrue(result["validation"]["artifact_family_body_map_bound"])
        self.assertTrue(result["validation"]["shared_loopback_ok"])
        self.assertTrue(result["validation"]["shared_loopback_collective_bound"])
        self.assertTrue(result["validation"]["shared_loopback_imc_bound"])
        self.assertTrue(result["validation"]["shared_loopback_participants_bound"])
        self.assertTrue(result["validation"]["shared_loopback_arbitrated"])
        self.assertTrue(result["validation"]["shared_loopback_owner_handoff"])
        self.assertTrue(result["validation"]["shared_loopback_family_tracked"])
        self.assertEqual("active", result["session"]["status"])
        self.assertTrue(result["session"]["avatar_body_map_ref"].startswith("avatar-body-map://"))
        self.assertEqual(3, result["artifact_family"]["scene_count"])
        self.assertEqual(2, result["artifact_family"]["guardian_intervention_count"])
        self.assertEqual("active", result["artifact_family"]["final_session_status"])
        self.assertEqual("guardian-hold", result["receipts"]["degraded"]["delivery_status"])
        self.assertEqual("collective-shared", result["shared_loopback"]["session"]["shared_space_mode"])
        self.assertEqual(
            "guardian-mediated",
            result["shared_loopback"]["receipts"]["mediated"]["arbitration_status"],
        )
        self.assertEqual(2, result["shared_loopback"]["artifact_family"]["scene_count"])
        self.assertEqual(1, result["shared_loopback"]["artifact_family"]["guardian_arbitration_count"])
        self.assertEqual(3, result["ledger_verification"]["category_counts"]["interface-sensory-loopback"])
        self.assertEqual(
            1,
            result["ledger_verification"]["category_counts"]["interface-sensory-loopback-guardian"],
        )
        self.assertEqual(
            1,
            result["ledger_verification"]["category_counts"]["interface-sensory-loopback-family"],
        )
        self.assertEqual(
            2,
            result["ledger_verification"]["category_counts"]["interface-sensory-loopback-shared"],
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
        self.assertEqual(0, report["missing_required_reference_file_count"])
        self.assertEqual(0, report["empty_eval_surface_count"])
        self.assertEqual(0, report["catalog_pending_count"])
        self.assertEqual(0, report["inventory_drift_count"])
        self.assertIn("decision_log_residual_count", report)
        self.assertEqual(
            report["decision_log_residual_count"],
            len(report["decision_log_residual_hits"]),
        )
        self.assertIn("decision_log_frontier_count", report)
        self.assertEqual(
            report["decision_log_frontier_count"],
            len(report["decision_log_frontier_hits"]),
        )

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

    def test_memory_replication_demo_returns_quorum_bound_reconcile_session(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_memory_replication_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["manifest"]["ok"])
        self.assertTrue(result["validation"]["replication"]["ok"])
        self.assertTrue(result["validation"]["consensus_quorum_ok"])
        self.assertTrue(result["validation"]["resync_required"])
        self.assertEqual(
            ["primary", "mirror"],
            result["validation"]["replication"]["immediate_target_ids"],
        )
        self.assertEqual(
            ["coldstore", "mirror", "primary"],
            result["validation"]["replication"]["consensus_target_ids"],
        )
        self.assertEqual(
            ["trustee"],
            result["validation"]["replication"]["mismatch_target_ids"],
        )
        self.assertEqual(
            "degraded-but-recoverable",
            result["memory_replication"]["session"]["status"],
        )
        self.assertEqual(
            1,
            result["ledger_verification"]["category_counts"]["memory-replication"],
        )

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
        self.assertTrue(result["validation"]["connectome"]["ok"])
        self.assertTrue(result["validation"]["semantic"]["ok"])
        self.assertTrue(result["validation"]["procedural_handoff"]["ok"])
        self.assertEqual(2, result["validation"]["semantic"]["concept_count"])
        self.assertEqual(
            ["council-review", "migration-check"],
            result["validation"]["semantic"]["labels"],
        )
        self.assertEqual(
            ["council-review", "migration-check"],
            result["validation"]["procedural_handoff"]["canonical_labels"],
        )
        self.assertEqual(
            "mind.procedural.v0",
            result["validation"]["procedural_handoff"]["target_namespace"],
        )
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["semantic-projection"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["semantic-handoff"])

    def test_procedural_demo_returns_valid_preview(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_procedural_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["connectome"]["ok"])
        self.assertTrue(result["validation"]["semantic"]["ok"])
        self.assertTrue(result["validation"]["semantic_handoff"]["ok"])
        self.assertTrue(result["validation"]["handoff_matches_preview_policy"])
        self.assertTrue(result["validation"]["procedural"]["ok"])
        self.assertEqual(2, result["validation"]["procedural"]["recommendation_count"])
        self.assertEqual(
            ["continuity_integrator->ethics_gate", "sensory_ingress->continuity_integrator"],
            sorted(result["validation"]["procedural"]["target_paths"]),
        )
        self.assertEqual("ready", result["procedural"]["semantic_handoff"]["status"])
        self.assertEqual(["skill-execution"], result["procedural"]["snapshot"]["deferred_surfaces"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["semantic-handoff"])
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
        self.assertTrue(result["validation"]["enactment"]["mandatory_eval_bound"])
        self.assertTrue(result["validation"]["enactment"]["command_eval_refs_bound"])
        self.assertTrue(result["validation"]["enactment"]["temp_workspace_removed"])
        self.assertEqual("passed", result["procedural"]["skill_enactment_session"]["status"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["procedural-enactment"])

    def test_procedural_actuation_demo_bridges_enactment_to_ewa_authorization(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_procedural_actuation_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["bridge"]["ok"])
        self.assertTrue(result["validation"]["bridge"]["source_enactment_bound"])
        self.assertTrue(result["validation"]["bridge"]["authorization_digest_bound"])
        self.assertTrue(result["validation"]["bridge"]["authorization_validation_bound"])
        self.assertTrue(result["validation"]["bridge"]["command_bound_to_authorization"])
        self.assertTrue(result["validation"]["bridge"]["stop_signal_adapter_receipt_bound"])
        self.assertTrue(result["validation"]["bridge"]["legal_execution_bound"])
        self.assertTrue(result["validation"]["bridge"]["guardian_oversight_gate_bound"])
        self.assertTrue(result["validation"]["authorization"]["stop_signal_adapter_receipt_bound"])
        self.assertTrue(result["validation"]["bridge"]["no_raw_instruction_text"])
        self.assertEqual(
            result["ewa"]["authorization"]["authorization_id"],
            result["procedural"]["actuation_bridge_session"]["command_binding"][
                "authorization_id"
            ],
        )
        self.assertEqual(
            "physical-device-actuation",
            result["procedural"]["actuation_bridge_session"]["command_binding"][
                "delivery_scope"
            ],
        )
        self.assertEqual(
            result["ewa"]["stop_signal_adapter_receipt"]["receipt_id"],
            result["procedural"]["actuation_bridge_session"]["command_binding"][
                "stop_signal_adapter_receipt_id"
            ],
        )
        self.assertEqual(
            1,
            result["ledger_verification"]["category_counts"][
                "procedural-actuation-bridge"
            ],
        )

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
        self.assertEqual(2, result["validation"]["delta_scan_changed_section_count"])
        self.assertEqual(2, result["validation"]["delta_scan_command_receipt_count"])
        self.assertTrue(result["validation"]["delta_scan_bound_to_manifest"])
        self.assertEqual(4, result["validation"]["manifest_planning_cue_count"])
        self.assertEqual(5, result["validation"]["build_request_planning_cue_count"])
        self.assertTrue(result["validation"]["council_review_required"])
        self.assertTrue(result["validation"]["guardian_review_required"])
        self.assertTrue(result["validation"]["build_request_has_design_delta_ref"])
        self.assertTrue(result["validation"]["build_request_has_design_delta_digest"])
        self.assertEqual(7, result["validation"]["output_path_count"])
        self.assertEqual(2, result["ledger_verification"]["category_counts"]["self-modify"])

    def test_patch_generator_demo_returns_ready_and_blocked_artifacts(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_patch_generator_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["design_reader_handoff_ok"])
        self.assertTrue(result["validation"]["ready_scope_allowed"])
        self.assertEqual("ready", result["validation"]["ready_artifact_status"])
        self.assertEqual(5, result["validation"]["ready_patch_count"])
        self.assertEqual(
            [
                "src/omoikane/self_construction/builders.py",
                "tests/unit/test_builders.py",
                "evals/continuity/council_output_build_request_pipeline.yaml",
                "docs/02-subsystems/self-construction/README.md",
                "meta/decision-log/build-l5-patch-generator-0001.md",
            ],
            result["validation"]["ready_patch_targets"],
        )
        self.assertEqual("blocked", result["validation"]["blocked_artifact_status"])
        self.assertTrue(result["validation"]["blocked_rule_mentions_scope_escape"])
        self.assertTrue(result["validation"]["blocked_rule_mentions_planning_cues"])
        self.assertTrue(result["validation"]["blocked_rule_mentions_immutable_boundary"])
        self.assertGreaterEqual(result["validation"]["blocked_rule_count"], 3)
        self.assertEqual(
            "blocked",
            result["patch_generator"]["blocked_artifact"]["status"],
        )
        self.assertEqual(3, result["ledger_verification"]["category_counts"]["self-modify"])

    def test_diff_eval_demo_classifies_promote_hold_and_rollback(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_diff_eval_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["design_reader_handoff_ok"])
        self.assertTrue(result["validation"]["scope_allowed"])
        self.assertTrue(result["validation"]["artifact_ready"])
        self.assertTrue(result["validation"]["sandbox_apply_ok"])
        self.assertEqual(2, result["validation"]["selected_eval_count"])
        self.assertEqual(
            [
                "evals/continuity/council_output_build_request_pipeline.yaml",
                "evals/continuity/differential_eval_execution_binding.yaml",
            ],
            result["validation"]["selected_evals"],
        )
        self.assertTrue(result["validation"]["execution_eval_selected"])
        self.assertEqual(2, result["validation"]["pass_report_count"])
        self.assertTrue(result["validation"]["pass_reports_all_pass"])
        self.assertEqual("promote", result["validation"]["promote_decision"])
        self.assertEqual("fail", result["validation"]["hold_outcome"])
        self.assertEqual("hold", result["validation"]["hold_decision"])
        self.assertEqual("regression", result["validation"]["rollback_outcome"])
        self.assertEqual("rollback", result["validation"]["rollback_decision"])
        self.assertTrue(result["validation"]["execution_report_bound"])
        self.assertEqual(2, result["validation"]["execution_command_count"])
        self.assertEqual("removed", result["validation"]["execution_cleanup_status"])
        self.assertEqual("passed", result["validation"]["execution_session_status"])
        self.assertTrue(result["validation"]["execution_reviewer_network_attested"])
        self.assertTrue(result["validation"]["pass_report_evidence_bound"])
        self.assertEqual("promote", result["diff_eval"]["decisions"]["promote"]["decision"])
        self.assertEqual("hold", result["diff_eval"]["decisions"]["hold"]["decision"])
        self.assertEqual("rollback", result["diff_eval"]["decisions"]["rollback"]["decision"])
        self.assertEqual(5, result["ledger_verification"]["category_counts"]["self-modify"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["guardian-oversight"])

    def test_builder_demo_returns_valid_build_pipeline(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_builder_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["design_reader_handoff_ok"])
        self.assertEqual("ready", result["validation"]["design_manifest_status"])
        self.assertEqual(16, result["validation"]["design_source_digest_count"])
        self.assertEqual(3, result["validation"]["must_sync_docs_count"])
        self.assertTrue(result["validation"]["scope_allowed"])
        self.assertTrue(result["validation"]["immutable_boundaries_preserved"])
        self.assertEqual(5, result["validation"]["patch_count"])
        self.assertTrue(result["validation"]["sandbox_apply_ok"])
        self.assertEqual("applied", result["validation"]["sandbox_apply_status"])
        self.assertEqual(5, result["validation"]["sandbox_apply_patch_count"])
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
            [
                "runtime-source",
                "test-coverage",
                "eval-sync",
                "docs-sync",
                "meta-decision-log",
            ],
            [patch["cue_kind"] for patch in result["builder"]["patches"]],
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
        self.assertTrue(result["validation"]["eval_execution_reviewer_network_attested"])
        self.assertEqual(
            "enactment-approved",
            result["validation"]["eval_execution_oversight_gate_status"],
        )
        self.assertTrue(
            result["builder"]["build_request"]["design_delta_ref"].startswith("design://")
        )
        self.assertEqual("applied", result["builder"]["sandbox_apply_receipt"]["status"])
        self.assertEqual("passed", result["builder"]["eval_execution_session"]["status"])
        self.assertEqual("promoted", result["builder"]["rollout_session"]["status"])
        self.assertEqual(8, result["ledger_verification"]["category_counts"]["self-modify"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["guardian-oversight"])

    def test_builder_live_demo_runs_actual_workspace_commands(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_builder_live_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["design_reader_handoff_ok"])
        self.assertEqual("ready", result["validation"]["design_manifest_status"])
        self.assertTrue(result["validation"]["scope_allowed"])
        self.assertTrue(result["validation"]["enactment_ok"])
        self.assertEqual("passed", result["validation"]["enactment_status"])
        self.assertEqual(5, result["validation"]["mutated_file_count"])
        self.assertEqual(2, result["validation"]["executed_command_count"])
        self.assertTrue(result["validation"]["all_commands_passed"])
        self.assertEqual("removed", result["validation"]["cleanup_status"])
        self.assertEqual("satisfied", result["validation"]["reviewer_oversight_status"])
        self.assertEqual(2, result["validation"]["reviewer_quorum_required"])
        self.assertEqual(2, result["validation"]["reviewer_quorum_received"])
        self.assertEqual(2, result["validation"]["reviewer_binding_count"])
        self.assertEqual(2, result["validation"]["reviewer_network_receipt_count"])
        self.assertTrue(result["validation"]["reviewer_network_attested"])
        self.assertTrue(result["validation"]["enactment_payload_ref_bound"])
        self.assertEqual("enactment-approved", result["validation"]["oversight_gate_status"])
        self.assertEqual("removed", result["validation"]["oversight_gate_cleanup_status"])
        self.assertEqual(2, result["validation"]["oversight_gate_command_count"])
        self.assertEqual(
            [
                "evals/continuity/builder_live_enactment_execution.yaml",
                "evals/continuity/builder_live_oversight_network.yaml",
            ],
            result["builder"]["suite_selection"]["selected_evals"],
        )
        self.assertEqual("passed", result["builder"]["enactment_session"]["status"])
        self.assertEqual(
            "enactment-approved",
            result["builder"]["enactment_session"]["oversight_gate"]["status"],
        )
        self.assertEqual(4, result["ledger_verification"]["category_counts"]["self-modify"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["guardian-oversight"])

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
        self.assertTrue(
            result["builder"]["enactment_session"]["oversight_gate"]["reviewer_network_attested"]
        )
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
        self.assertEqual(5, result["validation"]["reverted_patch_count"])
        self.assertEqual(5, result["validation"]["reverse_apply_journal_count"])
        self.assertEqual(5, result["validation"]["reverse_apply_command_count"])
        self.assertEqual(5, result["validation"]["reverse_apply_verified_count"])
        self.assertEqual(5, result["validation"]["repo_bound_verified_count"])
        self.assertEqual("current-checkout-subtree", result["validation"]["repo_binding_scope"])
        self.assertEqual(5, result["validation"]["repo_binding_path_count"])
        self.assertEqual("verified", result["validation"]["checkout_mutation_status"])
        self.assertEqual(5, result["validation"]["checkout_mutation_path_count"])
        self.assertEqual("removed", result["validation"]["checkout_mutation_cleanup_status"])
        self.assertTrue(result["validation"]["checkout_mutation_restored"])
        self.assertEqual("verified", result["validation"]["current_worktree_mutation_status"])
        self.assertEqual(5, result["validation"]["current_worktree_mutation_path_count"])
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
        self.assertEqual(2, result["ledger_verification"]["category_counts"]["guardian-oversight"])

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
        self.assertTrue(result["validation"]["attestation_chain_cross_host_verified"])
        self.assertTrue(result["validation"]["dual_allocation_window_opened"])
        self.assertTrue(result["validation"]["dual_allocation_shadow_allocated"])
        self.assertTrue(result["validation"]["dual_allocation_sync_complete"])
        self.assertTrue(result["validation"]["dual_allocation_cross_host_verified"])
        self.assertTrue(result["validation"]["attestation_stream_ready"])
        self.assertTrue(result["validation"]["attestation_stream_window_complete"])
        self.assertTrue(result["validation"]["attestation_stream_binds_selected_standby"])
        self.assertTrue(result["validation"]["attestation_stream_cross_host_verified"])
        self.assertTrue(result["validation"]["dual_allocation_closed"])
        self.assertTrue(result["validation"]["dual_allocation_cleanup_released"])
        self.assertTrue(result["validation"]["migration_binds_selected_standby"])
        self.assertTrue(result["validation"]["migration_binds_streamed_state"])
        self.assertEqual("critical", result["broker"]["energy_floor_signal"]["severity"])
        self.assertEqual(
            result["broker"]["selection"]["standby_substrate"]["substrate_id"],
            result["broker"]["migration"]["destination_substrate"],
        )
        self.assertEqual("ready", result["broker"]["standby_probe"]["probe_status"])
        self.assertEqual("handoff-ready", result["broker"]["attestation_chain"]["chain_status"])
        self.assertTrue(result["broker"]["attestation_chain"]["cross_host_verified"])
        self.assertEqual("B", result["broker"]["dual_allocation_window"]["method"])
        self.assertEqual("shadow-active", result["broker"]["dual_allocation_window"]["window_status"])
        self.assertTrue(result["broker"]["dual_allocation_window"]["cross_host_verified"])
        self.assertEqual(
            "sealed-handoff-ready",
            result["broker"]["attestation_stream"]["stream_status"],
        )
        self.assertTrue(result["broker"]["attestation_stream"]["cross_host_verified"])
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
        self.assertTrue(result["broker"]["migration"]["cross_host_verified"])
        self.assertEqual("released", result["broker"]["release"]["status"])
        self.assertEqual("released", result["broker"]["final_state"]["release"]["status"])

    def test_energy_budget_demo_blocks_ap1_pressure_and_binds_broker_signal(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_energy_budget_demo()
        receipt = result["energy_budget"]["receipt"]

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["floor_preserved"])
        self.assertTrue(result["validation"]["economic_pressure_blocked"])
        self.assertTrue(result["validation"]["broker_signal_bound"])
        self.assertTrue(result["validation"]["raw_payload_redacted"])
        self.assertEqual("blocked-economic-pressure", receipt["ap1_guard_status"])
        self.assertEqual("floor-protected", receipt["budget_status"])
        self.assertFalse(receipt["degradation_allowed"])
        self.assertEqual("migrate-standby", receipt["broker_recommended_action"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["energy-budget"])

    def test_continuity_demo_emits_profile_and_snapshot(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_continuity_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual("hmac-sha256", result["ledger_profile"]["signature_algorithm"])
        self.assertEqual(3, len(result["ledger_snapshot"]))
        self.assertEqual("self-modify", result["ledger_snapshot"][-1]["category"])
        self.assertTrue(result["public_verification_validation"]["ok"])
        self.assertTrue(result["public_verification_bundle"]["public_verification_ready"])
        self.assertEqual(
            "continuity-public-verification-key-management-v1",
            result["public_verification_bundle"]["profile_id"],
        )
        self.assertEqual(
            result["public_verification_bundle"]["entry_count"],
            result["public_verification_bundle"]["verified_entry_count"],
        )
        self.assertFalse(result["public_verification_bundle"]["raw_signature_payload_exposed"])

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

    def test_identity_confirmation_demo_reports_multidimensional_profile(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_identity_confirmation_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["all_required_dimensions_present"])
        self.assertTrue(result["validation"]["all_required_dimensions_pass"])
        self.assertTrue(result["validation"]["subjective_self_report_bound"])
        self.assertTrue(result["validation"]["third_party_witness_quorum_met"])
        self.assertTrue(result["validation"]["confirmation_digest_bound"])
        self.assertTrue(result["validation"]["ledger_event_bound"])
        self.assertTrue(result["validation"]["blocked_profile_fail_closed"])
        self.assertEqual("passed", result["confirmation_profile"]["result"])
        self.assertTrue(result["confirmation_profile"]["active_transition_allowed"])
        self.assertEqual("failed", result["blocked_profile"]["result"])
        self.assertFalse(result["blocked_profile"]["active_transition_allowed"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["identity-fidelity"])

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
        self.assertTrue(result["validation"]["method_b_broker_handoff_gate_blocked"])
        self.assertTrue(result["validation"]["method_b_broker_handoff_prepared"])
        self.assertTrue(result["validation"]["artifact_revocation_fail_closed"])
        self.assertTrue(result["validation"]["verifier_rotation_overlap_paused"])
        self.assertTrue(result["validation"]["verifier_rotation_cutover_recovered"])
        self.assertTrue(result["validation"]["verifier_rotation_dual_attested"])
        self.assertTrue(result["validation"]["verifier_revocation_fail_closed"])
        self.assertTrue(result["validation"]["method_b_broker_confirmation_gate_blocked"])
        self.assertTrue(result["validation"]["method_b_broker_handoff_confirmed"])
        self.assertTrue(result["validation"]["method_b_broker_cleanup_bound"])
        self.assertTrue(result["validation"]["execution_receipts_valid"])
        self.assertTrue(result["validation"]["method_a_execution_receipt_timeout_recovered"])
        self.assertTrue(result["validation"]["method_a_live_execution_receipt_bound"])
        self.assertTrue(result["validation"]["method_a_rotation_execution_receipt_cutover"])
        self.assertTrue(result["validation"]["method_b_execution_receipt_bound"])
        self.assertTrue(result["validation"]["method_c_execution_receipt_fail_closed"])
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
        self.assertEqual(
            "method-b-protected-handoff-execution-v1",
            result["execution_receipts"]["method_b"]["execution_profile_id"],
        )
        self.assertEqual(
            "confirmed",
            result["execution_receipts"]["method_b"]["broker_handoff_status"],
        )
        self.assertIn(
            "timeout-recovery",
            result["execution_receipts"]["method_a"]["scenario_labels"],
        )
        self.assertEqual(
            "reachable",
            result["execution_receipts"]["method_a_live"]["verifier_connectivity_status"],
        )
        self.assertEqual(
            "rotated",
            result["execution_receipts"]["method_a_rotation"]["verifier_rotation_state"],
        )
        self.assertEqual("cancelled", result["scenarios"]["method_a_cancel"]["cancelled"]["status"])
        self.assertEqual("cancelled", result["method_a_cancel_final_handle"]["status"])
        self.assertEqual(1, result["execution_receipts"]["method_a_cancel"]["cancel_count"])
        self.assertTrue(result["execution_receipts"]["method_a_cancel"]["outcome_summary"]["cancelled"])
        self.assertIn("cancelled", result["execution_receipts"]["method_a_cancel"]["scenario_labels"])
        self.assertTrue(result["validation"]["method_a_cancelled"])
        self.assertTrue(result["validation"]["method_a_cancel_execution_receipt_bound"])
        self.assertEqual(
            "confirmed",
            result["method_b_final_handle"]["broker_handoff_receipt"]["status"],
        )
        self.assertEqual(
            result["scenarios"]["method_b"]["broker_runtime"]["transfer"]["transfer_id"],
            result["method_b_final_handle"]["broker_handoff_receipt"]["migration_transfer_id"],
        )
        self.assertEqual(
            "released",
            result["method_b_final_handle"]["broker_handoff_receipt"]["cleanup_release_status"],
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
        self.assertTrue(result["validation"]["authority_cluster_discovery_bound"])
        self.assertTrue(result["validation"]["authority_route_targets_discovered"])
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
            "discovered",
            result["authority_cluster_discovery"]["federation_rotated"]["discovery_status"],
        )
        self.assertEqual(
            "review-capped-authority-cluster-discovery-v1",
            result["authority_cluster_discovery"]["federation_rotated"]["discovery_profile"],
        )
        self.assertEqual(
            "authority-cluster://federation/review-window",
            result["authority_cluster_discovery"]["federation_rotated"]["accepted_cluster_ref"],
        )
        self.assertEqual(
            2,
            result["authority_cluster_discovery"]["federation_rotated"]["review_budget"],
        )
        self.assertEqual(
            "budget-bound-authority-seed-review-policy-v1",
            result["authority_seed_review_policy"]["federation_rotated"]["policy_profile"],
        )
        self.assertEqual(
            "single-accepted-cluster-after-budget-review-v1",
            result["authority_seed_review_policy"]["federation_rotated"]["acceptance_mode"],
        )
        self.assertEqual(
            result["authority_seed_review_policy"]["federation_rotated"]["digest"],
            result["authority_cluster_discovery"]["federation_rotated"]["candidate_clusters"][0][
                "review_policy_digest"
            ],
        )
        self.assertEqual(
            1,
            len(result["authority_cluster_discovery"]["federation_rotated"]["candidate_clusters"]),
        )
        self.assertEqual(
            "discovered",
            result["authority_route_target_discovery"]["federation_rotated"]["discovery_status"],
        )
        self.assertEqual(
            "bounded-authority-route-target-discovery-v1",
            result["authority_route_target_discovery"]["federation_rotated"]["discovery_profile"],
        )
        self.assertEqual(
            2,
            result["authority_route_target_discovery"]["federation_rotated"]["route_target_count"],
        )
        self.assertTrue(
            result["authority_route_target_discovery"]["federation_rotated"][
                "all_active_members_targeted"
            ],
        )
        self.assertEqual(
            result["authority_cluster_discovery"]["federation_rotated"]["accepted_route_catalog"],
            result["authority_route_target_discovery"]["federation_rotated"]["route_targets"],
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
        self.assertEqual(
            "attested-cross-host-authority-binding-v1",
            result["authority_route_trace"]["federation_rotated"]["cross_host_binding_profile"],
        )
        self.assertEqual(
            "bounded-authority-route-target-discovery-v1",
            result["authority_route_trace"]["federation_rotated"]["route_target_discovery_profile"],
        )
        self.assertEqual(
            "authority-cluster://federation/review-window",
            result["authority_route_trace"]["federation_rotated"]["authority_cluster_ref"],
        )
        self.assertEqual(
            2,
            result["authority_route_trace"]["federation_rotated"]["distinct_remote_host_count"],
        )
        self.assertTrue(
            result["authority_route_trace"]["federation_rotated"]["os_observer_complete"],
        )
        self.assertTrue(
            result["authority_route_trace"]["federation_rotated"]["route_target_discovery_bound"],
        )
        self.assertTrue(result["authority_route_trace"]["federation_rotated"]["cross_host_verified"])
        self.assertTrue(
            all(
                binding["mtls_status"] == "authenticated"
                and binding["remote_host_ref"].startswith("host://federation/authority-edge-")
                and binding["authority_cluster_ref"]
                == "authority-cluster://federation/review-window"
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
                and binding["os_observer_receipt"]["remote_host_ref"] == binding["remote_host_ref"]
                and binding["os_observer_receipt"]["authority_cluster_ref"]
                == binding["authority_cluster_ref"]
                and binding["os_observer_receipt"]["host_binding_digest"]
                for binding in result["authority_route_trace"]["federation_rotated"]["route_bindings"]
            )
        )
        self.assertTrue(result["validation"]["authority_route_cross_host_bound"])
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
        self.assertTrue(result["validation"]["multi_jurisdiction_review_bound"])
        self.assertTrue(result["validation"]["distributed_signature_bound"])
        self.assertEqual(["JP-13", "US-CA"], result["validation"]["reviewer_jurisdictions"])
        self.assertTrue(result["validation"]["federation_gate_preserves_review"])
        self.assertTrue(result["validation"]["heritage_gate_preserves_boundary"])
        self.assertTrue(result["validation"]["conflict_escalates_human_governance"])
        self.assertEqual("federation-attested-review", result["bindings"]["federation"]["execution_gate"])
        self.assertEqual("heritage-veto-boundary", result["bindings"]["heritage"]["execution_gate"])
        self.assertEqual(
            "distributed-conflict-human-escalation",
            result["bindings"]["conflict"]["execution_gate"],
        )
        self.assertEqual(
            "distributed-council-verdict-signature-binding-v1",
            result["bindings"]["conflict"]["distributed_verdicts"][0]["signature_binding"][
                "profile_id"
            ],
        )
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["guardian-oversight"])
        self.assertEqual(2, result["ledger_verification"]["category_counts"]["council-distributed"])
        self.assertEqual(4, result["ledger_verification"]["category_counts"]["cognitive-audit"])

    def test_trust_demo_reports_update_policy_and_human_pin(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_trust_demo()

        self.assertEqual("reference-v0", result["policy"]["policy_id"])
        self.assertEqual("reference-trust-provenance-v1", result["policy"]["provenance_policy_id"])
        self.assertEqual(0.99, result["agents"]["integrity-guardian"]["global_score"])
        self.assertFalse(result["blocked_events"]["pinned_negative"]["applied"])
        self.assertEqual(0.62, result["agents"]["design-architect"]["global_score"])
        self.assertTrue(result["agents"]["codex-builder"]["eligibility"]["apply_to_runtime"])
        self.assertTrue(result["validation"]["self_issued_positive_blocked"])
        self.assertTrue(result["validation"]["reciprocal_positive_blocked"])
        self.assertTrue(result["validation"]["pinned_event_frozen"])
        self.assertEqual(
            "blocked-self-issued-positive",
            result["blocked_events"]["self_issued_positive"]["provenance_status"],
        )
        self.assertEqual(
            "blocked-reciprocal-positive",
            result["blocked_events"]["reciprocal_positive"]["provenance_status"],
        )

    def test_trust_transfer_demo_reports_digest_bound_cross_substrate_receipt(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_trust_transfer_demo()

        self.assertEqual("snapshot-clone-with-history", result["transfer"]["export_profile_id"])
        self.assertEqual(
            "bounded-cross-substrate-trust-transfer-v1",
            result["transfer"]["transfer_policy_id"],
        )
        self.assertEqual(
            "bounded-trust-transfer-attestation-federation-v1",
            result["transfer"]["attestation_policy_id"],
        )
        self.assertTrue(result["validation"]["source_snapshot_digest_bound"])
        self.assertTrue(result["validation"]["destination_snapshot_digest_bound"])
        self.assertTrue(result["validation"]["export_profile_bound"])
        self.assertTrue(result["validation"]["history_commitment_bound"])
        self.assertTrue(result["validation"]["history_preserved"])
        self.assertTrue(result["validation"]["thresholds_preserved"])
        self.assertTrue(result["validation"]["provenance_policy_preserved"])
        self.assertTrue(result["validation"]["eligibility_preserved"])
        self.assertTrue(result["validation"]["federation_quorum_attested"])
        self.assertTrue(result["validation"]["live_remote_verifier_attested"])
        self.assertTrue(result["validation"]["remote_verifier_receipts_bound"])
        self.assertTrue(result["validation"]["remote_verifier_disclosure_bound"])
        self.assertTrue(result["validation"]["re_attestation_cadence_bound"])
        self.assertTrue(result["validation"]["re_attestation_current"])
        self.assertTrue(result["validation"]["destination_lifecycle_bound"])
        self.assertTrue(result["validation"]["destination_lifecycle_disclosure_bound"])
        self.assertTrue(result["validation"]["destination_renewal_history_bound"])
        self.assertTrue(result["validation"]["destination_revocation_history_bound"])
        self.assertTrue(result["validation"]["destination_recovery_history_bound"])
        self.assertTrue(result["validation"]["recovery_quorum_bound"])
        self.assertTrue(result["validation"]["recovery_review_bound"])
        self.assertTrue(result["validation"]["recovery_notice_scope_bound"])
        self.assertTrue(result["validation"]["destination_current"])
        self.assertTrue(result["validation"]["destination_seeded"])
        self.assertTrue(result["validation"]["receipt_digest_bound"])
        self.assertEqual(result["source_snapshot"], result["destination_snapshot"])
        self.assertEqual("current", result["transfer"]["destination_lifecycle"]["current_status"])
        self.assertEqual(
            ["imported", "renewed", "revoked", "recovered"],
            [
                entry["event_type"]
                for entry in result["transfer"]["destination_lifecycle"]["history"]
            ],
        )
        self.assertEqual(
            3,
            result["transfer"]["federation_attestation"]["remote_verifier_federation"][
                "received_verifier_count"
            ],
        )
        self.assertEqual(
            "bounded-trust-transfer-multi-root-recovery-v1",
            result["transfer"]["federation_attestation"]["remote_verifier_federation"][
                "quorum_policy_id"
            ],
        )
        self.assertEqual(
            2,
            result["transfer"]["federation_attestation"]["remote_verifier_federation"][
                "trust_root_quorum"
            ],
        )
        self.assertEqual(
            2,
            result["transfer"]["federation_attestation"]["remote_verifier_federation"][
                "jurisdiction_quorum"
            ],
        )
        self.assertEqual(
            "trust_recovery_review",
            result["transfer"]["destination_lifecycle"]["history"][-1]["recovery_review"]["kind"],
        )
        self.assertEqual(
            "bounded-trust-recovery-legal-execution-scope-v1",
            result["transfer"]["destination_lifecycle"]["history"][-1]["recovery_review"][
                "execution_scope_manifest"
            ]["scope_profile_id"],
        )

    def test_trust_transfer_demo_can_emit_redacted_export_profile(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_trust_transfer_demo(
            export_profile_id="bounded-trust-transfer-redacted-export-v1"
        )

        self.assertEqual(
            "bounded-trust-transfer-redacted-export-v1",
            result["transfer"]["export_profile_id"],
        )
        self.assertTrue(result["validation"]["export_profile_bound"])
        self.assertTrue(result["validation"]["history_commitment_bound"])
        self.assertTrue(result["validation"]["remote_verifier_disclosure_bound"])
        self.assertTrue(result["validation"]["destination_lifecycle_disclosure_bound"])
        self.assertTrue(result["validation"]["recovery_quorum_bound"])
        self.assertTrue(result["validation"]["recovery_review_bound"])
        self.assertTrue(result["validation"]["recovery_notice_scope_bound"])
        self.assertTrue(result["validation"]["destination_seeded"])
        self.assertNotIn("source_snapshot", result["transfer"])
        self.assertNotIn("destination_snapshot", result["transfer"])
        self.assertIn("source_snapshot_redacted", result["transfer"])
        self.assertIn("destination_snapshot_redacted", result["transfer"])
        self.assertEqual(
            "trust_redacted_destination_lifecycle",
            result["transfer"]["destination_lifecycle"]["kind"],
        )
        self.assertNotIn("history", result["transfer"]["destination_lifecycle"])
        self.assertEqual(
            4,
            len(result["transfer"]["destination_lifecycle"]["history_summaries"]),
        )
        self.assertEqual(
            ["imported", "renewed", "revoked", "recovered"],
            [
                entry["event_type"]
                for entry in result["transfer"]["destination_lifecycle"]["history_summaries"]
            ],
        )
        self.assertNotIn(
            "verifier_receipts",
            result["transfer"]["federation_attestation"]["remote_verifier_federation"],
        )
        self.assertEqual(
            3,
            len(
                result["transfer"]["federation_attestation"][
                    "remote_verifier_federation"
                ]["verifier_receipt_summaries"]
            ),
        )
        self.assertEqual(
            3,
            result["transfer"]["destination_lifecycle"]["history_summaries"][-1][
                "covered_verifier_count"
            ],
        )
        self.assertEqual(
            "bounded-trust-transfer-history-redaction-v1",
            result["transfer"]["export_receipt"]["redaction_policy_id"],
        )
        self.assertEqual(
            "trust_redacted_destination_recovery_summary",
            result["transfer"]["destination_lifecycle"]["recovery_summary"]["kind"],
        )
        self.assertEqual(
            "bounded-trust-recovery-legal-execution-scope-v1",
            result["transfer"]["destination_lifecycle"]["recovery_summary"][
                "legal_proof_summary"
            ]["execution_scope_summary"]["scope_profile_id"],
        )
        self.assertEqual(
            result["transfer"]["destination_lifecycle"]["active_entry_digest"],
            result["transfer"]["destination_lifecycle"]["recovery_summary"]["bound_entry_digest"],
        )
        self.assertEqual(
            result["transfer"]["source_snapshot_redacted"]["sealed_snapshot_digest"],
            result["transfer"]["source_snapshot_digest"],
        )
        self.assertEqual(
            result["transfer"]["destination_snapshot_redacted"]["sealed_snapshot_digest"],
            result["transfer"]["destination_snapshot_digest"],
        )

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
        self.assertTrue(result["validation"]["legal_execution_ready"])
        self.assertTrue(result["validation"]["legal_execution_bound"])
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
        self.assertTrue(result["validation"]["binding_carries_transport_exchange"])
        self.assertTrue(result["validation"]["binding_carries_transport_exchange_digest"])
        self.assertTrue(result["validation"]["binding_carries_trust_root"])
        self.assertTrue(result["validation"]["binding_carries_authority_chain"])
        self.assertTrue(result["validation"]["legal_execution_executed"])
        self.assertTrue(result["validation"]["legal_execution_network_bound"])
        self.assertTrue(result["validation"]["binding_carries_legal_execution"])
        self.assertTrue(result["validation"]["binding_carries_legal_policy"])
        self.assertTrue(result["validation"]["transport_exchange_bound"])
        self.assertTrue(result["validation"]["transport_exchange_request_digest_bound"])
        self.assertEqual(
            "verifier://guardian-oversight.jp",
            result["reviewer"]["credential_verification"]["network_receipt"]["verifier_endpoint"],
        )
        self.assertEqual(
            "guardian-jurisdiction-legal-execution-v1",
            result["reviewer"]["credential_verification"]["legal_execution"]["execution_profile_id"],
        )
        self.assertEqual(
            "root://guardian-oversight.jp/reviewer-live-pki",
            result["event"]["reviewer_bindings"][0]["trust_root_ref"],
        )
        self.assertEqual(
            result["event"]["reviewer_bindings"][0]["transport_exchange_digest"],
            result["reviewer"]["credential_verification"]["network_receipt"]["transport_exchange"]["digest"],
        )
        self.assertEqual(
            result["event"]["reviewer_bindings"][0]["legal_execution_digest"],
            result["reviewer"]["credential_verification"]["legal_execution"]["digest"],
        )

    def test_yaoyorozu_demo_executes_local_worker_dispatch(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_yaoyorozu_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["workspace_discovery"]["validation"]["ok"])
        self.assertTrue(result["dispatch_plan"]["validation"]["ok"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["ok"])
        self.assertTrue(result["consensus_dispatch"]["validation"]["ok"])
        self.assertEqual(3, result["validation"]["workspace_count"])
        self.assertEqual(2, result["validation"]["non_source_workspace_count"])
        self.assertEqual("self-modify-patch-v1", result["validation"]["proposal_profile"])
        self.assertTrue(result["validation"]["workspace_discovery_ok"])
        self.assertTrue(result["validation"]["workspace_review_budget_respected"])
        self.assertEqual(3, result["validation"]["profile_workspace_review_budget"])
        self.assertEqual(
            ["runtime", "schema", "eval", "docs"],
            result["validation"]["profile_required_workspace_coverage_areas"],
        )
        self.assertEqual([], result["validation"]["profile_optional_workspace_coverage_areas"])
        self.assertEqual(
            ["runtime", "schema", "eval", "docs"],
            result["validation"]["required_builder_coverage_areas"],
        )
        self.assertEqual([], result["validation"]["optional_builder_coverage_areas"])
        self.assertTrue(result["validation"]["cross_workspace_coverage_complete"])
        self.assertEqual(4, result["validation"]["dispatch_unit_count"])
        self.assertEqual(4, result["validation"]["dispatch_success_count"])
        self.assertEqual(7, result["validation"]["consensus_message_count"])
        self.assertTrue(result["validation"]["consensus_dispatch_ok"])
        self.assertTrue(result["validation"]["consensus_direct_handoff_blocked"])
        self.assertTrue(result["validation"]["workspace_discovery_bound"])
        self.assertTrue(result["validation"]["builder_profile_policy_ready"])
        self.assertTrue(result["validation"]["workspace_profile_policy_ready"])
        self.assertTrue(result["validation"]["workspace_execution_bound"])
        self.assertTrue(result["validation"]["workspace_execution_policy_ready"])
        self.assertTrue(result["validation"]["worker_dispatch_coverage_complete"])
        self.assertEqual(4, result["validation"]["candidate_bound_dispatch_count"])
        self.assertEqual(0, result["validation"]["source_bound_dispatch_count"])
        self.assertEqual(4, result["validation"]["candidate_bound_success_count"])
        self.assertEqual(0, result["validation"]["source_bound_success_count"])
        self.assertTrue(result["validation"]["same_host_scope_only"])
        self.assertTrue(result["validation"]["external_workspace_seeded"])
        self.assertTrue(result["validation"]["external_dependencies_materialized"])
        self.assertTrue(result["validation"]["external_dependency_import_precedence_bound"])
        self.assertTrue(result["validation"]["external_dependency_module_origin_bound"])
        self.assertEqual(4, result["validation"]["external_dependency_materialized_count"])
        self.assertEqual(4, result["validation"]["external_dependency_import_precedence_count"])
        self.assertEqual(4, result["validation"]["external_dependency_module_origin_count"])
        self.assertEqual(
            "same-host-external-workspace-dependency-materialization-v1",
            result["validation"]["dependency_materialization_profile"],
        )
        self.assertEqual(
            "materialized-dependency-sealed-import-v1",
            result["validation"]["dependency_import_precedence_profile"],
        )
        self.assertEqual(
            "materialized-dependency-module-origin-v1",
            result["validation"]["dependency_module_origin_profile"],
        )
        self.assertTrue(result["validation"]["guardian_preseed_gate_bound"])
        self.assertTrue(result["validation"]["external_preseed_gates_passed"])
        self.assertEqual(4, result["validation"]["external_preseed_gate_pass_count"])
        self.assertEqual(
            "same-host-external-workspace-preseed-guardian-gate-v1",
            result["validation"]["preseed_gate_profile"],
        )
        self.assertTrue(result["validation"]["worker_delta_receipts_bound"])
        self.assertEqual("git-target-path-delta-v1", result["validation"]["worker_delta_scan_profile"])
        self.assertTrue(result["validation"]["worker_patch_candidate_receipts_bound"])
        self.assertEqual(
            "target-delta-to-patch-candidate-v1",
            result["validation"]["worker_patch_candidate_profile"],
        )
        self.assertEqual(
            "target-delta-priority-ranking-v1",
            result["validation"]["worker_patch_priority_profile"],
        )
        self.assertEqual(4, result["dispatch_receipt"]["execution_summary"]["successful_process_count"])
        self.assertEqual(
            4,
            result["dispatch_receipt"]["execution_summary"][
                "external_dependency_materialized_count"
            ],
        )
        self.assertEqual(
            4,
            result["dispatch_receipt"]["execution_summary"][
                "external_dependency_import_precedence_count"
            ],
        )
        self.assertEqual(
            4,
            result["dispatch_receipt"]["execution_summary"][
                "external_dependency_module_origin_count"
            ],
        )
        self.assertEqual(4, result["dispatch_receipt"]["execution_summary"]["target_ready_count"])
        self.assertEqual(4, result["dispatch_receipt"]["execution_summary"]["delta_bound_count"])
        self.assertEqual(
            4,
            result["dispatch_receipt"]["execution_summary"]["patch_candidate_bound_count"],
        )
        self.assertEqual(
            "target-delta-priority-ranking-v1",
            result["dispatch_receipt"]["execution_summary"]["patch_priority_profile"],
        )
        self.assertIn(
            result["dispatch_receipt"]["execution_summary"]["highest_patch_priority_tier"],
            {"none", "low", "medium", "high", "critical"},
        )
        self.assertGreaterEqual(
            result["dispatch_receipt"]["execution_summary"]["highest_patch_priority_score"],
            0,
        )
        self.assertEqual(
            "path-bound-target-delta-patch-candidate-v3",
            result["dispatch_receipt"]["execution_summary"]["ready_gate_profile"],
        )
        self.assertTrue(result["dispatch_receipt"]["validation"]["all_reports_bound_to_dispatch"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["all_delta_receipts_bound"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["all_patch_candidate_receipts_bound"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["all_target_paths_ready"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["external_dependency_module_origin_bound"])
        self.assertEqual(
            "consensus-bus-only",
            result["consensus_dispatch"]["transport_profile"],
        )
        self.assertEqual(
            result["convocation"]["session_id"],
            result["consensus_dispatch"]["consensus_session_id"],
        )
        self.assertEqual(
            1,
            result["consensus_dispatch"]["audit_summary"]["blocked_direct_attempts"],
        )
        self.assertTrue(
            all(
                process["workspace_scope"] == "same-host-external-workspace"
                and process["workspace_seed_status"] == "seeded"
                and len(process["workspace_seed_head_commit"]) == 40
                and process["guardian_preseed_gate_status"] == "pass"
                and process["guardian_preseed_gate_bound"]
                and process["guardian_preseed_gate"]["gate_profile"]
                == "same-host-external-workspace-preseed-guardian-gate-v1"
                and process["report"]["workspace_scope"] == "same-host-external-workspace"
                for process in result["dispatch_receipt"]["results"]
            )
        )
        self.assertTrue(
            all(
                process["report_binding_ok"]
                and process["delta_receipt_ok"]
                and process["target_paths_ready"]
                and process["report"]["coverage_evidence"]["all_targets_exist"]
                and process["report"]["coverage_evidence"]["all_targets_within_workspace"]
                and process["report"]["coverage_evidence"]["delta_scan_profile"]
                == "git-target-path-delta-v1"
                and process["report"]["coverage_evidence"]["patch_priority_profile"]
                == "target-delta-priority-ranking-v1"
                and process["report"]["coverage_evidence"]["highest_patch_priority_tier"]
                in {"none", "low", "medium", "high", "critical"}
                and process["report"]["coverage_evidence"]["highest_patch_priority_score"] >= 0
                and process["report"]["workspace_delta_receipt"]["status"] in {"clean", "delta-detected"}
                for process in result["dispatch_receipt"]["results"]
            )
        )
        self.assertEqual(
            ["runtime", "schema", "eval", "docs"],
            result["workspace_discovery"]["coverage_summary"]["non_source_supported_coverage_areas"],
        )
        self.assertTrue(result["validation"]["task_graph_bundle_strategy_ok"])
        self.assertEqual(
            "self-modify-three-root-bundle-v1",
            result["validation"]["task_graph_bundle_strategy_id"],
        )
        self.assertTrue(result["validation"]["build_request_binding_ok"])
        self.assertTrue(result["validation"]["build_request_scope_allowed"])
        self.assertEqual(
            "L5.PatchGenerator",
            result["validation"]["build_request_target_subsystem"],
        )
        self.assertEqual(
            result["convocation"]["session_id"],
            result["build_request_binding"]["council_action"]["session_id"],
        )
        self.assertIn(
            "evals/agentic/yaoyorozu_build_request_binding.yaml",
            result["build_request_binding"]["build_request"]["constraints"]["must_pass"],
        )
        self.assertIn(
            "evals/agentic/yaoyorozu_external_workspace_execution.yaml",
            result["build_request_binding"]["build_request"]["constraints"]["must_pass"],
        )
        self.assertTrue(result["validation"]["execution_chain_ok"])
        self.assertEqual("rollback", result["validation"]["execution_chain_rollout_decision"])
        self.assertTrue(result["validation"]["execution_chain_reviewer_network_attested"])
        self.assertEqual(
            result["build_request_binding"]["binding_ref"],
            result["execution_chain"]["build_request_binding_ref"],
        )
        self.assertEqual("rolled-back", result["execution_chain"]["rollback_session"]["status"])
        self.assertIn(
            "evals/agentic/yaoyorozu_execution_chain_binding.yaml",
            result["execution_chain"]["execution_summary"]["required_eval_refs"],
        )
        self.assertIn(
            "evals/agentic/yaoyorozu_external_workspace_execution.yaml",
            result["execution_chain"]["execution_summary"]["required_eval_refs"],
        )
        self.assertIn(
            ["docs", "eval"],
            sorted(
                sorted(binding["coverage_areas"])
                for binding in result["task_graph_binding"]["node_bindings"]
            ),
        )

    def test_yaoyorozu_demo_supports_memory_edit_profile(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_yaoyorozu_demo(proposal_profile="memory-edit-v1")

        self.assertEqual("memory-edit-v1", result["convocation"]["proposal_profile"])
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual(2, result["validation"]["workspace_count"])
        self.assertEqual(1, result["validation"]["non_source_workspace_count"])
        self.assertEqual(2, result["validation"]["profile_workspace_review_budget"])
        self.assertEqual(
            ["runtime", "eval", "docs"],
            result["validation"]["profile_required_workspace_coverage_areas"],
        )
        self.assertEqual(
            ["schema"],
            result["validation"]["profile_optional_workspace_coverage_areas"],
        )
        self.assertEqual(
            ["runtime", "eval", "docs"],
            result["validation"]["required_builder_coverage_areas"],
        )
        self.assertEqual(
            ["schema"],
            result["validation"]["optional_builder_coverage_areas"],
        )
        self.assertTrue(result["validation"]["workspace_discovery_bound"])
        self.assertTrue(result["validation"]["builder_profile_policy_ready"])
        self.assertTrue(result["validation"]["workspace_profile_policy_ready"])
        self.assertTrue(result["validation"]["worker_dispatch_coverage_complete"])
        self.assertEqual(3, result["validation"]["builder_coverage_count"])
        self.assertEqual(3, result["validation"]["dispatch_unit_count"])
        self.assertEqual(3, result["validation"]["dispatch_success_count"])
        self.assertIn(
            "memory-edit-v1",
            result["workspace_discovery"]["workspaces"][0]["proposal_profiles"],
        )
        self.assertEqual(
            ["runtime", "eval", "docs"],
            result["workspace_discovery"]["coverage_summary"][
                "non_source_profile_supported_coverage_areas"
            ],
        )
        self.assertEqual(
            ["schema"],
            result["workspace_discovery"]["coverage_summary"]["non_source_missing_coverage_areas"],
        )
        self.assertEqual(
            [
                "memory-archivist",
                "design-auditor",
                "conservatism-advocate",
                "ethics-committee",
            ],
            [selection["role_id"] for selection in result["convocation"]["council_panel"]],
        )
        self.assertTrue(result["validation"]["task_graph_bundle_strategy_ok"])
        self.assertEqual(
            "memory-edit-required-dispatch-three-root-v1",
            result["validation"]["task_graph_bundle_strategy_id"],
        )
        self.assertEqual(
            [["docs"], ["eval"], ["runtime"]],
            sorted(
                sorted(binding["coverage_areas"])
                for binding in result["task_graph_binding"]["node_bindings"]
            ),
        )
        self.assertIn(
            "evals/agentic/yaoyorozu_memory_edit_profile.yaml",
            result["build_request_binding"]["build_request"]["constraints"]["must_pass"],
        )
        self.assertTrue(result["validation"]["execution_chain_ok"])
        self.assertIn(
            "evals/agentic/yaoyorozu_memory_edit_profile.yaml",
            result["execution_chain"]["execution_summary"]["required_eval_refs"],
        )

    def test_yaoyorozu_demo_supports_memory_edit_optional_schema_dispatch(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_yaoyorozu_demo(
            proposal_profile="memory-edit-v1",
            include_optional_coverage=["schema"],
        )

        self.assertTrue(result["validation"]["ok"])
        self.assertEqual(
            ["schema"],
            result["validation"]["requested_optional_builder_coverage_areas"],
        )
        self.assertEqual(
            ["runtime", "eval", "docs", "schema"],
            result["validation"]["dispatch_builder_coverage_areas"],
        )
        self.assertEqual(4, result["validation"]["builder_coverage_count"])
        self.assertEqual(4, result["validation"]["dispatch_unit_count"])
        self.assertEqual(4, result["validation"]["dispatch_success_count"])
        self.assertEqual(
            ["schema"],
            result["dispatch_plan"]["selection_summary"]["requested_optional_coverage_areas"],
        )
        self.assertEqual(
            "memory-edit-optional-schema-dispatch-three-root-v1",
            result["validation"]["task_graph_bundle_strategy_id"],
        )
        self.assertTrue(result["validation"]["execution_chain_ok"])
        self.assertEqual(
            [["docs"], ["eval", "schema"], ["runtime"]],
            sorted(
                sorted(binding["coverage_areas"])
                for binding in result["task_graph_binding"]["node_bindings"]
            ),
        )

    def test_yaoyorozu_demo_supports_fork_request_profile(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_yaoyorozu_demo(proposal_profile="fork-request-v1")

        self.assertEqual("fork-request-v1", result["convocation"]["proposal_profile"])
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual(3, result["validation"]["profile_workspace_review_budget"])
        self.assertEqual(
            ["runtime", "schema", "docs"],
            result["validation"]["profile_required_workspace_coverage_areas"],
        )
        self.assertEqual(
            ["eval"],
            result["validation"]["profile_optional_workspace_coverage_areas"],
        )
        self.assertEqual(
            ["runtime", "schema", "docs"],
            result["validation"]["required_builder_coverage_areas"],
        )
        self.assertEqual(
            ["eval"],
            result["validation"]["optional_builder_coverage_areas"],
        )
        self.assertTrue(result["validation"]["workspace_discovery_bound"])
        self.assertTrue(result["validation"]["builder_profile_policy_ready"])
        self.assertTrue(result["validation"]["workspace_profile_policy_ready"])
        self.assertTrue(result["validation"]["worker_dispatch_coverage_complete"])
        self.assertEqual(3, result["validation"]["builder_coverage_count"])
        self.assertEqual(3, result["validation"]["dispatch_unit_count"])
        self.assertEqual(3, result["validation"]["dispatch_success_count"])
        self.assertIn(
            "fork-request-v1",
            result["workspace_discovery"]["workspaces"][0]["proposal_profiles"],
        )
        self.assertEqual(
            [
                "identity-protector",
                "legal-scholar",
                "conservatism-advocate",
                "ethics-committee",
            ],
            [selection["role_id"] for selection in result["convocation"]["council_panel"]],
        )
        self.assertEqual(
            "identity-guardian",
            result["convocation"]["council_panel"][0]["selected_agent_id"],
        )
        self.assertEqual(
            "legal-scholar",
            result["convocation"]["council_panel"][1]["selected_agent_id"],
        )
        self.assertTrue(result["validation"]["task_graph_bundle_strategy_ok"])
        self.assertEqual(
            "fork-request-required-dispatch-three-root-v1",
            result["validation"]["task_graph_bundle_strategy_id"],
        )
        self.assertEqual(
            [["docs"], ["runtime"], ["schema"]],
            sorted(
                sorted(binding["coverage_areas"])
                for binding in result["task_graph_binding"]["node_bindings"]
            ),
        )
        self.assertIn(
            "evals/agentic/yaoyorozu_fork_request_profile.yaml",
            result["build_request_binding"]["build_request"]["constraints"]["must_pass"],
        )
        self.assertTrue(result["validation"]["execution_chain_ok"])
        self.assertIn(
            "evals/agentic/yaoyorozu_fork_request_profile.yaml",
            result["execution_chain"]["execution_summary"]["required_eval_refs"],
        )

    def test_yaoyorozu_demo_supports_fork_request_optional_eval_dispatch(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_yaoyorozu_demo(
            proposal_profile="fork-request-v1",
            include_optional_coverage=["eval"],
        )

        self.assertTrue(result["validation"]["ok"])
        self.assertEqual(
            ["eval"],
            result["validation"]["requested_optional_builder_coverage_areas"],
        )
        self.assertEqual(
            ["runtime", "schema", "docs", "eval"],
            result["validation"]["dispatch_builder_coverage_areas"],
        )
        self.assertEqual(4, result["validation"]["builder_coverage_count"])
        self.assertEqual(4, result["validation"]["dispatch_unit_count"])
        self.assertEqual(4, result["validation"]["dispatch_success_count"])
        self.assertEqual(
            ["eval"],
            result["dispatch_plan"]["selection_summary"]["requested_optional_coverage_areas"],
        )
        self.assertEqual(
            "fork-request-optional-eval-dispatch-three-root-v1",
            result["validation"]["task_graph_bundle_strategy_id"],
        )
        self.assertEqual(
            [["docs", "eval"], ["runtime"], ["schema"]],
            sorted(
                sorted(binding["coverage_areas"])
                for binding in result["task_graph_binding"]["node_bindings"]
            ),
        )

    def test_yaoyorozu_demo_supports_inter_mind_negotiation_profile(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_yaoyorozu_demo(proposal_profile="inter-mind-negotiation-v1")

        self.assertEqual("inter-mind-negotiation-v1", result["convocation"]["proposal_profile"])
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual(3, result["validation"]["profile_workspace_review_budget"])
        self.assertEqual(
            ["runtime", "schema", "eval", "docs"],
            result["validation"]["profile_required_workspace_coverage_areas"],
        )
        self.assertEqual(
            [],
            result["validation"]["profile_optional_workspace_coverage_areas"],
        )
        self.assertEqual(
            ["runtime", "schema", "eval", "docs"],
            result["validation"]["required_builder_coverage_areas"],
        )
        self.assertEqual(
            [],
            result["validation"]["optional_builder_coverage_areas"],
        )
        self.assertTrue(result["validation"]["workspace_discovery_bound"])
        self.assertTrue(result["validation"]["builder_profile_policy_ready"])
        self.assertTrue(result["validation"]["workspace_profile_policy_ready"])
        self.assertTrue(result["validation"]["worker_dispatch_coverage_complete"])
        self.assertEqual(4, result["validation"]["builder_coverage_count"])
        self.assertEqual(4, result["validation"]["dispatch_unit_count"])
        self.assertEqual(4, result["validation"]["dispatch_success_count"])
        self.assertIn(
            "inter-mind-negotiation-v1",
            result["workspace_discovery"]["workspaces"][0]["proposal_profiles"],
        )
        self.assertEqual(
            [
                "legal-scholar",
                "design-auditor",
                "conservatism-advocate",
                "ethics-committee",
            ],
            [selection["role_id"] for selection in result["convocation"]["council_panel"]],
        )
        self.assertEqual(
            "legal-scholar",
            result["convocation"]["council_panel"][0]["selected_agent_id"],
        )
        self.assertTrue(result["validation"]["task_graph_bundle_strategy_ok"])
        self.assertEqual(
            "inter-mind-negotiation-contract-sync-v1",
            result["validation"]["task_graph_bundle_strategy_id"],
        )
        self.assertEqual(
            [["docs", "schema"], ["eval"], ["runtime"]],
            sorted(
                sorted(binding["coverage_areas"])
                for binding in result["task_graph_binding"]["node_bindings"]
            ),
        )
        self.assertIn(
            "evals/agentic/yaoyorozu_inter_mind_negotiation_profile.yaml",
            result["build_request_binding"]["build_request"]["constraints"]["must_pass"],
        )

    def test_ethics_demo_reports_rule_language_and_recorded_events(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_ethics_demo()

        self.assertEqual("deterministic-rule-tree-v0", result["language"]["language_id"])
        self.assertEqual("veto", result["decisions"]["immutable_boundary"]["outcome"])
        self.assertEqual("escalate", result["decisions"]["sandbox_escalation"]["outcome"])
        self.assertEqual("approval", result["decisions"]["approved_fork"]["outcome"])
        self.assertTrue(result["validation"]["resolution_policy_machine_readable"])
        self.assertTrue(result["validation"]["conflict_prefers_veto"])
        self.assertEqual(
            "A7-ewa-blocked-token",
            result["decisions"]["ewa_conflict_resolution"]["resolution"]["selected_rule_id"],
        )
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
        self.assertEqual(
            "cancelled",
            result["outcomes"]["completed"]["scheduler_cancellation"]["result"],
        )
        self.assertEqual("cancelled", result["scheduler"]["completed"]["handle"]["status"])
        self.assertEqual(1, result["scheduler"]["completed"]["execution_receipt"]["cancel_count"])
        self.assertIn(
            "cancelled",
            result["scheduler"]["completed"]["execution_receipt"]["scenario_labels"],
        )
        self.assertTrue(result["outcomes"]["completed"]["scheduler_cancellation"]["execution_receipt_digest"])
        self.assertEqual("cool-off-pending", result["observations"]["cool_off"]["status"])
        self.assertEqual("deferred", result["outcomes"]["cool_off"]["scheduler_cancellation"]["result"])
        self.assertEqual("advancing", result["scheduler"]["cool_off"]["handle"]["status"])
        self.assertEqual(
            "not-requested",
            result["outcomes"]["rejected"]["scheduler_cancellation"]["result"],
        )
        self.assertEqual("advancing", result["scheduler"]["rejected"]["handle"]["status"])
        self.assertEqual("released", result["substrate_snapshot"]["allocations"][0]["status"])
        self.assertEqual(3, result["ledger_verification"]["category_counts"]["terminate"])


if __name__ == "__main__":
    unittest.main()
