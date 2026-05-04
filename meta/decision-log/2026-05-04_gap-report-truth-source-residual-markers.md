---
date: 2026-05-04
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/07-reference-implementation/README.md
  - specs/interfaces/selfctor.gap_report.v0.idl
  - specs/schemas/gap_report.schema
  - src/omoikane/self_construction/gaps.py
status: decided
---

# Decision: Truth-source residual markers gate all-zero reports

## Context

`gap-report` already rejected English `future work` bullets in current truth
sources, but Japanese backlog wording such as implementation-backlog bullets
could remain invisible to the all-zero gate. That made automation-hygiene
dependent on manual reading even when the repo contained a deterministic
scanner contract.

## Options considered

- A: Leave Japanese residual wording as a manual review concern.
- B: Extend the truth-source residual scanner to Japanese backlog markers while
  ignoring explicitly closed backlog statements.
- C: Rename the report field away from `future_work_hits`.

## Decision

Adopt B. The existing `future_work_hits` surface now covers English future-work
markers and Japanese truth-source residual markers, but suppresses closed
inventory/backlog statements such as "resolved" or "none" notes. The public
schema and IDL describe the broader residual-marker contract without adding a
new report field.

## Consequences

Hourly automation can fail the all-zero gate when truth sources retain
machine-checkable backlog wording in Japanese. Current docs now describe ongoing
monitoring without leaving a residual-marker bullet, so a clean repo still
reports all zero.

## Revisit triggers

- A new language or house-style marker becomes common in truth sources.
- The field name `future_work_hits` becomes too misleading for API consumers.
- Closed-backlog wording starts suppressing a real actionable gap.
