---
date: 2026-05-06
deciders: [yasufumi, codex-builder]
related_docs:
  - README.md
  - docs/07-reference-implementation/README.md
  - meta/decision-log/2026-05-06_human-body-analysis-package.md
status: decided
---

# Decision: List the human body analysis demo

## Context

`human-body-analysis-demo --json` was implemented as part of the Neuro
Integration Workbench human body analysis package, but the main runnable command
inventories still skipped it. That made the quick-start truth source lag the CLI
surface even though runtime, schema, eval, and tests were already present.

## Decision

Add the command to the top-level runnable list and the reference implementation
command inventory. Keep the claim ceiling unchanged: this command emits a
bounded analysis package receipt and does not claim diagnosis, semantic thought
content, consciousness reproduction, identity replacement, or upload readiness.

## Consequences

Readers can discover and smoke-test the dedicated human body analysis package
from the same inventories as the other L6 reference runtime surfaces.

## Revisit Triggers

- the CLI inventory becomes generated from `argparse`
- the human body analysis package is renamed or split into source-specific demos
- a runnable command starts mutating the current checkout by default
