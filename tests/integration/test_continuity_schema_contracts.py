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
    return yaml.safe_load(schema_path.read_text(encoding="utf-8"))


class ContinuitySchemaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = OmoikaneReferenceOS()

    def _assert_schema_valid(self, schema_path: str, payload: dict[str, Any]) -> None:
        schema = _load_schema(schema_path)
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            formatted = "\n".join(error.message for error in errors[:5])
            self.fail(f"{schema_path} validation failed:\n{formatted}")

    def test_continuity_public_verification_bundle_matches_public_schema(self) -> None:
        result = self.runtime.run_continuity_demo()
        bundle = result["public_verification_bundle"]

        self._assert_schema_valid(
            "specs/schemas/continuity_public_verification_bundle.schema",
            bundle,
        )
        self.assertTrue(result["public_verification_validation"]["ok"])
        self.assertTrue(bundle["public_verification_ready"])
        self.assertFalse(bundle["raw_key_material_exposed"])
        self.assertFalse(bundle["raw_signature_payload_exposed"])


if __name__ == "__main__":
    unittest.main()
