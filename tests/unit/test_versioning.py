from __future__ import annotations

import copy
import unittest
from pathlib import Path

from omoikane.governance import VersioningService


class VersioningServiceTests(unittest.TestCase):
    def test_build_release_manifest_collects_runtime_contracts(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        service = VersioningService()

        manifest = service.build_release_manifest(repo_root)
        validation = service.validate_release_manifest(repo_root, manifest)

        self.assertTrue(validation["ok"])
        self.assertEqual("release_manifest", manifest["kind"])
        self.assertEqual("0.1.0", manifest["runtime_version"])
        self.assertEqual("2026.04", manifest["regulation_calver"])
        self.assertIn("agentic.council.v0", manifest["idl_versions"])
        self.assertIn("specs/schemas/release_manifest.schema", manifest["schema_versions"])

    def test_validate_release_manifest_detects_catalog_tamper(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        service = VersioningService()
        manifest = service.build_release_manifest(repo_root)
        tampered = copy.deepcopy(manifest)
        tampered["catalog_snapshot"]["sha256"] = "deadbeef"

        validation = service.validate_release_manifest(repo_root, tampered)

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["catalog_hash_matches"])
        self.assertTrue(any("catalog_snapshot.sha256" in error for error in validation["errors"]))


if __name__ == "__main__":
    unittest.main()
