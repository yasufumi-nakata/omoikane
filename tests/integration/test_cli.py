from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from omoikane.cli import main


class CliIntegrationTests(unittest.TestCase):
    def test_gap_report_emits_reference_ready_json(self) -> None:
        stdout = io.StringIO()
        repo_root = Path(__file__).resolve().parents[2]

        with patch(
            "sys.argv",
            ["omoikane", "gap-report", "--repo-root", str(repo_root), "--json"],
        ), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertEqual(0, result["missing_required_reference_file_count"])
        self.assertEqual([], result["missing_required_reference_files"])
        self.assertEqual(0, result["missing_expected_file_count"])
        self.assertEqual(0, result["inventory_drift_count"])
        self.assertEqual(0, result["catalog_coverage_gap_count"])
        self.assertEqual([], result["catalog_coverage_gap_hits"])
        self.assertEqual(0, result["implementation_stub_count"])
        self.assertEqual([], result["implementation_stub_hits"])
        self.assertIn("decision_log_residual_count", result)
        self.assertEqual(
            result["decision_log_residual_count"],
            len(result["decision_log_residual_hits"]),
        )
        self.assertIn("decision_log_frontier_count", result)
        self.assertEqual(
            result["decision_log_frontier_count"],
            len(result["decision_log_frontier_hits"]),
        )
        self.assertEqual(
            "self-construction-gap-report-scan-receipt-v1",
            result["scan_receipt"]["profile"],
        )
        self.assertTrue(result["scan_receipt"]["all_zero"])
        self.assertTrue(result["scan_receipt"]["validation"]["ok"])
        self.assertEqual(0, result["scan_receipt"]["counts"]["prioritized_task_count"])
        self.assertFalse(result["scan_receipt"]["raw_report_payload_stored"])
        self.assertTrue(result["scan_receipt"]["validation"]["scan_surface_digests_bound"])
        self.assertTrue(result["scan_receipt"]["validation"]["surface_manifest_digest_bound"])
        self.assertTrue(result["scan_receipt"]["validation"]["continuity_ledger_bound"])
        self.assertTrue(
            result["scan_receipt"]["validation"]["continuity_event_digest_bound"]
        )
        self.assertTrue(result["scan_receipt"]["continuity_ledger_appended"])
        self.assertTrue(
            result["scan_receipt"]["validation"]["continuity_ledger_entry_appended"]
        )
        self.assertTrue(
            result["scan_receipt"]["validation"]["continuity_ledger_payload_ref_bound"]
        )
        self.assertEqual(
            ["self", "guardian"],
            result["scan_receipt"]["continuity_ledger_signature_roles"],
        )
        self.assertFalse(result["scan_receipt"]["validation"]["raw_surface_payload_stored"])
        self.assertFalse(result["scan_receipt"]["raw_continuity_event_payload_stored"])
        self.assertFalse(
            result["scan_receipt"]["validation"]["raw_continuity_event_payload_stored"]
        )
        self.assertTrue(
            any(
                entry["path"] == "meta/open-questions.md"
                for entry in result["scan_receipt"]["scan_surface_digests"]
            )
        )

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
        self.assertTrue(result["validation"]["catalog_inventory_valid"])
        self.assertEqual(
            "specs-catalog-generated-inventory-v1",
            result["manifest"]["catalog_inventory_receipt"]["profile"],
        )
        self.assertTrue(result["manifest"]["catalog_inventory_receipt"]["validation"]["ok"])

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

    def test_energy_budget_demo_emits_ap1_floor_guard(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "energy-budget-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("floor-protected", result["validation"]["budget_status"])
        self.assertEqual("migrate-standby", result["validation"]["recommended_action"])
        self.assertTrue(result["energy_budget"]["receipt"]["floor_preserved"])
        self.assertFalse(result["energy_budget"]["receipt"]["raw_economic_payload_stored"])

    def test_energy_budget_pool_demo_emits_cross_identity_offset_guard(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "energy-budget-pool-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("floor-protected", result["validation"]["pool_budget_status"])
        self.assertTrue(result["validation"]["cross_identity_floor_offset_blocked"])
        self.assertFalse(
            result["energy_budget_pool"]["receipt"]["cross_identity_subsidy_allowed"]
        )
        self.assertEqual(2, result["energy_budget_pool"]["receipt"]["member_count"])

    def test_energy_budget_subsidy_demo_emits_consent_bound_subsidy(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "energy-budget-subsidy-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        receipt = result["energy_budget_subsidy"]["receipt"]
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("accepted", result["validation"]["subsidy_status"])
        self.assertTrue(receipt["voluntary_subsidy_allowed"])
        self.assertTrue(receipt["floor_protection_preserved"])
        self.assertTrue(receipt["all_consent_digests_valid"])
        self.assertTrue(receipt["funding_policy_signature_bound"])
        self.assertTrue(receipt["signer_roster_verifier_bound"])
        self.assertTrue(
            receipt["signer_roster_verifier_quorum_receipt"][
                "threshold_policy_source_bound"
            ]
        )
        self.assertTrue(
            receipt["signer_roster_verifier_quorum_receipt"][
                "threshold_policy_signature_bound"
            ]
        )
        self.assertFalse(
            receipt["signer_roster_verifier_quorum_receipt"][
                "raw_threshold_policy_payload_stored"
            ]
        )
        self.assertEqual(
            "verified",
            receipt["signer_roster_verifier_receipt"]["verifier_receipt_status"],
        )
        self.assertEqual(
            "live-http-json-energy-subsidy-signer-roster-verifier-v1",
            receipt["signer_roster_verifier_receipt"]["verifier_transport_profile"],
        )
        self.assertTrue(receipt["signer_roster_verifier_receipt"]["network_probe_bound"])
        self.assertEqual(
            64,
            len(receipt["signer_roster_verifier_receipt"]["network_response_digest"]),
        )
        self.assertTrue(receipt["revocation_registry_bound"])
        self.assertTrue(receipt["audit_authority_bound"])
        self.assertTrue(receipt["jurisdiction_authority_bound"])
        self.assertEqual("verified", receipt["authority_binding_status"])
        self.assertFalse(receipt["cross_identity_offset_used"])
        self.assertFalse(receipt["raw_funding_payload_stored"])
        self.assertFalse(receipt["raw_authority_payload_stored"])

    def test_energy_budget_fabric_demo_emits_shared_capacity_shortfalls(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "energy-budget-fabric-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        receipt = result["energy_budget_fabric"]["receipt"]
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual(
            "fabric-capacity-deficit-protected",
            result["validation"]["budget_status"],
        )
        self.assertFalse(receipt["shared_capacity_floor_preserved"])
        self.assertEqual(4, receipt["fabric_capacity_deficit_jps"])
        self.assertEqual(2, receipt["impacted_member_count"])
        self.assertTrue(receipt["broker_signal_bound"])
        self.assertFalse(receipt["degradation_allowed"])
        self.assertFalse(receipt["raw_capacity_payload_stored"])

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
        self.assertTrue(result["validation"]["memory_glimpse_receipt_ok"])
        self.assertTrue(result["validation"]["memory_glimpse_source_bound"])
        self.assertTrue(result["validation"]["memory_glimpse_witness_bound"])
        self.assertFalse(result["memory_glimpse_receipt"]["memory_source"]["raw_memory_payload_stored"])
        self.assertFalse(
            result["memory_glimpse_receipt"]["disclosure_binding"][
                "raw_message_payload_stored"
            ]
        )
        self.assertTrue(result["validation"]["merge_thought_ethics_receipt_ok"])
        self.assertTrue(result["validation"]["merge_thought_ethics_gate_bound"])
        self.assertTrue(
            result["validation"]["merge_thought_ethics_window_policy_authority_bound"]
        )
        self.assertTrue(
            result["validation"]["merge_thought_ethics_window_policy_live_verifier_bound"]
        )
        self.assertTrue(
            result["validation"]["merge_thought_ethics_window_policy_timeout_bound"]
        )
        self.assertFalse(
            result["validation"]["merge_thought_ethics_raw_window_policy_verifier_payload_stored"]
        )
        self.assertFalse(
            result["merge_thought_ethics_receipt"]["disclosure_binding"][
                "raw_thought_payload_stored"
            ]
        )
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
        self.assertTrue(result["validation"]["dissolution_receipt_bound"])
        self.assertTrue(result["validation"]["dissolution_member_confirmations_bound"])
        self.assertTrue(result["validation"]["dissolution_member_recovery_proofs_bound"])
        self.assertTrue(result["validation"]["dissolution_member_recovery_binding_digest_bound"])
        self.assertFalse(result["validation"]["dissolution_raw_identity_confirmation_profiles_stored"])
        self.assertTrue(result["validation"]["member_recovery_identity_confirmation_profiles_ok"])
        self.assertTrue(result["validation"]["recovery_verifier_transport_bound"])
        self.assertTrue(result["validation"]["recovery_verifier_transport_profile_bound"])
        self.assertTrue(
            result["validation"]["recovery_verifier_transport_dissolution_digest_bound"]
        )
        self.assertTrue(result["validation"]["recovery_verifier_transport_all_receipts_verified"])
        self.assertFalse(result["validation"]["recovery_verifier_transport_raw_payload_stored"])
        self.assertTrue(result["validation"]["recovery_route_trace_bound"])
        self.assertTrue(result["validation"]["recovery_route_trace_profile_bound"])
        self.assertTrue(result["validation"]["recovery_route_trace_authority_trace_bound"])
        self.assertTrue(result["validation"]["recovery_route_trace_member_bindings_bound"])
        self.assertFalse(result["validation"]["recovery_route_trace_raw_payload_stored"])
        self.assertTrue(result["validation"]["recovery_capture_export_bound"])
        self.assertTrue(result["validation"]["recovery_capture_export_packet_capture_bound"])
        self.assertTrue(result["validation"]["recovery_capture_export_privileged_capture_bound"])
        self.assertTrue(result["validation"]["recovery_capture_export_member_bindings_bound"])
        self.assertFalse(result["validation"]["recovery_capture_export_raw_packet_body_stored"])
        self.assertTrue(result["validation"]["external_registry_sync_bound"])
        self.assertTrue(result["validation"]["external_registry_sync_capture_export_bound"])
        self.assertTrue(result["validation"]["external_registry_sync_legal_registry_bound"])
        self.assertTrue(result["validation"]["external_registry_sync_governance_registry_bound"])
        self.assertTrue(result["validation"]["external_registry_sync_submission_ack_bound"])
        self.assertTrue(result["validation"]["external_registry_sync_ack_quorum_bound"])
        self.assertTrue(result["validation"]["external_registry_sync_ack_route_trace_bound"])
        self.assertTrue(
            result["validation"]["external_registry_sync_ack_route_packet_capture_bound"]
        )
        self.assertTrue(
            result["validation"]["external_registry_sync_ack_route_privileged_capture_bound"]
        )
        self.assertTrue(
            result["validation"]["external_registry_sync_ack_route_capture_bindings_bound"]
        )
        self.assertTrue(
            result["validation"]["external_registry_sync_ack_route_capture_export_bound"]
        )
        self.assertTrue(
            result["validation"]["external_registry_sync_ack_live_endpoint_probe_bound"]
        )
        self.assertTrue(
            result["validation"][
                "external_registry_sync_ack_live_endpoint_signed_response_envelope_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "external_registry_sync_ack_live_endpoint_mtls_client_certificate_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "external_registry_sync_ack_live_endpoint_mtls_client_certificate_freshness_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "external_registry_sync_ack_live_endpoint_mtls_client_certificate_lifecycle_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "external_registry_sync_ack_live_endpoint_mtls_client_certificate_lifecycle_chain_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "external_registry_sync_ack_live_endpoint_mtls_client_certificate_ct_log_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "external_registry_sync_ack_live_endpoint_mtls_client_certificate_ct_log_quorum_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "external_registry_sync_ack_live_endpoint_mtls_client_certificate_sct_policy_authority_bound"
            ]
        )
        self.assertFalse(
            result["validation"]["external_registry_sync_raw_registry_payload_stored"]
        )
        self.assertFalse(result["validation"]["external_registry_sync_raw_ack_payload_stored"])
        self.assertFalse(
            result["validation"]["external_registry_sync_raw_ack_route_payload_stored"]
        )
        self.assertFalse(
            result["validation"]["external_registry_sync_raw_ack_endpoint_payload_stored"]
        )
        self.assertFalse(
            result["validation"][
                "external_registry_sync_raw_response_signature_payload_stored"
            ]
        )
        self.assertFalse(
            result["validation"][
                "external_registry_sync_raw_client_certificate_payload_stored"
            ]
        )
        self.assertFalse(
            result["validation"][
                "external_registry_sync_raw_client_certificate_freshness_payload_stored"
            ]
        )
        self.assertFalse(
            result["validation"][
                "external_registry_sync_raw_client_certificate_lifecycle_payload_stored"
            ]
        )
        self.assertFalse(
            result["validation"][
                "external_registry_sync_raw_client_certificate_lifecycle_chain_payload_stored"
            ]
        )
        self.assertFalse(
            result["validation"][
                "external_registry_sync_raw_client_certificate_ct_log_payload_stored"
            ]
        )
        self.assertFalse(
            result["validation"][
                "external_registry_sync_raw_sct_policy_authority_payload_stored"
            ]
        )
        self.assertFalse(
            result["validation"]["external_registry_sync_raw_packet_body_stored"]
        )
        self.assertEqual(2, len(result["external_registry_ack_endpoint_probes"]))
        self.assertEqual("dissolved", result["collective"]["status"])
        self.assertEqual("1.0", result["dissolution"]["schema_version"])
        self.assertEqual(
            "collective-dissolution-identity-confirmation-binding-v1",
            result["dissolution"]["member_recovery_binding_profile"],
        )
        self.assertEqual("merge_thought", result["merge"]["merge_mode"])
        self.assertEqual("private_reality", result["wms"]["escape"]["new_mode"])

    def test_wms_demo_emits_reversible_physics_rules_change(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "wms-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["minor_reconciled"])
        self.assertTrue(result["validation"]["major_escape_offered"])
        self.assertTrue(result["validation"]["time_rate_deviation_escape_bound"])
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
        self.assertTrue(result["validation"]["remote_authority_slo_probe_quorum_bound"])
        self.assertTrue(
            result["validation"][
                "remote_authority_slo_quorum_threshold_policy_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["remote_authority_slo_quorum_threshold_policy"][
                "signer_roster_verifier_quorum_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["remote_authority_slo_quorum_threshold_policy"][
                "revocation_registry_bound"
            ]
        )
        self.assertTrue(result["validation"]["remote_authority_retry_budget_bound"])
        self.assertTrue(result["validation"]["static_approval_without_transport_rejected"])
        self.assertEqual("applied", result["scenarios"]["physics_change"]["decision"])
        self.assertEqual(3, len(result["scenarios"]["approval_transport_receipts"]))
        self.assertEqual(2, result["scenarios"]["approval_collection_receipt"]["batch_count"])
        self.assertEqual("complete", result["scenarios"]["approval_fanout_receipt"]["fanout_status"])
        self.assertEqual("recovered", result["scenarios"]["approval_fanout_receipt"]["partial_outage_status"])
        self.assertEqual("complete", result["scenarios"]["engine_transaction_log"]["engine_binding_status"])
        self.assertTrue(
            result["scenarios"]["engine_transaction_log"][
                "engine_adapter_signature_bound"
            ]
        )
        self.assertFalse(
            result["scenarios"]["engine_transaction_log"][
                "raw_adapter_signature_stored"
            ]
        )
        self.assertEqual("complete", result["scenarios"]["engine_route_binding"]["engine_route_binding_status"])
        self.assertEqual("complete", result["scenarios"]["engine_capture_binding"]["engine_capture_binding_status"])
        self.assertFalse(result["scenarios"]["engine_capture_binding"]["raw_packet_body_stored"])
        self.assertEqual("complete", result["scenarios"]["remote_authority_retry_budget"]["budget_status"])
        self.assertEqual(
            "signed-jurisdiction-rate-limit-retry-budget-v1",
            result["scenarios"]["remote_authority_retry_budget"]["signature_policy_id"],
        )
        self.assertEqual(
            ["JP-13"],
            result["scenarios"]["remote_authority_retry_budget"]["remote_jurisdictions"],
        )
        self.assertTrue(
            result["scenarios"]["remote_authority_retry_budget"][
                "signed_jurisdiction_retry_budget_bound"
            ]
        )
        self.assertTrue(
            result["scenarios"]["remote_authority_retry_budget"][
                "registry_bound_retry_budget_bound"
            ]
        )
        self.assertTrue(
            result["scenarios"]["remote_authority_retry_budget"][
                "registry_slo_schedule_bound"
            ]
        )
        self.assertTrue(
            result["scenarios"]["remote_authority_retry_budget"][
                "authority_slo_live_probe_bound"
            ]
        )
        self.assertEqual(
            [result["scenarios"]["remote_authority_slo_probe_receipt"]["digest"]],
            result["scenarios"]["remote_authority_retry_budget"][
                "authority_slo_probe_digests"
            ],
        )
        self.assertTrue(
            result["scenarios"]["remote_authority_slo_probe_receipt"][
                "network_probe_bound"
            ]
        )
        self.assertEqual(
            "complete",
            result["scenarios"]["remote_authority_slo_probe_quorum_receipt"][
                "quorum_status"
            ],
        )
        self.assertEqual(
            2,
            result["scenarios"]["remote_authority_slo_probe_quorum_receipt"][
                "accepted_authority_count"
            ],
        )
        self.assertEqual(
            result["scenarios"]["remote_authority_slo_probe_receipt"]["digest"],
            result["scenarios"]["remote_authority_slo_probe_quorum_receipt"][
                "primary_probe_digest"
            ],
        )
        self.assertTrue(
            result["scenarios"]["remote_authority_slo_probe_quorum_receipt"][
                "threshold_policy_signature_bound"
            ]
        )
        self.assertTrue(
            result["scenarios"]["remote_authority_slo_probe_quorum_receipt"][
                "threshold_signer_roster_verifier_quorum_bound"
            ]
        )
        self.assertTrue(
            result["scenarios"]["remote_authority_slo_probe_quorum_receipt"][
                "threshold_revocation_registry_bound"
            ]
        )
        self.assertEqual(
            result["scenarios"]["remote_authority_slo_quorum_threshold_policy"][
                "digest"
            ],
            result["scenarios"]["remote_authority_slo_probe_quorum_receipt"][
                "threshold_policy_digest"
            ],
        )
        self.assertFalse(
            result["scenarios"]["remote_authority_retry_budget"]["raw_remote_transcript_stored"]
        )
        self.assertEqual("offer-private-reality", result["scenarios"]["time_rate_deviation"]["decision"])
        self.assertTrue(result["scenarios"]["time_rate_deviation"]["time_rate_deviation_detected"])
        self.assertEqual("reverted", result["scenarios"]["physics_revert"]["decision"])
        self.assertEqual(
            result["scenarios"]["physics_change"]["change_id"],
            result["scenarios"]["physics_revert"]["revert_of_change_id"],
        )
        self.assertEqual(
            result["initial_state"]["physics_rules_ref"],
            result["final_state"]["physics_rules_ref"],
        )

    def test_ewa_demo_emits_vetoed_irreversible_command(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "ewa-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["motor_plan_ok"])
        self.assertTrue(result["validation"]["motor_plan_bound"])
        self.assertTrue(result["validation"]["stop_signal_path_ok"])
        self.assertTrue(result["validation"]["stop_signal_path_bound"])
        self.assertTrue(result["validation"]["stop_signal_adapter_receipt_ok"])
        self.assertTrue(result["validation"]["stop_signal_adapter_receipt_bound"])
        self.assertTrue(result["validation"]["production_connector_attestation_ok"])
        self.assertTrue(result["validation"]["production_connector_attestation_bound"])
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
        self.assertTrue(
            result["validation"]["authorization_production_connector_attestation_ready"]
        )
        self.assertTrue(result["validation"]["authorization_guardian_oversight_gate_ready"])
        self.assertEqual("physical-device-actuation", result["validation"]["authorization_delivery_scope"])
        self.assertEqual("executed", result["approved_command"]["status"])
        self.assertEqual(result["motor_plan"]["plan_id"], result["approved_command"]["motor_plan_id"])
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
        self.assertTrue(
            result["validation"]["approved_command_production_connector_attestation_bound"]
        )
        self.assertTrue(result["validation"]["approved_command_legal_execution_bound"])
        self.assertTrue(result["validation"]["emergency_stop_ok"])
        self.assertTrue(result["validation"]["emergency_stop_latched"])
        self.assertTrue(result["validation"]["emergency_stop_bus_delivery_latched"])
        self.assertTrue(result["validation"]["emergency_stop_bound_to_command"])
        self.assertTrue(result["validation"]["emergency_stop_bound_to_authorization"])
        self.assertTrue(result["validation"]["emergency_stop_bound_to_stop_signal_path"])
        self.assertTrue(result["validation"]["emergency_stop_bound_to_stop_signal_adapter_receipt"])
        self.assertTrue(
            result["validation"]["emergency_stop_bound_to_production_connector_attestation"]
        )
        self.assertTrue(result["validation"]["release_after_stop"])
        self.assertEqual("vetoed", result["veto"]["status"])
        self.assertIn("harm.human", result["veto"]["matched_tokens"])
        self.assertEqual(
            result["stop_signal_path"]["path_id"],
            result["emergency_stop"]["stop_signal_path_id"],
        )
        self.assertEqual(
            result["authorization"]["authorization_id"],
            result["approved_command"]["approval_path"]["authorization_id"],
        )
        self.assertEqual("watchdog-timeout", result["emergency_stop"]["trigger_source"])
        self.assertEqual("released", result["release"]["status"])
        self.assertEqual("released", result["veto_release"]["status"])
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
        self.assertEqual(
            1,
            result["ledger_verification"]["category_counts"]["interface-ewa-production-connector"],
        )
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["guardian-oversight"])
        self.assertEqual(6, result["ledger_verification"]["category_counts"]["interface-ewa"])
        self.assertEqual(1, result["ledger_verification"]["category_counts"]["interface-ewa-veto"])
        self.assertEqual(
            1,
            result["ledger_verification"]["category_counts"]["interface-ewa-emergency-stop"],
        )

    def test_sensory_loopback_demo_emits_guardian_hold_and_recovery(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "sensory-loopback-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual("delivered", result["receipts"]["coherent"]["delivery_status"])
        self.assertEqual("guardian-hold", result["receipts"]["degraded"]["delivery_status"])
        self.assertEqual("stabilized", result["receipts"]["stabilized"]["delivery_status"])
        self.assertTrue(result["validation"]["body_map_bound"])
        self.assertTrue(result["validation"]["proprioceptive_calibration_bound"])
        self.assertTrue(result["validation"]["alignment_ref_bound"])
        self.assertTrue(result["validation"]["artifact_family_ok"])
        self.assertTrue(result["validation"]["shared_loopback_ok"])
        self.assertTrue(result["validation"]["shared_loopback_collective_bound"])
        self.assertTrue(result["validation"]["shared_loopback_imc_bound"])
        self.assertTrue(result["validation"]["shared_loopback_participants_bound"])
        self.assertTrue(result["validation"]["shared_loopback_arbitrated"])
        self.assertTrue(result["validation"]["shared_loopback_owner_handoff"])
        self.assertTrue(result["validation"]["shared_loopback_family_tracked"])
        self.assertEqual(3, result["artifact_family"]["scene_count"])
        self.assertEqual(2, result["artifact_family"]["guardian_intervention_count"])
        self.assertEqual("active", result["session"]["status"])
        self.assertEqual("collective-shared", result["shared_loopback"]["session"]["shared_space_mode"])
        self.assertEqual(
            "guardian-mediated",
            result["shared_loopback"]["receipts"]["mediated"]["arbitration_status"],
        )
        self.assertEqual(2, result["shared_loopback"]["artifact_family"]["scene_count"])
        self.assertEqual(1, result["shared_loopback"]["artifact_family"]["guardian_arbitration_count"])

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

    def test_memory_replication_demo_emits_quorum_json(self) -> None:
        stdout = io.StringIO()

        with patch(
            "sys.argv",
            ["omoikane", "memory-replication-demo", "--json"],
        ), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["manifest"]["ok"])
        self.assertTrue(result["validation"]["replication"]["ok"])
        self.assertTrue(result["validation"]["consensus_quorum_ok"])
        self.assertTrue(result["validation"]["resync_required"])
        self.assertTrue(result["validation"]["key_succession_bound"])
        self.assertTrue(result["validation"]["key_succession_guardian_quorum_ok"])
        self.assertTrue(result["validation"]["key_succession_threshold_ok"])
        self.assertTrue(
            result["validation"]["key_succession_signer_roster_policy_bound"]
        )
        self.assertTrue(result["validation"]["key_succession_signer_roster_quorum_ok"])
        self.assertTrue(
            result["validation"][
                "key_succession_multi_jurisdiction_signer_roster_quorum_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "key_succession_multi_jurisdiction_signer_roster_quorum_ok"
            ]
        )
        self.assertTrue(result["validation"]["key_succession_quorum_threshold_policy_bound"])
        self.assertTrue(result["validation"]["key_succession_quorum_threshold_policy_ok"])
        self.assertTrue(result["validation"]["long_term_media_renewal_bound"])
        self.assertEqual(
            ["coldstore", "trustee"],
            result["validation"]["long_term_media_renewal_targets"],
        )
        self.assertTrue(result["validation"]["long_term_media_renewal_readback_ok"])
        self.assertEqual(3650, result["validation"]["long_term_media_renewal_refresh_interval_days"])
        self.assertEqual(1000, result["validation"]["long_term_media_renewal_target_horizon_years"])
        self.assertTrue(result["validation"]["long_term_media_renewal_cadence_policy_bound"])
        self.assertEqual(
            3650,
            result["validation"][
                "long_term_media_renewal_cadence_effective_refresh_interval_days"
            ],
        )
        self.assertTrue(result["validation"]["long_term_media_renewal_refresh_window_bound"])
        self.assertTrue(result["validation"]["long_term_media_renewal_source_proof_current"])
        self.assertTrue(result["validation"]["long_term_media_renewal_revocation_check_ok"])
        self.assertEqual(
            90,
            result["validation"]["long_term_media_renewal_revocation_check_window_days"],
        )
        self.assertTrue(
            result["validation"]["long_term_media_renewal_registry_verifier_bound"]
        )
        self.assertTrue(
            result["validation"][
                "long_term_media_renewal_registry_verifier_quorum_ok"
            ]
        )
        self.assertTrue(
            result["validation"][
                "long_term_media_renewal_registry_endpoint_certificate_lifecycle_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "long_term_media_renewal_registry_endpoint_certificate_freshness_ok"
            ]
        )
        self.assertTrue(
            result["validation"][
                "long_term_media_renewal_registry_endpoint_certificate_quorum_ok"
            ]
        )
        self.assertTrue(
            result["validation"][
                "long_term_media_renewal_registry_endpoint_certificate_ct_log_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "long_term_media_renewal_registry_endpoint_certificate_ct_log_quorum_ok"
            ]
        )
        self.assertTrue(
            result["validation"][
                "long_term_media_renewal_registry_endpoint_certificate_sct_policy_authority_bound"
            ]
        )
        self.assertEqual(
            3,
            result["validation"][
                "long_term_media_renewal_registry_endpoint_certificate_chain_generation_count"
            ],
        )
        self.assertFalse(result["validation"]["replication"]["raw_key_material_stored"])
        self.assertFalse(result["validation"]["replication"]["raw_shard_material_stored"])
        self.assertFalse(result["validation"]["raw_signer_roster_payload_stored"])
        self.assertFalse(result["validation"]["raw_jurisdiction_policy_payload_stored"])
        self.assertFalse(result["validation"]["raw_quorum_threshold_policy_payload_stored"])
        self.assertFalse(result["validation"]["raw_media_payload_stored"])
        self.assertFalse(result["validation"]["raw_media_readback_payload_stored"])
        self.assertFalse(result["validation"]["raw_media_cadence_payload_stored"])
        self.assertFalse(result["validation"]["raw_media_revocation_payload_stored"])
        self.assertFalse(result["validation"]["raw_media_refresh_payload_stored"])
        self.assertFalse(result["validation"]["raw_media_registry_payload_stored"])
        self.assertFalse(
            result["validation"]["raw_media_registry_response_payload_stored"]
        )
        self.assertFalse(
            result["validation"][
                "raw_media_registry_endpoint_certificate_payload_stored"
            ]
        )
        self.assertFalse(
            result["validation"][
                "raw_media_registry_endpoint_certificate_freshness_payload_stored"
            ]
        )
        self.assertFalse(
            result["validation"][
                "raw_media_registry_endpoint_certificate_lifecycle_payload_stored"
            ]
        )
        self.assertFalse(
            result["validation"][
                "raw_media_registry_endpoint_certificate_ct_log_payload_stored"
            ]
        )
        self.assertFalse(
            result["validation"][
                "raw_media_registry_endpoint_certificate_sct_policy_authority_payload_stored"
            ]
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
            "successor-key-prepared",
            result["memory_replication"]["session"]["key_succession"]["status"],
        )
        self.assertEqual(
            "complete",
            result["memory_replication"]["session"]["key_succession"][
                "signer_roster_policy"
            ]["quorum_status"],
        )
        self.assertEqual(
            "complete",
            result["memory_replication"]["session"]["key_succession"][
                "signer_roster_quorum"
            ]["quorum_status"],
        )
        self.assertEqual(
            "complete",
            result["memory_replication"]["session"]["key_succession"][
                "signer_roster_quorum"
            ]["threshold_policy_authority"]["quorum_status"],
        )
        self.assertTrue(
            result["memory_replication"]["session"]["key_succession"][
                "signer_roster_quorum"
            ]["threshold_policy_authority"]["threshold_policy_registry_bound"]
        )
        self.assertEqual(
            "long-term-media-renewal-proof-v1",
            result["memory_replication"]["session"]["long_term_media_renewal"][
                "policy_id"
            ],
        )
        self.assertEqual(
            ["coldstore", "trustee"],
            result["memory_replication"]["session"]["long_term_media_renewal"][
                "renewal_target_ids"
            ],
        )
        self.assertEqual(
            "long-term-media-renewal-refresh-window-v1",
            result["memory_replication"]["session"]["long_term_media_renewal"][
                "refresh_window"
            ]["policy_id"],
        )
        self.assertEqual(
            "long-term-media-renewal-cadence-policy-v1",
            result["memory_replication"]["session"]["long_term_media_renewal"][
                "cadence_policy"
            ]["policy_id"],
        )
        self.assertEqual(
            result["memory_replication"]["session"]["long_term_media_renewal"][
                "cadence_policy"
            ]["cadence_commit_digest"],
            result["memory_replication"]["session"]["long_term_media_renewal"][
                "refresh_window"
            ]["cadence_policy_digest"],
        )
        self.assertEqual(
            "current-not-revoked",
            result["memory_replication"]["session"]["long_term_media_renewal"][
                "refresh_window"
            ]["source_proof_status"],
        )
        self.assertEqual(
            "long-term-media-renewal-registry-verifier-v1",
            result["memory_replication"]["session"]["long_term_media_renewal"][
                "refresh_window"
            ]["registry_verifier"]["policy_id"],
        )
        self.assertEqual(
            ["JP-13", "SG-01"],
            result["memory_replication"]["session"]["long_term_media_renewal"][
                "refresh_window"
            ]["registry_verifier"]["registry_jurisdictions"],
        )
        self.assertEqual(
            ["JP-13", "SG-01"],
            result["memory_replication"]["session"]["key_succession"][
                "signer_roster_quorum"
            ]["accepted_jurisdictions"],
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
        self.assertTrue(result["validation"]["connectome"]["ok"])
        self.assertTrue(result["validation"]["semantic"]["ok"])
        self.assertTrue(result["validation"]["procedural_handoff"]["ok"])
        self.assertEqual(2, result["validation"]["semantic"]["concept_count"])
        self.assertEqual(
            ["council-review", "migration-check"],
            result["validation"]["semantic"]["labels"],
        )
        self.assertEqual(
            ["procedural-memory"],
            result["semantic"]["snapshot"]["deferred_surfaces"],
        )
        self.assertEqual("ready", result["semantic"]["procedural_handoff"]["status"])

    def test_procedural_demo_emits_valid_preview_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "procedural-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["semantic_handoff"]["ok"])
        self.assertTrue(result["validation"]["handoff_matches_preview_policy"])
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
        self.assertEqual("ready", result["procedural"]["semantic_handoff"]["status"])

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
        self.assertTrue(result["validation"]["enactment"]["mandatory_eval_bound"])
        self.assertTrue(result["validation"]["enactment"]["command_eval_refs_bound"])
        self.assertEqual("passed", result["procedural"]["skill_enactment_session"]["status"])

    def test_procedural_actuation_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "procedural-actuation-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["bridge"]["ok"])
        self.assertTrue(result["validation"]["bridge"]["command_bound_to_authorization"])
        self.assertTrue(result["validation"]["bridge"]["authorization_digest_bound"])
        self.assertTrue(result["validation"]["bridge"]["stop_signal_adapter_receipt_bound"])
        self.assertTrue(result["validation"]["bridge"]["production_connector_attestation_bound"])
        self.assertTrue(
            result["validation"]["authorization"]["production_connector_attestation_bound"]
        )
        self.assertTrue(result["validation"]["authorization"]["stop_signal_adapter_receipt_bound"])
        self.assertEqual(
            "physical-device-actuation",
            result["validation"]["bridge"]["delivery_scope"],
        )
        self.assertEqual(
            result["ewa"]["stop_signal_adapter_receipt"]["receipt_id"],
            result["procedural"]["actuation_bridge_session"]["command_binding"][
                "stop_signal_adapter_receipt_id"
            ],
        )
        self.assertEqual(
            result["ewa"]["production_connector_attestation"]["attestation_id"],
            result["procedural"]["actuation_bridge_session"]["command_binding"][
                "production_connector_attestation_id"
            ],
        )
        self.assertEqual(
            "bridged",
            result["procedural"]["actuation_bridge_session"]["status"],
        )

    def test_design_reader_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "design-reader-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
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
        self.assertTrue(result["validation"]["build_request_has_design_delta_ref"])
        self.assertTrue(result["validation"]["build_request_has_design_delta_digest"])
        self.assertEqual(7, result["validation"]["output_path_count"])

    def test_patch_generator_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "patch-generator-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["ready_scope_allowed"])
        self.assertEqual("ready", result["validation"]["ready_artifact_status"])
        self.assertEqual(5, result["validation"]["ready_patch_count"])
        self.assertEqual("blocked", result["validation"]["blocked_artifact_status"])
        self.assertTrue(result["validation"]["blocked_rule_mentions_scope_escape"])
        self.assertTrue(result["validation"]["blocked_rule_mentions_planning_cues"])
        self.assertTrue(result["validation"]["blocked_rule_mentions_immutable_boundary"])
        self.assertGreaterEqual(result["validation"]["blocked_rule_count"], 3)

    def test_diff_eval_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "diff-eval-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual(2, result["validation"]["selected_eval_count"])
        self.assertEqual(
            [
                "evals/continuity/council_output_build_request_pipeline.yaml",
                "evals/continuity/differential_eval_execution_binding.yaml",
            ],
            result["validation"]["selected_evals"],
        )
        self.assertTrue(result["validation"]["execution_eval_selected"])
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

    def test_builder_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "builder-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["design_reader_handoff_ok"])
        self.assertEqual("ready", result["validation"]["design_manifest_status"])
        self.assertEqual(16, result["validation"]["design_source_digest_count"])
        self.assertEqual(3, result["validation"]["must_sync_docs_count"])
        self.assertTrue(result["validation"]["scope_allowed"])
        self.assertEqual(5, result["validation"]["patch_count"])
        self.assertEqual("applied", result["validation"]["sandbox_apply_status"])
        self.assertTrue(result["validation"]["eval_execution_ok"])
        self.assertEqual("passed", result["validation"]["eval_execution_status"])
        self.assertEqual(2, result["validation"]["eval_execution_command_count"])
        self.assertEqual("removed", result["validation"]["eval_execution_cleanup_status"])
        self.assertEqual("promote", result["validation"]["rollout_decision"])
        self.assertEqual("promoted", result["validation"]["rollout_status"])
        self.assertEqual(4, result["validation"]["rollout_completed_stage_count"])
        self.assertTrue(result["validation"]["eval_report_evidence_bound"])
        self.assertTrue(result["validation"]["eval_execution_evidence_bound"])
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
        self.assertEqual(
            "emit_build_request",
            result["builder"]["council_output"]["approved_action"],
        )
        self.assertTrue(result["builder"]["build_request"]["design_delta_ref"].startswith("design://"))
        self.assertEqual("passed", result["builder"]["eval_execution_session"]["status"])
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
        self.assertTrue(
            result["builder"]["enactment_session"]["oversight_gate"]["reviewer_network_attested"]
        )
        self.assertEqual("eval-regression", result["validation"]["rollback_trigger"])
        self.assertEqual(6, result["validation"]["selected_eval_count"])
        self.assertTrue(result["validation"]["eval_report_evidence_bound"])
        self.assertTrue(result["validation"]["eval_execution_evidence_bound"])
        self.assertEqual(2, result["validation"]["eval_execution_command_count"])
        self.assertEqual("removed", result["validation"]["eval_execution_cleanup_status"])
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
        self.assertEqual(
            "mirage://build-l5-rollback-0001/snapshot/pre-apply",
            result["validation"]["restored_snapshot_ref"],
        )
        rollback_report = next(
            report
            for report in result["builder"]["eval_reports"]
            if report["eval_ref"] == "evals/continuity/builder_rollback_execution.yaml"
        )
        self.assertEqual("builder-rollback-trigger-evidence-v1", rollback_report["profile_id"])
        self.assertEqual("regression", rollback_report["outcome"])
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
        self.assertTrue(result["validation"]["standby_probe_ready"])
        self.assertTrue(result["validation"]["attestation_chain_ready"])
        self.assertTrue(result["validation"]["attestation_chain_cross_host_verified"])
        self.assertTrue(result["validation"]["dual_allocation_window_opened"])
        self.assertTrue(result["validation"]["dual_allocation_cross_host_verified"])
        self.assertTrue(result["validation"]["attestation_stream_ready"])
        self.assertTrue(result["validation"]["attestation_stream_window_complete"])
        self.assertTrue(result["validation"]["attestation_stream_cross_host_verified"])
        self.assertTrue(result["validation"]["dual_allocation_closed"])
        self.assertTrue(result["validation"]["dual_allocation_cleanup_released"])
        self.assertTrue(result["validation"]["migration_binds_selected_standby"])
        self.assertEqual("critical", result["broker"]["energy_floor_signal"]["severity"])
        self.assertEqual(
            result["broker"]["selection"]["standby_substrate"]["substrate_id"],
            result["broker"]["migration"]["destination_substrate"],
        )
        self.assertEqual("ready", result["broker"]["standby_probe"]["probe_status"])
        self.assertEqual("handoff-ready", result["broker"]["attestation_chain"]["chain_status"])
        self.assertEqual("shadow-active", result["broker"]["dual_allocation_window"]["window_status"])
        self.assertEqual("sealed-handoff-ready", result["broker"]["attestation_stream"]["stream_status"])
        self.assertTrue(result["broker"]["migration"]["cross_host_verified"])
        self.assertEqual("closed", result["broker"]["closed_dual_allocation_window"]["window_status"])
        self.assertEqual("hot-handoff", result["broker"]["migration"]["continuity_mode"])
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
        self.assertTrue(result["validation"]["calibration"]["ok"])
        self.assertEqual(
            "self-model-advisory-calibration-boundary-v1",
            result["calibration"]["policy_id"],
        )
        self.assertFalse(result["calibration"]["accepted_for_writeback"])
        self.assertEqual(
            "self-model-pathology-escalation-boundary-v1",
            result["pathology_escalation"]["policy_id"],
        )
        self.assertTrue(result["validation"]["pathology_escalation"]["care_handoff_required"])
        self.assertEqual(
            "self-model-care-trustee-responsibility-handoff-v1",
            result["care_trustee_handoff"]["policy_id"],
        )
        self.assertTrue(result["validation"]["care_trustee_handoff"]["long_term_review_required"])
        self.assertTrue(
            result["validation"]["care_trustee_handoff"][
                "responsibility_commit_digest_bound"
            ]
        )
        self.assertFalse(result["care_trustee_handoff"]["os_trustee_role_allowed"])
        self.assertFalse(result["care_trustee_handoff"]["raw_trustee_payload_stored"])
        self.assertEqual(
            "self-model-care-trustee-registry-binding-v1",
            result["care_trustee_registry_binding"]["policy_id"],
        )
        self.assertTrue(
            result["validation"]["care_trustee_registry_binding"][
                "external_registry_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["care_trustee_registry_binding"][
                "registry_binding_digest_bound"
            ]
        )
        self.assertFalse(
            result["care_trustee_registry_binding"]["raw_registry_payload_stored"]
        )
        self.assertFalse(
            result["care_trustee_registry_binding"]["os_trustee_role_allowed"]
        )
        self.assertEqual(
            "self-model-external-adjudication-live-verifier-network-v1",
            result["external_adjudication_verifier"]["policy_id"],
        )
        self.assertEqual(
            "complete",
            result["validation"]["external_adjudication_verifier"][
                "verifier_quorum_status"
            ],
        )
        self.assertTrue(
            result["validation"]["external_adjudication_verifier"][
                "appeal_review_live_verifier_bound"
            ]
        )
        self.assertFalse(
            result["external_adjudication_verifier"]["stale_response_accepted"]
        )
        self.assertFalse(
            result["external_adjudication_verifier"]["raw_verifier_payload_stored"]
        )
        self.assertEqual(
            "self-model-self-authored-value-generation-v1",
            result["value_generation"]["policy_id"],
        )
        self.assertTrue(result["validation"]["value_generation"]["self_authored"])
        self.assertFalse(result["value_generation"]["external_veto_allowed"])
        self.assertFalse(result["value_generation"]["accepted_for_writeback"])
        self.assertEqual(
            "self-model-future-self-acceptance-writeback-v1",
            result["value_acceptance"]["policy_id"],
        )
        self.assertTrue(result["validation"]["value_acceptance"]["future_self_acceptance_satisfied"])
        self.assertTrue(result["validation"]["value_acceptance"]["accepted_for_writeback"])
        self.assertTrue(result["validation"]["value_acceptance"]["writeback_digest_bound"])
        self.assertFalse(result["value_acceptance"]["external_veto_allowed"])
        self.assertFalse(result["value_acceptance"]["raw_value_payload_stored"])
        self.assertEqual(
            "self-model-future-self-reevaluation-retirement-v1",
            result["value_reassessment"]["policy_id"],
        )
        self.assertTrue(
            result["validation"]["value_reassessment"][
                "future_self_reevaluation_satisfied"
            ]
        )
        self.assertTrue(result["validation"]["value_reassessment"]["active_writeback_retired"])
        self.assertTrue(result["validation"]["value_reassessment"]["retirement_digest_bound"])
        self.assertTrue(result["value_reassessment"]["historical_value_archived"])
        self.assertFalse(result["value_reassessment"]["external_veto_allowed"])
        self.assertFalse(result["value_reassessment"]["raw_value_payload_stored"])
        self.assertEqual(
            "self-model-value-lineage-timeline-v1",
            result["value_timeline"]["policy_id"],
        )
        self.assertTrue(result["validation"]["value_timeline"]["active_retired_disjoint"])
        self.assertTrue(result["validation"]["value_timeline"]["archive_retention_required"])
        self.assertTrue(result["validation"]["value_timeline"]["timeline_commit_digest_bound"])
        self.assertFalse(result["value_timeline"]["external_veto_allowed"])
        self.assertFalse(result["value_timeline"]["raw_value_payload_stored"])
        self.assertEqual(
            "self-model-value-archive-retention-proof-v1",
            result["value_archive_retention_proof"]["policy_id"],
        )
        self.assertTrue(
            result["validation"]["value_archive_retention_proof"][
                "timeline_archive_retention_verified"
            ]
        )
        self.assertTrue(
            result["validation"]["value_archive_retention_proof"][
                "retention_commit_digest_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["value_archive_retention_proof"]["trustee_proof_bound"]
        )
        self.assertFalse(
            result["value_archive_retention_proof"]["archive_deletion_allowed"]
        )
        self.assertFalse(
            result["value_archive_retention_proof"]["raw_archive_payload_stored"]
        )
        self.assertEqual(
            "self-model-value-archive-retention-refresh-window-v1",
            result["value_archive_retention_refresh"]["policy_id"],
        )
        self.assertTrue(
            result["validation"]["value_archive_retention_refresh"][
                "refresh_commit_digest_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["value_archive_retention_refresh"][
                "revocation_check_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["value_archive_retention_refresh"]["expiry_fail_closed"]
        )
        self.assertFalse(
            result["value_archive_retention_refresh"]["source_proof_revoked"]
        )
        self.assertFalse(
            result["value_archive_retention_refresh"]["raw_revocation_payload_stored"]
        )

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

    def test_perception_demo_emits_qualia_bound_safe_scene_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "perception-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["baseline_primary"])
        self.assertEqual("continuity_projection_v1", result["validation"]["selected_backend"])
        self.assertTrue(result["validation"]["guard_aligned"])
        self.assertTrue(result["validation"]["safe_scene_selected"])
        self.assertTrue(result["validation"]["qualia_bound"])
        self.assertEqual("guardian-review-scene", result["perception"]["frame"]["scene_label"])
        self.assertEqual("guardian-review", result["validation"]["perception_gate"])
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
        self.assertTrue(result["public_verification_validation"]["ok"])
        self.assertTrue(result["public_verification_bundle"]["public_verification_ready"])
        self.assertEqual(
            "continuity-public-verification-key-management-v1",
            result["public_verification_bundle"]["profile_id"],
        )

    def test_identity_demo_emits_pause_resume_contract_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "identity-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
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
        self.assertEqual(4, result["ledger_verification"]["category_counts"]["identity-lifecycle"])

    def test_identity_confirmation_demo_emits_profile_json(self) -> None:
        stdout = io.StringIO()

        with patch(
            "sys.argv",
            ["omoikane", "identity-confirmation-demo", "--json"],
        ), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["validation"]["subjective_self_report_bound"])
        self.assertTrue(result["validation"]["third_party_witness_quorum_met"])
        self.assertTrue(result["validation"]["self_report_witness_consistency_bound"])
        self.assertTrue(result["validation"]["consistency_digest_bound"])
        self.assertTrue(result["validation"]["witness_registry_binding_bound"])
        self.assertTrue(result["validation"]["registry_binding_digest_bound"])
        self.assertTrue(result["validation"]["witness_revocation_verifier_quorum_bound"])
        self.assertTrue(result["validation"]["revocation_verifier_quorum_digest_bound"])
        self.assertTrue(result["validation"]["witness_revocation_verifier_roster_bound"])
        self.assertTrue(result["validation"]["revocation_verifier_roster_digest_bound"])
        self.assertTrue(result["validation"]["blocked_profile_fail_closed"])
        self.assertTrue(result["validation"]["revoked_witness_registry_fail_closed"])
        self.assertTrue(result["validation"]["revocation_verifier_quorum_fail_closed"])
        self.assertTrue(result["validation"]["revocation_verifier_roster_fail_closed"])
        self.assertEqual(
            "multidimensional-identity-confirmation-v1",
            result["confirmation_profile"]["profile_id"],
        )
        self.assertEqual("passed", result["confirmation_profile"]["result"])
        self.assertEqual("met", result["confirmation_profile"]["witness_quorum"]["status"])
        self.assertEqual(
            "identity-self-report-witness-consistency-v1",
            result["confirmation_profile"]["self_report_witness_consistency"]["policy_id"],
        )
        self.assertEqual("failed", result["blocked_profile"]["result"])
        self.assertEqual(
            "identity-witness-registry-binding-v1",
            result["confirmation_profile"]["witness_registry_binding"]["policy_id"],
        )
        self.assertEqual("bound", result["confirmation_profile"]["witness_registry_binding"]["status"])
        self.assertEqual(
            "complete",
            result["confirmation_profile"]["witness_registry_binding"][
                "revocation_verifier_quorum_status"
            ],
        )
        self.assertFalse(
            result["confirmation_profile"]["witness_registry_binding"][
                "raw_registry_payload_stored"
            ]
        )
        self.assertFalse(
            result["confirmation_profile"]["witness_registry_binding"][
                "raw_revocation_verifier_payload_stored"
            ]
        )
        self.assertEqual("failed", result["revoked_witness_profile"]["result"])
        self.assertEqual("failed", result["verifier_blocked_profile"]["result"])

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
        self.assertEqual(
            "confirmed",
            result["method_b_final_handle"]["broker_handoff_receipt"]["status"],
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
        self.assertTrue(result["validation"]["multi_jurisdiction_review_bound"])
        self.assertTrue(result["validation"]["distributed_signature_bound"])
        self.assertEqual(["JP-13", "US-CA"], result["validation"]["reviewer_jurisdictions"])
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
        self.assertEqual(
            "distributed-council-verdict-signature-binding-v1",
            result["bindings"]["conflict"]["distributed_verdicts"][0]["signature_binding"][
                "profile_id"
            ],
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
        self.assertEqual("reference-trust-provenance-v1", result["policy"]["provenance_policy_id"])
        self.assertEqual(0.99, result["agents"]["integrity-guardian"]["global_score"])
        self.assertFalse(result["blocked_events"]["pinned_negative"]["applied"])
        self.assertTrue(result["agents"]["design-architect"]["eligibility"]["count_for_weighted_vote"])
        self.assertTrue(result["validation"]["self_issued_positive_blocked"])
        self.assertTrue(result["validation"]["reciprocal_positive_blocked"])
        self.assertEqual(
            "blocked-self-issued-positive",
            result["blocked_events"]["self_issued_positive"]["provenance_status"],
        )
        self.assertEqual(
            "blocked-reciprocal-positive",
            result["blocked_events"]["reciprocal_positive"]["provenance_status"],
        )

    def test_trust_transfer_demo_emits_cross_substrate_receipt_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "trust-transfer-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
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
        self.assertEqual("current", result["transfer"]["destination_lifecycle"]["current_status"])
        self.assertEqual(
            ["imported", "renewed", "revoked", "recovered"],
            [
                entry["event_type"]
                for entry in result["transfer"]["destination_lifecycle"]["history"]
            ],
        )
        self.assertTrue(result["validation"]["receipt_digest_bound"])
        self.assertEqual(result["source_snapshot"], result["destination_snapshot"])
        self.assertEqual(
            3,
            result["transfer"]["federation_attestation"]["remote_verifier_federation"][
                "received_verifier_count"
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

    def test_trust_transfer_demo_emits_redacted_export_profile_json(self) -> None:
        stdout = io.StringIO()

        with patch(
            "sys.argv",
            [
                "omoikane",
                "trust-transfer-demo",
                "--export-profile",
                "bounded-trust-transfer-redacted-export-v1",
                "--json",
            ],
        ), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
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
            3,
            result["transfer"]["destination_lifecycle"]["history_summaries"][-1][
                "covered_verifier_count"
            ],
        )
        self.assertEqual(
            "bounded-trust-transfer-history-redaction-v1",
            result["transfer"]["export_receipt"]["redaction_policy_id"],
        )

    def test_yaoyorozu_demo_emits_registry_and_convocation_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "yaoyorozu-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["workspace_discovery"]["validation"]["ok"])
        self.assertTrue(result["convocation"]["validation"]["builder_handoff_coverage_ok"])
        self.assertTrue(result["dispatch_plan"]["validation"]["ok"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["ok"])
        self.assertTrue(result["consensus_dispatch"]["validation"]["ok"])
        self.assertEqual(3, result["validation"]["workspace_count"])
        self.assertEqual(2, result["validation"]["non_source_workspace_count"])
        self.assertEqual("self-modify-patch-v1", result["validation"]["proposal_profile"])
        self.assertTrue(result["validation"]["workspace_discovery_ok"])
        self.assertTrue(result["validation"]["registry_source_digest_manifest_bound"])
        self.assertFalse(result["validation"]["raw_source_payload_stored"])
        self.assertTrue(result["validation"]["workspace_review_budget_respected"])
        self.assertEqual(3, result["validation"]["profile_workspace_review_budget"])
        self.assertEqual(
            ["runtime", "schema", "eval", "docs"],
            result["validation"]["profile_required_workspace_coverage_areas"],
        )
        self.assertEqual([], result["validation"]["profile_optional_workspace_coverage_areas"])
        self.assertTrue(result["validation"]["cross_workspace_coverage_complete"])
        self.assertEqual(
            "selected",
            result["convocation"]["standing_roles"]["guardian_liaison"]["status"],
        )
        self.assertTrue(result["validation"]["standing_role_scope_binding_ok"])
        self.assertTrue(result["validation"]["council_panel_scope_binding_ok"])
        self.assertTrue(result["validation"]["builder_handoff_scope_binding_ok"])
        self.assertTrue(result["validation"]["builder_coverage_target_paths_bound"])
        self.assertFalse(result["validation"]["raw_selection_scope_payload_stored"])
        self.assertEqual(
            "registry-selection-scope-binding-v1",
            result["convocation"]["builder_handoff"][0]["selection_scope_binding_profile"],
        )
        self.assertGreaterEqual(result["registry"]["entry_count"], 10)
        self.assertEqual(4, result["validation"]["dispatch_success_count"])
        self.assertEqual(7, result["validation"]["consensus_message_count"])
        self.assertTrue(result["validation"]["consensus_dispatch_ok"])
        self.assertTrue(result["validation"]["consensus_direct_handoff_blocked"])
        self.assertTrue(result["validation"]["task_graph_binding_ok"])
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
        self.assertEqual(3, result["validation"]["task_graph_ready_node_count"])
        self.assertEqual(4, result["validation"]["task_graph_dispatch_unit_count"])
        self.assertEqual(3, result["validation"]["task_graph_synthesis_count"])
        self.assertTrue(result["validation"]["task_graph_guardian_gate_bound"])
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
        self.assertTrue(result["validation"]["task_graph_worker_claims_bound"])
        self.assertTrue(result["validation"]["task_graph_coverage_grouping_ok"])
        self.assertEqual(
            result["convocation"]["session_id"],
            result["consensus_dispatch"]["consensus_session_id"],
        )
        self.assertTrue(result["validation"]["workspace_discovery_bound"])
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
        self.assertTrue(result["validation"]["external_dependency_lockfile_attested"])
        self.assertTrue(result["validation"]["external_dependency_wheel_attested"])
        self.assertTrue(result["validation"]["external_dependency_import_precedence_bound"])
        self.assertTrue(result["validation"]["external_dependency_module_origin_bound"])
        self.assertEqual(4, result["validation"]["external_dependency_materialized_count"])
        self.assertEqual(4, result["validation"]["external_dependency_lockfile_attested_count"])
        self.assertEqual(4, result["validation"]["external_dependency_wheel_attested_count"])
        self.assertEqual(4, result["validation"]["external_dependency_import_precedence_count"])
        self.assertEqual(4, result["validation"]["external_dependency_module_origin_count"])
        self.assertEqual(
            "materialized-dependency-lockfile-v1",
            result["validation"]["dependency_lockfile_profile"],
        )
        self.assertEqual(
            "materialized-dependency-wheel-attestation-v1",
            result["validation"]["dependency_wheel_attestation_profile"],
        )
        self.assertEqual(
            "materialized-dependency-sealed-import-v1",
            result["validation"]["dependency_import_precedence_profile"],
        )
        self.assertEqual(
            "materialized-dependency-module-origin-v1",
            result["validation"]["dependency_module_origin_profile"],
        )
        self.assertTrue(result["dispatch_receipt"]["validation"]["all_reports_bound_to_dispatch"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["all_delta_receipts_bound"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["all_patch_candidate_receipts_bound"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["all_target_paths_ready"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["same_host_scope_only"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["external_workspace_seeded"])
        self.assertTrue(result["dispatch_receipt"]["validation"]["external_dependencies_materialized"])
        self.assertTrue(
            result["dispatch_receipt"]["validation"][
                "external_dependency_import_precedence_bound"
            ]
        )
        self.assertTrue(
            result["dispatch_receipt"]["validation"][
                "external_dependency_module_origin_bound"
            ]
        )
        self.assertEqual(4, result["dispatch_receipt"]["execution_summary"]["target_ready_count"])
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
        self.assertEqual(4, result["dispatch_receipt"]["execution_summary"]["delta_bound_count"])
        self.assertEqual(
            4,
            result["dispatch_receipt"]["execution_summary"]["patch_candidate_bound_count"],
        )
        self.assertEqual(4, result["dispatch_receipt"]["execution_summary"]["candidate_bound_success_count"])
        self.assertEqual(0, result["dispatch_receipt"]["execution_summary"]["source_bound_success_count"])
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
            ["docs", "eval"],
            sorted(
                next(
                    binding["coverage_areas"]
                    for binding in result["task_graph_binding"]["node_bindings"]
                    if "docs" in binding["coverage_areas"]
                )
            ),
        )

    def test_yaoyorozu_demo_supports_memory_edit_profile(self) -> None:
        stdout = io.StringIO()

        with patch(
            "sys.argv",
            [
                "omoikane",
                "yaoyorozu-demo",
                "--proposal-profile",
                "memory-edit-v1",
                "--json",
            ],
        ), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
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
        self.assertTrue(result["validation"]["workspace_discovery_bound"])
        self.assertTrue(result["validation"]["workspace_profile_policy_ready"])
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
        self.assertEqual(3, result["validation"]["dispatch_unit_count"])
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
        stdout = io.StringIO()

        with patch(
            "sys.argv",
            [
                "omoikane",
                "yaoyorozu-demo",
                "--proposal-profile",
                "memory-edit-v1",
                "--include-optional-coverage",
                "schema",
                "--json",
            ],
        ), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual(
            ["schema"],
            result["validation"]["requested_optional_builder_coverage_areas"],
        )
        self.assertEqual(
            ["runtime", "eval", "docs", "schema"],
            result["validation"]["dispatch_builder_coverage_areas"],
        )
        self.assertEqual(4, result["validation"]["dispatch_unit_count"])
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
        stdout = io.StringIO()

        with patch(
            "sys.argv",
            [
                "omoikane",
                "yaoyorozu-demo",
                "--proposal-profile",
                "fork-request-v1",
                "--json",
            ],
        ), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
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
        self.assertTrue(result["validation"]["workspace_discovery_bound"])
        self.assertTrue(result["validation"]["workspace_profile_policy_ready"])
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
        self.assertTrue(result["validation"]["task_graph_bundle_strategy_ok"])
        self.assertEqual(
            "fork-request-required-dispatch-three-root-v1",
            result["validation"]["task_graph_bundle_strategy_id"],
        )
        self.assertEqual(3, result["validation"]["dispatch_unit_count"])
        self.assertEqual(
            [["docs"], ["runtime"], ["schema"]],
            sorted(
                sorted(binding["coverage_areas"])
                for binding in result["task_graph_binding"]["node_bindings"]
            ),
        )
        self.assertEqual(
            "identity-guardian",
            result["convocation"]["council_panel"][0]["selected_agent_id"],
        )
        self.assertEqual(
            "legal-scholar",
            result["convocation"]["council_panel"][1]["selected_agent_id"],
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
        stdout = io.StringIO()

        with patch(
            "sys.argv",
            [
                "omoikane",
                "yaoyorozu-demo",
                "--proposal-profile",
                "fork-request-v1",
                "--include-optional-coverage",
                "eval",
                "--json",
            ],
        ), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertEqual(
            ["eval"],
            result["validation"]["requested_optional_builder_coverage_areas"],
        )
        self.assertEqual(
            ["runtime", "schema", "docs", "eval"],
            result["validation"]["dispatch_builder_coverage_areas"],
        )
        self.assertEqual(4, result["validation"]["dispatch_unit_count"])
        self.assertEqual(
            "fork-request-optional-eval-dispatch-three-root-v1",
            result["validation"]["task_graph_bundle_strategy_id"],
        )
        self.assertTrue(result["validation"]["execution_chain_ok"])
        self.assertEqual(
            [["docs", "eval"], ["runtime"], ["schema"]],
            sorted(
                sorted(binding["coverage_areas"])
                for binding in result["task_graph_binding"]["node_bindings"]
            ),
        )

    def test_yaoyorozu_demo_supports_inter_mind_negotiation_profile(self) -> None:
        stdout = io.StringIO()

        with patch(
            "sys.argv",
            [
                "omoikane",
                "yaoyorozu-demo",
                "--proposal-profile",
                "inter-mind-negotiation-v1",
                "--json",
            ],
        ), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
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
        self.assertTrue(result["validation"]["workspace_profile_policy_ready"])
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
        self.assertTrue(result["validation"]["task_graph_bundle_strategy_ok"])
        self.assertEqual(
            "inter-mind-negotiation-contract-sync-v1",
            result["validation"]["task_graph_bundle_strategy_id"],
        )
        self.assertEqual(4, result["validation"]["dispatch_unit_count"])
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
        self.assertTrue(result["validation"]["execution_chain_ok"])
        self.assertIn(
            "evals/agentic/yaoyorozu_inter_mind_negotiation_profile.yaml",
            result["execution_chain"]["execution_summary"]["required_eval_refs"],
        )

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
        self.assertTrue(result["validation"]["legal_execution_ready"])
        self.assertTrue(result["validation"]["legal_execution_bound"])
        self.assertTrue(result["validation"]["responsibility_scope_enforced"])
        self.assertTrue(result["validation"]["pin_breach_propagated"])
        self.assertEqual("joint", result["events"]["veto"]["reviewer_bindings"][0]["liability_mode"])
        self.assertEqual(
            "reviewer-live-proof-bridge-v1",
            result["events"]["veto"]["reviewer_bindings"][0]["transport_profile"],
        )
        self.assertEqual(
            "policy://guardian-oversight/jp-13/reviewer-attestation/v1",
            result["events"]["veto"]["reviewer_bindings"][0]["legal_policy_ref"],
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
        self.assertTrue(result["validation"]["binding_carries_transport_exchange"])
        self.assertTrue(result["validation"]["binding_carries_transport_exchange_digest"])
        self.assertTrue(result["validation"]["binding_carries_trust_root"])
        self.assertTrue(result["validation"]["legal_execution_executed"])
        self.assertTrue(result["validation"]["legal_execution_network_bound"])
        self.assertTrue(result["validation"]["binding_carries_legal_execution"])
        self.assertTrue(result["validation"]["binding_carries_legal_policy"])
        self.assertTrue(result["validation"]["transport_exchange_bound"])
        self.assertTrue(result["validation"]["transport_exchange_request_digest_bound"])
        self.assertEqual(
            "guardian-reviewer-remote-attestation-v1",
            result["reviewer"]["credential_verification"]["network_receipt"]["network_profile_id"],
        )
        self.assertEqual(
            "verifier://guardian-oversight.jp",
            result["reviewer"]["credential_verification"]["network_receipt"]["verifier_endpoint"],
        )
        self.assertEqual(
            "digest-bound-reviewer-transport-exchange-v1",
            result["reviewer"]["credential_verification"]["network_receipt"]["transport_exchange"]["exchange_profile_id"],
        )
        self.assertEqual(
            "guardian-jurisdiction-legal-execution-v1",
            result["reviewer"]["credential_verification"]["legal_execution"]["execution_profile_id"],
        )

    def test_ethics_demo_emits_rule_language_and_events(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "ethics-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertEqual("deterministic-rule-tree-v0", result["language"]["language_id"])
        self.assertEqual("veto", result["decisions"]["immutable_boundary"]["outcome"])
        self.assertEqual("escalate", result["decisions"]["sandbox_escalation"]["outcome"])
        self.assertEqual("veto", result["rule_explanation"]["outcome"])
        self.assertTrue(result["validation"]["conflict_records_all_matches"])
        self.assertEqual(
            "A7-ewa-blocked-token",
            result["decisions"]["ewa_conflict_resolution"]["resolution"]["selected_rule_id"],
        )
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
        self.assertEqual("cool-off-pending", result["outcomes"]["cool_off"]["status"])
        self.assertEqual("deferred", result["outcomes"]["cool_off"]["scheduler_cancellation"]["result"])
        self.assertEqual("advancing", result["scheduler"]["cool_off"]["handle"]["status"])
        self.assertEqual("invalid-self-proof", result["outcomes"]["rejected"]["reject_reason"])
        self.assertEqual(
            "not-requested",
            result["outcomes"]["rejected"]["scheduler_cancellation"]["result"],
        )
        self.assertEqual("advancing", result["scheduler"]["rejected"]["handle"]["status"])
        self.assertTrue(result["ledger_verification"]["ok"])


if __name__ == "__main__":
    unittest.main()
