---
decision_id: parallel-codex-integration-pre-apply-dry-run-2026-05-01
status: accepted
date: 2026-05-01
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-integration-pre-apply-dry-run-binding
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

Parallel Codex integration execution receipts now bind a pre-apply dry-run
manifest before any main-checkout mutation.

# Rationale

The prior execution receipt bound the source batch digest, current checkout
head, ordered apply steps, and post-apply verification. That still allowed a
digest-bound apply plan to appear `ready-to-apply` without proving that each
patch can apply cleanly to the current main checkout before mutation.

# Consequences

- `parallel_codex_integration_execution_receipt` includes
  `pre_apply_dry_run_profile`, per-step dry-run results,
  `pre_apply_dry_run_manifest_digest`, and `pre_apply_dry_run_passed`.
- Dry-run failures keep `execution_decision=blocked`, even when the source batch
  is integration-ready and post-apply verification results are otherwise
  present.
- Dry-run stdout / stderr is reduced to digests; raw dry-run payloads are not
  persisted.

# Revisit Triggers

- Replace synthetic reference dry-run receipts with actual `git apply --check`
  command receipts when worker patches are materialized as repo-local patch
  files or provider-native merge queue artifacts.
