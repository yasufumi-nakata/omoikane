---
decision_id: parallel-codex-commit-finalization-gate-2026-05-02
status: accepted
date: 2026-05-02
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-commit-finalization-gate
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
deciders: [yasufumi, codex-builder]
related_docs:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_integration_execution_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_integration_execution.yaml
---

# Decision

Parallel Codex integration execution now carries a commit finalization gate
before a main-checkout commit is accepted.

# Rationale

The previous execution receipt proved source batch readiness, command-bound
pre-apply dry-run, post-apply verification context, and checkout mutation
attestation. Those facts were individually bound, but there was no final
receipt-level gate that stated the exact combination was commit-ready. That left
the commit boundary implicit.

# Consequences

- Execution receipts carry `main-checkout-commit-finalization-gate-v1`.
- The gate digest binds source batch digest, current checkout head, apply plan
  digest, patch artifact manifest digest, pre-apply dry-run manifest digest,
  post-apply verification context digest, checkout mutation event digest,
  post-apply head, changed-file owner manifest digest, and passing verification
  state.
- The gate is `ready` only when the batch is integration-ready, the checkout head
  matches, dry-run and verification pass, patch artifacts are bound, and
  checkout mutation is attested.
- Raw commit finalization payloads remain redacted.

# Revisit Triggers

- Replace reference-runtime finalization gates with provider-native merge queue
  or protected-branch commit receipts when those become available.
