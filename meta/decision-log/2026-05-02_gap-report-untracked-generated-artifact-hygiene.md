---
decision_id: gap-report-untracked-generated-artifact-hygiene-2026-05-02
status: accepted
date: 2026-05-02
area: self-construction/gap-report
closes_next_gaps:
  - gap-report-untracked-generated-artifact-hygiene
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
  - agents/guardians/integrity-guardian.policy.md
  - tests/unit/test_gap_scanner.py
  - tests/integration/test_gap_report_schema_contracts.py
  - tests/integration/test_reference_runtime.py
  - tests/integration/test_cli.py
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

GapReport now treats untracked generated artifacts as a first-class hygiene
surface for automation completion.

# Rationale

The previous scanner could reject tracked workspace marker residue, but it did
not distinguish clean source state from leftover untracked generated artifacts
such as repo-local patch artifacts, build output, coverage output, bytecode, or
packaging output. That made all-zero completion silent about generated files
outside the tracked diff.

# Consequences

- `git:untracked-generated-artifacts` is included in the digest-bound scan
  surface.
- `git ls-files --others --exclude-standard` is filtered to generated artifact
  paths only, so ordinary untracked notes are not treated as source gaps.
- Matching paths are reported as `untracked_generated_artifact_hits`, and
  `untracked_generated_artifact_count` participates in the all-zero gate.
- Raw artifact payloads are not read or stored; the receipt binds only the
  generated artifact path manifest digest.

# Revisit Triggers

- Extend artifact classes if a new generated output directory becomes part of
  the automation workflow.
