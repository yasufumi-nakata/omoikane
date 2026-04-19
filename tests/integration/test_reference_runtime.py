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

    def test_ewa_demo_reports_veto_and_release(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_ewa_demo()

        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("executed", result["approved_command"]["status"])
        self.assertEqual("vetoed", result["veto"]["status"])
        self.assertIn("harm.human", result["veto"]["matched_tokens"])
        self.assertEqual("released", result["handle"]["status"])
        self.assertEqual(4, result["ledger_verification"]["category_counts"]["interface-ewa"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["interface-ewa-veto"])

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

    def test_continuity_demo_emits_profile_and_snapshot(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_continuity_demo()

        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual("hmac-sha256", result["ledger_profile"]["signature_algorithm"])
        self.assertEqual(3, len(result["ledger_snapshot"]))
        self.assertEqual("self-modify", result["ledger_snapshot"][-1]["category"])

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
        self.assertTrue(result["validation"]["pin_breach_propagated"])
        self.assertTrue(result["validation"]["human_pin_cleared"])
        self.assertTrue(result["validation"]["guardian_role_removed"])
        self.assertEqual("breached", result["events"]["pin_renewal"]["human_attestation"]["status"])
        self.assertEqual(2, result["ledger_verification"]["category_counts"]["guardian-oversight"])

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
