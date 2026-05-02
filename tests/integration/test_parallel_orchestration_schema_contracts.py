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
        self._assert_schema_valid(
            "specs/schemas/parallel_codex_integration_execution_receipt.schema",
            result["execution_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/parallel_codex_post_commit_publication_receipt.schema",
            result["post_commit_publication_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/parallel_codex_integration_execution_receipt.schema",
            result["conflict_execution_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/parallel_codex_post_commit_publication_receipt.schema",
            result["blocked_post_commit_publication_receipt"],
        )
        self.assertEqual(13, len(result["schema_contracts"]))
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
        self.assertTrue(result["validation"]["marker_only_classifier_digest_bound"])
        self.assertTrue(
            result["validation"]["marker_only_segment_manifest_digest_bound"]
        )
        self.assertTrue(result["validation"]["marker_only_structured_segment_classifier"])
        self.assertTrue(result["validation"]["marker_only_classifier_detected"])
        self.assertTrue(result["validation"]["marker_only_change_blocked"])
        self.assertTrue(
            result["validation"]["marker_only_raw_workspace_marker_payload_redacted"]
        )
        self.assertTrue(result["validation"]["marker_only_raw_segment_payload_redacted"])
        self.assertEqual(
            "repo-local-workspace-marker-diff-classifier-v1",
            result["marker_only_receipt"]["workspace_marker_classifier_profile"],
        )
        self.assertEqual(
            "structured-patch-segment-manifest-v1",
            result["marker_only_receipt"]["workspace_marker_diff_summaries"][0][
                "classifier_evidence_profile"
            ],
        )
        self.assertEqual(
            "marker-only",
            result["marker_only_receipt"]["workspace_marker_diff_summaries"][0][
                "classifier_status"
            ],
        )
        self.assertEqual(
            1,
            result["marker_only_receipt"]["workspace_marker_diff_summaries"][0][
                "marker_segment_count"
            ],
        )
        self.assertFalse(
            result["marker_only_receipt"]["workspace_marker_diff_summaries"][0][
                "raw_segment_payload_stored"
            ],
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
        self.assertEqual(
            "parallel-codex-integration-execution-plan-v1",
            result["execution_receipt"]["profile_id"],
        )
        self.assertEqual(
            "ready-to-apply",
            result["execution_receipt"]["execution_decision"],
        )
        self.assertTrue(result["validation"]["execution_receipt_ok"])
        self.assertTrue(result["validation"]["execution_ready_to_apply"])
        self.assertTrue(
            result["validation"]["execution_source_batch_receipt_digest_bound"]
        )
        self.assertTrue(result["validation"]["execution_apply_plan_digest_bound"])
        self.assertTrue(
            result["validation"]["execution_patch_artifact_manifest_digest_bound"]
        )
        self.assertTrue(
            result["validation"]["execution_repo_local_patch_artifacts_bound"]
        )
        self.assertTrue(
            result["validation"]["execution_patch_artifact_cleanup_digest_bound"]
        )
        self.assertTrue(
            result["validation"][
                "execution_patch_artifact_cleanup_artifact_paths_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "execution_patch_artifact_cleanup_artifact_count_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["execution_patch_artifact_cleanup_verified"]
        )
        self.assertTrue(
            result["validation"]["execution_pre_apply_dry_run_manifest_digest_bound"]
        )
        self.assertTrue(
            result["validation"]["execution_pre_apply_dry_run_command_bound"]
        )
        self.assertTrue(
            result["validation"]["execution_pre_apply_patch_artifact_digest_bound"]
        )
        self.assertTrue(
            result["validation"]["execution_pre_apply_command_receipt_digest_bound"]
        )
        self.assertTrue(result["validation"]["execution_pre_apply_dry_run_passed"])
        for step in result["execution_receipt"]["apply_steps"]:
            self.assertTrue(step["patch_artifact_ref"].startswith("patch://parallel-codex/"))
            self.assertEqual(
                "repo-local-patch-artifact-binding-v1",
                step["patch_artifact_profile"],
            )
            self.assertEqual("repo-local-patch-file", step["patch_artifact_source"])
            self.assertTrue(
                step["patch_artifact_path"].startswith("artifacts/parallel-codex/")
            )
            self.assertTrue(step["patch_artifact_path"].endswith(".patch"))
            self.assertEqual(
                step["patch_artifact_path"],
                step["patch_artifact_command_target"],
            )
            self.assertTrue(step["patch_artifact_digest"])
            self.assertFalse(step["raw_patch_payload_stored"])
        for dry_run in result["execution_receipt"]["pre_apply_dry_run_results"]:
            self.assertEqual(
                "command-bound-git-apply-check-v1",
                dry_run["command_profile"],
            )
            self.assertEqual(
                "repo-local-patch-artifact-binding-v1",
                dry_run["patch_artifact_profile"],
            )
            self.assertEqual("repo-local-patch-file", dry_run["patch_artifact_source"])
            self.assertTrue(
                dry_run["patch_artifact_path"].startswith(
                    "artifacts/parallel-codex/"
                )
            )
            self.assertEqual(
                f"git apply --check {dry_run['patch_artifact_path']}",
                dry_run["command"],
            )
            self.assertEqual(
                dry_run["patch_artifact_path"],
                dry_run["patch_artifact_command_target"],
            )
            self.assertTrue(dry_run["patch_artifact_digest_bound"])
            self.assertTrue(dry_run["command_receipt_digest"])
            self.assertFalse(dry_run["raw_patch_payload_stored"])
        self.assertEqual(
            "repo-local-patch-artifact-cleanup-v1",
            result["execution_receipt"]["patch_artifact_cleanup_profile"],
        )
        self.assertEqual(
            "removed",
            result["execution_receipt"]["patch_artifact_cleanup_status"],
        )
        self.assertTrue(
            result["execution_receipt"]["patch_artifact_cleanup_verified"]
        )
        self.assertTrue(
            result["validation"][
                "execution_post_apply_verification_manifest_digest_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["execution_post_apply_verification_context_bound"]
        )
        self.assertTrue(
            result["validation"][
                "execution_post_apply_verification_context_digest_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "execution_post_apply_verification_apply_plan_digest_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "execution_post_apply_verification_patch_artifact_manifest_digest_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "execution_post_apply_verification_pre_apply_manifest_digest_bound"
            ]
        )
        self.assertTrue(result["validation"]["execution_checkout_mutation_attested"])
        self.assertTrue(
            result["validation"]["execution_checkout_mutation_event_digest_bound"]
        )
        self.assertTrue(
            result["validation"]["execution_checkout_mutation_context_bound"]
        )
        self.assertTrue(
            result["validation"]["execution_commit_finalization_digest_bound"]
        )
        self.assertTrue(
            result["validation"]["execution_commit_finalization_context_bound"]
        )
        self.assertTrue(
            result["validation"][
                "execution_commit_finalization_patch_artifact_cleanup_digest_bound"
            ]
        )
        self.assertTrue(result["validation"]["execution_commit_finalization_ready"])
        self.assertEqual(
            "main-checkout-commit-finalization-gate-v1",
            result["execution_receipt"]["commit_finalization_profile"],
        )
        self.assertEqual("ready", result["execution_receipt"]["commit_finalization_status"])
        self.assertFalse(
            result["execution_receipt"]["raw_checkout_mutation_payload_stored"]
        )
        self.assertFalse(
            result["execution_receipt"][
                "raw_patch_artifact_cleanup_payload_stored"
            ]
        )
        self.assertFalse(
            result["execution_receipt"]["raw_commit_finalization_payload_stored"]
        )
        self.assertTrue(
            result["validation"]["post_commit_publication_receipt_ok"]
        )
        self.assertTrue(
            result["validation"][
                "post_commit_publication_ready_for_github_handoff"
            ]
        )
        self.assertTrue(
            result["validation"]["post_commit_publication_source_execution_bound"]
        )
        self.assertTrue(
            result["validation"][
                "post_commit_publication_commit_finalization_ready"
            ]
        )
        self.assertTrue(
            result["validation"][
                "post_commit_publication_local_commit_matches_source"
            ]
        )
        self.assertTrue(
            result["validation"]["post_commit_publication_remote_head_matches"]
        )
        self.assertTrue(
            result["validation"][
                "post_commit_publication_push_command_digest_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "post_commit_publication_remote_verification_digest_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "post_commit_publication_remote_verification_output_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "post_commit_publication_remote_verification_observed_head_matches"
            ]
        )
        self.assertTrue(
            result["validation"][
                "post_commit_publication_remote_verification_observed_ref_matches"
            ]
        )
        self.assertTrue(
            result["validation"][
                "post_commit_publication_protected_branch_policy_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "post_commit_publication_protected_branch_receipt_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "post_commit_publication_protected_branch_status_protected"
            ]
        )
        self.assertTrue(
            result["validation"][
                "post_commit_publication_protected_branch_freshness_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["post_commit_publication_protected_branch_fresh"]
        )
        self.assertTrue(
            result["validation"][
                "post_commit_publication_protected_branch_timestamp_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "post_commit_publication_protected_branch_timestamp_signed_current"
            ]
        )
        self.assertTrue(
            result["validation"][
                "post_commit_publication_protected_branch_timestamp_replay_bound"
            ]
        )
        self.assertTrue(
            result["validation"][
                "post_commit_publication_protected_branch_timestamp_unique"
            ]
        )
        self.assertTrue(
            result["validation"][
                "post_commit_publication_publication_digest_bound"
            ]
        )
        self.assertTrue(
            result["validation"]["post_commit_publication_raw_payload_redacted"]
        )
        self.assertEqual(
            "published",
            result["post_commit_publication_receipt"]["publication_status"],
        )
        self.assertEqual(
            "git push origin HEAD:refs/heads/main",
            result["post_commit_publication_receipt"]["push_command_result"][
                "command"
            ],
        )
        self.assertEqual(
            "protected",
            result["post_commit_publication_receipt"]["protected_branch_status"],
        )
        self.assertFalse(
            result["post_commit_publication_receipt"][
                "raw_post_commit_publication_payload_stored"
            ]
        )
        self.assertFalse(
            result["post_commit_publication_receipt"][
                "raw_protected_branch_provider_payload_stored"
            ]
        )
        self.assertEqual(
            "blocked",
            result["conflict_execution_receipt"]["execution_decision"],
        )
        self.assertTrue(result["validation"]["conflict_execution_receipt_ok"])
        self.assertTrue(result["validation"]["conflict_execution_blocked"])
        self.assertTrue(
            result["validation"]["conflict_execution_blocked_on_source_batch"]
        )
        self.assertTrue(
            result["conflict_execution_receipt"]["pre_apply_dry_run_passed"]
        )
        self.assertTrue(
            result["validation"]["blocked_post_commit_publication_receipt_ok"]
        )
        self.assertTrue(
            result["validation"][
                "blocked_post_commit_publication_result_blocked"
            ]
        )
        self.assertEqual(
            "blocked",
            result["blocked_post_commit_publication_receipt"][
                "publication_status"
            ],
        )
        self.assertTrue(result["validation"]["ledger_bound"])


if __name__ == "__main__":
    unittest.main()
