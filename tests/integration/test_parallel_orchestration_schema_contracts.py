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
            result["yaoyorozu_bridge_receipt"],
        )
        self.assertEqual(4, len(result["schema_contracts"]))
        self.assertTrue(result["validation"]["ready_for_main_checkout"])
        self.assertTrue(result["validation"]["ready_worker_identity_evidence_bound"])
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
        self.assertTrue(result["validation"]["blocked_stale_worker_result"])
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
        self.assertTrue(result["validation"]["ledger_bound"])


if __name__ == "__main__":
    unittest.main()
