from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from omoikane.common import canonical_json, sha256_text
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

    def test_scan_requires_parallel_codex_orchestration_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            (repo_root / "references" / "parallel-codex-orchestration.md").unlink()

            report = GapScanner().scan(repo_root)

            self.assertEqual(1, report["missing_required_reference_file_count"])
            self.assertEqual(
                ["references/parallel-codex-orchestration.md"],
                report["missing_required_reference_files"],
            )
            self.assertTrue(
                any(
                    task["kind"] == "missing-reference-file"
                    and "parallel-codex-orchestration.md" in task["summary"]
                    for task in report["prioritized_tasks"]
                )
            )

    def test_scan_receipt_binds_all_zero_report_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)

            report = GapScanner().scan(repo_root)

            receipt = report["scan_receipt"]
            self.assertEqual("gap_report_scan_receipt", receipt["kind"])
            self.assertEqual(
                "self-construction-gap-report-scan-receipt-v1",
                receipt["profile"],
            )
            self.assertTrue(receipt["all_zero"])
            self.assertTrue(receipt["validation"]["ok"])
            self.assertFalse(receipt["raw_report_payload_stored"])
            self.assertEqual(0, receipt["counts"]["prioritized_task_count"])
            self.assertTrue(receipt["validation"]["scan_surface_digests_bound"])
            self.assertTrue(receipt["validation"]["surface_manifest_digest_bound"])
            self.assertFalse(receipt["validation"]["raw_surface_payload_stored"])
            self.assertFalse(receipt["continuity_ledger_appended"])
            self.assertIsNone(receipt["continuity_ledger_entry_ref"])
            self.assertFalse(receipt["validation"]["continuity_ledger_entry_appended"])
            digest_payload = {
                key: value for key, value in report.items() if key != "scan_receipt"
            }
            self.assertEqual(
                sha256_text(canonical_json(digest_payload)),
                receipt["report_digest"],
            )
            surface_manifest_payload = {
                "scanned_surfaces": receipt["scanned_surfaces"],
                "scan_surface_digests": receipt["scan_surface_digests"],
            }
            self.assertEqual(
                sha256_text(canonical_json(surface_manifest_payload)),
                receipt["surface_manifest_digest"],
            )
            open_question_digest = next(
                entry
                for entry in receipt["scan_surface_digests"]
                if entry["path"] == "meta/open-questions.md"
            )
            self.assertEqual("meta/open-questions.md", open_question_digest["surface_pattern"])
            self.assertEqual(sha256_text("# Open Questions\n"), open_question_digest["sha256"])
            self.assertEqual(len("# Open Questions\n".encode("utf-8")), open_question_digest["byte_length"])

    def test_scan_receipt_marks_non_zero_gap_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            (repo_root / "references" / "verification-checklist.md").unlink()

            report = GapScanner().scan(repo_root)

            receipt = report["scan_receipt"]
            self.assertFalse(receipt["all_zero"])
            self.assertFalse(receipt["validation"]["ok"])
            self.assertEqual(
                1,
                receipt["counts"]["missing_required_reference_file_count"],
            )
            self.assertEqual(1, receipt["counts"]["prioritized_task_count"])
            self.assertTrue(receipt["validation"]["scan_surface_digests_bound"])
            self.assertTrue(receipt["validation"]["surface_manifest_digest_bound"])

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

    def test_scan_reports_eval_inventory_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            eval_root = repo_root / "evals" / "continuity"
            eval_root.mkdir(parents=True, exist_ok=True)
            (eval_root / "README.md").write_text(
                "# Continuity Evals\n\n- `ledger_integrity.yaml`\n",
                encoding="utf-8",
            )
            (eval_root / "ledger_integrity.yaml").write_text(
                "eval_id: ledger_integrity\n",
                encoding="utf-8",
            )
            (eval_root / "scheduler_execution_receipt.yaml").write_text(
                "eval_id: scheduler_execution_receipt\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(1, report["inventory_drift_count"])
            self.assertEqual(
                "evals/continuity/README.md",
                report["inventory_drift_hits"][0]["path"],
            )
            self.assertIn(
                "scheduler_execution_receipt.yaml",
                report["inventory_drift_hits"][0]["line"],
            )
            self.assertTrue(
                any(task["kind"] == "inventory-drift" for task in report["prioritized_tasks"])
            )

    def test_scan_reports_uncataloged_implemented_spec_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            interfaces_root = repo_root / "specs" / "interfaces"
            schemas_root = repo_root / "specs" / "schemas"
            (interfaces_root / "README.md").write_text(
                "# Interfaces\n\n- `kernel.identity.v0.idl`\n",
                encoding="utf-8",
            )
            (schemas_root / "README.md").write_text(
                "# Schemas\n\n- `identity_record.schema`\n",
                encoding="utf-8",
            )
            (interfaces_root / "kernel.identity.v0.idl").write_text(
                "idl_version: 1\n",
                encoding="utf-8",
            )
            (schemas_root / "identity_record.schema").write_text(
                "{\n  \"type\": \"object\"\n}\n",
                encoding="utf-8",
            )
            (repo_root / "specs" / "catalog.yaml").write_text(
                "catalog_version: 1\n"
                "entries:\n"
                "  - priority: P1\n"
                "    kind: schema\n"
                "    file: specs/schemas/identity_record.schema\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(1, report["catalog_coverage_gap_count"])
            self.assertEqual(
                "specs/catalog.yaml",
                report["catalog_coverage_gap_hits"][0]["path"],
            )
            self.assertEqual(
                "specs/interfaces/kernel.identity.v0.idl",
                report["catalog_coverage_gap_hits"][0]["missing_catalog_file"],
            )
            self.assertTrue(
                any(task["kind"] == "catalog-coverage-gap" for task in report["prioritized_tasks"])
            )

    def test_scan_ignores_cross_surface_eval_references(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            eval_root = repo_root / "evals" / "cognitive"
            eval_root.mkdir(parents=True, exist_ok=True)
            (eval_root / "README.md").write_text(
                "# Cognitive Evals\n\n"
                "- `qualia_contract.yaml`\n"
                "- `../agentic/cognitive_audit_governance_binding.yaml`\n",
                encoding="utf-8",
            )
            (eval_root / "qualia_contract.yaml").write_text(
                "eval_id: qualia_contract\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(0, report["inventory_drift_count"])
            self.assertEqual([], report["inventory_drift_hits"])

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

    def test_scan_reports_non_abstract_not_implemented_runtime_stubs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            module_path = repo_root / "src" / "omoikane" / "kernel" / "scheduler.py"
            module_path.parent.mkdir(parents=True, exist_ok=True)
            module_path.write_text(
                "class Scheduler:\n"
                "    def advance(self):\n"
                "        raise NotImplementedError('method B execution is not implemented')\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(1, report["implementation_stub_count"])
            self.assertEqual(
                "src/omoikane/kernel/scheduler.py",
                report["implementation_stub_hits"][0]["path"],
            )
            self.assertIn(
                "NotImplementedError",
                report["implementation_stub_hits"][0]["line"],
            )
            self.assertEqual(
                "Scheduler.advance",
                report["implementation_stub_hits"][0]["symbol"],
            )
            self.assertTrue(
                any(task["kind"] == "implementation-stub" for task in report["prioritized_tasks"])
            )

    def test_scan_ignores_abstract_backend_not_implemented_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            module_path = repo_root / "src" / "omoikane" / "cognitive" / "reasoning.py"
            module_path.parent.mkdir(parents=True, exist_ok=True)
            module_path.write_text(
                "class ReasoningBackend:\n"
                "    def _reason(self, request):\n"
                "        raise NotImplementedError\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(0, report["implementation_stub_count"])
            self.assertEqual([], report["implementation_stub_hits"])

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

    def test_scan_reports_latest_decision_log_residuals(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            decision_log_root = repo_root / "meta" / "decision-log"
            (decision_log_root / "2026-04-22_old-gap.md").write_text(
                "---\n"
                "date: 2026-04-22\n"
                "status: decided\n"
                "---\n\n"
                "- residual gap は generic な old backlog ではなく、 historical surface へ縮小する\n",
                encoding="utf-8",
            )
            (decision_log_root / "2026-04-23_recent-gap.md").write_text(
                "---\n"
                "date: 2026-04-23\n"
                "status: decided\n"
                "---\n\n"
                "## Options considered\n"
                "- residual gap は option text なので拾わない\n\n"
                "## Consequences\n"
                "- residual gap は generic な profile unawareness ではなく、 inter-mind-negotiation-v1 へ縮小する\n",
                encoding="utf-8",
            )
            (decision_log_root / "2026-04-23_gap-report-meta.md").write_text(
                "---\n"
                "date: 2026-04-23\n"
                "status: decided\n"
                "---\n\n"
                "## Consequences\n"
                "- residual gap は gap-report 自身の meta note なので拾わない\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(1, report["decision_log_residual_count"])
            self.assertEqual(
                "meta/decision-log/2026-04-23_recent-gap.md",
                report["decision_log_residual_hits"][0]["path"],
            )
            self.assertEqual(
                "2026-04-23",
                report["decision_log_residual_hits"][0]["decision_date"],
            )
            self.assertTrue(
                any(task["kind"] == "decision-log-residual" for task in report["prioritized_tasks"])
            )

    def test_scan_suppresses_closed_latest_decision_log_residuals(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            decision_log_root = repo_root / "meta" / "decision-log"
            (decision_log_root / "2026-04-23_earlier-gap.md").write_text(
                "---\n"
                "date: 2026-04-23\n"
                "status: decided\n"
                "next_gap_ids:\n"
                "  - yaoyorozu.worker.delta-only\n"
                "---\n\n"
                "## Consequences\n"
                "- residual gap は generic な worker visibility ではなく、 patch candidate handoff へ縮小する\n",
                encoding="utf-8",
            )
            (decision_log_root / "2026-04-23_later-gap.md").write_text(
                "---\n"
                "date: 2026-04-23\n"
                "status: decided\n"
                "closes_next_gaps:\n"
                "  - 2026-04-23_earlier-gap.md#yaoyorozu.worker.delta-only\n"
                "---\n\n"
                "## Consequences\n"
                "- next-stage frontier は generic な dispatch 不在ではなく、 build_request execution chain へ縮小する\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(0, report["decision_log_residual_count"])
            self.assertEqual([], report["decision_log_residual_hits"])
            self.assertEqual(1, report["decision_log_frontier_count"])
            self.assertEqual(
                "meta/decision-log/2026-04-23_later-gap.md",
                report["decision_log_frontier_hits"][0]["path"],
            )
            self.assertTrue(
                any(task["kind"] == "decision-log-frontier" for task in report["prioritized_tasks"])
            )

    def test_scan_reports_latest_decision_log_frontiers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            decision_log_root = repo_root / "meta" / "decision-log"
            (decision_log_root / "2026-04-23_frontier-gap.md").write_text(
                "---\n"
                "date: 2026-04-23\n"
                "status: decided\n"
                "---\n\n"
                "## Consequences\n"
                "- next-stage frontier は broad な L4/L5 separation ではなく、 same-digest builder chain へ縮小する\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(0, report["decision_log_residual_count"])
            self.assertEqual(1, report["decision_log_frontier_count"])
            self.assertEqual(
                "meta/decision-log/2026-04-23_frontier-gap.md",
                report["decision_log_frontier_hits"][0]["path"],
            )
            self.assertEqual(
                "2026-04-23",
                report["decision_log_frontier_hits"][0]["decision_date"],
            )

    def test_scan_reports_remaining_scope_operational_followups(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            decision_log_root = repo_root / "meta" / "decision-log"
            (decision_log_root / "2026-04-23_wms-adapter-gap.md").write_text(
                "---\n"
                "date: 2026-04-23\n"
                "status: decided\n"
                "---\n\n"
                "## Remaining scope\n"
                "- real WMS engine adapter の transaction log 統合は adapter surface を持つ段階で扱う\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(1, report["decision_log_frontier_count"])
            self.assertEqual(
                "meta/decision-log/2026-04-23_wms-adapter-gap.md",
                report["decision_log_frontier_hits"][0]["path"],
            )
            self.assertEqual(
                "2026-04-23_wms-adapter-gap.md#gap-1",
                report["decision_log_frontier_hits"][0]["next_gap_ref"],
            )

    def test_scan_suppresses_closed_remaining_scope_followups(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            decision_log_root = repo_root / "meta" / "decision-log"
            (decision_log_root / "2026-04-23_wms-adapter-gap.md").write_text(
                "---\n"
                "date: 2026-04-23\n"
                "status: decided\n"
                "---\n\n"
                "## Deferred scope\n"
                "- real WMS engine adapter の transaction log 統合は adapter surface を持つ段階で扱う\n",
                encoding="utf-8",
            )
            (decision_log_root / "2026-04-23_wms-adapter-closed.md").write_text(
                "---\n"
                "date: 2026-04-23\n"
                "status: decided\n"
                "closes_next_gaps:\n"
                "  - 2026-04-23_wms-adapter-gap.md#gap-1\n"
                "---\n\n"
                "## Consequences\n"
                "- engine adapter transaction log surface is now covered by schema/runtime/eval\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(0, report["decision_log_frontier_count"])
            self.assertEqual([], report["decision_log_frontier_hits"])

    def test_scan_ignores_superseded_latest_decision_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._bootstrap_repo(repo_root)
            decision_log_root = repo_root / "meta" / "decision-log"
            (decision_log_root / "2026-04-22_recent-gap.md").write_text(
                "---\n"
                "date: 2026-04-22\n"
                "status: decided\n"
                "---\n\n"
                "## Consequences\n"
                "- unresolved gap は generic な trust tampering 全般ではなく、 cross-substrate trust transfer へ縮小する\n",
                encoding="utf-8",
            )
            (decision_log_root / "2026-04-23_superseded-gap.md").write_text(
                "---\n"
                "date: 2026-04-23\n"
                "status: superseded\n"
                "---\n\n"
                "- residual future work は generic な packet export 一般論ではなく、 live capture へ縮小する\n",
                encoding="utf-8",
            )

            report = GapScanner().scan(repo_root)

            self.assertEqual(1, report["decision_log_residual_count"])
            self.assertEqual(
                "meta/decision-log/2026-04-22_recent-gap.md",
                report["decision_log_residual_hits"][0]["path"],
            )

    @staticmethod
    def _bootstrap_repo(repo_root: Path) -> None:
        (repo_root / "meta").mkdir(parents=True)
        (repo_root / "meta" / "open-questions.md").write_text("# Open Questions\n", encoding="utf-8")
        (repo_root / "meta" / "decision-log").mkdir(parents=True, exist_ok=True)
        references_root = repo_root / "references"
        references_root.mkdir(parents=True, exist_ok=True)
        for filename in (
            "operating-playbook.md",
            "parallel-codex-orchestration.md",
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
