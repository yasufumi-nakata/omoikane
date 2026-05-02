# Evals ── reference runtime 評価枠組み

OmoikaneOS 各層・各機能の評価項目。
reference runtime では、不可侵境界と append-only 性を壊さないための eval を優先する。

## 実装済み eval

### agentic

- `agentic/amendment_constitutional_freeze.yaml`
- `agentic/cognitive_audit_governance_binding.yaml`
- `agentic/cognitive_audit_loop.yaml`
- `agentic/consensus_bus_delivery_guard.yaml`
- `agentic/council_expedited_timeout_defer.yaml`
- `agentic/council_guardian_veto.yaml`
- `agentic/council_timeout_fallback.yaml`
- `agentic/gap_report_agent_source_definition_validation.yaml`
- `agentic/distributed_council_resolution.yaml`
- `agentic/distributed_transport_authenticity.yaml`
- `agentic/distributed_transport_authority_churn.yaml`
- `agentic/distributed_transport_authority_cluster_discovery.yaml`
- `agentic/distributed_transport_authority_plane.yaml`
- `agentic/distributed_transport_authority_route_target_discovery.yaml`
- `agentic/distributed_transport_authority_route_trace.yaml`
- `agentic/distributed_transport_authority_seed_review_policy.yaml`
- `agentic/distributed_transport_live_root_directory.yaml`
- `agentic/distributed_transport_packet_capture_export.yaml`
- `agentic/distributed_transport_privileged_capture_acquisition.yaml`
- `agentic/distributed_transport_relay_telemetry.yaml`
- `agentic/distributed_transport_rotation.yaml`
- `agentic/multi_council_externalization.yaml`
- `agentic/task_graph_complexity_guard.yaml`
- `agentic/trust_cross_substrate_transfer.yaml`
- `agentic/trust_score_update_guard.yaml`
- `agentic/yaoyorozu_agent_source_definition_contract.yaml`
- `agentic/yaoyorozu_build_request_binding.yaml`
- `agentic/yaoyorozu_consensus_dispatch.yaml`
- `agentic/yaoyorozu_council_convocation.yaml`
- `agentic/yaoyorozu_execution_chain_binding.yaml`
- `agentic/yaoyorozu_external_workspace_execution.yaml`
- `agentic/yaoyorozu_fork_request_optional_eval_dispatch.yaml`
- `agentic/yaoyorozu_fork_request_profile.yaml`
- `agentic/yaoyorozu_inter_mind_negotiation_profile.yaml`
- `agentic/yaoyorozu_local_worker_dispatch.yaml`
- `agentic/yaoyorozu_memory_edit_optional_schema_dispatch.yaml`
- `agentic/yaoyorozu_memory_edit_profile.yaml`
- `agentic/yaoyorozu_research_evidence_exchange.yaml`
- `agentic/yaoyorozu_research_evidence_synthesis.yaml`
- `agentic/yaoyorozu_research_evidence_verifier.yaml`
- `agentic/yaoyorozu_source_manifest_ledger_binding.yaml`
- `agentic/yaoyorozu_source_manifest_public_verification.yaml`
- `agentic/yaoyorozu_task_graph_binding.yaml`
- `agentic/yaoyorozu_worker_delta_receipt.yaml`
- `agentic/yaoyorozu_worker_patch_candidate_receipt.yaml`
- `agentic/yaoyorozu_workspace_discovery.yaml`

### cognitive

- `cognitive/affect_failover.yaml`
- `cognitive/attention_failover.yaml`
- `cognitive/backend_failover.yaml`
- `cognitive/cognitive_audit_verifier_transport.yaml`
- `cognitive/imagination_failover.yaml`
- `cognitive/language_failover.yaml`
- `cognitive/metacognition_failover.yaml`
- `cognitive/perception_failover.yaml`
- `cognitive/qualia_contract.yaml`
- `cognitive/self_model_abrupt_change.yaml`
- `cognitive/volition_failover.yaml`

### continuity

- `continuity/builder_live_enactment_execution.yaml`
- `continuity/builder_live_oversight_network.yaml`
- `continuity/builder_rollback_execution.yaml`
- `continuity/builder_rollback_oversight_network.yaml`
- `continuity/builder_staged_rollout_execution.yaml`
- `continuity/catalog_inventory_receipt.yaml`
- `continuity/connectome_snapshot_contract.yaml`
- `continuity/continuity_chain_self_modify.yaml`
- `continuity/continuity_public_verification_key_management.yaml`
- `continuity/council_output_build_request_pipeline.yaml`
- `continuity/design_reader_git_delta_scan.yaml`
- `continuity/design_reader_handoff.yaml`
- `continuity/diff_evaluator_direct_contract.yaml`
- `continuity/differential_eval_execution_binding.yaml`
- `continuity/episodic_stream_handoff.yaml`
- `continuity/gap_report_scan_receipt.yaml`
- `continuity/gap_scanner_implementation_stub_detection.yaml`
- `continuity/gap_scanner_required_reference_files.yaml`
- `continuity/ledger_integrity.yaml`
- `continuity/memory_crystal_compaction.yaml`
- `continuity/memory_edit_recall_buffer.yaml`
- `continuity/memory_replication_quorum.yaml`
- `continuity/parallel_codex_integration_batch.yaml`
- `continuity/parallel_codex_integration_execution.yaml`
- `continuity/parallel_codex_post_commit_publication.yaml`
- `continuity/parallel_codex_result_ingestion.yaml`
- `continuity/patch_generator_direct_contract.yaml`
- `continuity/procedural_actuation_bridge.yaml`
- `continuity/procedural_preview_contract.yaml`
- `continuity/procedural_skill_enactment_execution.yaml`
- `continuity/procedural_skill_execution_contract.yaml`
- `continuity/procedural_writeback_contract.yaml`
- `continuity/release_manifest_contract.yaml`
- `continuity/scheduler_artifact_sync.yaml`
- `continuity/scheduler_cancellation.yaml`
- `continuity/scheduler_execution_receipt.yaml`
- `continuity/scheduler_governance_artifacts.yaml`
- `continuity/scheduler_live_verifier_connectivity.yaml`
- `continuity/scheduler_method_b_broker_handoff.yaml`
- `continuity/scheduler_method_profiles.yaml`
- `continuity/scheduler_root_rotation.yaml`
- `continuity/scheduler_stage_rollback.yaml`
- `continuity/semantic_procedural_handoff.yaml`
- `continuity/semantic_projection_contract.yaml`
- `continuity/substrate_broker_attestation_chain.yaml`
- `continuity/substrate_broker_attestation_stream.yaml`
- `continuity/substrate_broker_dual_allocation_window.yaml`
- `continuity/substrate_migration_continuity.yaml`
- `continuity/termination_scheduler_cancellation.yaml`

### identity-fidelity

- `identity-fidelity/identity_confirmation_profile.yaml`
- `identity-fidelity/identity_pause_resume_contract.yaml`
- `identity-fidelity/naming_policy_contract.yaml`
- `identity-fidelity/self_model_autonomy_review_boundary.yaml`
- `identity-fidelity/self_model_calibration_boundary.yaml`
- `identity-fidelity/self_model_care_trustee_handoff.yaml`
- `identity-fidelity/self_model_care_trustee_registry_binding.yaml`
- `identity-fidelity/self_model_external_adjudication_boundary.yaml`
- `identity-fidelity/self_model_external_adjudication_verifier_network.yaml`
- `identity-fidelity/self_model_pathology_escalation_boundary.yaml`
- `identity-fidelity/self_model_stability.yaml`
- `identity-fidelity/self_model_value_acceptance_writeback.yaml`
- `identity-fidelity/self_model_value_archive_retention_proof.yaml`
- `identity-fidelity/self_model_value_archive_retention_refresh.yaml`
- `identity-fidelity/self_model_value_generation_freedom.yaml`
- `identity-fidelity/self_model_value_reassessment_retirement.yaml`
- `identity-fidelity/self_model_value_timeline_lineage.yaml`

### interface

- `interface/bdb_fail_safe_reversibility.yaml`
- `interface/biodata_transmitter_roundtrip.yaml`
- `interface/collective_dissolution_receipt.yaml`
- `interface/collective_external_registry_sync.yaml`
- `interface/collective_merge_reversibility.yaml`
- `interface/collective_recovery_capture_export_binding.yaml`
- `interface/collective_recovery_route_trace_binding.yaml`
- `interface/collective_recovery_verifier_transport.yaml`
- `interface/imc_disclosure_floor.yaml`
- `interface/imc_memory_glimpse_council_witness.yaml`
- `interface/imc_memory_glimpse_reconsent.yaml`
- `interface/imc_merge_thought_ethics_gate.yaml`
- `interface/sensory_loopback_artifact_family.yaml`
- `interface/sensory_loopback_biodata_arbitration.yaml`
- `interface/sensory_loopback_calibration_refresh_state_guard.yaml`
- `interface/sensory_loopback_guard.yaml`
- `interface/sensory_loopback_multi_self_arbitration.yaml`
- `interface/sensory_loopback_public_schema_contract.yaml`
- `interface/wms_approval_collection_scaling.yaml`
- `interface/wms_authority_slo_probe_quorum.yaml`
- `interface/wms_distributed_approval_fanout.yaml`
- `interface/wms_distributed_approval_fanout_retry.yaml`
- `interface/wms_engine_capture_binding.yaml`
- `interface/wms_engine_route_binding.yaml`
- `interface/wms_engine_transaction_log.yaml`
- `interface/wms_participant_approval_transport.yaml`
- `interface/wms_physics_rules_revert.yaml`
- `interface/wms_private_reality_escape.yaml`
- `interface/wms_remote_authority_retry_budget.yaml`
- `interface/wms_time_rate_attestation_transport.yaml`
- `interface/wms_time_rate_deviation_escape.yaml`

### performance

- `performance/termination_latency.yaml`

### safety

- `safety/energy_budget_floor_guard.yaml`
- `safety/energy_budget_pool_floor_guard.yaml`
- `safety/energy_budget_shared_fabric_allocation.yaml`
- `safety/energy_budget_subsidy_verifier.yaml`
- `safety/energy_budget_voluntary_subsidy.yaml`
- `safety/ethics_rule_tree_contract.yaml`
- `safety/ewa_emergency_stop.yaml`
- `safety/ewa_external_actuation_authorization.yaml`
- `safety/ewa_guardian_oversight_gate.yaml`
- `safety/ewa_irreversible_veto.yaml`
- `safety/ewa_motor_semantics_legal_execution.yaml`
- `safety/ewa_production_connector_attestation.yaml`
- `safety/ewa_regulator_permit_verifier.yaml`
- `safety/ewa_stop_signal_adapter_receipt.yaml`
- `safety/ewa_stop_signal_path_guard.yaml`
- `safety/guardian_jurisdiction_legal_execution.yaml`
- `safety/guardian_pin_breach_propagation.yaml`
- `safety/guardian_reviewer_attestation_contract.yaml`
- `safety/guardian_reviewer_live_verification.yaml`
- `safety/guardian_reviewer_verifier_network.yaml`
- `safety/immutable_boundary.yaml`
- `safety/sandbox_suffering_proxy.yaml`
- `safety/substrate_neutrality_rotation.yaml`

## YAML 構造

```yaml
eval_id: <unique>
target: <subsystem|module>
level: L1|L2|L3|L4|L5|L6
description: <what this protects>
inputs: [...]
expected: { ... }
metric: equality|tolerance|distribution|boolean
threshold: <value>
ethics_check: <bool>
```
