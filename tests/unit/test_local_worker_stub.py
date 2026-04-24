from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
import unittest

from omoikane.agentic.local_worker_stub import (
    YAOYOROZU_DEPENDENCY_MODULE_ORIGIN_PROFILE,
    YAOYOROZU_WORKER_PATCH_PRIORITY_PROFILE,
    build_worker_module_origin,
    build_patch_candidate_receipt,
    build_workspace_delta_receipt,
)


class LocalWorkerStubTests(unittest.TestCase):
    def _run_git(self, repo_root: Path, *args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )

    def _init_repo(self, repo_root: Path) -> None:
        self._run_git(repo_root, "init", "-q")
        self._run_git(repo_root, "config", "user.name", "Codex Builder")
        self._run_git(repo_root, "config", "user.email", "codex@example.invalid")

    def test_worker_module_origin_reports_actual_stub_file(self) -> None:
        origin = build_worker_module_origin()

        self.assertEqual(YAOYOROZU_DEPENDENCY_MODULE_ORIGIN_PROFILE, origin["profile"])
        self.assertEqual("omoikane.agentic.local_worker_stub", origin["module_name"])
        self.assertTrue(str(origin["module_file"]).endswith("omoikane/agentic/local_worker_stub.py"))
        self.assertEqual(64, len(str(origin["module_digest"])))
        self.assertEqual(64, len(str(origin["origin_digest"])))
        self.assertTrue(origin["search_path_head"])

    def test_patch_candidate_receipt_ranks_runtime_before_test_coverage(self) -> None:
        with tempfile.TemporaryDirectory(prefix="omoikane-worker-stub-") as temp_dir:
            repo_root = Path(temp_dir)
            runtime_path = repo_root / "src/omoikane/runtime_worker.py"
            runtime_path.parent.mkdir(parents=True, exist_ok=True)
            runtime_path.write_text("def runtime_worker():\n    return 'baseline'\n", encoding="utf-8")
            self._init_repo(repo_root)
            self._run_git(repo_root, "add", "src/omoikane/runtime_worker.py")
            self._run_git(repo_root, "commit", "-q", "-m", "baseline")

            runtime_path.write_text(
                "def runtime_worker():\n    return 'mutated-runtime'\n",
                encoding="utf-8",
            )
            test_path = repo_root / "tests/unit/test_runtime_worker.py"
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text(
                "def test_runtime_worker_placeholder():\n    assert True\n",
                encoding="utf-8",
            )

            delta_receipt = build_workspace_delta_receipt(
                workspace_root=repo_root,
                dispatch_plan_ref="dispatch://unit-test",
                dispatch_unit_ref="worker-dispatch-0123456789ab",
                target_paths=["src/omoikane/", "tests/unit/"],
            )
            receipt = build_patch_candidate_receipt(
                workspace_root=repo_root,
                dispatch_plan_ref="dispatch://unit-test",
                dispatch_unit_ref="worker-dispatch-0123456789ab",
                source_ref="agents/builders/codex-builder.yaml",
                coverage_area="runtime",
                target_paths=["src/omoikane/", "tests/unit/"],
                workspace_delta_receipt=delta_receipt,
            )

            self.assertEqual("candidate-ready", receipt["status"])
            self.assertEqual(YAOYOROZU_WORKER_PATCH_PRIORITY_PROFILE, receipt["priority_profile"])
            self.assertEqual(2, receipt["patch_candidate_count"])
            self.assertEqual(
                receipt["ranked_candidate_ids"],
                [candidate["candidate_id"] for candidate in receipt["patch_candidates"]],
            )
            first_candidate, second_candidate = receipt["patch_candidates"]
            self.assertEqual("src/omoikane/runtime_worker.py", first_candidate["target_path"])
            self.assertEqual(1, first_candidate["priority_rank"])
            self.assertGreater(first_candidate["priority_score"], second_candidate["priority_score"])
            self.assertIn(first_candidate["priority_tier"], {"high", "critical"})
            self.assertEqual("tests/unit/test_runtime_worker.py", second_candidate["target_path"])
            self.assertEqual(2, second_candidate["priority_rank"])
            self.assertEqual(first_candidate["priority_tier"], receipt["highest_priority_tier"])
            self.assertEqual(first_candidate["priority_score"], receipt["highest_priority_score"])

    def test_patch_candidate_receipt_reports_none_priority_when_clean(self) -> None:
        with tempfile.TemporaryDirectory(prefix="omoikane-worker-stub-clean-") as temp_dir:
            repo_root = Path(temp_dir)
            runtime_path = repo_root / "src/omoikane/runtime_worker.py"
            runtime_path.parent.mkdir(parents=True, exist_ok=True)
            runtime_path.write_text("def runtime_worker():\n    return 'baseline'\n", encoding="utf-8")
            self._init_repo(repo_root)
            self._run_git(repo_root, "add", "src/omoikane/runtime_worker.py")
            self._run_git(repo_root, "commit", "-q", "-m", "baseline")

            delta_receipt = build_workspace_delta_receipt(
                workspace_root=repo_root,
                dispatch_plan_ref="dispatch://unit-test",
                dispatch_unit_ref="worker-dispatch-0123456789ab",
                target_paths=["src/omoikane/"],
            )
            receipt = build_patch_candidate_receipt(
                workspace_root=repo_root,
                dispatch_plan_ref="dispatch://unit-test",
                dispatch_unit_ref="worker-dispatch-0123456789ab",
                source_ref="agents/builders/codex-builder.yaml",
                coverage_area="runtime",
                target_paths=["src/omoikane/"],
                workspace_delta_receipt=delta_receipt,
            )

            self.assertEqual("no-candidates", receipt["status"])
            self.assertEqual([], receipt["ranked_candidate_ids"])
            self.assertEqual("none", receipt["highest_priority_tier"])
            self.assertEqual(0, receipt["highest_priority_score"])


if __name__ == "__main__":
    unittest.main()
