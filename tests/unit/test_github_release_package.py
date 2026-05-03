from __future__ import annotations

import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


class GitHubReleasePackageWorkflowTests(unittest.TestCase):
    def _load_workflow(self, name: str) -> dict:
        workflow_path = REPO_ROOT / ".github" / "workflows" / name
        self.assertTrue(workflow_path.is_file(), name)
        return yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    def test_release_workflow_publishes_release_assets_and_ghcr_image(self) -> None:
        workflow = self._load_workflow("release.yml")

        self.assertIn("push", workflow["on"])
        self.assertIn("workflow_dispatch", workflow["on"])
        self.assertEqual("write", workflow["permissions"]["contents"])
        self.assertEqual("write", workflow["permissions"]["packages"])

        steps = "\n".join(
            str(step)
            for job in workflow["jobs"].values()
            for step in job.get("steps", [])
        )
        self.assertIn("python -m unittest discover -s tests -t .", steps)
        self.assertIn("python -m build", steps)
        self.assertIn("gh release", steps)
        self.assertIn("docker push", steps)
        self.assertIn("release-manifest.json", steps)
        self.assertIn("gap-report.json", steps)

    def test_package_workflow_builds_python_artifact_and_publishes_ghcr(self) -> None:
        workflow = self._load_workflow("package.yml")

        self.assertIn("push", workflow["on"])
        self.assertIn("pull_request", workflow["on"])
        self.assertEqual("write", workflow["permissions"]["packages"])

        self.assertIn("python-package", workflow["jobs"])
        self.assertIn("container-package", workflow["jobs"])

        steps = "\n".join(
            str(step)
            for job in workflow["jobs"].values()
            for step in job.get("steps", [])
        )
        self.assertIn("python -m build", steps)
        self.assertIn("actions/upload-artifact@v4", steps)
        self.assertIn("docker build", steps)
        self.assertIn("docker push", steps)

    def test_dockerfile_runs_omoikane_cli_by_default(self) -> None:
        dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("FROM python:3.11-slim", dockerfile)
        self.assertIn('ENTRYPOINT ["omoikane"]', dockerfile)
        self.assertIn('CMD ["demo", "--json"]', dockerfile)
