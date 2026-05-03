from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def _load_wiki_sync_module():
    repo_root = Path(__file__).resolve().parents[2]
    module_path = repo_root / "scripts" / "sync_docs_to_wiki.py"
    spec = importlib.util.spec_from_file_location("sync_docs_to_wiki", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load sync_docs_to_wiki.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class WikiSyncTests(unittest.TestCase):
    def test_generate_wiki_flattens_docs_and_rewrites_doc_links(self) -> None:
        module = _load_wiki_sync_module()
        with tempfile.TemporaryDirectory(prefix="omoikane-wiki-sync-test-") as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            output_dir = Path(temp_dir) / "wiki"
            (repo_root / "docs" / "00-philosophy").mkdir(parents=True)
            (repo_root / "docs" / "01-architecture").mkdir(parents=True)
            (repo_root / "agents").mkdir(parents=True)
            (repo_root / "meta").mkdir(parents=True)
            (repo_root / "docs" / "00-philosophy" / "manifesto.md").write_text(
                "# Manifesto\n\nSee [Overview](../01-architecture/overview.md#layers).\n",
                encoding="utf-8",
            )
            (repo_root / "docs" / "01-architecture" / "overview.md").write_text(
                "# Overview\n\nSee [Glossary](../../meta/glossary.md) and [Agents](../../agents/).\n",
                encoding="utf-8",
            )
            (repo_root / "agents" / "agent.yaml").write_text("id: test\n", encoding="utf-8")
            (repo_root / "meta" / "glossary.md").write_text("# Glossary\n", encoding="utf-8")

            result = module.generate_wiki(
                repo_root=repo_root,
                output_dir=output_dir,
                repo_url="https://example.invalid/repo/blob/main",
                source_ref="test-ref",
            )

            self.assertEqual(2, result["doc_count"])
            self.assertTrue((output_dir / "Home.md").exists())
            self.assertTrue((output_dir / "_Sidebar.md").exists())
            manifesto_page = output_dir / "docs-00-philosophy-manifesto.md"
            overview_page = output_dir / "docs-01-architecture-overview.md"
            self.assertTrue(manifesto_page.exists())
            self.assertTrue(overview_page.exists())
            self.assertIn(
                "[Overview](docs-01-architecture-overview#layers)",
                manifesto_page.read_text(encoding="utf-8"),
            )
            overview_text = overview_page.read_text(encoding="utf-8")
            self.assertIn(
                "[Glossary](https://example.invalid/repo/blob/main/meta/glossary.md)",
                overview_text,
            )
            self.assertIn(
                "[Agents](https://example.invalid/repo/tree/main/agents)",
                overview_text,
            )

    def test_generate_wiki_removes_only_manifested_stale_pages(self) -> None:
        module = _load_wiki_sync_module()
        with tempfile.TemporaryDirectory(prefix="omoikane-wiki-sync-test-") as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            output_dir = Path(temp_dir) / "wiki"
            (repo_root / "docs").mkdir(parents=True)
            first_doc = repo_root / "docs" / "first.md"
            first_doc.write_text("# First\n", encoding="utf-8")

            module.generate_wiki(
                repo_root=repo_root,
                output_dir=output_dir,
                repo_url="https://example.invalid/repo/blob/main",
                source_ref="first-ref",
            )
            unmanaged = output_dir / "manual-page.md"
            unmanaged.write_text("# Manual\n", encoding="utf-8")
            first_doc.unlink()
            second_doc = repo_root / "docs" / "second.md"
            second_doc.write_text("# Second\n", encoding="utf-8")

            module.generate_wiki(
                repo_root=repo_root,
                output_dir=output_dir,
                repo_url="https://example.invalid/repo/blob/main",
                source_ref="second-ref",
            )

            self.assertFalse((output_dir / "docs-first.md").exists())
            self.assertTrue((output_dir / "docs-second.md").exists())
            self.assertTrue(unmanaged.exists())


if __name__ == "__main__":
    unittest.main()
