---
date: 2026-05-03
deciders: [yasufumi, codex-builder]
related_docs:
  - README.md
  - docs/07-reference-implementation/README.md
status: decided
---

# Decision: README runnable output guide

## Context

The top-level README listed runnable commands, but it did not explain what a reader should expect after running them.
That made the commands look closer to a product launcher than to a reference-runtime verification surface.

## Options considered

- A: Leave the command list as-is and rely on each JSON payload to explain itself.
- B: Add a separate long tutorial under `docs/07-reference-implementation/`.
- C: Add a compact table directly under the README command list.

## Decision

Adopt option C.
The README now explains that the commands emit deterministic JSON for checking docs/specs/evals boundaries, and it separates what each command group demonstrates from what it intentionally does not provide.

## Consequences

Readers can run the listed commands and immediately understand whether they are seeing tests, receipts, policy gates, validation summaries, or gap counts.
The claim ceiling stays explicit: the runnable surfaces do not prove consciousness, identity continuity, medical validity, legal approval, or production operation.

## Revisit triggers

- the command list is reorganized into a generated CLI inventory
- the reference runtime gains an interactive UI or long-running service mode
- a runnable command begins to mutate the current checkout by default
