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


class ParallelOrchestrationSchemaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = OmoikaneReferenceOS()

    def _assert_schema_valid(self, schema_path: str, payload: dict[str, Any]) -> None:
        schema = _load_schema(schema_path)
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            formatted = "\n".join(error.message for error in errors[:5])
            self.fail(f"{schema_path} validation failed:\n{formatted}")

    def test_parallel_orchestration_demo_receipts_match_public_schema(self) -> None:
        result = self.runtime.run_parallel_orchestration_demo()

        self.assertTrue(result["validation"]["ok"])
        self._assert_schema_valid(
            "specs/schemas/parallel_codex_worker_result_receipt.schema",
            result["ready_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/parallel_codex_worker_result_receipt.schema",
            result["remote_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/parallel_codex_worker_result_receipt.schema",
            result["blocked_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/parallel_codex_worker_result_receipt.schema",
            result["content_mismatch_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/parallel_codex_worker_result_receipt.schema",
            result["unrelated_ancestry_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/parallel_codex_worker_result_receipt.schema",
            result["marker_only_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/parallel_codex_worker_result_receipt.schema",
            result["yaoyorozu_bridge_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/parallel_codex_integration_batch_receipt.schema",
            result["batch_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/parallel_codex_integration_batch_receipt.schema",
            result["conflict_batch_receipt"],
        )
        self.assertEqual(9, len(result["schema_contracts"]))
        self.assertTrue(result["validation"]["ready_for_main_checkout"])
        self.assertTrue(result["validation"]["ready_worker_identity_evidence_bound"])
        self.assertTrue(result["validation"]["ready_workspace_marker_hygiene_clean"])
        self.assertTrue(
            result["validation"]["ready_workspace_marker_hygiene_digest_bound"]
        )
        self.assertTrue(result["validation"]["remote_ready_for_main_checkout"])
        self.assertTrue(result["validation"]["remote_branch_pr_metadata_bound"])
        self.assertTrue(
            result["validation"]["remote_source_revocation_digest_bound"]
        )
        self.assertTrue(
            result["validation"][
                "remote_source_revocation_freshness_digest_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["remote_source_revocation_timestamp_digest_bound"]
        )
        self.assertTrue(
            result["validation"]["remote_source_revocation_timestamp_signature_bound"]
        )
        self.assertTrue(
            result["validation"]["remote_source_revocation_timestamp_signed_current"]
        )
        self.assertTrue(
            result["validation"][
                "remote_source_revocation_timestamp_replay_guard_digest_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["remote_source_revocation_timestamp_unique"]
        )
        self.assertTrue(result["validation"]["remote_source_content_digest_bound"])
        self.assertTrue(result["validation"]["remote_source_content_bound"])
        self.assertTrue(result["validation"]["remote_source_content_status_bound"])
        self.assertTrue(result["validation"]["remote_source_ancestry_digest_bound"])
        self.assertTrue(result["validation"]["remote_source_ancestry_bound"])
        self.assertTrue(result["validation"]["remote_source_ancestry_status_bound"])
        self.assertTrue(
            result["validation"]["remote_source_base_commit_matches_worker"]
        )
        self.assertTrue(result["validation"]["remote_source_revocation_not_revoked"])
        self.assertTrue(result["validation"]["remote_source_revocation_fresh"])
        self.assertTrue(result["validation"]["remote_review_authority_digest_bound"])
        self.assertTrue(
            result["validation"]["remote_accepted_source_policy_digest_bound"]
        )
        self.assertTrue(result["validation"]["remote_worker_identity_evidence_bound"])
        self.assertTrue(result["validation"]["remote_raw_metadata_payload_redacted"])
        self.assertTrue(result["validation"]["remote_raw_revocation_payload_redacted"])
        self.assertTrue(
            result["validation"]["remote_raw_revocation_freshness_payload_redacted"]
        )
        self.assertTrue(
            result["validation"]["remote_raw_revocation_timestamp_payload_redacted"]
        )
        self.assertTrue(
            result["validation"][
                "remote_raw_revocation_timestamp_replay_guard_payload_redacted"
            ]
        )
        self.assertTrue(
            result["validation"]["remote_raw_source_content_payload_redacted"]
        )
        self.assertTrue(
            result["validation"]["remote_raw_source_ancestry_payload_redacted"]
        )
        self.assertTrue(result["validation"]["content_mismatch_result_blocked"])
        self.assertTrue(result["validation"]["content_mismatch_digest_bound"])
        self.assertTrue(result["validation"]["content_mismatch_status_rejected"])
        self.assertTrue(
            result["validation"][
                "content_mismatch_raw_source_content_payload_redacted"
            ]
        )
        self.assertTrue(result["validation"]["unrelated_ancestry_result_blocked"])
        self.assertTrue(result["validation"]["unrelated_ancestry_digest_bound"])
        self.assertTrue(result["validation"]["unrelated_ancestry_status_rejected"])
        self.assertTrue(
            result["validation"][
                "unrelated_ancestry_raw_source_ancestry_payload_redacted"
            ]
        )
        self.assertTrue(result["validation"]["blocked_stale_worker_result"])
        self.assertTrue(result["validation"]["marker_only_result_blocked"])
        self.assertTrue(result["validation"]["marker_only_hygiene_digest_bound"])
        self.assertTrue(result["validation"]["marker_only_change_blocked"])
        self.assertTrue(
            result["validation"]["marker_only_raw_workspace_marker_payload_redacted"]
        )
        self.assertTrue(
            result["validation"]["yaoyorozu_bridge_ready_for_main_checkout"]
        )
        self.assertTrue(result["validation"]["yaoyorozu_bridge_patch_candidates_bound"])
        self.assertTrue(
            result["validation"]["yaoyorozu_bridge_worker_identity_evidence_bound"]
        )
        self.assertTrue(
            result["validation"]["yaoyorozu_bridge_raw_upstream_payload_redacted"]
        )
        self.assertTrue(
            result["validation"][
                "yaoyorozu_bridge_raw_worker_identity_payload_redacted"
            ]
        )
        self.assertEqual(
            "parallel-codex-integration-batch-arbitration-v1",
            result["batch_receipt"]["profile_id"],
        )
        self.assertEqual("integration-ready", result["batch_receipt"]["batch_decision"])
        self.assertTrue(result["validation"]["batch_receipt_ok"])
        self.assertTrue(result["validation"]["batch_ready_for_integration"])
        self.assertTrue(
            result["validation"]["batch_input_receipt_set_digest_bound"]
        )
        self.assertTrue(
            result["validation"]["batch_ordered_integration_digest_bound"]
        )
        self.assertTrue(
            result["validation"]["batch_changed_file_owner_manifest_digest_bound"]
        )
        self.assertTrue(
            result["validation"]["batch_quarantined_receipt_set_digest_bound"]
        )
        self.assertTrue(result["validation"]["batch_conflict_free"])
        self.assertTrue(result["validation"]["batch_blocked_receipts_quarantined"])
        self.assertTrue(result["validation"]["batch_required_verifications_passed"])
        self.assertTrue(
            result["validation"]["batch_raw_worker_receipt_payload_redacted"]
        )
        self.assertTrue(result["validation"]["batch_raw_conflict_payload_redacted"])
        self.assertEqual("blocked", result["conflict_batch_receipt"]["batch_decision"])
        self.assertTrue(result["validation"]["conflict_batch_receipt_ok"])
        self.assertTrue(result["validation"]["conflict_batch_result_blocked"])
        self.assertTrue(result["validation"]["conflict_batch_conflict_digest_bound"])
        self.assertTrue(
            result["validation"][
                "conflict_batch_changed_file_owner_manifest_digest_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "conflict_batch_quarantined_receipt_set_digest_bound"
            ]
        )
        self.assertTrue(result["validation"]["conflict_batch_conflict_blocked"])
        self.assertTrue(
            result["validation"]["conflict_batch_raw_conflict_payload_redacted"]
        )
        self.assertTrue(result["validation"]["ledger_bound"])


if __name__ == "__main__":
    unittest.main()
