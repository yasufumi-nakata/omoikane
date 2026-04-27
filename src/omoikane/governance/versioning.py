"""Hybrid semver/calver release manifest for the reference runtime."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

SCHEMA_VERSION = "1.0.0"
DEFAULT_STABILITY = "bootstrap"
REGULATION_CALVER = "2026.04"
CATALOG_CALVER = "2026.04"
CATALOG_INVENTORY_PROFILE = "specs-catalog-generated-inventory-v1"
SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
CALVER_PATTERN = re.compile(r"^[0-9]{4}\.[0-9]{2}(?:\+rev[0-9]+)?$")


class VersioningService:
    """Deterministic release-manifest builder for OmoikaneOS."""

    def policy_snapshot(self, repo_root: Path) -> Dict[str, Any]:
        runtime_version = self._read_project_version(repo_root / "pyproject.toml")
        return {
            "kind": "versioning_policy",
            "schema_version": SCHEMA_VERSION,
            "runtime": {
                "scheme": "semver",
                "version": runtime_version,
                "stability": DEFAULT_STABILITY,
            },
            "contracts": {
                "idl_scheme": "namespace-major + idl_version -> semver",
                "schema_scheme": "schema examples -> semver",
                "default_stability": DEFAULT_STABILITY,
            },
            "regulation": {
                "scheme": "calver",
                "version": REGULATION_CALVER,
            },
            "catalog_snapshot": {
                "scheme": "calver+sha256",
                "calver": CATALOG_CALVER,
                "inventory_profile": CATALOG_INVENTORY_PROFILE,
            },
        }

    def build_release_manifest(self, repo_root: Path) -> Dict[str, Any]:
        runtime_version = self._read_project_version(repo_root / "pyproject.toml")
        catalog_text = self._read_text(repo_root / "specs" / "catalog.yaml")
        catalog_inventory_receipt = self.build_catalog_inventory_receipt(repo_root)
        idl_versions = self._collect_idl_versions(repo_root / "specs" / "interfaces")
        schema_versions = self._collect_schema_versions(repo_root / "specs" / "schemas")

        return {
            "kind": "release_manifest",
            "schema_version": SCHEMA_VERSION,
            "manifest_id": new_id("release-manifest"),
            "generated_at": utc_now_iso(),
            "runtime_version": runtime_version,
            "runtime_stability": DEFAULT_STABILITY,
            "regulation_calver": REGULATION_CALVER,
            "idl_versions": idl_versions,
            "schema_versions": schema_versions,
            "catalog_snapshot": {
                "calver": CATALOG_CALVER,
                "sha256": sha256_text(catalog_text),
            },
            "catalog_inventory_receipt": catalog_inventory_receipt,
            "notes": [
                "reference runtime uses semver for package/runtime surfaces",
                "IDL and schema contracts default to bootstrap stability until external governance promotes them",
                "governance layers use calver because amendment timing follows human review cadence",
                "catalog inventory receipt binds the generated file inventory to the catalog hash and contract coverage counts",
            ],
        }

    def build_catalog_inventory_receipt(self, repo_root: Path) -> Dict[str, Any]:
        catalog_path = repo_root / "specs" / "catalog.yaml"
        catalog_text = self._read_text(catalog_path)
        catalog_entries = self._collect_catalog_entries(catalog_text, repo_root)
        declared_files = [entry["file"] for entry in catalog_entries if entry.get("file")]
        declared_file_set = set(declared_files)
        implemented_contract_files = self._implemented_contract_files(repo_root)
        priority_counts = self._count_by_key(catalog_entries, "priority")
        kind_counts = self._count_by_key(catalog_entries, "kind")
        duplicate_files = sorted(
            file_name for file_name in declared_file_set if declared_files.count(file_name) > 1
        )
        missing_files = sorted(
            file_name for file_name in declared_file_set if not (repo_root / file_name).is_file()
        )
        catalog_coverage_gap_files = sorted(
            file_name for file_name in implemented_contract_files if file_name not in declared_file_set
        )

        receipt: Dict[str, Any] = {
            "kind": "catalog_inventory_receipt",
            "schema_version": SCHEMA_VERSION,
            "receipt_id": new_id("catalog-inventory"),
            "generated_at": utc_now_iso(),
            "profile": CATALOG_INVENTORY_PROFILE,
            "source_ref": "specs/catalog.yaml",
            "source_digest": sha256_text(catalog_text),
            "source_byte_count": len(catalog_text.encode("utf-8")),
            "catalog_calver": CATALOG_CALVER,
            "entry_count": len(catalog_entries),
            "priority_counts": priority_counts,
            "kind_counts": kind_counts,
            "declared_file_count": len(declared_file_set),
            "implemented_contract_file_count": len(implemented_contract_files),
            "missing_file_count": len(missing_files),
            "duplicate_file_count": len(duplicate_files),
            "catalog_coverage_gap_count": len(catalog_coverage_gap_files),
            "missing_files": missing_files,
            "duplicate_files": duplicate_files,
            "catalog_coverage_gap_files": catalog_coverage_gap_files,
            "entries": catalog_entries,
        }
        receipt["inventory_digest"] = sha256_text(
            canonical_json(self._catalog_inventory_digest_payload(receipt))
        )
        receipt["validation"] = {
            "ok": (
                not missing_files
                and not duplicate_files
                and not catalog_coverage_gap_files
            ),
            "all_declared_files_exist": not missing_files,
            "no_duplicate_declared_files": not duplicate_files,
            "all_implemented_contract_files_declared": not catalog_coverage_gap_files,
            "entry_count_matches": receipt["entry_count"] == len(catalog_entries),
            "catalog_digest_bound": receipt["source_digest"] == sha256_text(catalog_text),
            "inventory_digest_bound": bool(receipt["inventory_digest"]),
        }
        return receipt

    def validate_release_manifest(self, repo_root: Path, manifest: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        pyproject_version = self._read_project_version(repo_root / "pyproject.toml")
        catalog_text = self._read_text(repo_root / "specs" / "catalog.yaml")
        expected_catalog_hash = sha256_text(catalog_text)

        runtime_matches = manifest.get("runtime_version") == pyproject_version
        regulation_valid = bool(CALVER_PATTERN.match(str(manifest.get("regulation_calver", ""))))
        idl_major_alignment = self._validate_idl_alignment(manifest.get("idl_versions", {}))
        schema_semver_valid = self._validate_contract_versions(manifest.get("schema_versions", {}))
        idl_semver_valid = self._validate_contract_versions(manifest.get("idl_versions", {}))
        catalog_snapshot = manifest.get("catalog_snapshot", {})
        catalog_hash_matches = catalog_snapshot.get("sha256") == expected_catalog_hash
        catalog_calver_valid = catalog_snapshot.get("calver") == CATALOG_CALVER
        runtime_semver_valid = bool(SEMVER_PATTERN.match(str(manifest.get("runtime_version", ""))))
        runtime_stability_valid = manifest.get("runtime_stability") == DEFAULT_STABILITY
        catalog_inventory_validation = self.validate_catalog_inventory_receipt(
            repo_root,
            manifest.get("catalog_inventory_receipt", {}),
        )

        if not runtime_matches:
            errors.append("runtime_version does not match pyproject.toml")
        if not runtime_semver_valid:
            errors.append("runtime_version is not semver")
        if not runtime_stability_valid:
            errors.append("runtime_stability must remain bootstrap in the reference runtime")
        if not regulation_valid:
            errors.append("regulation_calver is invalid")
        if not catalog_hash_matches:
            errors.append("catalog_snapshot.sha256 does not match specs/catalog.yaml")
        if not catalog_calver_valid:
            errors.append("catalog_snapshot.calver does not match the fixed bootstrap calver")
        if not idl_major_alignment:
            errors.append("one or more IDL semver majors do not match namespace majors")
        if not idl_semver_valid:
            errors.append("one or more IDL semver/stability entries are invalid")
        if not schema_semver_valid:
            errors.append("one or more schema semver/stability entries are invalid")
        if not catalog_inventory_validation["ok"]:
            errors.append("catalog_inventory_receipt does not match specs/catalog.yaml")

        return {
            "ok": not errors,
            "errors": errors,
            "runtime_version_matches_pyproject": runtime_matches,
            "runtime_version_semver_valid": runtime_semver_valid,
            "runtime_stability_valid": runtime_stability_valid,
            "regulation_calver_valid": regulation_valid,
            "catalog_hash_matches": catalog_hash_matches,
            "catalog_calver_valid": catalog_calver_valid,
            "idl_major_alignment": idl_major_alignment,
            "idl_semver_valid": idl_semver_valid,
            "schema_semver_valid": schema_semver_valid,
            "catalog_inventory_valid": catalog_inventory_validation["ok"],
            "catalog_inventory_validation": catalog_inventory_validation,
            "idl_count": len(manifest.get("idl_versions", {})),
            "schema_count": len(manifest.get("schema_versions", {})),
        }

    def validate_catalog_inventory_receipt(
        self,
        repo_root: Path,
        receipt: Dict[str, Any],
    ) -> Dict[str, Any]:
        errors = []
        if not isinstance(receipt, dict):
            return {
                "ok": False,
                "errors": ["catalog_inventory_receipt must be an object"],
                "missing_file_count": 0,
                "duplicate_file_count": 0,
                "catalog_coverage_gap_count": 0,
            }

        expected = self.build_catalog_inventory_receipt(repo_root)
        stable_keys = (
            "kind",
            "schema_version",
            "profile",
            "source_ref",
            "source_digest",
            "source_byte_count",
            "catalog_calver",
            "entry_count",
            "priority_counts",
            "kind_counts",
            "declared_file_count",
            "implemented_contract_file_count",
            "missing_file_count",
            "duplicate_file_count",
            "catalog_coverage_gap_count",
            "missing_files",
            "duplicate_files",
            "catalog_coverage_gap_files",
            "entries",
        )
        for key in stable_keys:
            if receipt.get(key) != expected.get(key):
                errors.append(f"catalog_inventory_receipt.{key} mismatch")

        try:
            expected_digest = sha256_text(
                canonical_json(self._catalog_inventory_digest_payload(receipt))
            )
        except KeyError:
            expected_digest = ""
            errors.append("catalog_inventory_receipt digest payload is missing required fields")
        if receipt.get("inventory_digest") != expected_digest:
            errors.append("catalog_inventory_receipt.inventory_digest mismatch")

        validation = receipt.get("validation", {})
        if not isinstance(validation, dict):
            validation = {}
            errors.append("catalog_inventory_receipt.validation must be an object")
        if validation.get("all_declared_files_exist") is not True:
            errors.append("catalog inventory must confirm all declared files exist")
        if validation.get("no_duplicate_declared_files") is not True:
            errors.append("catalog inventory must confirm no duplicate declared files")
        if validation.get("all_implemented_contract_files_declared") is not True:
            errors.append("catalog inventory must confirm all implemented contract files are declared")
        if validation.get("catalog_digest_bound") is not True:
            errors.append("catalog inventory must bind the catalog digest")
        if validation.get("inventory_digest_bound") is not True:
            errors.append("catalog inventory must bind the inventory digest")
        if validation.get("ok") is not True:
            errors.append("catalog inventory validation must be ok")

        return {
            "ok": not errors,
            "errors": errors,
            "profile": str(receipt.get("profile", "")),
            "entry_count": int(receipt.get("entry_count", 0))
            if isinstance(receipt.get("entry_count", 0), int)
            else 0,
            "declared_file_count": int(receipt.get("declared_file_count", 0))
            if isinstance(receipt.get("declared_file_count", 0), int)
            else 0,
            "implemented_contract_file_count": int(
                receipt.get("implemented_contract_file_count", 0)
            )
            if isinstance(receipt.get("implemented_contract_file_count", 0), int)
            else 0,
            "missing_file_count": int(receipt.get("missing_file_count", 0))
            if isinstance(receipt.get("missing_file_count", 0), int)
            else 0,
            "duplicate_file_count": int(receipt.get("duplicate_file_count", 0))
            if isinstance(receipt.get("duplicate_file_count", 0), int)
            else 0,
            "catalog_coverage_gap_count": int(receipt.get("catalog_coverage_gap_count", 0))
            if isinstance(receipt.get("catalog_coverage_gap_count", 0), int)
            else 0,
        }

    def release_digest(self, manifest: Dict[str, Any]) -> str:
        return sha256_text(canonical_json(manifest))

    def _collect_idl_versions(self, interfaces_dir: Path) -> Dict[str, Dict[str, str]]:
        versions: Dict[str, Dict[str, str]] = {}
        for path in sorted(interfaces_dir.rglob("*.idl")):
            text = self._read_text(path)
            namespace = self._extract_required(text, r"^namespace:\s*(\S+)\s*$", "namespace")
            idl_version = int(self._extract_required(text, r"^idl_version:\s*(\d+)\s*$", "idl_version"))
            major = self._namespace_major(namespace)
            versions[namespace] = {
                "semver": f"{major}.{idl_version}.0",
                "stability": DEFAULT_STABILITY,
            }
        return versions

    def _collect_schema_versions(self, schemas_dir: Path) -> Dict[str, Dict[str, str]]:
        versions: Dict[str, Dict[str, str]] = {}
        repo_root = schemas_dir.parents[1]
        for path in sorted(self._schema_paths(schemas_dir)):
            text = self._read_text(path)
            versions[path.relative_to(repo_root).as_posix()] = {
                "semver": self._extract_schema_semver(text),
                "stability": DEFAULT_STABILITY,
            }
        return versions

    @staticmethod
    def _schema_paths(schemas_dir: Path) -> Iterable[Path]:
        for extension in ("*.schema", "*.yaml"):
            yield from schemas_dir.rglob(extension)

    def _collect_catalog_entries(self, catalog_text: str, repo_root: Path) -> list[Dict[str, Any]]:
        entries: list[Dict[str, Any]] = []
        current: Dict[str, Any] | None = None
        current_consumers: list[str] = []
        in_consumers = False

        def close_current() -> None:
            if current is None:
                return
            current["consumer_count"] = len(current_consumers)
            current["consumers_digest"] = sha256_text(canonical_json({"consumers": current_consumers}))
            rationale = str(current.get("rationale", ""))
            current["rationale_digest"] = sha256_text(rationale)
            file_name = str(current.get("file", ""))
            file_path = repo_root / file_name
            current["file_exists"] = file_path.is_file()
            current["file_digest"] = (
                sha256_text(self._read_text(file_path)) if file_path.is_file() else ""
            )
            entries.append(current)

        for raw_line in catalog_text.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            if stripped.startswith("- priority:"):
                close_current()
                current = {
                    "entry_index": len(entries) + 1,
                    "priority": stripped.partition(":")[2].strip().strip("'\""),
                    "kind": "",
                    "file": "",
                    "file_exists": False,
                    "file_digest": "",
                    "consumer_count": 0,
                    "consumers_digest": "",
                    "rationale_digest": "",
                }
                current_consumers = []
                in_consumers = False
                continue
            if current is None:
                continue
            if stripped == "consumers:":
                in_consumers = True
                continue
            if in_consumers and stripped.startswith("- "):
                current_consumers.append(stripped[2:].strip().strip("'\""))
                continue
            if ":" not in stripped:
                continue
            key, _, value = stripped.partition(":")
            normalized_key = key.strip()
            normalized_value = value.strip().strip("'\"")
            if normalized_key in {"kind", "file", "rationale"}:
                current[normalized_key] = normalized_value
                in_consumers = False
                continue
            in_consumers = False

        close_current()
        return entries

    @staticmethod
    def _implemented_contract_files(repo_root: Path) -> list[str]:
        paths: list[str] = []
        for directory_name, suffixes in (
            ("specs/interfaces", (".idl",)),
            ("specs/schemas", (".schema", ".yaml")),
        ):
            directory_path = repo_root / directory_name
            if not directory_path.exists():
                continue
            for path in sorted(directory_path.iterdir()):
                if path.is_file() and path.suffix in suffixes:
                    paths.append(path.relative_to(repo_root).as_posix())
        return paths

    @staticmethod
    def _count_by_key(entries: list[Dict[str, Any]], key: str) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for entry in entries:
            value = str(entry.get(key, "")).strip()
            if not value:
                continue
            counts[value] = counts.get(value, 0) + 1
        return dict(sorted(counts.items()))

    @staticmethod
    def _catalog_inventory_digest_payload(receipt: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "profile": receipt["profile"],
            "source_ref": receipt["source_ref"],
            "source_digest": receipt["source_digest"],
            "catalog_calver": receipt["catalog_calver"],
            "entry_count": receipt["entry_count"],
            "priority_counts": receipt["priority_counts"],
            "kind_counts": receipt["kind_counts"],
            "declared_file_count": receipt["declared_file_count"],
            "implemented_contract_file_count": receipt["implemented_contract_file_count"],
            "missing_file_count": receipt["missing_file_count"],
            "duplicate_file_count": receipt["duplicate_file_count"],
            "catalog_coverage_gap_count": receipt["catalog_coverage_gap_count"],
            "missing_files": receipt["missing_files"],
            "duplicate_files": receipt["duplicate_files"],
            "catalog_coverage_gap_files": receipt["catalog_coverage_gap_files"],
            "entries": receipt["entries"],
        }

    @staticmethod
    def _read_text(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _read_project_version(pyproject_path: Path) -> str:
        text = pyproject_path.read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"\s*$', text, re.MULTILINE)
        if not match:
            raise ValueError("project version is missing from pyproject.toml")
        return match.group(1)

    @staticmethod
    def _extract_required(text: str, pattern: str, field_name: str) -> str:
        match = re.search(pattern, text, re.MULTILINE)
        if not match:
            raise ValueError(f"{field_name} is missing")
        return match.group(1)

    @staticmethod
    def _namespace_major(namespace: str) -> int:
        match = re.search(r"\.v([0-9]+)$", namespace)
        if not match:
            raise ValueError(f"namespace major is missing in {namespace!r}")
        return int(match.group(1))

    @staticmethod
    def _extract_schema_semver(text: str) -> str:
        matches = re.findall(
            r'^\s*schema_version:\s*["\']?([0-9]+\.[0-9]+\.[0-9]+)["\']?\s*$',
            text,
            re.MULTILINE,
        )
        if matches:
            return matches[0]
        return SCHEMA_VERSION

    def _validate_idl_alignment(self, versions: Dict[str, Dict[str, str]]) -> bool:
        for namespace, payload in versions.items():
            semver = payload.get("semver", "")
            if not SEMVER_PATTERN.match(semver):
                return False
            major = self._namespace_major(namespace)
            if int(semver.split(".", 1)[0]) != major:
                return False
        return True

    @staticmethod
    def _validate_contract_versions(versions: Dict[str, Dict[str, str]]) -> bool:
        if not versions:
            return False
        for payload in versions.values():
            semver = payload.get("semver", "")
            stability = payload.get("stability", "")
            if not SEMVER_PATTERN.match(semver):
                return False
            if stability not in {"bootstrap", "stable", "frozen"}:
                return False
        return True
