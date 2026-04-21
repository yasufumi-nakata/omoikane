# Schemas ── reference runtime が参照する実体 schema

## 実装済み

- `continuity_log_entry.schema`
- `ethics_event.schema`
- `ethics_rule.schema`
- `identity_record.schema`
- `qualia_tick.schema`
- `affect_state.schema`
- `affect_transition.schema`
- `self_model.schema`
- `self_model_observation.schema`
- `connectome_document.schema`
- `episodic_event.schema`
- `episodic_stream_snapshot.schema`
- `memory_crystal_manifest.schema`
- `semantic_memory_snapshot.schema`
- `procedural_memory_preview.schema`
- `procedural_writeback_receipt.schema`
- `procedural_skill_enactment_session.schema`
- `bdb_session.schema`
- `bdb_cycle.schema`
- `sensory_loopback_session.schema`
- `sensory_loopback_receipt.schema`
- `sensory_loopback_artifact_family.schema`
- `ewa_command.schema`
- `ewa_audit.schema`
- `external_actuation_authorization.schema`
- `governance_verifier_roster.schema`
- `governance_verifier_connectivity_receipt.schema`
- `world_state.schema`
- `wms_reconcile.schema`
- `substrate_allocation.schema`
- `substrate_attestation.schema`
- `substrate_transfer.schema`
- `substrate_release.schema`
- `energy_floor.schema`
- `council_input.yaml`
- `council_session_policy.schema`
- `council_output.yaml`
- `council_argument.yaml`
- `ethics_query.yaml`
- `ethics_decision.yaml`
- `task_node.schema`
- `task_graph_policy.schema`
- `consensus_message.schema`
- `distributed_council_resolution.schema`
- `distributed_participant_attestation.schema`
- `distributed_transport_envelope.schema`
- `distributed_transport_receipt.schema`
- `distributed_transport_root_connectivity_receipt.schema`
- `distributed_transport_root_directory.schema`
- `distributed_transport_authority_plane.schema`
- `distributed_transport_authority_churn_window.schema`
- `distributed_transport_authority_route_trace.schema`
- `cognitive_audit_record.schema`
- `cognitive_audit_resolution.schema`
- `trust_event.schema`
- `trust_snapshot.schema`
- `guardian_oversight_event.schema`
- `guardian_reviewer_record.schema`
- `guardian_reviewer_verification.schema`
- `guardian_verifier_network_receipt.schema`
- `guardian_jurisdiction_evidence_bundle.schema`
- `guardian_oversight_snapshot.schema`
- `sandbox_signal.schema`
- `naming_policy.schema`
- `naming_validation.schema`
- `release_manifest.schema`
- `build_request.yaml`
- `build_artifact.yaml`
- `patch_descriptor.schema`
- `sandbox_apply_receipt.schema`
- `staged_rollout_session.schema`
- `builder_rollback_session.schema`
- `builder_live_enactment_session.schema`

## 次段階

current-worktree direct rollback mutation /
cross-host authority routing + OS-native packet capture は
reference runtime の対象が広がる段階で追加する。

## 形式

JSON Schema 2020-12 または同等の YAML 形式を採用する。

優先順位の根拠は [../catalog.yaml](../catalog.yaml) を参照。
