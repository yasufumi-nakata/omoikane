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


class BuilderSchemaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = OmoikaneReferenceOS()

    def _assert_schema_valid(self, schema_path: str, payload: dict[str, Any]) -> None:
        schema = _load_schema(schema_path)
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            formatted = "\n".join(error.message for error in errors[:5])
            self.fail(f"{schema_path} validation failed:\n{formatted}")

    def test_builder_demo_rollout_matches_public_schema(self) -> None:
        result = self.runtime.run_builder_demo()

        self._assert_schema_valid(
            "specs/schemas/staged_rollout_session.schema",
            result["builder"]["rollout_session"],
        )

    def test_builder_live_demo_matches_public_schema(self) -> None:
        result = self.runtime.run_builder_live_demo()

        self._assert_schema_valid(
            "specs/schemas/builder_live_enactment_session.schema",
            result["builder"]["enactment_session"],
        )

    def test_rollback_demo_matches_public_schema(self) -> None:
        result = self.runtime.run_rollback_demo()

        self._assert_schema_valid(
            "specs/schemas/builder_rollback_session.schema",
            result["builder"]["rollback_session"],
        )

