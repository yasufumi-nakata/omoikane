"""Gap scanning utilities for the self-construction layer."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List

from ..common import canonical_json, new_id, sha256_text, utc_now_iso


GAP_REPORT_SCHEMA_VERSION = "1.0.0"
GAP_REPORT_SCAN_RECEIPT_PROFILE = "self-construction-gap-report-scan-receipt-v1"
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
DECISION_LOG_FRONTIER_MARKERS = (
    "next-stage frontier",
    "次段の frontier",
)
DECISION_LOG_OPERATIONAL_FOLLOWUP_MARKERS = (
    "engine adapter",
    "transaction log",
    "adapter surface",
)
DECISION_LOG_GAP_MARKER_RULES = (
    ("decision-log-residual", DECISION_LOG_RESIDUAL_MARKERS),
    ("decision-log-frontier", DECISION_LOG_FRONTIER_MARKERS),
)
DECISION_LOG_FOLLOWUP_SECTIONS = {
    "## Remaining scope",
    "## Deferred scope",
}
DECISION_LOG_IGNORED_NAME_SNIPPETS = ("gap-report",)
DECISION_LOG_NEXT_GAP_IDS_KEY = "next_gap_ids"
DECISION_LOG_CLOSES_NEXT_GAPS_KEY = "closes_next_gaps"
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
CATALOG_COVERAGE_SPECS = (
    ("specs/interfaces", (".idl",)),
    ("specs/schemas", (".schema", ".yaml")),
)
EVAL_INVENTORY_GLOB = "evals/*/README.md"
IMPLEMENTATION_STUB_GLOB = "src/omoikane/**/*.py"
IMPLEMENTATION_STUB_ABSTRACT_CLASS_SUFFIXES = ("Backend",)


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
        catalog_coverage_hits = self._catalog_coverage_hits(repo_root)
        future_work_hits = self._future_work_hits(repo_root)
        implementation_stub_hits = self._implementation_stub_hits(repo_root)
        decision_log_gap_hits = self._decision_log_gap_hits(repo_root)
        decision_log_residual_hits = [
            hit for hit in decision_log_gap_hits if hit["kind"] == "decision-log-residual"
        ]
        decision_log_frontier_hits = [
            hit for hit in decision_log_gap_hits if hit["kind"] == "decision-log-frontier"
        ]

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
        for hit in catalog_coverage_hits[:10]:
            prioritized_tasks.append(
                {
                    "priority": "high",
                    "kind": "catalog-coverage-gap",
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
        for hit in implementation_stub_hits[:10]:
            prioritized_tasks.append(
                {
                    "priority": "high",
                    "kind": "implementation-stub",
                    "summary": f"{hit['path']}: {hit['line']}",
                }
            )
        for hit in decision_log_frontier_hits[:10]:
            prioritized_tasks.append(
                {
                    "priority": "medium",
                    "kind": "decision-log-frontier",
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

        report = {
            "repo_root": str(repo_root),
            "open_question_count": len(open_questions),
            "missing_expected_file_count": len(missing_specs),
            "missing_required_reference_file_count": len(missing_reference_files),
            "empty_eval_surface_count": len(empty_eval_surfaces),
            "placeholder_hit_count": len(placeholder_hits),
            "inventory_drift_count": len(inventory_drift_hits),
            "catalog_coverage_gap_count": len(catalog_coverage_hits),
            "future_work_hit_count": len(future_work_hits),
            "implementation_stub_count": len(implementation_stub_hits),
            "decision_log_residual_count": len(decision_log_residual_hits),
            "decision_log_frontier_count": len(decision_log_frontier_hits),
            "open_questions": open_questions,
            "missing_expected_files": missing_specs,
            "missing_required_reference_files": missing_reference_files,
            "empty_eval_surfaces": empty_eval_surfaces,
            "catalog_pending_count": len(catalog_pending),
            "catalog_pending_files": catalog_pending,
            "placeholder_hits": placeholder_hits,
            "inventory_drift_hits": inventory_drift_hits,
            "catalog_coverage_gap_hits": catalog_coverage_hits,
            "future_work_hits": future_work_hits,
            "implementation_stub_hits": implementation_stub_hits,
            "decision_log_residual_hits": decision_log_residual_hits,
            "decision_log_frontier_hits": decision_log_frontier_hits,
            "prioritized_tasks": prioritized_tasks,
        }
        report["scan_receipt"] = self._build_scan_receipt(report)
        return report

    def _build_scan_receipt(self, report: Dict[str, Any]) -> Dict[str, Any]:
        counts = {
            "open_question_count": int(report["open_question_count"]),
            "missing_expected_file_count": int(report["missing_expected_file_count"]),
            "missing_required_reference_file_count": int(
                report["missing_required_reference_file_count"]
            ),
            "empty_eval_surface_count": int(report["empty_eval_surface_count"]),
            "placeholder_hit_count": int(report["placeholder_hit_count"]),
            "inventory_drift_count": int(report["inventory_drift_count"]),
            "catalog_coverage_gap_count": int(report["catalog_coverage_gap_count"]),
            "future_work_hit_count": int(report["future_work_hit_count"]),
            "implementation_stub_count": int(report["implementation_stub_count"]),
            "decision_log_residual_count": int(report["decision_log_residual_count"]),
            "decision_log_frontier_count": int(report["decision_log_frontier_count"]),
            "catalog_pending_count": int(report["catalog_pending_count"]),
            "prioritized_task_count": len(report["prioritized_tasks"]),
        }
        all_zero = all(value == 0 for value in counts.values())
        report_digest = sha256_text(canonical_json(self._report_digest_payload(report)))
        receipt: Dict[str, Any] = {
            "kind": "gap_report_scan_receipt",
            "schema_version": GAP_REPORT_SCHEMA_VERSION,
            "receipt_id": new_id("gap-report-scan"),
            "generated_at": utc_now_iso(),
            "profile": GAP_REPORT_SCAN_RECEIPT_PROFILE,
            "repo_root": str(report["repo_root"]),
            "scanned_surfaces": [
                "meta/open-questions.md",
                "references/*.md",
                "specs/catalog.yaml",
                "specs/interfaces/README.md",
                "specs/schemas/README.md",
                "evals/*/README.md",
                "README.md",
                "docs/07-reference-implementation/README.md",
                "specs/interfaces/**/*.idl",
                "specs/schemas/README.md",
                "src/omoikane/**/*.py",
                "meta/decision-log/*.md",
            ],
            "counts": counts,
            "all_zero": all_zero,
            "report_digest": report_digest,
            "raw_report_payload_stored": False,
            "validation": {
                "ok": all_zero,
                "counts_match_report": True,
                "report_digest_bound": True,
                "prioritized_tasks_empty_when_all_zero": (
                    len(report["prioritized_tasks"]) == 0 if all_zero else True
                ),
                "raw_report_payload_stored": False,
            },
        }
        return receipt

    @staticmethod
    def _report_digest_payload(report: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: value
            for key, value in report.items()
            if key != "scan_receipt"
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

    def _catalog_coverage_hits(self, repo_root: Path) -> List[Dict[str, str]]:
        catalog_path = repo_root / "specs" / "catalog.yaml"
        if not catalog_path.exists():
            return []

        catalog_files = self._catalog_declared_files(catalog_path)
        hits: List[Dict[str, str]] = []
        for directory_name, suffixes in CATALOG_COVERAGE_SPECS:
            directory_path = repo_root / directory_name
            if not directory_path.exists():
                continue
            for path in sorted(directory_path.iterdir()):
                if not path.is_file() or path.suffix not in suffixes:
                    continue
                relative_path = str(path.relative_to(repo_root))
                if relative_path in catalog_files:
                    continue
                hits.append(
                    {
                        "path": "specs/catalog.yaml",
                        "line": f"`{relative_path}` is implemented but missing from catalog entries",
                        "missing_catalog_file": relative_path,
                    }
                )
        return hits

    @staticmethod
    def _catalog_declared_files(catalog_path: Path) -> set[str]:
        files: set[str] = set()
        for line in catalog_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped.startswith("file:"):
                continue
            _, _, value = stripped.partition(":")
            candidate = value.strip().strip("'\"")
            if candidate:
                files.add(candidate)
        return files

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

    def _implementation_stub_hits(self, repo_root: Path) -> List[Dict[str, str]]:
        """Find runtime code paths that still raise non-abstract NotImplementedError."""

        hits: List[Dict[str, str]] = []
        for path in sorted(repo_root.glob(IMPLEMENTATION_STUB_GLOB)):
            if not path.is_file():
                continue
            try:
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError):
                continue
            line_lookup = source.splitlines()
            relative_path = str(path.relative_to(repo_root))
            visitor = _ImplementationStubVisitor(relative_path, line_lookup)
            visitor.visit(tree)
            hits.extend(visitor.hits)
        return hits

    def _decision_log_gap_hits(self, repo_root: Path) -> List[Dict[str, str]]:
        hits: List[Dict[str, str]] = []
        seen = set()
        decision_logs = self._latest_decision_logs(repo_root / "meta" / "decision-log")
        closed_gap_refs = self._closed_decision_log_gap_refs(decision_logs)
        for path in decision_logs:
            if any(snippet in path.name for snippet in DECISION_LOG_IGNORED_NAME_SNIPPETS):
                continue
            relative_path = path.relative_to(repo_root)
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            next_gap_ids = self._decision_log_frontmatter_string_list(
                path, DECISION_LOG_NEXT_GAP_IDS_KEY
            )
            in_consequences = False
            in_followup_scope = False
            matched_gap_count = 0
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("## "):
                    in_consequences = stripped == "## Consequences"
                    in_followup_scope = stripped in DECISION_LOG_FOLLOWUP_SECTIONS
                    continue
                if not in_consequences and not in_followup_scope:
                    continue
                lowered = stripped.lower()
                if not stripped.startswith("- "):
                    continue
                hit_kind = (
                    self._decision_log_hit_kind(lowered)
                    if in_consequences
                    else self._decision_log_followup_hit_kind(lowered)
                )
                if hit_kind is None:
                    continue
                next_gap_id = (
                    next_gap_ids[matched_gap_count]
                    if matched_gap_count < len(next_gap_ids)
                    else f"gap-{matched_gap_count + 1}"
                )
                matched_gap_count += 1
                next_gap_ref = f"{path.name}#{next_gap_id}"
                if next_gap_ref in closed_gap_refs:
                    continue
                key = (str(relative_path), stripped, hit_kind)
                if key in seen:
                    continue
                seen.add(key)
                hits.append(
                    {
                        "kind": hit_kind,
                        "path": str(relative_path),
                        "line": stripped,
                        "decision_date": path.name[:10],
                        "next_gap_ref": next_gap_ref,
                    }
                )
        return hits

    @staticmethod
    def _decision_log_hit_kind(line_lowered: str) -> str | None:
        for hit_kind, markers in DECISION_LOG_GAP_MARKER_RULES:
            if any(marker in line_lowered for marker in markers):
                return hit_kind
        return None

    @staticmethod
    def _decision_log_followup_hit_kind(line_lowered: str) -> str | None:
        if any(marker in line_lowered for marker in DECISION_LOG_OPERATIONAL_FOLLOWUP_MARKERS):
            return "decision-log-frontier"
        return None

    def _closed_decision_log_gap_refs(self, decision_logs: List[Path]) -> set[str]:
        closed_refs: set[str] = set()
        for path in decision_logs:
            for entry in self._decision_log_frontmatter_string_list(
                path, DECISION_LOG_CLOSES_NEXT_GAPS_KEY
            ):
                normalized = self._normalize_decision_log_gap_ref(entry)
                if normalized:
                    closed_refs.add(normalized)
        return closed_refs

    @staticmethod
    def _normalize_decision_log_gap_ref(value: str) -> str:
        text = str(value).strip()
        if not text or "#" not in text:
            return ""
        path_part, _, gap_id = text.partition("#")
        normalized_gap_id = gap_id.strip()
        if not normalized_gap_id:
            return ""
        normalized_name = Path(path_part.strip()).name
        if not normalized_name:
            return ""
        return f"{normalized_name}#{normalized_gap_id}"

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
        metadata = GapScanner._decision_log_frontmatter(path)
        status = metadata.get("status")
        if not isinstance(status, str) or not status.strip():
            return "decided"
        return status.strip().lower()

    @staticmethod
    def _decision_log_frontmatter(path: Path) -> Dict[str, Any]:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            return {}
        if not lines or lines[0].strip() != "---":
            return {}

        metadata: Dict[str, Any] = {}
        index = 1
        while index < len(lines):
            stripped = lines[index].strip()
            if stripped == "---":
                break
            if not stripped or ":" not in stripped:
                index += 1
                continue
            key, _, value = stripped.partition(":")
            normalized_key = key.strip()
            normalized_value = value.strip()
            if normalized_value:
                metadata[normalized_key] = GapScanner._parse_frontmatter_scalar(normalized_value)
                index += 1
                continue

            items: List[str] = []
            index += 1
            while index < len(lines):
                child = lines[index]
                child_stripped = child.strip()
                if child_stripped == "---":
                    break
                if not child_stripped:
                    index += 1
                    continue
                if not child.startswith("  - ") and not child.startswith("- "):
                    break
                items.append(child_stripped[2:].strip().strip("'\""))
                index += 1
            metadata[normalized_key] = items
        return metadata

    @staticmethod
    def _parse_frontmatter_scalar(value: str) -> Any:
        candidate = value.strip()
        if candidate.startswith("[") and candidate.endswith("]"):
            try:
                parsed = ast.literal_eval(candidate)
            except (SyntaxError, ValueError):
                return candidate.strip("'\"")
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        return candidate.strip("'\"")

    @staticmethod
    def _decision_log_frontmatter_string_list(path: Path, key: str) -> List[str]:
        value = GapScanner._decision_log_frontmatter(path).get(key, [])
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    @staticmethod
    def _looks_like_iso_date(value: str) -> bool:
        if len(value) != 10 or value[4] != "-" or value[7] != "-":
            return False
        year, month, day = value[:4], value[5:7], value[8:10]
        return year.isdigit() and month.isdigit() and day.isdigit()


class _ImplementationStubVisitor(ast.NodeVisitor):
    """AST visitor that keeps intentional abstract backend hooks out of gap reports."""

    def __init__(self, relative_path: str, line_lookup: List[str]) -> None:
        self.relative_path = relative_path
        self.line_lookup = line_lookup
        self.class_stack: List[str] = []
        self.function_stack: List[str] = []
        self.hits: List[Dict[str, str]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        self.visit_FunctionDef(node)

    def visit_Raise(self, node: ast.Raise) -> Any:
        if not self._raises_not_implemented(node):
            return
        if self._is_intentional_abstract_hook():
            return
        line = self.line_lookup[node.lineno - 1].strip() if node.lineno <= len(self.line_lookup) else ""
        self.hits.append(
            {
                "path": self.relative_path,
                "line": line,
                "symbol": self._current_symbol(),
            }
        )

    @staticmethod
    def _raises_not_implemented(node: ast.Raise) -> bool:
        exc = node.exc
        if isinstance(exc, ast.Call):
            exc = exc.func
        if isinstance(exc, ast.Name):
            return exc.id == "NotImplementedError"
        if isinstance(exc, ast.Attribute):
            return exc.attr == "NotImplementedError"
        return False

    def _is_intentional_abstract_hook(self) -> bool:
        if not self.class_stack or not self.function_stack:
            return False
        class_name = self.class_stack[-1]
        function_name = self.function_stack[-1]
        return class_name.endswith(IMPLEMENTATION_STUB_ABSTRACT_CLASS_SUFFIXES) and function_name.startswith("_")

    def _current_symbol(self) -> str:
        parts = [*self.class_stack, *self.function_stack]
        return ".".join(parts)
