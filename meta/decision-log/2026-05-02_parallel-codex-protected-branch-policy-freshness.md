---
decision_id: parallel-codex-protected-branch-policy-freshness-2026-05-02
status: accepted
date: 2026-05-02
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-protected-branch-policy-freshness-timestamp
touchpoints:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_post_commit_publication_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_post_commit_publication.yaml
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/07-reference-implementation/README.md
  - agents/guardians/integrity-guardian.yaml
  - agents/guardians/integrity-guardian.policy.md
  - tests/unit/test_parallel_orchestration.py
  - tests/integration/test_parallel_orchestration_schema_contracts.py
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

Parallel Codex post-commit publication now requires protected-branch provider
policy freshness, signed provider timestamp evidence, and timestamp replay guard
evidence before `ready_for_github_handoff` can become true.

# Rationale

The prior publication receipt bound the protected-branch status, required
verification checks, provider policy digest, and provider receipt digest. That
made the handoff depend on protected status but did not show whether the provider
policy observation was current or replay-resistant.

# Consequences

- `parallel_codex_post_commit_publication_receipt` now records a 900 second
  freshness window, checked-at ref, freshness digest, signed provider timestamp
  digest, timestamp signature digest, timestamp nonce ref, and replay-guard
  digest.
- Publication is `published` only when the provider policy is `fresh`, the
  timestamp status is `signed-current`, and the replay status is `unique`.
- Raw provider policy freshness, timestamp, and replay-guard payloads are not
  stored; only refs, bounded statuses, and digests are retained.

# Revisit Triggers

- Replace the reference freshness / timestamp receipts with live GitHub branch
  protection or merge-queue provider receipts when the runtime gains a network
  integration layer.
