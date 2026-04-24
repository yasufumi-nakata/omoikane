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


class DistributedTransportSchemaContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = OmoikaneReferenceOS().run_distributed_transport_demo()

    def _assert_schema_valid(self, schema_path: str, payload: dict[str, Any]) -> None:
        schema = _load_schema(schema_path)
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            formatted = "\n".join(error.message for error in errors[:5])
            self.fail(f"{schema_path} validation failed:\n{formatted}")

    def test_authority_seed_review_policy_matches_public_schema(self) -> None:
        policy = self.result["authority_seed_review_policy"]["federation_rotated"]

        self._assert_schema_valid(
            "specs/schemas/distributed_transport_authority_seed_review_policy.schema",
            policy,
        )

    def test_authority_cluster_discovery_matches_public_schema(self) -> None:
        discovery = self.result["authority_cluster_discovery"]["federation_rotated"]

        self._assert_schema_valid(
            "specs/schemas/distributed_transport_authority_cluster_discovery.schema",
            discovery,
        )

    def test_seed_review_policy_is_digest_bound_to_candidate_review(self) -> None:
        policy = self.result["authority_seed_review_policy"]["federation_rotated"]
        discovery = self.result["authority_cluster_discovery"]["federation_rotated"]

        self.assertEqual(policy, discovery["seed_review_policy"])
        self.assertEqual(
            policy["digest"],
            discovery["candidate_clusters"][0]["review_policy_digest"],
        )
        self.assertEqual(
            policy["policy_ref"],
            discovery["candidate_clusters"][0]["review_policy_ref"],
        )


if __name__ == "__main__":
    unittest.main()
