---
decision_id: parallel-codex-status-check-freshness-2026-05-02
status: accepted
date: 2026-05-02
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-status-check-suite-freshness
touchpoints:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_post_commit_publication_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_post_commit_publication.yaml
  - evals/continuity/README.md
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/07-reference-implementation/README.md
  - agents/guardians/integrity-guardian.yaml
  - agents/guardians/integrity-guardian.policy.md
  - tests/unit/test_parallel_orchestration.py
  - tests/integration/test_parallel_orchestration_schema_contracts.py
  - tests/integration/test_reference_runtime.py
  - tests/integration/test_cli.py
deciders: [yasufumi, codex-builder]
related_docs:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_post_commit_publication_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_post_commit_publication.yaml
---

# Decision

Parallel Codex post-commit publication now binds the post-push status/check
suite to a freshness receipt before GitHub handoff.

# Rationale

The prior publication receipt could prove that required checks were reported
for the published commit, but it did not separately bind when the provider
status/check suite snapshot was checked. A stale provider snapshot could
therefore remain internally digest-bound while still being too old for a
handoff decision.

# Implementation

`parallel_codex_post_commit_publication_receipt` now includes a
`post-push-provider-status-check-suite-freshness-v1` profile with a checked-at
ref, freshness window, freshness status, digest, digest-bound flag, and raw
payload redaction flag. The publication digest includes those fields, and the
runtime blocks GitHub handoff unless the suite freshness status is `fresh`
within the 900 second provider evidence window.

# Verification

The reference runtime, schema contract tests, CLI integration test, continuity
eval, IDL, catalog, docs, and IntegrityGuardian policy all require the new
freshness binding and raw status/check freshness payload redaction.

# Revisit Triggers

- Replace reference freshness receipts with live GitHub check-suite provider
  timestamps when network integration is available.
