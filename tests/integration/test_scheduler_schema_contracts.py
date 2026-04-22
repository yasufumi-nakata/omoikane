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


class SchedulerSchemaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = OmoikaneReferenceOS()
        self.result = self.runtime.run_scheduler_demo()

    def _assert_schema_valid(self, schema_path: str, payload: dict[str, Any]) -> None:
        schema = _load_schema(schema_path)
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            formatted = "\n".join(error.message for error in errors[:5])
            self.fail(f"{schema_path} validation failed:\n{formatted}")

    def test_method_a_execution_receipt_matches_public_schema(self) -> None:
        self._assert_schema_valid(
            "specs/schemas/scheduler_execution_receipt.schema",
            self.result["execution_receipts"]["method_a"],
        )

    def test_method_a_live_execution_receipt_matches_public_schema(self) -> None:
        self._assert_schema_valid(
            "specs/schemas/scheduler_execution_receipt.schema",
            self.result["execution_receipts"]["method_a_live"],
        )

    def test_method_b_execution_receipt_matches_public_schema(self) -> None:
        self._assert_schema_valid(
            "specs/schemas/scheduler_execution_receipt.schema",
            self.result["execution_receipts"]["method_b"],
        )

    def test_method_c_execution_receipt_matches_public_schema(self) -> None:
        self._assert_schema_valid(
            "specs/schemas/scheduler_execution_receipt.schema",
            self.result["execution_receipts"]["method_c"],
        )

    def test_method_a_cancel_execution_receipt_matches_public_schema(self) -> None:
        self._assert_schema_valid(
            "specs/schemas/scheduler_execution_receipt.schema",
            self.result["execution_receipts"]["method_a_cancel"],
        )

    def test_method_b_handoff_receipt_matches_public_schema(self) -> None:
        self._assert_schema_valid(
            "specs/schemas/scheduler_method_b_handoff_receipt.schema",
            self.result["method_b_final_handle"]["broker_handoff_receipt"],
        )


if __name__ == "__main__":
    unittest.main()
