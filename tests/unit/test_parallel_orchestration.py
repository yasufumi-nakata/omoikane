from __future__ import annotations

import unittest

from omoikane.self_construction import ParallelCodexOrchestrationService


MAIN_HEAD = "a" * 40


def _verification_results() -> list[dict[str, object]]:
    return [
        {
            "command": "PYTHONPATH=src python3 -m unittest discover -s tests -t .",
            "status": "pass",
            "exit_code": 0,
            "stdout_excerpt": "tests passed",
            "stderr_excerpt": "",
        },
        {
            "command": "PYTHONPATH=src python3 -m omoikane.cli gap-report --json",
            "status": "pass",
            "exit_code": 0,
            "stdout_excerpt": "all_zero true",
            "stderr_excerpt": "",
        },
    ]


class ParallelCodexOrchestrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ParallelCodexOrchestrationService()

    def test_completed_worker_result_is_ready_when_scope_and_verification_pass(self) -> None:
        receipt = self.service.ingest_worker_result(
            worker_id="codex-worker-unit",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/", "tests/unit/"],
            changed_files=[
                "src/omoikane/self_construction/parallel_orchestration.py",
                "tests/unit/test_parallel_orchestration.py",
            ],
            verification_results=_verification_results(),
            result_summary="Unit worker result ready for main checkout integration.",
        )
        validation = self.service.validate_worker_result_receipt(receipt)

        self.assertEqual("accept-ready", receipt["integration_decision"])
        self.assertEqual([], receipt["blocking_reasons"])
        self.assertTrue(validation["ok"])
        self.assertTrue(validation["ready_for_main_checkout"])
        self.assertTrue(validation["changed_file_manifest_digest_bound"])
        self.assertTrue(validation["verification_manifest_digest_bound"])
        self.assertTrue(validation["worker_identity_evidence_bound"])
        self.assertTrue(validation["remote_metadata_bound"])
        self.assertTrue(validation["workspace_marker_hygiene_clean"])
        self.assertTrue(validation["workspace_marker_hygiene_digest_bound"])
        self.assertTrue(receipt["worker_identity_evidence_bound"])
        self.assertEqual("clean", receipt["workspace_marker_hygiene_status"])
        self.assertEqual([], receipt["workspace_marker_only_changed_files"])
        self.assertEqual(
            "signed-worker-identity-evidence-v1",
            receipt["worker_identity_profile"],
        )
        self.assertEqual("not-applicable", receipt["remote_metadata_profile"])
        self.assertEqual(
            "not-applicable",
            receipt["remote_source_revocation_profile"],
        )
        self.assertEqual(
            "not-applicable",
            receipt["remote_source_revocation_status"],
        )
        self.assertEqual(
            "not-applicable",
            receipt["remote_source_revocation_freshness_profile"],
        )
        self.assertEqual(
            "not-applicable",
            receipt["remote_source_revocation_freshness_status"],
        )
        self.assertEqual(
            "not-applicable",
            receipt["remote_source_revocation_timestamp_profile"],
        )
        self.assertEqual(
            "not-applicable",
            receipt["remote_source_revocation_timestamp_status"],
        )
        self.assertEqual(
            "not-applicable",
            receipt["remote_source_revocation_timestamp_replay_guard_profile"],
        )
        self.assertEqual(
            "not-applicable",
            receipt["remote_source_revocation_timestamp_replay_status"],
        )
        self.assertEqual(
            "not-applicable",
            receipt["remote_source_content_profile"],
        )
        self.assertEqual(
            "not-applicable",
            receipt["remote_source_content_status"],
        )
        self.assertTrue(receipt["remote_source_content_bound"])
        self.assertEqual(0, receipt["remote_source_revocation_freshness_window_seconds"])
        self.assertTrue(validation["receipt_digest_bound"])
        self.assertFalse(receipt["raw_patch_payload_stored"])
        self.assertFalse(receipt["raw_worker_identity_payload_stored"])
        self.assertFalse(receipt["raw_workspace_marker_payload_stored"])
        self.assertFalse(receipt["raw_remote_metadata_payload_stored"])
        self.assertFalse(receipt["raw_remote_revocation_payload_stored"])
        self.assertFalse(receipt["raw_remote_revocation_freshness_payload_stored"])
        self.assertFalse(receipt["raw_remote_revocation_timestamp_payload_stored"])
        self.assertFalse(
            receipt["raw_remote_revocation_timestamp_replay_guard_payload_stored"]
        )
        self.assertFalse(receipt["raw_remote_source_content_payload_stored"])
        self.assertFalse(receipt["raw_transcript_payload_stored"])
        self.assertFalse(receipt["raw_verification_payload_stored"])

    def test_workspace_marker_only_worker_result_blocks_integration(self) -> None:
        marker_path = "docs/02-subsystems/agentic/README.md"
        marker_diff = (
            "diff --git a/docs/02-subsystems/agentic/README.md "
            "b/docs/02-subsystems/agentic/README.md\n"
            "@@\n"
            "+# workspace-enacted: patch-unit-marker "
            "target=docs/02-subsystems/agentic/README.md\n"
        )
        receipt = self.service.ingest_worker_result(
            worker_id="codex-marker-only-worker",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["docs/"],
            changed_files=[marker_path],
            workspace_diff_by_file={marker_path: marker_diff},
            verification_results=_verification_results(),
            result_summary="Worker result only appends workspace-enacted markers.",
        )
        validation = self.service.validate_worker_result_receipt(receipt)

        self.assertEqual("blocked", receipt["integration_decision"])
        self.assertEqual(
            "marker-only-blocked",
            receipt["workspace_marker_hygiene_status"],
        )
        self.assertIn(
            "workspace marker-only changes cannot be the only integration payload",
            receipt["blocking_reasons"],
        )
        self.assertTrue(validation["ok"])
        self.assertFalse(validation["ready_for_main_checkout"])
        self.assertTrue(validation["workspace_marker_only_change_blocked"])
        self.assertTrue(validation["workspace_marker_classifier_digest_bound"])
        self.assertTrue(validation["workspace_marker_classifier_marker_only_detected"])
        self.assertEqual(1, receipt["workspace_marker_diff_summary_count"])
        self.assertEqual(
            "marker-only",
            receipt["workspace_marker_diff_summaries"][0]["classifier_status"],
        )
        self.assertEqual(
            "repo-local-diff-line-classifier-v1",
            receipt["workspace_marker_diff_summaries"][0][
                "classifier_evidence_profile"
            ],
        )
        self.assertFalse(
            receipt["workspace_marker_diff_summaries"][0]["raw_diff_payload_stored"]
        )
        self.assertFalse(
            receipt["workspace_marker_diff_summaries"][0][
                "raw_segment_payload_stored"
            ]
        )
        self.assertTrue(validation["workspace_marker_hygiene_digest_bound"])
        self.assertFalse(receipt["raw_workspace_marker_payload_stored"])

    def test_structured_patch_segment_marker_only_result_blocks_integration(self) -> None:
        marker_path = "docs/02-subsystems/agentic/README.md"
        receipt = self.service.ingest_worker_result(
            worker_id="codex-segment-marker-only-worker",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["docs/"],
            changed_files=[marker_path],
            workspace_patch_segments_by_file={
                marker_path: [
                    {
                        "operation": "add",
                        "line_count": 1,
                        "contains_workspace_marker": True,
                    }
                ]
            },
            verification_results=_verification_results(),
            result_summary=(
                "Structured patch segment evidence shows only workspace markers."
            ),
        )
        validation = self.service.validate_worker_result_receipt(receipt)
        summary = receipt["workspace_marker_diff_summaries"][0]

        self.assertEqual("blocked", receipt["integration_decision"])
        self.assertIn(marker_path, receipt["workspace_marker_only_changed_files"])
        self.assertEqual(
            "structured-patch-segment-manifest-v1",
            summary["classifier_evidence_profile"],
        )
        self.assertEqual("marker-only", summary["classifier_status"])
        self.assertEqual(summary["diff_digest"], summary["segment_manifest_digest"])
        self.assertEqual(1, summary["segment_count"])
        self.assertEqual(1, summary["marker_segment_count"])
        self.assertEqual(0, summary["substantive_segment_count"])
        self.assertTrue(validation["ok"])
        self.assertFalse(validation["ready_for_main_checkout"])
        self.assertTrue(validation["workspace_marker_classifier_digest_bound"])
        self.assertTrue(validation["workspace_marker_only_change_blocked"])
        self.assertFalse(summary["raw_segment_payload_stored"])
        self.assertFalse(receipt["raw_workspace_marker_payload_stored"])

    def test_structured_patch_segment_substantive_payload_with_marker_is_ready(self) -> None:
        marker_path = "docs/02-subsystems/agentic/README.md"
        test_path = "tests/unit/test_parallel_orchestration.py"
        receipt = self.service.ingest_worker_result(
            worker_id="codex-segment-substantive-worker",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["docs/", "tests/unit/"],
            changed_files=[marker_path, test_path],
            workspace_patch_segments_by_file={
                marker_path: [
                    {
                        "operation": "add",
                        "line_count": 1,
                        "contains_workspace_marker": True,
                    }
                ],
                test_path: [
                    {
                        "operation": "add",
                        "line_count": 4,
                        "contains_workspace_marker": False,
                    }
                ],
            },
            verification_results=_verification_results(),
            result_summary=(
                "Structured patch segment evidence separates marker and "
                "substantive payloads."
            ),
        )
        validation = self.service.validate_worker_result_receipt(receipt)
        summaries = {
            summary["file_path"]: summary
            for summary in receipt["workspace_marker_diff_summaries"]
        }

        self.assertEqual("accept-ready", receipt["integration_decision"])
        self.assertEqual(
            "marker-only-reviewed",
            receipt["workspace_marker_hygiene_status"],
        )
        self.assertEqual([marker_path], receipt["workspace_marker_only_changed_files"])
        self.assertEqual(
            "substantive",
            summaries[test_path]["classifier_status"],
        )
        self.assertEqual(1, summaries[test_path]["substantive_segment_count"])
        self.assertTrue(validation["ok"])
        self.assertTrue(validation["ready_for_main_checkout"])
        self.assertTrue(validation["workspace_marker_hygiene_digest_bound"])
        self.assertTrue(validation["workspace_marker_classifier_digest_bound"])

    def test_workspace_marker_diff_classifier_marks_substantive_diff_reviewed(self) -> None:
        marker_path = "docs/02-subsystems/agentic/README.md"
        substantive_path = "tests/unit/test_parallel_orchestration.py"
        marker_diff = (
            "diff --git a/docs/02-subsystems/agentic/README.md "
            "b/docs/02-subsystems/agentic/README.md\n"
            "@@\n"
            "+# workspace-enacted: patch-unit-marker "
            "target=docs/02-subsystems/agentic/README.md\n"
        )
        substantive_diff = (
            "diff --git a/tests/unit/test_parallel_orchestration.py "
            "b/tests/unit/test_parallel_orchestration.py\n"
            "@@\n"
            "+self.assertTrue(validation['workspace_marker_classifier_digest_bound'])\n"
        )
        receipt = self.service.ingest_worker_result(
            worker_id="codex-marker-classifier-worker",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["docs/", "tests/unit/"],
            changed_files=[marker_path, substantive_path],
            workspace_diff_by_file={
                marker_path: marker_diff,
                substantive_path: substantive_diff,
            },
            verification_results=_verification_results(),
            result_summary=(
                "Repo-local diff classifier separates marker-only and "
                "substantive changed files."
            ),
        )
        validation = self.service.validate_worker_result_receipt(receipt)

        self.assertEqual("accept-ready", receipt["integration_decision"])
        self.assertEqual(
            "marker-only-reviewed",
            receipt["workspace_marker_hygiene_status"],
        )
        self.assertEqual([marker_path], receipt["workspace_marker_only_changed_files"])
        self.assertEqual(2, receipt["workspace_marker_diff_summary_count"])
        self.assertEqual(
            ["marker-only", "substantive"],
            [
                summary["classifier_status"]
                for summary in receipt["workspace_marker_diff_summaries"]
            ],
        )
        self.assertTrue(validation["ok"])
        self.assertTrue(validation["ready_for_main_checkout"])
        self.assertTrue(validation["workspace_marker_classifier_digest_bound"])
        self.assertTrue(validation["workspace_marker_hygiene_digest_bound"])

    def test_workspace_marker_hygiene_allows_substantive_payload_with_reviewed_marker(self) -> None:
        marker_path = "docs/02-subsystems/agentic/README.md"
        receipt = self.service.ingest_worker_result(
            worker_id="codex-marker-reviewed-worker",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["docs/", "tests/unit/"],
            changed_files=[marker_path, "tests/unit/test_parallel_orchestration.py"],
            workspace_marker_only_changed_files=[marker_path],
            verification_results=_verification_results(),
            result_summary=(
                "Worker result carries a reviewed marker comment plus a "
                "substantive test change."
            ),
        )
        validation = self.service.validate_worker_result_receipt(receipt)

        self.assertEqual("accept-ready", receipt["integration_decision"])
        self.assertEqual(
            "marker-only-reviewed",
            receipt["workspace_marker_hygiene_status"],
        )
        self.assertTrue(validation["ok"])
        self.assertTrue(validation["ready_for_main_checkout"])
        self.assertTrue(validation["workspace_marker_hygiene_digest_bound"])
        self.assertTrue(validation["workspace_marker_classifier_digest_bound"])

    def test_remote_branch_pr_worker_result_requires_review_metadata(self) -> None:
        receipt = self.service.ingest_worker_result(
            worker_id="codex-remote-pr-worker",
            worker_role="external",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=[
                "src/omoikane/self_construction/",
                "specs/schemas/",
                "tests/unit/",
            ],
            changed_files=[
                "src/omoikane/self_construction/parallel_orchestration.py",
                "specs/schemas/parallel_codex_worker_result_receipt.schema",
                "tests/unit/test_parallel_orchestration.py",
            ],
            verification_results=_verification_results(),
            result_summary="Remote worker result carries branch and PR metadata.",
            source_system="remote-branch-pr-worker-result",
            remote_branch_ref="refs/remotes/origin/codex/remote-worker-metadata",
            remote_pr_ref="pull-request://omoikane/128",
        )
        validation = self.service.validate_worker_result_receipt(receipt)

        self.assertEqual("accept-ready", receipt["integration_decision"])
        self.assertEqual("remote-branch-pr-metadata-binding-v1", receipt["remote_metadata_profile"])
        self.assertEqual(
            "integrity-guardian-remote-review-authority-v1",
            receipt["remote_review_authority_profile"],
        )
        self.assertTrue(receipt["remote_metadata_bound"])
        self.assertTrue(validation["remote_metadata_bound"])
        self.assertTrue(validation["remote_metadata_digest_bound"])
        self.assertEqual(
            "remote-source-system-revocation-check-v1",
            receipt["remote_source_revocation_profile"],
        )
        self.assertEqual(
            "current-not-revoked",
            receipt["remote_source_revocation_status"],
        )
        self.assertTrue(validation["remote_source_revocation_digest_bound"])
        self.assertTrue(validation["remote_source_revocation_freshness_digest_bound"])
        self.assertTrue(validation["remote_source_revocation_not_revoked"])
        self.assertTrue(validation["remote_source_revocation_fresh"])
        self.assertTrue(validation["worker_identity_evidence_bound"])
        self.assertEqual(
            "remote-source-revocation-freshness-window-v1",
            receipt["remote_source_revocation_freshness_profile"],
        )
        self.assertEqual("fresh", receipt["remote_source_revocation_freshness_status"])
        self.assertEqual(
            "remote-source-revocation-signed-provider-timestamp-v1",
            receipt["remote_source_revocation_timestamp_profile"],
        )
        self.assertEqual(
            "remote-source-revocation-provider-timestamp-signature-v1",
            receipt["remote_source_revocation_timestamp_signature_profile"],
        )
        self.assertEqual(
            "remote-source-revocation-timestamp-replay-guard-v1",
            receipt["remote_source_revocation_timestamp_replay_guard_profile"],
        )
        self.assertEqual(
            "signed-current",
            receipt["remote_source_revocation_timestamp_status"],
        )
        self.assertEqual(
            "unique",
            receipt["remote_source_revocation_timestamp_replay_status"],
        )
        self.assertGreater(receipt["remote_source_revocation_freshness_window_seconds"], 0)
        self.assertLessEqual(
            receipt["remote_source_revocation_freshness_window_seconds"],
            900,
        )
        self.assertTrue(validation["remote_source_revocation_timestamp_digest_bound"])
        self.assertTrue(validation["remote_source_revocation_timestamp_signature_bound"])
        self.assertTrue(validation["remote_source_revocation_timestamp_signed_current"])
        self.assertTrue(
            validation[
                "remote_source_revocation_timestamp_replay_guard_digest_bound"
            ]
        )
        self.assertTrue(validation["remote_source_revocation_timestamp_unique"])
        self.assertEqual(
            "remote-source-content-identity-binding-v1",
            receipt["remote_source_content_profile"],
        )
        self.assertEqual("bound", receipt["remote_source_content_status"])
        self.assertTrue(receipt["remote_source_content_bound"])
        self.assertTrue(validation["remote_source_content_digest_bound"])
        self.assertTrue(validation["remote_source_content_bound"])
        self.assertTrue(validation["remote_source_content_status_bound"])
        self.assertEqual(
            "remote-source-main-ancestry-binding-v1",
            receipt["remote_source_ancestry_profile"],
        )
        self.assertEqual(MAIN_HEAD, receipt["remote_source_base_commit"])
        self.assertEqual(MAIN_HEAD, receipt["remote_source_merge_base_commit"])
        self.assertEqual("ancestor-bound", receipt["remote_source_ancestry_status"])
        self.assertTrue(receipt["remote_source_ancestry_bound"])
        self.assertTrue(validation["remote_source_ancestry_digest_bound"])
        self.assertTrue(validation["remote_source_ancestry_bound"])
        self.assertTrue(validation["remote_source_ancestry_status_bound"])
        self.assertTrue(validation["remote_source_base_commit_matches_worker"])
        self.assertTrue(receipt["remote_source_head_commit"])
        self.assertTrue(receipt["remote_source_tree_digest"])
        self.assertTrue(receipt["remote_source_diff_digest"])
        self.assertTrue(receipt["remote_source_content_digest"])
        self.assertTrue(receipt["remote_source_ancestry_digest"])
        self.assertFalse(receipt["raw_remote_metadata_payload_stored"])
        self.assertFalse(receipt["raw_remote_revocation_payload_stored"])
        self.assertFalse(receipt["raw_remote_revocation_freshness_payload_stored"])
        self.assertFalse(receipt["raw_remote_revocation_timestamp_payload_stored"])
        self.assertFalse(
            receipt["raw_remote_revocation_timestamp_replay_guard_payload_stored"]
        )
        self.assertFalse(receipt["raw_remote_source_content_payload_stored"])
        self.assertFalse(receipt["raw_remote_source_ancestry_payload_stored"])

    def test_remote_branch_pr_worker_result_blocks_revoked_source(self) -> None:
        receipt = self.service.ingest_worker_result(
            worker_id="codex-remote-pr-worker",
            worker_role="external",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=["src/omoikane/self_construction/parallel_orchestration.py"],
            verification_results=_verification_results(),
            result_summary="Remote worker result carries a revoked source check.",
            source_system="remote-branch-pr-worker-result",
            remote_branch_ref="refs/remotes/origin/codex/revoked-worker",
            remote_pr_ref="pull-request://omoikane/129",
            remote_source_revocation_status="revoked",
        )
        validation = self.service.validate_worker_result_receipt(receipt)

        self.assertEqual("blocked", receipt["integration_decision"])
        self.assertIn(
            "remote source revocation status must be current-not-revoked",
            receipt["blocking_reasons"],
        )
        self.assertTrue(validation["ok"])
        self.assertFalse(validation["ready_for_main_checkout"])
        self.assertTrue(validation["remote_source_revocation_digest_bound"])
        self.assertFalse(validation["remote_source_revocation_not_revoked"])
        self.assertTrue(validation["remote_source_revocation_fresh"])

    def test_remote_branch_pr_worker_result_blocks_expired_revocation_freshness(self) -> None:
        receipt = self.service.ingest_worker_result(
            worker_id="codex-remote-pr-worker",
            worker_role="external",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=["src/omoikane/self_construction/parallel_orchestration.py"],
            verification_results=_verification_results(),
            result_summary="Remote worker result carries an expired revocation check.",
            source_system="remote-branch-pr-worker-result",
            remote_branch_ref="refs/remotes/origin/codex/expired-worker",
            remote_pr_ref="pull-request://omoikane/130",
            remote_source_revocation_freshness_status="expired",
        )
        validation = self.service.validate_worker_result_receipt(receipt)

        self.assertEqual("blocked", receipt["integration_decision"])
        self.assertIn(
            "remote source revocation freshness status must be fresh",
            receipt["blocking_reasons"],
        )
        self.assertTrue(validation["ok"])
        self.assertFalse(validation["ready_for_main_checkout"])
        self.assertTrue(validation["remote_source_revocation_digest_bound"])
        self.assertTrue(validation["remote_source_revocation_freshness_digest_bound"])
        self.assertFalse(validation["remote_source_revocation_fresh"])

    def test_remote_branch_pr_worker_result_blocks_stale_provider_timestamp(self) -> None:
        receipt = self.service.ingest_worker_result(
            worker_id="codex-remote-pr-worker",
            worker_role="external",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=["src/omoikane/self_construction/parallel_orchestration.py"],
            verification_results=_verification_results(),
            result_summary="Remote worker result carries a stale provider timestamp.",
            source_system="remote-branch-pr-worker-result",
            remote_branch_ref="refs/remotes/origin/codex/stale-timestamp-worker",
            remote_pr_ref="pull-request://omoikane/131",
            remote_source_revocation_timestamp_status="stale",
        )
        validation = self.service.validate_worker_result_receipt(receipt)

        self.assertEqual("blocked", receipt["integration_decision"])
        self.assertIn(
            "remote source revocation timestamp status must be signed-current",
            receipt["blocking_reasons"],
        )
        self.assertTrue(validation["ok"])
        self.assertFalse(validation["ready_for_main_checkout"])
        self.assertTrue(validation["remote_source_revocation_timestamp_digest_bound"])
        self.assertTrue(validation["remote_source_revocation_timestamp_signature_bound"])
        self.assertFalse(
            validation["remote_source_revocation_timestamp_signed_current"]
        )

    def test_remote_branch_pr_worker_result_blocks_replayed_provider_timestamp(self) -> None:
        receipt = self.service.ingest_worker_result(
            worker_id="codex-remote-pr-worker",
            worker_role="external",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=["src/omoikane/self_construction/parallel_orchestration.py"],
            verification_results=_verification_results(),
            result_summary="Remote worker result carries a replayed provider timestamp.",
            source_system="remote-branch-pr-worker-result",
            remote_branch_ref="refs/remotes/origin/codex/replayed-timestamp-worker",
            remote_pr_ref="pull-request://omoikane/132",
            remote_source_revocation_timestamp_replay_status="replayed",
        )
        validation = self.service.validate_worker_result_receipt(receipt)

        self.assertEqual("blocked", receipt["integration_decision"])
        self.assertIn(
            "remote source revocation timestamp replay status must be unique",
            receipt["blocking_reasons"],
        )
        self.assertTrue(validation["ok"])
        self.assertFalse(validation["ready_for_main_checkout"])
        self.assertTrue(
            validation[
                "remote_source_revocation_timestamp_replay_guard_digest_bound"
            ]
        )
        self.assertFalse(validation["remote_source_revocation_timestamp_unique"])

    def test_remote_branch_pr_worker_result_blocks_content_mismatch(self) -> None:
        receipt = self.service.ingest_worker_result(
            worker_id="codex-remote-pr-worker",
            worker_role="external",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=["src/omoikane/self_construction/parallel_orchestration.py"],
            verification_results=_verification_results(),
            result_summary="Remote worker result reports a content identity mismatch.",
            source_system="remote-branch-pr-worker-result",
            remote_branch_ref="refs/remotes/origin/codex/content-mismatch-worker",
            remote_pr_ref="pull-request://omoikane/133",
            remote_source_content_status="mismatch",
        )
        validation = self.service.validate_worker_result_receipt(receipt)

        self.assertEqual("blocked", receipt["integration_decision"])
        self.assertIn(
            "remote source content status must be bound",
            receipt["blocking_reasons"],
        )
        self.assertTrue(validation["ok"])
        self.assertFalse(validation["ready_for_main_checkout"])
        self.assertTrue(validation["remote_source_content_digest_bound"])
        self.assertTrue(validation["remote_source_content_bound"])
        self.assertFalse(validation["remote_source_content_status_bound"])

    def test_remote_branch_pr_worker_result_blocks_unrelated_ancestry(self) -> None:
        receipt = self.service.ingest_worker_result(
            worker_id="codex-remote-pr-worker",
            worker_role="external",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=["src/omoikane/self_construction/parallel_orchestration.py"],
            verification_results=_verification_results(),
            result_summary="Remote worker result reports unrelated source ancestry.",
            source_system="remote-branch-pr-worker-result",
            remote_branch_ref="refs/remotes/origin/codex/unrelated-ancestry-worker",
            remote_pr_ref="pull-request://omoikane/134",
            remote_source_ancestry_status="unrelated",
        )
        validation = self.service.validate_worker_result_receipt(receipt)

        self.assertEqual("blocked", receipt["integration_decision"])
        self.assertIn(
            "remote source ancestry status must be ancestor-bound",
            receipt["blocking_reasons"],
        )
        self.assertTrue(validation["ok"])
        self.assertFalse(validation["ready_for_main_checkout"])
        self.assertTrue(validation["remote_source_ancestry_digest_bound"])
        self.assertTrue(validation["remote_source_ancestry_bound"])
        self.assertFalse(validation["remote_source_ancestry_status_bound"])
        self.assertTrue(validation["remote_source_base_commit_matches_worker"])
        self.assertFalse(receipt["raw_remote_source_ancestry_payload_stored"])

    def test_remote_branch_pr_worker_result_without_pr_metadata_blocks(self) -> None:
        receipt = self.service.ingest_worker_result(
            worker_id="codex-remote-pr-worker",
            worker_role="external",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=["src/omoikane/self_construction/parallel_orchestration.py"],
            verification_results=_verification_results(),
            result_summary="Remote worker result is missing PR metadata.",
            source_system="remote-branch-pr-worker-result",
            remote_branch_ref="refs/remotes/origin/codex/remote-worker-metadata",
        )

        self.assertEqual("blocked", receipt["integration_decision"])
        self.assertIn(
            "remote PR metadata requires remote_pr_ref",
            receipt["blocking_reasons"],
        )

    def test_stale_worker_result_is_schema_bound_but_blocked(self) -> None:
        receipt = self.service.ingest_worker_result(
            worker_id="codex-worker-stale",
            worker_role="explorer",
            worker_result_status="stale",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit="b" * 40,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=["src/omoikane/self_construction/parallel_orchestration.py"],
            verification_results=_verification_results(),
            result_summary="Stale worker result should not be integrated.",
        )
        validation = self.service.validate_worker_result_receipt(receipt)

        self.assertEqual("blocked", receipt["integration_decision"])
        self.assertIn(
            "worker_base_commit must match main_checkout_head",
            receipt["blocking_reasons"],
        )
        self.assertTrue(validation["ok"])
        self.assertFalse(validation["ready_for_main_checkout"])
        self.assertFalse(validation["base_head_matches"])

    def test_scope_escape_blocks_integration(self) -> None:
        receipt = self.service.ingest_worker_result(
            worker_id="codex-worker-escape",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=["tests/unit/test_parallel_orchestration.py"],
            verification_results=_verification_results(),
            result_summary="Worker touched a file outside its declared ownership.",
        )

        self.assertEqual("blocked", receipt["integration_decision"])
        self.assertTrue(
            any(
                reason.startswith("changed file outside worker ownership scope")
                for reason in receipt["blocking_reasons"]
            )
        )

    def test_receipt_digest_detects_tampering(self) -> None:
        receipt = self.service.ingest_worker_result(
            worker_id="codex-worker-unit",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=["src/omoikane/self_construction/parallel_orchestration.py"],
            verification_results=_verification_results(),
            result_summary="Unit worker result ready for main checkout integration.",
        )
        tampered = dict(receipt)
        tampered["changed_files"] = [
            "src/omoikane/self_construction/parallel_orchestration.py",
            "src/omoikane/self_construction/gaps.py",
        ]

        validation = self.service.validate_worker_result_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertIn("changed_file_count mismatch", validation["errors"])
        self.assertIn("receipt_digest mismatch", validation["errors"])

    def test_worker_identity_signature_tampering_blocks_integration(self) -> None:
        receipt = self.service.ingest_worker_result(
            worker_id="codex-worker-unit",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=["src/omoikane/self_construction/parallel_orchestration.py"],
            verification_results=_verification_results(),
            result_summary="Worker result with tampered identity evidence.",
        )
        tampered = dict(receipt)
        tampered["worker_identity_signature_digest"] = "f" * 64
        tampered["receipt_digest"] = self.service._receipt_digest(tampered)

        validation = self.service.validate_worker_result_receipt(tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["ready_for_main_checkout"])
        self.assertFalse(validation["worker_identity_evidence_bound"])
        self.assertIn(
            "worker_identity_signature_digest mismatch",
            tampered["blocking_reasons"] or validation["errors"],
        )

    def test_yaoyorozu_dispatch_receipt_bridges_to_parallel_ingestion(self) -> None:
        patch_receipt_digest = "c" * 64
        dispatch_receipt = {
            "kind": "yaoyorozu_worker_dispatch_receipt",
            "receipt_id": "yaoyorozu-dispatch-receipt-aaaaaaaaaaaa",
            "dispatch_plan_digest": "d" * 64,
            "receipt_digest": "e" * 64,
            "results": [
                {
                    "report": {
                        "patch_candidate_receipt": {
                            "receipt_ref": (
                                "worker-patch://"
                                "yaoyorozu-worker-patch-candidate-bbbbbbbbbbbb"
                            ),
                            "receipt_digest": patch_receipt_digest,
                            "patch_candidates": [
                                {
                                    "target_path": (
                                        "src/omoikane/agentic/yaoyorozu.py"
                                    ),
                                    "patch_descriptor": {
                                        "target_path": (
                                            "src/omoikane/agentic/yaoyorozu.py"
                                        )
                                    },
                                }
                            ],
                        }
                    }
                }
            ],
        }

        receipt = self.service.ingest_yaoyorozu_dispatch_receipt(
            dispatch_receipt=dispatch_receipt,
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            verification_results=_verification_results(),
        )
        validation = self.service.validate_worker_result_receipt(receipt)

        self.assertEqual("yaoyorozu-worker-dispatch", receipt["source_system"])
        self.assertEqual("accept-ready", receipt["integration_decision"])
        self.assertEqual(
            ["src/omoikane/agentic/yaoyorozu.py"],
            receipt["changed_files"],
        )
        self.assertEqual(
            [patch_receipt_digest],
            receipt["upstream_patch_candidate_receipt_digests"],
        )
        self.assertTrue(receipt["worker_identity_evidence_bound"])
        self.assertTrue(validation["ok"])
        self.assertTrue(validation["ready_for_main_checkout"])
        self.assertTrue(validation["worker_identity_evidence_bound"])
        self.assertFalse(receipt["raw_upstream_payload_stored"])
        self.assertFalse(receipt["raw_worker_identity_payload_stored"])

    def test_integration_batch_orders_ready_receipts_and_quarantines_blocked(self) -> None:
        first_receipt = self.service.ingest_worker_result(
            worker_id="codex-worker-runtime",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=[
                "src/omoikane/self_construction/parallel_orchestration.py",
            ],
            verification_results=_verification_results(),
            result_summary="Runtime orchestration patch is ready.",
        )
        second_receipt = self.service.ingest_worker_result(
            worker_id="codex-worker-tests",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["tests/unit/"],
            changed_files=["tests/unit/test_parallel_orchestration.py"],
            verification_results=_verification_results(),
            result_summary="Unit test patch is ready.",
        )
        blocked_receipt = self.service.ingest_worker_result(
            worker_id="codex-worker-stale",
            worker_role="explorer",
            worker_result_status="stale",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit="b" * 40,
            ownership_scope=["docs/"],
            changed_files=["docs/07-reference-implementation/README.md"],
            verification_results=_verification_results(),
            result_summary="Stale read-only result must stay quarantined.",
        )

        batch = self.service.plan_integration_batch(
            receipts=[blocked_receipt, second_receipt, first_receipt],
            main_checkout_head=MAIN_HEAD,
            verification_results=_verification_results(),
            result_summary="Two disjoint ready receipts can be integrated.",
        )
        validation = self.service.validate_integration_batch_receipt(batch)

        self.assertEqual("integration-ready", batch["batch_decision"])
        self.assertEqual(3, batch["source_receipt_count"])
        self.assertEqual(1, batch["quarantined_receipt_count"])
        self.assertEqual(2, len(batch["ordered_integration_receipt_refs"]))
        self.assertEqual(
            sorted(
                [first_receipt["receipt_digest"], second_receipt["receipt_digest"]],
            ),
            batch["ordered_integration_receipt_digests"],
        )
        self.assertEqual([blocked_receipt["receipt_ref"]], batch["quarantined_receipt_refs"])
        self.assertEqual(
            "blocked-receipt-quarantine-manifest-v1",
            batch["quarantine_profile"],
        )
        self.assertTrue(batch["quarantined_receipt_set_digest"])
        self.assertTrue(batch["blocked_receipts_quarantined"])
        self.assertEqual(0, batch["conflict_count"])
        self.assertTrue(validation["ok"])
        self.assertTrue(validation["ready_for_integration"])
        self.assertTrue(validation["input_receipt_set_digest_bound"])
        self.assertTrue(validation["ordered_integration_digest_bound"])
        self.assertTrue(validation["changed_file_owner_manifest_digest_bound"])
        self.assertTrue(validation["quarantined_receipt_set_digest_bound"])
        self.assertTrue(validation["conflict_free"])
        self.assertTrue(validation["blocked_receipts_quarantined"])
        self.assertFalse(batch["raw_worker_receipt_payload_stored"])
        self.assertFalse(batch["raw_conflict_payload_stored"])
        self.assertFalse(batch["raw_verification_payload_stored"])

    def test_integration_batch_blocks_changed_file_conflicts(self) -> None:
        changed_file = "src/omoikane/self_construction/parallel_orchestration.py"
        first_receipt = self.service.ingest_worker_result(
            worker_id="codex-worker-runtime-a",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=[changed_file],
            verification_results=_verification_results(),
            result_summary="First runtime patch is ready.",
        )
        second_receipt = self.service.ingest_worker_result(
            worker_id="codex-worker-runtime-b",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=[changed_file],
            verification_results=_verification_results(),
            result_summary="Second runtime patch overlaps the first.",
        )

        batch = self.service.plan_integration_batch(
            receipts=[first_receipt, second_receipt],
            main_checkout_head=MAIN_HEAD,
            verification_results=_verification_results(),
            result_summary="Overlapping ready receipts must be blocked.",
        )
        validation = self.service.validate_integration_batch_receipt(batch)

        self.assertEqual("blocked", batch["batch_decision"])
        self.assertEqual(1, batch["conflict_count"])
        self.assertEqual(changed_file, batch["changed_file_conflicts"][0]["file_path"])
        self.assertIn(
            "changed file conflicts must be resolved before integration",
            batch["blocking_reasons"],
        )
        self.assertTrue(validation["ok"])
        self.assertFalse(validation["ready_for_integration"])
        self.assertTrue(validation["conflict_blocked"])
        self.assertTrue(validation["conflict_digest_bound"])
        self.assertTrue(validation["changed_file_owner_manifest_digest_bound"])
        self.assertTrue(validation["quarantined_receipt_set_digest_bound"])

    def test_integration_execution_receipt_binds_ordered_apply_plan(self) -> None:
        first_receipt = self.service.ingest_worker_result(
            worker_id="codex-worker-runtime",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=[
                "src/omoikane/self_construction/parallel_orchestration.py",
            ],
            verification_results=_verification_results(),
            result_summary="Runtime orchestration patch is ready.",
        )
        second_receipt = self.service.ingest_worker_result(
            worker_id="codex-worker-tests",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["tests/unit/"],
            changed_files=["tests/unit/test_parallel_orchestration.py"],
            verification_results=_verification_results(),
            result_summary="Unit test patch is ready.",
        )
        batch = self.service.plan_integration_batch(
            receipts=[first_receipt, second_receipt],
            main_checkout_head=MAIN_HEAD,
            verification_results=_verification_results(),
            result_summary="Disjoint ready receipts can be integrated.",
        )

        execution = self.service.plan_integration_execution(
            batch_receipt=batch,
            current_checkout_head=MAIN_HEAD,
            post_apply_verification_results=_verification_results(),
            result_summary="Ordered apply plan is ready before commit.",
        )
        validation = self.service.validate_integration_execution_receipt(execution)

        self.assertEqual("ready-to-apply", execution["execution_decision"])
        self.assertEqual(
            "parallel-codex-integration-execution-plan-v1",
            execution["profile_id"],
        )
        self.assertEqual(2, execution["apply_step_count"])
        for step in execution["apply_steps"]:
            self.assertTrue(step["patch_artifact_ref"].startswith("patch://parallel-codex/"))
            self.assertTrue(step["patch_artifact_digest"])
            self.assertFalse(step["raw_patch_payload_stored"])
        self.assertTrue(validation["ok"])
        self.assertTrue(validation["ready_to_apply"])
        self.assertTrue(validation["source_batch_receipt_digest_bound"])
        self.assertTrue(validation["current_head_matches_batch"])
        self.assertTrue(validation["apply_plan_digest_bound"])
        self.assertTrue(validation["pre_apply_dry_run_manifest_digest_bound"])
        self.assertTrue(validation["pre_apply_dry_run_passed"])
        self.assertTrue(validation["post_apply_verification_manifest_digest_bound"])
        self.assertTrue(validation["required_verifications_passed"])
        self.assertEqual(
            "pre-apply-dry-run-check-v1",
            execution["pre_apply_dry_run_profile"],
        )
        self.assertEqual(
            execution["apply_step_count"],
            execution["pre_apply_dry_run_result_count"],
        )
        for dry_run in execution["pre_apply_dry_run_results"]:
            self.assertEqual(
                "command-bound-git-apply-check-v1",
                dry_run["command_profile"],
            )
            self.assertEqual(
                f"git apply --check {dry_run['patch_artifact_ref']}",
                dry_run["command"],
            )
            self.assertTrue(dry_run["patch_artifact_digest_bound"])
            self.assertTrue(dry_run["command_receipt_digest"])
            self.assertFalse(dry_run["raw_patch_payload_stored"])
        self.assertTrue(execution["pre_apply_dry_run_passed"])
        self.assertFalse(execution["raw_batch_payload_stored"])
        self.assertFalse(execution["raw_apply_plan_payload_stored"])
        self.assertFalse(execution["raw_pre_apply_dry_run_payload_stored"])
        self.assertFalse(execution["raw_worker_receipt_payload_stored"])
        self.assertFalse(execution["raw_verification_payload_stored"])

    def test_integration_execution_blocks_failed_pre_apply_dry_run(self) -> None:
        receipt = self.service.ingest_worker_result(
            worker_id="codex-worker-runtime",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=[
                "src/omoikane/self_construction/parallel_orchestration.py",
            ],
            verification_results=_verification_results(),
            result_summary="Runtime orchestration patch is ready.",
        )
        batch = self.service.plan_integration_batch(
            receipts=[receipt],
            main_checkout_head=MAIN_HEAD,
            verification_results=_verification_results(),
            result_summary="Single ready receipt can be rehearsed.",
        )

        execution = self.service.plan_integration_execution(
            batch_receipt=batch,
            current_checkout_head=MAIN_HEAD,
            pre_apply_dry_run_results=[
                {
                    "status": "fail",
                    "exit_code": 1,
                    "stdout_excerpt": "",
                    "stderr_excerpt": "patch does not apply",
                }
            ],
            post_apply_verification_results=_verification_results(),
            result_summary="Failed dry-run blocks checkout mutation.",
        )
        validation = self.service.validate_integration_execution_receipt(execution)

        self.assertEqual("blocked", execution["execution_decision"])
        self.assertIn(
            "pre-apply dry-run checks must pass",
            execution["blocking_reasons"],
        )
        self.assertTrue(validation["ok"])
        self.assertFalse(validation["ready_to_apply"])
        self.assertTrue(validation["pre_apply_dry_run_manifest_digest_bound"])
        self.assertFalse(validation["pre_apply_dry_run_passed"])
        self.assertTrue(validation["apply_plan_digest_bound"])

    def test_integration_execution_blocks_unbound_pre_apply_command(self) -> None:
        receipt = self.service.ingest_worker_result(
            worker_id="codex-worker-runtime",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=[
                "src/omoikane/self_construction/parallel_orchestration.py",
            ],
            verification_results=_verification_results(),
            result_summary="Runtime orchestration patch is ready.",
        )
        batch = self.service.plan_integration_batch(
            receipts=[receipt],
            main_checkout_head=MAIN_HEAD,
            verification_results=_verification_results(),
            result_summary="Single ready receipt can be rehearsed.",
        )

        execution = self.service.plan_integration_execution(
            batch_receipt=batch,
            current_checkout_head=MAIN_HEAD,
            pre_apply_dry_run_results=[
                {
                    "command": "git apply --check receipt://parallel-codex/unit",
                    "status": "pass",
                    "exit_code": 0,
                    "stdout_excerpt": "pre-apply dry run passed",
                    "stderr_excerpt": "",
                }
            ],
            post_apply_verification_results=_verification_results(),
            result_summary="Unbound dry-run command blocks checkout mutation.",
        )
        validation = self.service.validate_integration_execution_receipt(execution)

        self.assertEqual("blocked", execution["execution_decision"])
        self.assertIn(
            "pre-apply dry-run checks must pass",
            execution["blocking_reasons"],
        )
        self.assertFalse(validation["ok"])
        self.assertIn(
            "pre_apply command must be git apply --check patch artifact",
            validation["errors"],
        )
        self.assertFalse(validation["ready_to_apply"])
        self.assertTrue(validation["pre_apply_dry_run_manifest_digest_bound"])
        self.assertFalse(validation["pre_apply_dry_run_passed"])
        self.assertTrue(
            execution["pre_apply_dry_run_results"][0][
                "patch_artifact_digest_bound"
            ]
        )

    def test_integration_execution_blocks_conflict_batch(self) -> None:
        changed_file = "src/omoikane/self_construction/parallel_orchestration.py"
        first_receipt = self.service.ingest_worker_result(
            worker_id="codex-worker-runtime-a",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=[changed_file],
            verification_results=_verification_results(),
            result_summary="First runtime patch is ready.",
        )
        second_receipt = self.service.ingest_worker_result(
            worker_id="codex-worker-runtime-b",
            worker_role="worker",
            worker_result_status="completed",
            main_checkout_head=MAIN_HEAD,
            worker_base_commit=MAIN_HEAD,
            ownership_scope=["src/omoikane/self_construction/"],
            changed_files=[changed_file],
            verification_results=_verification_results(),
            result_summary="Second runtime patch overlaps the first.",
        )
        batch = self.service.plan_integration_batch(
            receipts=[first_receipt, second_receipt],
            main_checkout_head=MAIN_HEAD,
            verification_results=_verification_results(),
            result_summary="Overlapping ready receipts must be blocked.",
        )

        execution = self.service.plan_integration_execution(
            batch_receipt=batch,
            current_checkout_head=MAIN_HEAD,
            post_apply_verification_results=_verification_results(),
            result_summary="Conflict batch cannot be applied.",
        )
        validation = self.service.validate_integration_execution_receipt(execution)

        self.assertEqual("blocked", execution["execution_decision"])
        self.assertIn(
            "source integration batch must be integration-ready before apply",
            execution["blocking_reasons"],
        )
        self.assertTrue(validation["ok"])
        self.assertFalse(validation["ready_to_apply"])
        self.assertTrue(validation["blocked_on_source_batch"])
        self.assertTrue(validation["apply_plan_digest_bound"])


if __name__ == "__main__":
    unittest.main()
