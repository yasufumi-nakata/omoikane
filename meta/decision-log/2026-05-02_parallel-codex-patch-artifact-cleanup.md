---
decision_id: parallel-codex-patch-artifact-cleanup-2026-05-02
status: accepted
date: 2026-05-02
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-patch-artifact-cleanup-gate
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
---

# Decision

Parallel Codex integration execution now requires a digest-bound patch artifact
cleanup receipt before commit finalization can become ready.

# Rationale

The execution receipt already bound ordered `artifacts/parallel-codex/*.patch`
paths and command-bound `git apply --check` dry-run receipts. Without an
explicit cleanup receipt, the main checkout commit gate could prove that patch
artifacts were rehearsed, but not that repo-local patch artifacts were removed
after the checkout mutation.

# Consequences

- Execution receipts carry `repo-local-patch-artifact-cleanup-v1`.
- Cleanup binds the ordered patch artifact paths, patch artifact manifest
  digest, pre-apply dry-run manifest digest, checkout mutation event digest, and
  post-apply head.
- `commit_finalization_digest` now includes the cleanup digest and verified
  state.
- Cleanup status other than `removed` leaves execution blocked.
- Raw cleanup payloads are not stored.

# Revisit Triggers

- Add actual patch-file materialization and subprocess-backed `git apply
  --check` receipts when provider-native patch payloads are introduced.
