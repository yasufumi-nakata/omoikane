---
decision_id: gap-report-platform-cache-artifact-hygiene-2026-05-02
status: accepted
date: 2026-05-02
area: self-construction/gap-report
closes_next_gaps:
  - gap-report-platform-cache-artifact-hygiene
touchpoints:
  - src/omoikane/self_construction/gaps.py
  - specs/interfaces/selfctor.gap_report.v0.idl
  - specs/schemas/gap_report.schema
  - specs/catalog.yaml
  - evals/continuity/gap_report_scan_receipt.yaml
  - evals/continuity/README.md
  - docs/07-reference-implementation/README.md
  - agents/guardians/integrity-guardian.yaml
  - agents/guardians/integrity-guardian.policy.md
  - tests/unit/test_gap_scanner.py
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/self_construction/gaps.py
  - specs/interfaces/selfctor.gap_report.v0.idl
  - specs/schemas/gap_report.schema
  - specs/catalog.yaml
  - evals/continuity/gap_report_scan_receipt.yaml
  - evals/continuity/README.md
  - docs/07-reference-implementation/README.md
  - agents/guardians/integrity-guardian.yaml
---

# Decision: gap-report は platform/cache 生成物も監査する

## Context

GapReport already blocks generated outputs such as `artifacts/`, `build/`,
`dist/`, `htmlcov/`, coverage files, bytecode, and packaging metadata when they
are visible through tracked or untracked Git path manifests.

Local automation runs can also leave platform metadata and test or analysis
caches that do not belong in the source completion contract. Examples include
`.DS_Store`, `Thumbs.db`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`,
`.tox/`, and `.nox/`.

## Decision

GapReport now classifies platform metadata as `platform-metadata-output` and
test or analysis caches as `test-or-analysis-cache`.

The scanner still stores only digest-bound path manifests for
`git:tracked-generated-artifacts` and `git:untracked-generated-artifacts`; it
does not read or persist raw artifact payloads.

## Consequences

- Tracked cache and platform metadata paths stop all-zero completion through
  `tracked_generated_artifact_hits`.
- Visible untracked cache and platform metadata paths stop all-zero completion
  through `untracked_generated_artifact_hits`.
- The current clean checkout remains all-zero because ignored local artifacts
  stay outside `git ls-files --others --exclude-standard`.
