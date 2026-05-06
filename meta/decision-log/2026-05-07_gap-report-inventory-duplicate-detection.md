---
date: 2026-05-07
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/07-reference-implementation/README.md
  - specs/interfaces/selfctor.gap_report.v0.idl
  - specs/schemas/gap_report.schema
  - specs/schemas/README.md
status: decided
---

# Decision: Detect duplicate inventory entries

## Context

`gap-report --json` was all-zero while `specs/schemas/README.md` listed
`yaoyorozu_cross_workspace_dispatch_manifest.schema` twice. The existing
inventory scanner compared actual files against a set of listed entries, so a
duplicate top-level inventory item could pass all-zero as long as every file was
mentioned at least once.

## Decision

Keep inventory drift as the existing gate, but make it include duplicate
top-level inventory entries. Nested bullets remain explanatory references and do
not count as inventory entries.

## Consequences

Automation hygiene now catches duplicate spec / eval inventory bullets before
all-zero completion. The current schema README keeps one
`yaoyorozu_cross_workspace_dispatch_manifest.schema` entry and preserves its
raw-payload-free dispatch manifest explanation.

## Revisit Triggers

- inventory README files become generated from the filesystem
- nested bullets are intentionally promoted to inventory items
- a non-spec inventory needs duplicate detection under a separate gate
