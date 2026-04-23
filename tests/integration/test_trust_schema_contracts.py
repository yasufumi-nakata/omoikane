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


class TrustSchemaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = OmoikaneReferenceOS()

    def _assert_schema_valid(self, schema_path: str, payload: dict[str, Any]) -> None:
        schema = _load_schema(schema_path)
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            formatted = "\n".join(error.message for error in errors[:5])
            self.fail(f"{schema_path} validation failed:\n{formatted}")

    def test_trust_demo_events_match_public_schema(self) -> None:
        result = self.runtime.run_trust_demo()

        for event in result["events"]:
            self._assert_schema_valid("specs/schemas/trust_event.schema", event)

    def test_trust_demo_snapshots_match_public_schema(self) -> None:
        result = self.runtime.run_trust_demo()

        for snapshot in result["agents"].values():
            self._assert_schema_valid("specs/schemas/trust_snapshot.schema", snapshot)

    def test_trust_transfer_demo_receipt_matches_public_schema(self) -> None:
        result = self.runtime.run_trust_transfer_demo()

        self._assert_schema_valid(
            "specs/schemas/trust_transfer_receipt.schema",
            result["transfer"],
        )

    def test_trust_transfer_demo_redacted_receipt_matches_public_schema(self) -> None:
        result = self.runtime.run_trust_transfer_demo(
            export_profile_id="bounded-trust-transfer-redacted-export-v1"
        )

        self._assert_schema_valid(
            "specs/schemas/trust_transfer_receipt.schema",
            result["transfer"],
        )
        self._assert_schema_valid(
            "specs/schemas/trust_redacted_snapshot.schema",
            result["transfer"]["source_snapshot_redacted"],
        )
        self._assert_schema_valid(
            "specs/schemas/trust_redacted_snapshot.schema",
            result["transfer"]["destination_snapshot_redacted"],
        )
