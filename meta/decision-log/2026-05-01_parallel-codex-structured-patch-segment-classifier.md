---
decision_id: parallel-codex-structured-patch-segment-classifier-2026-05-01
status: accepted
date: 2026-05-01
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-structured-patch-segment-marker-classifier
touchpoints:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_worker_result_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_result_ingestion.yaml
  - evals/continuity/README.md
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/07-reference-implementation/README.md
  - agents/guardians/integrity-guardian.policy.md
  - tests/unit/test_parallel_orchestration.py
  - tests/integration/test_parallel_orchestration_schema_contracts.py
---

# Decision

Parallel Codex workspace marker classification now accepts structured patch
segment manifests as first-class evidence.

# Rationale

The repo-local diff classifier already prevented marker-only worker output from
entering main-checkout integration, but live enactment can expose bounded patch
segments before or without preserving a raw diff. The classifier therefore needs
to bind segment counts and segment-manifest digests while keeping raw segment
payloads out of persisted receipts.

# Consequences

- Worker result receipts may classify marker-only payloads from either diff-line
  evidence or structured patch-segment manifests.
- Segment evidence records only operation, line counts, marker/substantive
  counts, and digest fields in the classifier summary.
- Marker-only segment manifests remain schema-bound but blocked from
  integration; marker segments plus substantive files remain reviewable.
- Raw diff text and raw segment payloads are not persisted.

# Revisit Triggers

- When Parallel Codex integration receives actual patch artifacts, replace the
  synthetic pre-apply dry-run receipt with a command-bound `git apply --check`
  receipt before commit flow.
