---
date: 2026-05-03
deciders: [yasufumi, codex-builder]
related_docs:
  - README.md
  - scripts/sync_docs_to_wiki.py
  - tests/unit/test_wiki_sync.py
status: decided
---

# Decision: docs wiki mirror

## Context

The design corpus under `docs/` is the canonical human-readable surface for
OmoikaneOS, but browsing it only through repository paths makes the design
harder to scan as a connected knowledge base.

## Options considered

- A: Move `docs/` content out of the repository into GitHub Wiki.
- B: Keep `docs/` as the source of truth and mirror it into GitHub Wiki.
- C: Keep only a manually edited wiki index that links back to repository docs.

## Decision

Adopt option B.
`docs/` remains canonical for Builder handoff, DesignReader inputs, and
repo-local review, while `scripts/sync_docs_to_wiki.py` generates flat GitHub
Wiki pages, `Home.md`, `_Sidebar.md`, and a manifest from the current docs tree.

## Consequences

The wiki can serve as the browse-first view without weakening the repository
contract that specs, evals, tests, and runtime remain synchronized with docs.
Future docs updates should regenerate the wiki mirror rather than editing mirror
pages by hand.

## Revisit triggers

- GitHub Wiki gains a first-class directory-aware docs import path.
- DesignReader starts treating wiki pages as canonical source inputs.
- Wiki pages need hand-authored pages that are not derived from `docs/`.
