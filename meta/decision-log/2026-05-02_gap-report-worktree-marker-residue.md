---
decision_id: gap-report-worktree-marker-residue-2026-05-02
status: accepted
date: 2026-05-02
area: self-construction/gap-report
closes_next_gaps:
  - gap-report-worktree-marker-residue
touchpoints:
  - src/omoikane/self_construction/gaps.py
  - specs/interfaces/selfctor.gap_report.v0.idl
  - specs/schemas/gap_report.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/gap_report_scan_receipt.yaml
  - evals/continuity/README.md
  - docs/07-reference-implementation/README.md
  - agents/guardians/integrity-guardian.yaml
  - tests/unit/test_gap_scanner.py
  - tests/integration/test_gap_report_schema_contracts.py
  - tests/integration/test_reference_runtime.py
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/self_construction/gaps.py
  - specs/interfaces/selfctor.gap_report.v0.idl
  - specs/schemas/gap_report.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/gap_report_scan_receipt.yaml
  - evals/continuity/README.md
  - docs/07-reference-implementation/README.md
---

# Decision

GapReport now treats tracked worktree workspace marker residue as a first-class
gap surface.

# Rationale

Parallel Codex worker-result receipts already block marker-only worker output,
but the repository-level scanner could still return all-zero while the checkout
itself had dirty tracked files containing only workspace marker residue. That
made automation completion ambiguous: the worker ingestion contract rejected the
payload shape, while the repo scanner did not surface the same condition.

# Consequences

- `git:tracked-worktree-diff` is included in the digest-bound scan surface.
- Added dirty diff lines beginning with the workspace marker prefix are reported
  as `worktree_workspace_marker_hits`.
- The scan receipt count set includes `worktree_workspace_marker_count`, so
  all-zero cannot pass while tracked marker residue remains.
- Raw git diff payloads are not stored; the report keeps path, marker counts,
  dirty status, and digest-bound scan surface evidence only.

# Revisit Triggers

- Extend the same worktree hygiene scan to untracked generated artifacts if they
  become part of the automation completion contract.
