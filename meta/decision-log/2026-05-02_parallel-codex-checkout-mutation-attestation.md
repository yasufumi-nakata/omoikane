---
decision_id: parallel-codex-checkout-mutation-attestation-2026-05-02
status: accepted
date: 2026-05-02
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-live-checkout-mutation-attestation
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

Parallel Codex integration execution now carries digest-only checkout mutation
attestation before commit.

# Rationale

The prior execution receipt proved that an integration-ready batch had an
ordered apply plan, repo-local patch artifacts, command-bound dry-run receipts,
and post-apply verification bound to that context. It still stopped short of
recording which main checkout mutation or commit-like event those proofs were
about. A passing verification manifest could therefore be replayed without a
separate digest binding to the observed pre/post checkout heads.

# Consequences

- Execution receipts carry `main-checkout-mutation-attestation-v1`.
- The mutation event digest binds source batch digest, current checkout head,
  pre-apply head, post-apply head, apply plan digest, patch artifact manifest
  digest, pre-apply dry-run manifest digest, post-apply verification context
  digest, and changed-file owner manifest digest.
- `checkout_mutation_status` must be `attested`, the post-apply head must
  advance beyond the pre-apply head, and raw mutation payloads remain redacted.
- Missing, mismatched, or context-unbound checkout mutation attestation keeps
  the execution receipt blocked before commit.

# Revisit Triggers

- Replace reference-runtime mutation attestations with provider-native merge
  queue receipts when those receipts are available to the runtime.
