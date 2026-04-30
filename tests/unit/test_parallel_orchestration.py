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
        self.assertTrue(receipt["worker_identity_evidence_bound"])
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
        self.assertEqual(0, receipt["remote_source_revocation_freshness_window_seconds"])
        self.assertTrue(validation["receipt_digest_bound"])
        self.assertFalse(receipt["raw_patch_payload_stored"])
        self.assertFalse(receipt["raw_worker_identity_payload_stored"])
        self.assertFalse(receipt["raw_remote_metadata_payload_stored"])
        self.assertFalse(receipt["raw_remote_revocation_payload_stored"])
        self.assertFalse(receipt["raw_remote_revocation_freshness_payload_stored"])
        self.assertFalse(receipt["raw_remote_revocation_timestamp_payload_stored"])
        self.assertFalse(
            receipt["raw_remote_revocation_timestamp_replay_guard_payload_stored"]
        )
        self.assertFalse(receipt["raw_transcript_payload_stored"])
        self.assertFalse(receipt["raw_verification_payload_stored"])

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
        self.assertFalse(receipt["raw_remote_metadata_payload_stored"])
        self.assertFalse(receipt["raw_remote_revocation_payload_stored"])
        self.assertFalse(receipt["raw_remote_revocation_freshness_payload_stored"])
        self.assertFalse(receipt["raw_remote_revocation_timestamp_payload_stored"])
        self.assertFalse(
            receipt["raw_remote_revocation_timestamp_replay_guard_payload_stored"]
        )

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


if __name__ == "__main__":
    unittest.main()
