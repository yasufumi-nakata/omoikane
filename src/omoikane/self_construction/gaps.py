"""Gap scanning utilities for the self-construction layer."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List


PLACEHOLDER_MARKERS = (
    "プレースホルダ",
    "すべて未生成",
    "本体記述",
    "未生成",
)
DECISION_LOG_RESIDUAL_MARKERS = (
    "residual gap",
    "residual future work",
    "residual scope",
    "unresolved gap",
)
DECISION_LOG_IGNORED_NAME_SNIPPETS = ("gap-report",)
REQUIRED_REFERENCE_FILES = (
    "references/operating-playbook.md",
    "references/repo-coverage-checklist.md",
    "references/verification-checklist.md",
)
TRUTH_SOURCE_FUTURE_WORK_GLOBS = (
    "README.md",
    "docs/07-reference-implementation/README.md",
    "specs/interfaces/**/*.idl",
    "specs/schemas/README.md",
)
FUTURE_WORK_IGNORED_SNIPPETS = (
    "deferred surface",
    "deferred surfaces",
)
TRUTH_SOURCE_INVENTORY_SPECS = (
    ("specs/interfaces/README.md", "specs/interfaces", (".idl",)),
    ("specs/schemas/README.md", "specs/schemas", (".schema", ".yaml")),
)
EVAL_INVENTORY_GLOB = "evals/*/README.md"


class GapScanner:
    """Extract unresolved implementation gaps from the repository."""

    def scan(self, repo_root: Path) -> Dict[str, object]:
        repo_root = repo_root.resolve()
        open_questions = self._unchecked_items(repo_root / "meta" / "open-questions.md")
        missing_specs = self._missing_expected_files(repo_root / "specs")
        missing_reference_files = self._missing_required_reference_files(repo_root)
        empty_eval_surfaces = self._empty_eval_surfaces(repo_root / "evals")
        catalog_pending = self._catalog_pending_files(repo_root / "specs" / "catalog.yaml", repo_root)
        placeholder_hits = self._placeholder_hits(repo_root)
        inventory_drift_hits = self._inventory_drift_hits(repo_root)
        future_work_hits = self._future_work_hits(repo_root)
        decision_log_residual_hits = self._decision_log_residual_hits(repo_root)

        prioritized_tasks: List[Dict[str, str]] = []
        for filename in missing_specs:
            prioritized_tasks.append(
                {
                    "priority": "high",
                    "kind": "missing-spec",
                    "summary": f"期待される spec/eval ファイルが未作成です: {filename}",
                }
            )
        for filename in missing_reference_files:
            prioritized_tasks.append(
                {
                    "priority": "high",
                    "kind": "missing-reference-file",
                    "summary": f"automation 用 reference file が未作成です: {filename}",
                }
            )
        for surface in empty_eval_surfaces:
            prioritized_tasks.append(
                {
                    "priority": "high",
                    "kind": "empty-eval-surface",
                    "summary": f"評価 surface が空です: {surface}",
                }
            )
        for filename in catalog_pending:
            prioritized_tasks.append(
                {
                    "priority": "high",
                    "kind": "catalog-next-priority",
                    "summary": f"catalog の次優先ファイルが未実装です: {filename}",
                }
            )
        for hit in inventory_drift_hits[:10]:
            prioritized_tasks.append(
                {
                    "priority": "high",
                    "kind": "inventory-drift",
                    "summary": f"{hit['path']}: {hit['line']}",
                }
            )
        for hit in future_work_hits[:10]:
            prioritized_tasks.append(
                {
                    "priority": "high",
                    "kind": "future-work",
                    "summary": f"{hit['path']}: {hit['line']}",
                }
            )
        for hit in decision_log_residual_hits[:10]:
            prioritized_tasks.append(
                {
                    "priority": "medium",
                    "kind": "decision-log-residual",
                    "summary": f"{hit['path']}: {hit['line']}",
                }
            )
        for item in open_questions[:10]:
            prioritized_tasks.append(
                {
                    "priority": "medium",
                    "kind": "open-question",
                    "summary": item,
                }
            )
        for hit in placeholder_hits[:10]:
            prioritized_tasks.append(
                {
                    "priority": "medium",
                    "kind": "placeholder",
                    "summary": f"{hit['path']}: {hit['line']}",
                }
            )

        return {
            "repo_root": str(repo_root),
            "open_question_count": len(open_questions),
            "missing_expected_file_count": len(missing_specs),
            "missing_required_reference_file_count": len(missing_reference_files),
            "empty_eval_surface_count": len(empty_eval_surfaces),
            "placeholder_hit_count": len(placeholder_hits),
            "inventory_drift_count": len(inventory_drift_hits),
            "future_work_hit_count": len(future_work_hits),
            "decision_log_residual_count": len(decision_log_residual_hits),
            "open_questions": open_questions,
            "missing_expected_files": missing_specs,
            "missing_required_reference_files": missing_reference_files,
            "empty_eval_surfaces": empty_eval_surfaces,
            "catalog_pending_count": len(catalog_pending),
            "catalog_pending_files": catalog_pending,
            "placeholder_hits": placeholder_hits,
            "inventory_drift_hits": inventory_drift_hits,
            "future_work_hits": future_work_hits,
            "decision_log_residual_hits": decision_log_residual_hits,
            "prioritized_tasks": prioritized_tasks,
        }

    @staticmethod
    def _catalog_pending_files(catalog_path: Path, repo_root: Path) -> List[str]:
        if not catalog_path.exists():
            return []

        pending: List[str] = []
        in_next_priority = False
        for line in catalog_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped == "next_priority:":
                in_next_priority = True
                continue
            if not in_next_priority:
                continue
            if stripped.startswith("- "):
                candidate = stripped[2:].strip().strip("'\"")
                if candidate and not (repo_root / candidate).exists():
                    pending.append(candidate)
                continue
            if stripped and not stripped.startswith("#"):
                break
        return pending

    @staticmethod
    def _unchecked_items(path: Path) -> List[str]:
        if not path.exists():
            return []
        items: List[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("- [ ] "):
                items.append(stripped[6:])
        return items

    def _missing_expected_files(self, specs_root: Path) -> List[str]:
        readmes = [
            specs_root / "interfaces" / "README.md",
            specs_root / "schemas" / "README.md",
            specs_root / "invariants" / "README.md",
        ]
        expected_paths: List[Path] = []
        for readme in readmes:
            if not readme.exists():
                continue
            expected_paths.extend(self._extract_expected_paths(readme))

        return [
            str(path.relative_to(specs_root.parent))
            for path in expected_paths
            if not path.exists()
        ]

    @staticmethod
    def _missing_required_reference_files(repo_root: Path) -> List[str]:
        return [
            filename
            for filename in REQUIRED_REFERENCE_FILES
            if not (repo_root / filename).exists()
        ]

    @staticmethod
    def _extract_expected_paths(readme_path: Path) -> List[Path]:
        return [readme_path.parent / candidate for candidate in GapScanner._extract_inventory_entries(readme_path)]

    @staticmethod
    def _extract_inventory_entries(readme_path: Path) -> List[str]:
        entries: List[str] = []
        for line in readme_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped.startswith("- "):
                continue
            if "`" not in stripped:
                continue
            parts = stripped.split("`")
            for index in range(1, len(parts), 2):
                candidate = parts[index].strip()
                if not candidate or "/" in candidate:
                    continue
                entries.append(candidate)
        return entries

    @staticmethod
    def _empty_eval_surfaces(evals_root: Path) -> List[str]:
        if not evals_root.exists():
            return []

        surfaces: List[str] = []
        for child in sorted(path for path in evals_root.iterdir() if path.is_dir()):
            has_eval_files = any(
                candidate.is_file() and candidate.suffix.lower() in {".yaml", ".yml"}
                for candidate in child.rglob("*")
            )
            if not has_eval_files:
                surfaces.append(str(child.relative_to(evals_root.parent)))
        return surfaces

    def _placeholder_hits(self, repo_root: Path) -> List[Dict[str, str]]:
        hits: List[Dict[str, str]] = []
        for path in repo_root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".md", ".yaml", ".yml", ".json"}:
                continue
            relative_path = path.relative_to(repo_root)
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("- [x] "):
                    continue
                if any(marker in stripped for marker in PLACEHOLDER_MARKERS):
                    hits.append({"path": str(relative_path), "line": stripped})
        return hits

    def _inventory_drift_hits(self, repo_root: Path) -> List[Dict[str, str]]:
        hits: List[Dict[str, str]] = []
        inventory_specs = list(TRUTH_SOURCE_INVENTORY_SPECS)
        for readme_path in sorted(repo_root.glob(EVAL_INVENTORY_GLOB)):
            relative_path = readme_path.relative_to(repo_root)
            inventory_specs.append(
                (
                    str(relative_path),
                    str(relative_path.parent),
                    (".yaml", ".yml"),
                )
            )

        for readme_name, directory_name, suffixes in inventory_specs:
            readme_path = repo_root / readme_name
            directory_path = repo_root / directory_name
            if not readme_path.exists() or not directory_path.exists():
                continue
            listed_entries = set(self._extract_inventory_entries(readme_path))
            actual_entries = {
                path.name
                for suffix in suffixes
                for path in directory_path.glob(f"*{suffix}")
                if path.is_file()
            }
            for missing_entry in sorted(actual_entries - listed_entries):
                hits.append(
                    {
                        "path": readme_name,
                        "line": f"`{missing_entry}` is implemented but missing from the README inventory",
                    }
                )
        return hits

    def _future_work_hits(self, repo_root: Path) -> List[Dict[str, str]]:
        hits: List[Dict[str, str]] = []
        seen_paths = set()
        candidates: List[Path] = []
        for pattern in TRUTH_SOURCE_FUTURE_WORK_GLOBS:
            for path in sorted(repo_root.glob(pattern)):
                if not path.is_file():
                    continue
                relative = str(path.relative_to(repo_root))
                if relative in seen_paths:
                    continue
                seen_paths.add(relative)
                candidates.append(path)

        for path in candidates:
            relative_path = path.relative_to(repo_root)
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for line in text.splitlines():
                stripped = line.strip()
                lowered = stripped.lower()
                if not stripped or stripped.startswith("#"):
                    continue
                if not stripped.startswith("- "):
                    continue
                if "future work" not in lowered:
                    continue
                if any(snippet in lowered for snippet in FUTURE_WORK_IGNORED_SNIPPETS):
                    continue
                hits.append({"path": str(relative_path), "line": stripped})
        return hits

    def _decision_log_residual_hits(self, repo_root: Path) -> List[Dict[str, str]]:
        hits: List[Dict[str, str]] = []
        seen = set()
        decision_logs = self._latest_decision_logs(repo_root / "meta" / "decision-log")
        for path in decision_logs:
            if any(snippet in path.name for snippet in DECISION_LOG_IGNORED_NAME_SNIPPETS):
                continue
            relative_path = path.relative_to(repo_root)
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            in_consequences = False
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("## "):
                    in_consequences = stripped == "## Consequences"
                    continue
                if not in_consequences:
                    continue
                lowered = stripped.lower()
                if not stripped.startswith("- "):
                    continue
                if not any(marker in lowered for marker in DECISION_LOG_RESIDUAL_MARKERS):
                    continue
                key = (str(relative_path), stripped)
                if key in seen:
                    continue
                seen.add(key)
                hits.append(
                    {
                        "path": str(relative_path),
                        "line": stripped,
                        "decision_date": path.name[:10],
                    }
                )
        return hits

    @staticmethod
    def _latest_decision_logs(decision_log_root: Path) -> List[Path]:
        if not decision_log_root.exists():
            return []

        candidates: List[tuple[str, Path]] = []
        for path in sorted(decision_log_root.glob("*.md")):
            if not path.is_file():
                continue
            date_prefix = path.name[:10]
            if not GapScanner._looks_like_iso_date(date_prefix):
                continue
            if GapScanner._decision_log_status(path) == "superseded":
                continue
            candidates.append((date_prefix, path))

        if not candidates:
            return []

        latest_date = max(date_prefix for date_prefix, _ in candidates)
        return [path for date_prefix, path in candidates if date_prefix == latest_date]

    @staticmethod
    def _decision_log_status(path: Path) -> str:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            return "decided"
        if not lines or lines[0].strip() != "---":
            return "decided"
        for line in lines[1:]:
            stripped = line.strip()
            if stripped == "---":
                break
            if stripped.startswith("status:"):
                return stripped.partition(":")[2].strip().lower()
        return "decided"

    @staticmethod
    def _looks_like_iso_date(value: str) -> bool:
        if len(value) != 10 or value[4] != "-" or value[7] != "-":
            return False
        year, month, day = value[:4], value[5:7], value[8:10]
        return year.isdigit() and month.isdigit() and day.isdigit()
