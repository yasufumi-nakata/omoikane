---
decision_id: parallel-codex-integration-execution-plan-2026-05-01
status: accepted
date: 2026-05-01
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-integration-ready-batch-apply-plan-binding
touchpoints:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_integration_execution_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_integration_execution.yaml
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
---

# Decision

Parallel Codex integration-ready batches now produce an execution receipt before
main checkout commit.

# Rationale

Batch arbitration fixed deterministic receipt ordering, quarantined blocked
receipts, and changed-file conflict detection. It still left the final step from
`integration-ready` batch to main-checkout apply / post-apply verification as an
implicit operator action.

# Consequences

- `parallel_codex_integration_execution_receipt` binds the source batch receipt,
  current checkout head, ordered apply steps, apply plan digest, and post-apply
  verification manifest.
- Source batches that are blocked, conflict-bearing, or digest-unbound cannot
  become `ready-to-apply`.
- Current checkout head drift after batch planning keeps the execution receipt
  blocked.
- Raw batch, apply plan, worker receipt, patch, stdout, and stderr payloads are
  not persisted.

# Revisit Triggers

- Replace digest-only apply steps with provider-native merge queue evidence if
  Parallel Codex adopts a standardized remote integration backend.
