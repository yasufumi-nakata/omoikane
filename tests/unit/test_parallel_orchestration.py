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
        self.assertTrue(validation["receipt_digest_bound"])
        self.assertFalse(receipt["raw_patch_payload_stored"])
        self.assertFalse(receipt["raw_transcript_payload_stored"])
        self.assertFalse(receipt["raw_verification_payload_stored"])

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


if __name__ == "__main__":
    unittest.main()
