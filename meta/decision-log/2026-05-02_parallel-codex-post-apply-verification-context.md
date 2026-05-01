---
decision_id: parallel-codex-post-apply-verification-context-2026-05-02
status: accepted
date: 2026-05-02
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-post-apply-verification-context-binding
touchpoints:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_integration_execution_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_integration_execution.yaml
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

Parallel Codex integration execution now binds post-apply verification to the
exact apply context it claims to verify.

# Rationale

The execution receipt already required post-apply unittest and gap-report
commands to pass. The manifest for those verification commands was digest-bound,
but it was not itself bound to the ordered apply plan, repo-local patch artifact
manifest, or command-bound pre-apply dry-run manifest. A receipt could therefore
model passing verification without proving which apply plan those checks
followed.

# Consequences

- Execution receipts carry
  `post_apply_verification_context_profile=post-apply-verification-apply-context-binding-v1`.
- The context digest binds the source batch receipt digest, current checkout
  head, apply plan digest, patch artifact manifest digest, pre-apply dry-run
  manifest digest, and post-apply verification manifest digest.
- Validation exposes explicit booleans for apply plan, patch artifact manifest,
  pre-apply dry-run manifest, context digest, and overall context binding.
- Any execution whose post-apply verification context is unbound remains
  `blocked` before main-checkout commit.
- Raw verification stdout, stderr, patch payloads, batch payloads, and worker
  receipt payloads remain redacted.

# Revisit Triggers

- Add provider-native merge queue receipts or live repository commit attestations
  when Parallel Codex can verify actual checkout mutation events directly.
