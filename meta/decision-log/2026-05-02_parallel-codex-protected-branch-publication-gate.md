---
decision_id: parallel-codex-protected-branch-publication-gate-2026-05-02
status: accepted
date: 2026-05-02
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-protected-branch-provider-policy-receipt
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

Parallel Codex post-commit publication now requires a digest-only GitHub
protected-branch provider policy receipt before GitHub handoff is ready.

# Rationale

The prior publication receipt bound the finalized execution to local commit
head, origin/main remote head, push command evidence, and remote-head
verification. That proved publication mechanics, but did not bind the provider
side policy that should protect `refs/heads/main` after publication.

# Consequences

- `parallel_codex_post_commit_publication_receipt` records provider, branch ref,
  policy ref, policy digest, protected status, required reference verification
  checks, and provider receipt digest.
- `ready_for_github_handoff=true` requires `protected_branch_status=protected`
  and required verification checks bound into the provider policy receipt.
- Unprotected or unknown branch status remains schema-bound with
  `publication_status=blocked`.
- Raw provider branch-protection payloads are not stored; only refs, status,
  required check names, and digests are retained.

# Revisit Triggers

- Replace the reference provider-policy receipt with live GitHub branch
  protection or merge-queue provider receipts when the runtime gains a network
  integration layer.
