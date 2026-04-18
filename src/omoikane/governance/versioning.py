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
            },
        }

    def build_release_manifest(self, repo_root: Path) -> Dict[str, Any]:
        runtime_version = self._read_project_version(repo_root / "pyproject.toml")
        catalog_text = self._read_text(repo_root / "specs" / "catalog.yaml")
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
            "notes": [
                "reference runtime uses semver for package/runtime surfaces",
                "IDL and schema contracts default to bootstrap stability until external governance promotes them",
                "governance layers use calver because amendment timing follows human review cadence",
            ],
        }

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
            "idl_count": len(manifest.get("idl_versions", {})),
            "schema_count": len(manifest.get("schema_versions", {})),
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
