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


class EthicsSchemaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = OmoikaneReferenceOS()

    def _assert_schema_valid(self, schema_path: str, payload: dict[str, Any]) -> None:
        schema = _load_schema(schema_path)
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            formatted = "\n".join(error.message for error in errors[:5])
            self.fail(f"{schema_path} validation failed:\n{formatted}")

    def test_ethics_demo_decisions_match_public_schema(self) -> None:
        result = self.runtime.run_ethics_demo()

        for decision in result["decisions"].values():
            self._assert_schema_valid("specs/schemas/ethics_decision.yaml", decision)

    def test_ethics_demo_rules_match_public_schema(self) -> None:
        result = self.runtime.run_ethics_demo()

        for rule in result["rules"]:
            self._assert_schema_valid("specs/schemas/ethics_rule.schema", rule)

    def test_ethics_demo_events_match_public_schema(self) -> None:
        result = self.runtime.run_ethics_demo()

        for event in result["ethics_events"]:
            self._assert_schema_valid("specs/schemas/ethics_event.schema", event)
            receipt = event["action_snapshot"].get("consent_authenticity_receipt")
            if receipt is not None:
                self._assert_schema_valid(
                    "specs/schemas/ethics_consent_authenticity_receipt.schema",
                    receipt,
                )

    def test_ethics_consent_receipt_examples_match_public_schema(self) -> None:
        schema = _load_schema("specs/schemas/ethics_consent_authenticity_receipt.schema")
        validator = jsonschema.Draft202012Validator(schema)

        for index, payload in enumerate(schema.get("examples", []), start=1):
            errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
            if errors:
                formatted = "\n".join(error.message for error in errors[:5])
                self.fail(
                    "specs/schemas/ethics_consent_authenticity_receipt.schema "
                    f"example {index} validation failed:\n{formatted}"
                )


if __name__ == "__main__":
    unittest.main()
