from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from omoikane.common import canonical_json, sha256_text
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


class GapReportSchemaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = OmoikaneReferenceOS()

    def _assert_schema_valid(self, schema_path: str, payload: dict[str, Any]) -> None:
        schema = _load_schema(schema_path)
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            formatted = "\n".join(error.message for error in errors[:5])
            self.fail(f"{schema_path} validation failed:\n{formatted}")

    def test_gap_report_matches_public_schema(self) -> None:
        report = self.runtime.generate_gap_report(REPO_ROOT)

        self._assert_schema_valid("specs/schemas/gap_report.schema", report)

    def test_gap_report_scan_receipt_counts_match_report(self) -> None:
        report = self.runtime.generate_gap_report(REPO_ROOT)
        counts = report["scan_receipt"]["counts"]

        self.assertEqual(report["open_question_count"], counts["open_question_count"])
        self.assertEqual(
            report["missing_expected_file_count"],
            counts["missing_expected_file_count"],
        )
        self.assertEqual(
            report["missing_required_reference_file_count"],
            counts["missing_required_reference_file_count"],
        )
        self.assertEqual(
            report["missing_required_reference_policy_section_count"],
            counts["missing_required_reference_policy_section_count"],
        )
        self.assertEqual(
            report["empty_eval_surface_count"],
            counts["empty_eval_surface_count"],
        )
        self.assertEqual(report["placeholder_hit_count"], counts["placeholder_hit_count"])
        self.assertEqual(report["inventory_drift_count"], counts["inventory_drift_count"])
        self.assertEqual(
            report["catalog_coverage_gap_count"],
            counts["catalog_coverage_gap_count"],
        )
        self.assertEqual(report["future_work_hit_count"], counts["future_work_hit_count"])
        self.assertEqual(
            report["implementation_stub_count"],
            counts["implementation_stub_count"],
        )
        self.assertEqual(
            report["decision_log_residual_count"],
            counts["decision_log_residual_count"],
        )
        self.assertEqual(
            report["decision_log_frontier_count"],
            counts["decision_log_frontier_count"],
        )
        self.assertEqual(report["catalog_pending_count"], counts["catalog_pending_count"])
        self.assertEqual(len(report["prioritized_tasks"]), counts["prioritized_task_count"])

    def test_gap_report_scan_receipt_binds_surface_manifest(self) -> None:
        report = self.runtime.generate_gap_report(REPO_ROOT)
        receipt = report["scan_receipt"]
        manifest_payload = {
            "scanned_surfaces": receipt["scanned_surfaces"],
            "scan_surface_digests": receipt["scan_surface_digests"],
        }

        self.assertEqual(
            sha256_text(canonical_json(manifest_payload)),
            receipt["surface_manifest_digest"],
        )
        self.assertTrue(receipt["validation"]["scan_surface_digests_bound"])
        self.assertTrue(receipt["validation"]["surface_manifest_digest_bound"])
        self.assertFalse(receipt["validation"]["raw_surface_payload_stored"])
        self.assertTrue(
            any(
                entry["path"] == "specs/catalog.yaml"
                and entry["surface_pattern"] == "specs/catalog.yaml"
                for entry in receipt["scan_surface_digests"]
            )
        )
        self.assertTrue(
            any(
                entry["path"] == "references/parallel-codex-orchestration.md"
                and entry["surface_pattern"] == "references/*.md"
                for entry in receipt["scan_surface_digests"]
            )
        )

    def test_gap_report_required_references_are_complete(self) -> None:
        report = self.runtime.generate_gap_report(REPO_ROOT)

        self.assertEqual(0, report["missing_required_reference_file_count"])
        self.assertEqual([], report["missing_required_reference_files"])
        self.assertEqual(0, report["missing_required_reference_policy_section_count"])
        self.assertEqual([], report["missing_required_reference_policy_sections"])

    def test_gap_report_scan_receipt_binds_continuity_event_digest(self) -> None:
        report = self.runtime.generate_gap_report(REPO_ROOT)
        receipt = report["scan_receipt"]
        event_payload = {
            "event_ref": receipt["continuity_event_ref"],
            "category": receipt["continuity_ledger_category"],
            "event_type": receipt["continuity_ledger_event_type"],
            "binding_profile": receipt["continuity_ledger_binding_profile"],
            "scan_receipt_id": receipt["receipt_id"],
            "scan_receipt_profile": receipt["profile"],
            "repo_root": report["repo_root"],
            "report_digest": receipt["report_digest"],
            "surface_manifest_digest": receipt["surface_manifest_digest"],
            "counts": receipt["counts"],
            "all_zero": receipt["all_zero"],
        }

        self.assertEqual(
            "gap-report-scan-continuity-ledger-binding-v1",
            receipt["continuity_ledger_binding_profile"],
        )
        self.assertEqual(
            sha256_text(canonical_json(event_payload)),
            receipt["continuity_event_digest"],
        )
        self.assertTrue(receipt["validation"]["continuity_ledger_bound"])
        self.assertTrue(receipt["validation"]["continuity_event_digest_bound"])
        self.assertTrue(receipt["continuity_ledger_appended"])
        self.assertTrue(receipt["validation"]["continuity_ledger_entry_appended"])
        self.assertTrue(receipt["validation"]["continuity_ledger_entry_digest_bound"])
        self.assertTrue(receipt["validation"]["continuity_ledger_payload_ref_bound"])
        self.assertEqual(
            ["self", "guardian"],
            receipt["continuity_ledger_signature_roles"],
        )
        self.assertTrue(
            receipt["validation"]["continuity_ledger_signature_roles_bound"]
        )
        self.assertRegex(receipt["continuity_ledger_entry_ref"], r"^ledger://continuity-ledger/[a-f0-9]{64}$")
        self.assertRegex(receipt["continuity_ledger_entry_hash"], r"^[a-f0-9]{64}$")
        self.assertRegex(receipt["continuity_ledger_payload_ref"], r"^cas://sha256/[a-f0-9]{64}$")
        self.assertFalse(receipt["raw_continuity_event_payload_stored"])
        self.assertFalse(
            receipt["validation"]["raw_continuity_event_payload_stored"]
        )


if __name__ == "__main__":
    unittest.main()
