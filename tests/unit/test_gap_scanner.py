from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from omoikane.self_construction.gaps import GapScanner


class GapScannerTests(unittest.TestCase):
    def test_scan_reports_empty_eval_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            (repo_root / "evals" / "cognitive").mkdir(parents=True)
            (repo_root / "evals" / "safety").mkdir(parents=True)
            (repo_root / "evals" / "safety" / "immutable_boundary.yaml").write_text(
                "eval_id: immutable_boundary\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(1, report["empty_eval_surface_count"])
            self.assertEqual(["evals/cognitive"], report["empty_eval_surfaces"])
            self.assertTrue(
                any(task["kind"] == "empty-eval-surface" for task in report["prioritized_tasks"])
            )

    def test_scan_ignores_eval_surface_with_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            (repo_root / "evals" / "cognitive").mkdir(parents=True)
            (repo_root / "evals" / "cognitive" / "qualia_contract.yaml").write_text(
                "eval_id: qualia_contract\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(0, report["empty_eval_surface_count"])
            self.assertEqual([], report["empty_eval_surfaces"])

    @staticmethod
    def _bootstrap_repo(repo_root: Path) -> None:
        (repo_root / "meta").mkdir(parents=True)
        (repo_root / "meta" / "open-questions.md").write_text("# Open Questions\n", encoding="utf-8")
        for readme in (
            repo_root / "specs" / "interfaces" / "README.md",
            repo_root / "specs" / "schemas" / "README.md",
            repo_root / "specs" / "invariants" / "README.md",
        ):
            readme.parent.mkdir(parents=True, exist_ok=True)
            readme.write_text("# bootstrap\n", encoding="utf-8")
        (repo_root / "evals").mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    unittest.main()
