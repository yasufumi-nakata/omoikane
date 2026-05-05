from __future__ import annotations

import unittest
from pathlib import Path
try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised only on Python 3.10
    import tomli as tomllib

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


class GitHubReleasePackageWorkflowTests(unittest.TestCase):
    def _load_workflow(self, name: str) -> dict:
        workflow_path = REPO_ROOT / ".github" / "workflows" / name
        self.assertTrue(workflow_path.is_file(), name)
        return yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    def _workflow_steps_text(self, workflow: dict) -> str:
        return "\n".join(
            str(step)
            for job in workflow["jobs"].values()
            for step in job.get("steps", [])
        )

    def _job_names(self, workflow: dict, job_name: str) -> list[str]:
        return [step.get("name", "") for step in workflow["jobs"][job_name].get("steps", [])]

    def test_release_workflow_publishes_release_assets_and_ghcr_image(self) -> None:
        workflow = self._load_workflow("release.yml")

        self.assertIn("push", workflow["on"])
        self.assertIn("workflow_dispatch", workflow["on"])
        self.assertEqual("write", workflow["permissions"]["contents"])
        self.assertEqual("write", workflow["permissions"]["packages"])
        self.assertIn("release-metadata", workflow["jobs"])
        self.assertIn("python-package", workflow["jobs"])
        self.assertIn("installed-wheel-smoke", workflow["jobs"])
        self.assertIn("container-package", workflow["jobs"])
        self.assertIn("publish-release", workflow["jobs"])

        steps = self._workflow_steps_text(workflow)
        self.assertIn("python -m unittest discover -s tests -t .", steps)
        self.assertIn("python -m build --sdist --wheel", steps)
        self.assertIn("gh release", steps)
        self.assertIn("docker/build-push-action@v6", steps)
        self.assertIn("release-manifest.json", steps)
        self.assertIn("gap-report.json", steps)

    def test_release_workflow_checks_tag_version_and_smokes_wheel_on_each_os(self) -> None:
        workflow = self._load_workflow("release.yml")

        metadata_steps = self._job_names(workflow, "release-metadata")
        self.assertIn("Check tag matches project version", metadata_steps)

        smoke_job = workflow["jobs"]["installed-wheel-smoke"]
        self.assertEqual(
            ["ubuntu-latest", "macos-latest", "windows-latest"],
            smoke_job["strategy"]["matrix"]["os"],
        )

        publish_needs = set(workflow["jobs"]["publish-release"]["needs"])
        self.assertIn("installed-wheel-smoke", publish_needs)
        self.assertIn("python-package", publish_needs)

        steps = self._workflow_steps_text(workflow)
        self.assertIn("RELEASE_TAG", steps)
        self.assertIn("project_version", steps)
        self.assertIn("tomllib.loads", steps)
        self.assertIn("Verify installed wheel", steps)
        self.assertIn("human-body-analysis-demo", steps)
        self.assertIn("installed-human-body-analysis.json", steps)
        self.assertIn("installed console script not found", steps)
        self.assertIn("installed-demo.json", steps)

    def test_release_workflow_uses_portable_checksums(self) -> None:
        workflow = self._load_workflow("release.yml")
        steps = self._workflow_steps_text(workflow)

        self.assertIn("hashlib.sha256", steps)
        self.assertIn("SHA256SUMS", steps)
        self.assertNotIn("sha256sum", steps)
        self.assertNotIn("shasum", steps)

    def test_package_workflow_builds_python_artifact_and_publishes_ghcr(self) -> None:
        workflow = self._load_workflow("package.yml")

        self.assertIn("push", workflow["on"])
        self.assertIn("pull_request", workflow["on"])
        self.assertEqual("write", workflow["permissions"]["packages"])

        self.assertIn("python-package", workflow["jobs"])
        self.assertIn("container-package", workflow["jobs"])

        matrix = workflow["jobs"]["python-package"]["strategy"]["matrix"]["include"]
        os_names = {entry["os"] for entry in matrix}
        python_versions = {entry["python-version"] for entry in matrix}
        self.assertEqual({"ubuntu-latest", "macos-latest", "windows-latest"}, os_names)
        self.assertIn("3.10", python_versions)
        self.assertIn("3.12", python_versions)

        steps = self._workflow_steps_text(workflow)
        self.assertIn("python -m build --sdist --wheel", steps)
        self.assertIn("actions/upload-artifact@v4", steps)
        self.assertIn("docker/build-push-action@v6", steps)
        self.assertIn("Verify installed wheel", steps)
        self.assertIn("human-body-analysis-demo", steps)
        self.assertIn("installed-human-body-analysis.json", steps)
        self.assertIn("installed console script not found", steps)
        self.assertIn("hashlib.sha256", steps)
        self.assertNotIn("sha256sum", steps)
        self.assertNotIn("shasum", steps)

    def test_container_workflows_publish_multi_arch_ghcr_images(self) -> None:
        for workflow_name in ("package.yml", "release.yml"):
            workflow = self._load_workflow(workflow_name)
            steps = self._workflow_steps_text(workflow)

            self.assertIn("docker/setup-qemu-action@v3", steps)
            self.assertIn("docker/setup-buildx-action@v3", steps)
            self.assertIn("docker/login-action@v3", steps)
            self.assertIn("docker/build-push-action@v6", steps)
            self.assertIn("platforms': 'linux/amd64,linux/arm64", steps)
            self.assertIn("ghcr.io/", steps)

    def test_pyproject_declares_pure_python_package_metadata(self) -> None:
        pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual("setuptools.build_meta", pyproject["build-system"]["build-backend"])
        self.assertIn("wheel>=0.42", pyproject["build-system"]["requires"])

        project = pyproject["project"]
        self.assertEqual("omoikane-os", project["name"])
        self.assertEqual(">=3.10", project["requires-python"])
        self.assertIn("Operating System :: OS Independent", project["classifiers"])
        self.assertIn("Programming Language :: Python :: 3 :: Only", project["classifiers"])
        self.assertEqual("omoikane.cli:main", project["scripts"]["omoikane"])

        setuptools = pyproject["tool"]["setuptools"]
        self.assertFalse(setuptools["include-package-data"])
        self.assertEqual({"": "src"}, setuptools["package-dir"])
        self.assertEqual(["src"], pyproject["tool"]["setuptools"]["packages"]["find"]["where"])
        self.assertEqual(
            ["*.py[cod]", "__pycache__/*", ".DS_Store"],
            pyproject["tool"]["setuptools"]["exclude-package-data"]["*"],
        )

    def test_dockerfile_runs_omoikane_cli_by_default(self) -> None:
        dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("FROM python:3.11-slim", dockerfile)
        self.assertIn('ENTRYPOINT ["omoikane"]', dockerfile)
        self.assertIn('CMD ["demo", "--json"]', dockerfile)
