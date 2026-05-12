from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any

import jsonschema
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPO_ROOT / "specs" / "schemas"
SCHEMA_EXAMPLE_PATTERNS = ("*.schema", "*.yaml")


def _load_schema(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise AssertionError(f"{path} root is not an object")
    return _resolve_local_refs(loaded, path.parent)


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


def _example_entries(schema: dict[str, Any]) -> list[tuple[str, Any]]:
    entries: list[tuple[str, Any]] = []
    if "example" in schema:
        entries.append(("example", schema["example"]))
    examples = schema.get("examples", [])
    if examples is None:
        examples = []
    if not isinstance(examples, list):
        raise AssertionError("examples must be an array")
    entries.extend((f"examples[{index}]", item) for index, item in enumerate(examples))
    return entries


def _json_path(path: Any) -> str:
    parts = list(path)
    if not parts:
        return "$"
    rendered = "$"
    for part in parts:
        rendered += f"[{part}]" if isinstance(part, int) else f".{part}"
    return rendered


class SchemaExampleContractTests(unittest.TestCase):
    def test_all_schema_examples_validate_against_their_schema(self) -> None:
        failures: list[str] = []
        example_count = 0
        yaml_example_count = 0

        schema_paths = sorted(
            {
                path
                for pattern in SCHEMA_EXAMPLE_PATTERNS
                for path in SCHEMA_ROOT.glob(pattern)
                if path.is_file()
            }
        )
        self.assertTrue(
            any(path.suffix == ".yaml" for path in schema_paths),
            "schema example contract must include YAML schema files",
        )

        for schema_path in schema_paths:
            raw_schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
            if not isinstance(raw_schema, dict):
                failures.append(f"{schema_path.relative_to(REPO_ROOT)}: schema root is not an object")
                continue
            try:
                schema = _load_schema(schema_path)
                validator = jsonschema.Draft202012Validator(schema)
                entries = _example_entries(raw_schema)
                if schema_path.suffix == ".yaml":
                    yaml_example_count += len(entries)
            except Exception as exc:  # pragma: no cover - failure path is test output only
                failures.append(f"{schema_path.relative_to(REPO_ROOT)}: {exc}")
                continue

            for label, payload in entries:
                example_count += 1
                errors = sorted(
                    validator.iter_errors(payload),
                    key=lambda error: (
                        tuple(str(part) for part in error.path),
                        tuple(str(part) for part in error.schema_path),
                    ),
                )
                for error in errors[:3]:
                    failures.append(
                        f"{schema_path.relative_to(REPO_ROOT)} {label} "
                        f"{_json_path(error.path)}: {error.message}"
                    )

        self.assertGreater(example_count, 0)
        self.assertGreater(yaml_example_count, 0)
        if failures:
            self.fail("\n".join(failures[:50]))


if __name__ == "__main__":
    unittest.main()
