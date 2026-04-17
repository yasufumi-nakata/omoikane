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


class GapScanner:
    """Extract unresolved implementation gaps from the repository."""

    def scan(self, repo_root: Path) -> Dict[str, object]:
        repo_root = repo_root.resolve()
        open_questions = self._unchecked_items(repo_root / "meta" / "open-questions.md")
        missing_specs = self._missing_expected_files(repo_root / "specs")
        empty_eval_surfaces = self._empty_eval_surfaces(repo_root / "evals")
        catalog_pending = self._catalog_pending_files(repo_root / "specs" / "catalog.yaml", repo_root)
        placeholder_hits = self._placeholder_hits(repo_root)

        prioritized_tasks: List[Dict[str, str]] = []
        for filename in missing_specs:
            prioritized_tasks.append(
                {
                    "priority": "high",
                    "kind": "missing-spec",
                    "summary": f"期待される spec/eval ファイルが未作成です: {filename}",
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
            "empty_eval_surface_count": len(empty_eval_surfaces),
            "placeholder_hit_count": len(placeholder_hits),
            "open_questions": open_questions,
            "missing_expected_files": missing_specs,
            "empty_eval_surfaces": empty_eval_surfaces,
            "catalog_pending_count": len(catalog_pending),
            "catalog_pending_files": catalog_pending,
            "placeholder_hits": placeholder_hits,
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
    def _extract_expected_paths(readme_path: Path) -> List[Path]:
        expected: List[Path] = []
        base_dir = readme_path.parent
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
                expected.append(base_dir / candidate)
        return expected

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
