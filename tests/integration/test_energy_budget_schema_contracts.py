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


class EnergyBudgetSchemaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.result = OmoikaneReferenceOS().run_energy_budget_demo()

    def _assert_schema_valid(self, schema_path: str, payload: dict[str, Any]) -> None:
        schema = _load_schema(schema_path)
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            formatted = "\n".join(error.message for error in errors[:5])
            self.fail(f"{schema_path} validation failed:\n{formatted}")

    def test_energy_budget_floor_receipt_matches_public_schema(self) -> None:
        self.assertTrue(self.result["validation"]["ok"])
        self._assert_schema_valid(
            "specs/schemas/energy_budget_floor_receipt.schema",
            self.result["energy_budget"]["receipt"],
        )

    def test_energy_budget_pool_receipt_matches_public_schema(self) -> None:
        result = OmoikaneReferenceOS().run_energy_budget_pool_demo()

        self.assertTrue(result["validation"]["ok"])
        self._assert_schema_valid(
            "specs/schemas/energy_budget_pool_receipt.schema",
            result["energy_budget_pool"]["receipt"],
        )

    def test_energy_budget_voluntary_subsidy_receipt_matches_public_schema(self) -> None:
        result = OmoikaneReferenceOS().run_energy_budget_subsidy_demo()

        self.assertTrue(result["validation"]["ok"])
        self._assert_schema_valid(
            "specs/schemas/energy_budget_voluntary_subsidy_receipt.schema",
            result["energy_budget_subsidy"]["receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/energy_budget_subsidy_verifier_receipt.schema",
            result["energy_budget_subsidy"]["receipt"][
                "signer_roster_verifier_receipt"
            ],
        )
        self._assert_schema_valid(
            "specs/schemas/energy_budget_subsidy_verifier_quorum_receipt.schema",
            result["energy_budget_subsidy"]["receipt"][
                "signer_roster_verifier_quorum_receipt"
            ],
        )
        self._assert_schema_valid(
            "specs/schemas/energy_budget_subsidy_verifier_quorum_threshold_policy_receipt.schema",
            result["energy_budget_subsidy"]["receipt"][
                "signer_roster_verifier_quorum_receipt"
            ]["threshold_policy_receipt"],
        )

    def test_energy_budget_shared_fabric_receipt_matches_public_schema(self) -> None:
        result = OmoikaneReferenceOS().run_energy_budget_fabric_demo()

        self.assertTrue(result["validation"]["ok"])
        self._assert_schema_valid(
            "specs/schemas/energy_budget_shared_fabric_allocation_receipt.schema",
            result["energy_budget_fabric"]["receipt"],
        )


if __name__ == "__main__":
    unittest.main()
