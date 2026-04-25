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
        self.assertTrue(result["validation"]["remote_authority_slo_probe_quorum_bound"])
        self.assertTrue(
            result["validation"][
                "remote_authority_slo_quorum_threshold_policy_bound"
            ]
        )
        self.assertTrue(result["validation"]["approval_fanout"]["retry_policy_bound"])
        self.assertTrue(result["validation"]["physics_revert"]["digest_bound"])


if __name__ == "__main__":
    unittest.main()
