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


class YaoyorozuSchemaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = OmoikaneReferenceOS()

    def _assert_schema_valid(self, schema_path: str, payload: dict[str, Any]) -> None:
        schema = _load_schema(schema_path)
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            formatted = "\n".join(error.message for error in errors[:5])
            self.fail(f"{schema_path} validation failed:\n{formatted}")

    def test_yaoyorozu_registry_snapshot_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_registry_snapshot.schema",
            result["registry"],
        )

    def test_workspace_discovery_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_workspace_discovery.schema",
            result["workspace_discovery"],
        )

    def test_council_convocation_session_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/council_convocation_session.schema",
            result["convocation"],
        )

    def test_worker_dispatch_plan_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_worker_dispatch_plan.schema",
            result["dispatch_plan"],
        )

    def test_worker_dispatch_receipt_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_worker_dispatch_receipt.schema",
            result["dispatch_receipt"],
        )

    def test_consensus_dispatch_binding_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_consensus_dispatch_binding.schema",
            result["consensus_dispatch"],
        )

    def test_task_graph_binding_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_task_graph_binding.schema",
            result["task_graph_binding"],
        )

    def test_fork_request_profile_matches_public_schemas(self) -> None:
        result = self.runtime.run_yaoyorozu_demo(proposal_profile="fork-request-v1")

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_workspace_discovery.schema",
            result["workspace_discovery"],
        )
        self._assert_schema_valid(
            "specs/schemas/council_convocation_session.schema",
            result["convocation"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_worker_dispatch_plan.schema",
            result["dispatch_plan"],
        )
