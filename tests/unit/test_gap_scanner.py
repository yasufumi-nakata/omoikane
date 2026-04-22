from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from omoikane.self_construction.gaps import GapScanner


class GapScannerTests(unittest.TestCase):
    def test_scan_reports_missing_required_reference_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            (repo_root / "references" / "verification-checklist.md").unlink()

            report = GapScanner().scan(repo_root)

            self.assertEqual(1, report["missing_required_reference_file_count"])
            self.assertEqual(
                ["references/verification-checklist.md"],
                report["missing_required_reference_files"],
            )
            self.assertTrue(
                any(task["kind"] == "missing-reference-file" for task in report["prioritized_tasks"])
            )

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

    def test_scan_reports_missing_catalog_next_priority(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            (repo_root / "specs" / "catalog.yaml").write_text(
                "catalog_version: 1\nnext_priority:\n  - specs/schemas/connectome_document.schema\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(1, report["catalog_pending_count"])
            self.assertEqual(
                ["specs/schemas/connectome_document.schema"],
                report["catalog_pending_files"],
            )
            self.assertTrue(
                any(task["kind"] == "catalog-next-priority" for task in report["prioritized_tasks"])
            )

    def test_scan_reports_interface_inventory_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            interfaces_root = repo_root / "specs" / "interfaces"
            (interfaces_root / "README.md").write_text(
                "# Interfaces\n\n- `kernel.identity.v0.idl`\n",
                encoding="utf-8",
            )
            (interfaces_root / "kernel.identity.v0.idl").write_text(
                "idl_version: 1\n",
                encoding="utf-8",
            )
            (interfaces_root / "kernel.broker.v0.idl").write_text(
                "idl_version: 1\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(1, report["inventory_drift_count"])
            self.assertEqual(
                "specs/interfaces/README.md",
                report["inventory_drift_hits"][0]["path"],
            )
            self.assertIn("kernel.broker.v0.idl", report["inventory_drift_hits"][0]["line"])
            self.assertTrue(
                any(task["kind"] == "inventory-drift" for task in report["prioritized_tasks"])
            )

    def test_scan_reports_schema_inventory_drift_for_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            schemas_root = repo_root / "specs" / "schemas"
            (schemas_root / "README.md").write_text(
                "# Schemas\n\n- `identity_record.schema`\n",
                encoding="utf-8",
            )
            (schemas_root / "identity_record.schema").write_text(
                "{\n  \"type\": \"object\"\n}\n",
                encoding="utf-8",
            )
            (schemas_root / "build_request.yaml").write_text(
                "type: object\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(1, report["inventory_drift_count"])
            self.assertEqual(
                "specs/schemas/README.md",
                report["inventory_drift_hits"][0]["path"],
            )
            self.assertIn("build_request.yaml", report["inventory_drift_hits"][0]["line"])

    def test_scan_reports_truth_source_future_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            interface_path = repo_root / "specs" / "interfaces" / "governance.oversight.v0.idl"
            interface_path.write_text(
                "compatibility:\n"
                "  notes:\n"
                "    - Jurisdiction-specific legal execution remains future work.\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(1, report["future_work_hit_count"])
            self.assertEqual(
                "specs/interfaces/governance.oversight.v0.idl",
                report["future_work_hits"][0]["path"],
            )
            self.assertTrue(
                any(task["kind"] == "future-work" for task in report["prioritized_tasks"])
            )

    def test_scan_ignores_deferred_surface_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            interface_path = repo_root / "specs" / "interfaces" / "mind.semantic.v0.idl"
            interface_path.write_text(
                "compatibility:\n"
                "  notes:\n"
                "    - procedural-memory must remain a deferred surface in v0\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(0, report["future_work_hit_count"])
            self.assertEqual([], report["future_work_hits"])

    @staticmethod
    def _bootstrap_repo(repo_root: Path) -> None:
        (repo_root / "meta").mkdir(parents=True)
        (repo_root / "meta" / "open-questions.md").write_text("# Open Questions\n", encoding="utf-8")
        references_root = repo_root / "references"
        references_root.mkdir(parents=True, exist_ok=True)
        for filename in (
            "operating-playbook.md",
            "repo-coverage-checklist.md",
            "verification-checklist.md",
        ):
            (references_root / filename).write_text("# bootstrap\n", encoding="utf-8")
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
