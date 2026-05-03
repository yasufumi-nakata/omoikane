#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import quote


DEFAULT_REPO_URL = "https://github.com/yasufumi-nakata/omoikane/blob/main"
MANIFEST_NAME = ".omoikane-docs-wiki-manifest.json"
LINK_PATTERN = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")


@dataclass(frozen=True)
class DocPage:
    source_path: Path
    page_name: str
    title: str
    sha256: str

    @property
    def page_file(self) -> str:
        return f"{self.page_name}.md"


def _run_git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return "unknown"
    return completed.stdout.strip() or "unknown"


def _page_name_for_doc(path: Path) -> str:
    without_suffix = path.with_suffix("")
    parts = list(without_suffix.parts)
    if parts[-1].lower() == "readme":
        parts = parts[:-1]
    slug = "-".join(parts)
    slug = re.sub(r"[^A-Za-z0-9]+", "-", slug).strip("-").lower()
    return slug or "docs"


def _first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip() or fallback
    return fallback


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _discover_docs(repo_root: Path) -> list[DocPage]:
    pages: list[DocPage] = []
    for source in sorted((repo_root / "docs").rglob("*.md")):
        relative = source.relative_to(repo_root)
        text = source.read_text(encoding="utf-8")
        pages.append(
            DocPage(
                source_path=relative,
                page_name=_page_name_for_doc(relative),
                title=_first_heading(text, relative.as_posix()),
                sha256=_sha256(text),
            )
        )
    return pages


def _split_link_target(target: str) -> tuple[str, str]:
    match = re.match(r"^(\S+)(\s+\"[^\"]*\")$", target)
    if match:
        return match.group(1), match.group(2)
    return target, ""


def _repo_source_url(repo_root: Path, repo_url: str, path: Path, fragment: str) -> str:
    encoded_path = quote(path.as_posix(), safe="/")
    encoded_fragment = f"#{fragment}" if fragment else ""
    base_url = repo_url.rstrip("/")
    if (repo_root / path).is_dir():
        base_url = base_url.replace("/blob/", "/tree/")
    return f"{base_url}/{encoded_path}{encoded_fragment}"


def _resolve_repo_path(repo_root: Path, source_path: Path, target: str) -> Path | None:
    if not target or target.startswith("#"):
        return None
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
        return None

    path_part, _, _fragment = target.partition("#")
    if not path_part:
        return None
    if path_part.startswith("/"):
        candidate = repo_root / path_part.lstrip("/")
    else:
        candidate = repo_root / source_path.parent / path_part
    candidate = candidate.resolve()
    if candidate.is_dir():
        readme_path = candidate / "README.md"
        if readme_path.exists():
            candidate = readme_path
    if candidate.suffix == "":
        markdown_candidate = candidate.with_suffix(".md")
        if markdown_candidate.exists():
            candidate = markdown_candidate
    try:
        return candidate.relative_to(repo_root.resolve())
    except ValueError:
        return None


def _rewrite_links(
    *,
    text: str,
    repo_root: Path,
    source_path: Path,
    page_by_doc: dict[Path, str],
    repo_url: str,
) -> str:
    def replace(match: re.Match[str]) -> str:
        label = match.group(1)
        original_target = match.group(2)
        target, title = _split_link_target(original_target)
        _path_part, separator, fragment = target.partition("#")
        resolved = _resolve_repo_path(repo_root, source_path, target)
        if resolved is None:
            return match.group(0)
        if resolved in page_by_doc:
            wiki_target = page_by_doc[resolved]
            if separator:
                wiki_target = f"{wiki_target}#{fragment}"
            return f"[{label}]({wiki_target}{title})"
        if (repo_root / resolved).exists():
            source_url = _repo_source_url(repo_root, repo_url, resolved, fragment)
            return f"[{label}]({source_url}{title})"
        return match.group(0)

    return LINK_PATTERN.sub(replace, text)


def _build_home(pages: Iterable[DocPage], repo_url: str, source_ref: str) -> str:
    grouped: dict[str, list[DocPage]] = {}
    for page in pages:
        group = page.source_path.parent.as_posix()
        grouped.setdefault(group, []).append(page)

    lines = [
        "# OmoikaneOS Wiki",
        "",
        "この wiki は `omoikane` repo の `docs/` 以下から生成した設計 mirror です。",
        "編集の正本は main repo 側の docs であり、wiki は閲覧用の索引として扱います。",
        "",
        f"- Source: [{repo_url.rstrip('/')}]({repo_url.rstrip('/')})",
        f"- Source ref: `{source_ref}`",
        "- Generated by: `scripts/sync_docs_to_wiki.py`",
        "",
        "## Docs Index",
        "",
    ]
    for group in sorted(grouped):
        lines.append(f"### `{group}/`")
        for page in grouped[group]:
            lines.append(
                f"- [{page.title}]({page.page_name}) "
                f"<br><sub>`{page.source_path.as_posix()}`</sub>"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _build_sidebar(pages: Iterable[DocPage]) -> str:
    grouped: dict[str, list[DocPage]] = {}
    for page in pages:
        group = page.source_path.parent.as_posix()
        grouped.setdefault(group, []).append(page)

    lines = ["# Docs", ""]
    for group in sorted(grouped):
        lines.append(f"## {group.removeprefix('docs/') or 'docs'}")
        for page in grouped[group]:
            lines.append(f"- [{page.title}]({page.page_name})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _build_page(
    *,
    repo_root: Path,
    page: DocPage,
    page_by_doc: dict[Path, str],
    repo_url: str,
) -> str:
    body = (repo_root / page.source_path).read_text(encoding="utf-8")
    rewritten = _rewrite_links(
        text=body,
        repo_root=repo_root,
        source_path=page.source_path,
        page_by_doc=page_by_doc,
        repo_url=repo_url,
    )
    source_url = _repo_source_url(repo_root, repo_url, page.source_path, "")
    header = (
        "<!-- Generated from "
        f"{page.source_path.as_posix()} by scripts/sync_docs_to_wiki.py. "
        "Edit the source doc, not this wiki mirror. -->\n\n"
        f"> Source: [{page.source_path.as_posix()}]({source_url})\n\n"
    )
    return header + rewritten.rstrip() + "\n"


def _write_if_changed(path: Path, text: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def _load_previous_manifest(output_dir: Path) -> set[str]:
    manifest_path = output_dir / MANIFEST_NAME
    if not manifest_path.exists():
        return set()
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    return {str(path) for path in payload.get("generated_files", [])}


def generate_wiki(
    *,
    repo_root: Path,
    output_dir: Path,
    repo_url: str = DEFAULT_REPO_URL,
    source_ref: str | None = None,
) -> dict[str, object]:
    repo_root = repo_root.resolve()
    output_dir = output_dir.resolve()
    source_ref = source_ref or _run_git(repo_root, "rev-parse", "HEAD")
    pages = _discover_docs(repo_root)
    page_by_doc = {page.source_path: page.page_name for page in pages}

    generated: dict[str, str] = {
        "Home.md": _build_home(pages, repo_url, source_ref),
        "_Sidebar.md": _build_sidebar(pages),
    }
    for page in pages:
        generated[page.page_file] = _build_page(
            repo_root=repo_root,
            page=page,
            page_by_doc=page_by_doc,
            repo_url=repo_url,
        )

    previous_files = _load_previous_manifest(output_dir)
    for stale in sorted(previous_files - set(generated) - {MANIFEST_NAME}):
        stale_path = output_dir / stale
        if stale_path.exists() and stale_path.is_file():
            stale_path.unlink()

    changed_files: list[str] = []
    for filename, text in sorted(generated.items()):
        if _write_if_changed(output_dir / filename, text):
            changed_files.append(filename)

    manifest = {
        "profile": "omoikane-docs-wiki-mirror-v1",
        "source_ref": source_ref,
        "source_root": "docs",
        "repo_url": repo_url,
        "doc_count": len(pages),
        "generated_files": sorted([*generated.keys(), MANIFEST_NAME]),
        "source_docs": [
            {
                "source_path": page.source_path.as_posix(),
                "page_file": page.page_file,
                "sha256": page.sha256,
            }
            for page in pages
        ],
    }
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if _write_if_changed(output_dir / MANIFEST_NAME, manifest_text):
        changed_files.append(MANIFEST_NAME)

    return {
        "doc_count": len(pages),
        "generated_file_count": len(generated) + 1,
        "changed_files": sorted(changed_files),
        "output_dir": str(output_dir),
        "source_ref": source_ref,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mirror docs/*.md into GitHub Wiki pages.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Omoikane repository root.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Wiki checkout or staging directory to write.",
    )
    parser.add_argument(
        "--repo-url",
        default=DEFAULT_REPO_URL,
        help="GitHub blob URL prefix for non-wiki source links.",
    )
    parser.add_argument(
        "--source-ref",
        default=None,
        help="Source revision label. Defaults to git rev-parse HEAD.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = generate_wiki(
        repo_root=args.repo_root,
        output_dir=args.output_dir,
        repo_url=args.repo_url,
        source_ref=args.source_ref,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
