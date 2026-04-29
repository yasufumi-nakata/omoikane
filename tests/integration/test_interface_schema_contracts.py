from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from omoikane.reference_os import OmoikaneReferenceOS


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_schema(path: str) -> dict[str, Any]:
    schema_path = REPO_ROOT / path
    loaded = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    return _resolve_local_refs(loaded, schema_path.parent)


def _resolve_local_refs(node: Any, base_dir: Path) -> Any:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and not ref.startswith("#"):
            ref_path = (base_dir / ref).resolve()
            loaded = yaml.safe_load(ref_path.read_text(encoding="utf-8"))
            return _resolve_local_refs(loaded, ref_path.parent)
        return {key: _resolve_local_refs(value, base_dir) for key, value in node.items()}
    if isinstance(node, list):
        return [_resolve_local_refs(item, base_dir) for item in node]
    return node


class InterfaceSchemaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = OmoikaneReferenceOS()

    def _assert_schema_valid(self, schema_path: str, payload: dict[str, Any]) -> None:
        schema = _load_schema(schema_path)
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            formatted = "\n".join(error.message for error in errors[:5])
            self.fail(f"{schema_path} validation failed:\n{formatted}")

    def _payload_at(self, payload: dict[str, Any], dotted_path: str) -> dict[str, Any]:
        cursor: Any = payload
        for part in dotted_path.split("."):
            cursor = cursor[part]
        self.assertIsInstance(cursor, dict)
        return cursor

    def test_biodata_transmitter_demo_matches_public_schemas(self) -> None:
        result = self.runtime.run_biodata_transmitter_demo()

        self._assert_schema_valid(
            "specs/schemas/biodata_transmitter_session.schema",
            result["session"],
        )
        self._assert_schema_valid(
            "specs/schemas/biodata_dataset_adapter_receipt.schema",
            result["dataset_adapter_receipt"],
        )
        for receipt in result["dataset_adapter_receipts"]:
            self._assert_schema_valid(
                "specs/schemas/biodata_dataset_adapter_receipt.schema",
                receipt,
            )
        self._assert_schema_valid(
            "specs/schemas/biodata_feature_window_series_profile.schema",
            result["feature_window_series_profile"],
        )
        self._assert_schema_valid(
            "specs/schemas/biodata_body_state_latent.schema",
            result["latent_state"],
        )
        self._assert_schema_valid(
            "specs/schemas/biodata_signal_bundle.schema",
            result["generated_bundle"],
        )
        self._assert_schema_valid(
            "specs/schemas/biodata_calibration_profile.schema",
            result["calibration_profile"],
        )
        self._assert_schema_valid(
            "specs/schemas/biodata_calibration_confidence_gate.schema",
            result["calibration_confidence_gate"],
        )
        for latent in result["calibration_latent_states"]:
            self._assert_schema_valid(
                "specs/schemas/biodata_body_state_latent.schema",
                latent,
        )
        self.assertTrue(result["validation"]["mind_upload_conflict_sink_bound"])
        self.assertTrue(result["validation"]["literature_backed_intermediate"])
        self.assertTrue(result["validation"]["dataset_adapter_ok"])
        self.assertTrue(result["validation"]["dataset_manifest_digest_bound"])
        self.assertTrue(result["validation"]["dataset_adapter_receipt_digest_bound"])
        self.assertTrue(result["validation"]["feature_window_series_profile_ok"])
        self.assertTrue(result["validation"]["feature_window_series_digest_set_bound"])
        self.assertTrue(result["validation"]["feature_window_series_profile_digest_bound"])
        self.assertTrue(result["validation"]["feature_window_series_adapter_receipts_bound"])
        self.assertTrue(result["validation"]["feature_window_series_latent_digest_set_bound"])
        self.assertTrue(result["validation"]["feature_window_series_required_modalities_bound"])
        self.assertTrue(result["validation"]["feature_window_series_circadian_profile_bound"])
        self.assertTrue(result["validation"]["feature_window_series_axis_drift_summary_bound"])
        self.assertTrue(result["validation"]["calibration_profile_ok"])
        self.assertTrue(result["validation"]["multi_day_calibration_bound"])
        self.assertTrue(result["validation"]["calibration_confidence_gate_ok"])
        self.assertTrue(result["validation"]["identity_confirmation_confidence_gate_bound"])
        self.assertTrue(result["validation"]["sensory_loopback_confidence_gate_bound"])
        self.assertFalse(result["validation"]["raw_calibration_payload_stored"])
        self.assertFalse(result["validation"]["raw_gate_payload_stored"])
        self.assertFalse(result["validation"]["raw_series_payload_stored"])

    def test_wms_demo_states_and_reconcile_match_public_schemas(self) -> None:
        result = self.runtime.run_wms_demo()

        self._assert_schema_valid("specs/schemas/world_state.schema", result["initial_state"])
        self._assert_schema_valid("specs/schemas/world_state.schema", result["final_state"])
        self._assert_schema_valid(
            "specs/schemas/wms_reconcile.schema",
            result["scenarios"]["minor_diff"],
        )
        self._assert_schema_valid(
            "specs/schemas/wms_reconcile.schema",
            result["scenarios"]["major_diff"],
        )
        self._assert_schema_valid(
            "specs/schemas/wms_reconcile.schema",
            result["scenarios"]["time_rate_deviation"],
        )
        self._assert_schema_valid(
            "specs/schemas/wms_reconcile.schema",
            result["scenarios"]["malicious_diff"],
        )
        for receipt in result["scenarios"]["time_rate_attestation_receipts"]:
            self._assert_schema_valid(
                "specs/schemas/wms_time_rate_attestation_receipt.schema",
                receipt,
            )
        self.assertTrue(result["validation"]["time_rate_attestation_transport_bound"])

    def test_collective_demo_matches_public_schemas(self) -> None:
        result = self.runtime.run_collective_demo()

        self._assert_schema_valid("specs/schemas/collective_record.schema", result["collective"])
        self._assert_schema_valid(
            "specs/schemas/collective_merge_session.schema",
            result["merge"],
        )
        self._assert_schema_valid(
            "specs/schemas/collective_dissolution_receipt.schema",
            result["dissolution"],
        )
        self._assert_schema_valid(
            "specs/schemas/collective_recovery_verifier_transport_binding.schema",
            result["recovery_verifier_transport"],
        )
        self._assert_schema_valid(
            "specs/schemas/distributed_transport_authority_route_trace.schema",
            result["recovery_route_trace"],
        )
        self._assert_schema_valid(
            "specs/schemas/collective_recovery_route_trace_binding.schema",
            result["recovery_route_trace_binding"],
        )
        self._assert_schema_valid(
            "specs/schemas/distributed_transport_packet_capture_export.schema",
            result["recovery_packet_capture_export"],
        )
        self._assert_schema_valid(
            "specs/schemas/distributed_transport_privileged_capture_acquisition.schema",
            result["recovery_privileged_capture_acquisition"],
        )
        self._assert_schema_valid(
            "specs/schemas/collective_recovery_capture_export_binding.schema",
            result["recovery_capture_export_binding"],
        )
        self._assert_schema_valid(
            "specs/schemas/collective_external_registry_sync.schema",
            result["external_registry_sync"],
        )
        for profile in result["member_recovery"]["identity_confirmation_profiles"].values():
            self._assert_schema_valid(
                "specs/schemas/identity_confirmation_profile.schema",
                profile,
            )
        self.assertTrue(result["validation"]["dissolution_receipt_bound"])
        self.assertTrue(result["validation"]["dissolution_member_confirmations_bound"])
        self.assertTrue(result["validation"]["dissolution_member_recovery_proofs_bound"])
        self.assertTrue(result["validation"]["dissolution_member_recovery_digest_set_bound"])
        self.assertTrue(result["validation"]["dissolution_member_recovery_binding_digest_bound"])
        self.assertFalse(result["validation"]["dissolution_raw_identity_confirmation_profiles_stored"])
        self.assertTrue(result["validation"]["recovery_verifier_transport_bound"])
        self.assertTrue(
            result["validation"]["recovery_verifier_transport_binding_digest_bound"]
        )
        self.assertFalse(result["validation"]["recovery_verifier_transport_raw_payload_stored"])
        self.assertTrue(result["validation"]["recovery_route_trace_bound"])
        self.assertTrue(result["validation"]["recovery_route_trace_authority_trace_bound"])
        self.assertTrue(result["validation"]["recovery_route_trace_member_bindings_bound"])
        self.assertFalse(result["validation"]["recovery_route_trace_raw_payload_stored"])
        self.assertTrue(result["validation"]["recovery_capture_export_bound"])
        self.assertTrue(result["validation"]["recovery_capture_export_packet_capture_bound"])
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

    def test_imc_demo_matches_public_schemas(self) -> None:
        result = self.runtime.run_imc_demo()

        self._assert_schema_valid("specs/schemas/imc_handshake.schema", result["handshake"])
        self._assert_schema_valid("specs/schemas/imc_message.schema", result["message"])
        self._assert_schema_valid("specs/schemas/imc_session.schema", result["session"])
        self._assert_schema_valid(
            "specs/schemas/imc_memory_glimpse_receipt.schema",
            result["memory_glimpse_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/imc_memory_glimpse_reconsent_receipt.schema",
            result["memory_glimpse_reconsent_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/imc_merge_thought_ethics_receipt.schema",
            result["merge_thought_ethics_receipt"],
        )
        for receipt in result["merge_thought_ethics_receipt"]["risk_boundary"][
            "merge_window_policy_authority"
        ]["live_verifier_receipts"]:
            self._assert_schema_valid(
                "specs/schemas/imc_merge_thought_window_policy_verifier_receipt.schema",
                receipt,
            )
        self.assertTrue(result["validation"]["memory_glimpse_receipt_ok"])
        self.assertTrue(result["validation"]["memory_glimpse_source_bound"])
        self.assertTrue(result["validation"]["memory_glimpse_disclosure_bound"])
        self.assertTrue(result["validation"]["memory_glimpse_witness_bound"])
        self.assertTrue(result["validation"]["merge_thought_ethics_receipt_ok"])
        self.assertFalse(result["validation"]["memory_glimpse_raw_memory_payload_stored"])
        self.assertFalse(result["validation"]["memory_glimpse_raw_message_payload_stored"])
        self.assertTrue(result["validation"]["memory_glimpse_reconsent_receipt_ok"])
        self.assertTrue(
            result["validation"]["memory_glimpse_reconsent_source_receipt_bound"]
        )
        self.assertTrue(
            result["validation"]["memory_glimpse_reconsent_consent_window_bound"]
        )
        self.assertTrue(result["validation"]["memory_glimpse_reconsent_revocation_bound"])
        self.assertTrue(result["validation"]["memory_glimpse_reconsent_bound"])
        self.assertFalse(result["validation"]["memory_glimpse_reconsent_raw_payload_stored"])
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
            result["merge_thought_ethics_receipt"]["risk_boundary"][
                "merge_window_policy_authority"
            ]["raw_policy_payload_stored"]
        )
        self.assertFalse(
            result["merge_thought_ethics_receipt"]["risk_boundary"][
                "merge_window_policy_authority"
            ]["raw_verifier_payload_stored"]
        )

    def test_wms_physics_rules_receipts_match_public_schema(self) -> None:
        result = self.runtime.run_wms_demo()

        self._assert_schema_valid(
            "specs/schemas/wms_physics_rules_change_receipt.schema",
            result["scenarios"]["physics_change"],
        )
        for receipt in result["scenarios"]["approval_transport_receipts"]:
            self._assert_schema_valid(
                "specs/schemas/wms_participant_approval_transport_receipt.schema",
                receipt,
            )
        self._assert_schema_valid(
            "specs/schemas/wms_approval_collection_receipt.schema",
            result["scenarios"]["approval_collection_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/wms_distributed_approval_fanout_receipt.schema",
            result["scenarios"]["approval_fanout_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/wms_physics_rules_change_receipt.schema",
            result["scenarios"]["physics_revert"],
        )
        self._assert_schema_valid(
            "specs/schemas/wms_engine_transaction_log.schema",
            result["scenarios"]["engine_transaction_log"],
        )
        self._assert_schema_valid(
            "specs/schemas/wms_engine_route_binding_receipt.schema",
            result["scenarios"]["engine_route_binding"],
        )
        self._assert_schema_valid(
            "specs/schemas/distributed_transport_packet_capture_export.schema",
            result["scenarios"]["engine_packet_capture_export"],
        )
        self._assert_schema_valid(
            "specs/schemas/distributed_transport_privileged_capture_acquisition.schema",
            result["scenarios"]["engine_privileged_capture_acquisition"],
        )
        self._assert_schema_valid(
            "specs/schemas/wms_engine_capture_binding_receipt.schema",
            result["scenarios"]["engine_capture_binding"],
        )
        self._assert_schema_valid(
            "specs/schemas/wms_remote_authority_retry_budget_receipt.schema",
            result["scenarios"]["remote_authority_retry_budget"],
        )
        self._assert_schema_valid(
            "specs/schemas/wms_authority_slo_probe_receipt.schema",
            result["scenarios"]["remote_authority_slo_probe_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/wms_authority_slo_probe_receipt.schema",
            result["scenarios"]["remote_authority_slo_backup_probe_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/wms_authority_slo_probe_quorum_receipt.schema",
            result["scenarios"]["remote_authority_slo_probe_quorum_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/wms_authority_slo_quorum_threshold_policy_receipt.schema",
            result["scenarios"]["remote_authority_slo_quorum_threshold_policy"],
        )
        self.assertTrue(result["validation"]["physics_change_reversible"])
        self.assertTrue(result["validation"]["physics_approval_transport_bound"])
        self.assertTrue(result["validation"]["approval_collection_scaling_bound"])
        self.assertTrue(result["validation"]["distributed_approval_fanout_bound"])
        self.assertTrue(result["validation"]["distributed_approval_fanout_retry_bound"])
        self.assertTrue(result["validation"]["engine_transaction_log_bound"])
        self.assertTrue(result["validation"]["engine_route_binding_bound"])
        self.assertTrue(result["validation"]["engine_capture_binding_bound"])
        self.assertTrue(result["validation"]["remote_authority_retry_budget_bound"])
        self.assertTrue(result["validation"]["physics_change"]["digest_bound"])
        self.assertTrue(result["validation"]["physics_change"]["approval_transport_digest_bound"])
        self.assertTrue(result["validation"]["physics_change"]["approval_collection_complete"])
        self.assertTrue(result["validation"]["physics_change"]["approval_fanout_complete"])
        self.assertTrue(result["validation"]["engine_transaction_log"]["digest_bound"])
        self.assertTrue(
            result["validation"]["engine_transaction_log"][
                "engine_adapter_signature_bound"
            ]
        )
        self.assertTrue(result["validation"]["engine_route_binding"]["digest_bound"])
        self.assertTrue(result["validation"]["engine_capture_binding"]["digest_bound"])
        self.assertTrue(
            result["validation"]["remote_authority_retry_budget"][
                "signed_jurisdiction_retry_budget_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["remote_authority_retry_budget"][
                "registry_bound_retry_budget_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["remote_authority_retry_budget"][
                "authority_slo_live_probe_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["remote_authority_retry_budget"][
                "authority_slo_probe_quorum_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["remote_authority_retry_budget"][
                "retry_budget_transport_trace_bound"
            ]
        )
        self.assertFalse(
            result["scenarios"]["remote_authority_retry_budget"][
                "raw_transport_payload_stored"
            ]
        )
        self.assertTrue(result["validation"]["remote_authority_slo_probe_quorum_bound"])
        self.assertTrue(
            result["validation"]["remote_authority_slo_probe_quorum"][
                "authority_slo_transport_trace_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["remote_authority_slo_probe_quorum"][
                "authority_slo_transport_cross_host_bound"
            ]
        )
        self.assertFalse(
            result["scenarios"]["remote_authority_slo_probe_quorum_receipt"][
                "raw_transport_payload_stored"
            ]
        )
        self.assertTrue(
            result["validation"][
                "remote_authority_slo_quorum_threshold_policy_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["remote_authority_slo_quorum_threshold_policy"][
                "signer_roster_bound"
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
        self.assertTrue(result["validation"]["approval_fanout"]["retry_policy_bound"])
        self.assertTrue(result["validation"]["physics_revert"]["digest_bound"])

    def test_sensory_loopback_demo_matches_public_schemas(self) -> None:
        result = self.runtime.run_sensory_loopback_demo()

        self.assertEqual(
            "sensory-loopback-public-schema-contract-v1",
            result["profile"]["public_schema_contract_profile"],
        )
        self.assertTrue(result["validation"]["public_schema_contract_bound"])
        schema_contracts = result["schema_contracts"]
        self.assertEqual(9, len(schema_contracts))
        for contract in schema_contracts:
            self._assert_schema_valid(
                contract["schema_path"],
                self._payload_at(result, contract["payload_path"]),
            )
        self.assertTrue(result["validation"]["shared_loopback_ok"])
        self.assertTrue(result["shared_loopback"]["validation"]["artifact_family_arbitration_tracked"])


if __name__ == "__main__":
    unittest.main()
