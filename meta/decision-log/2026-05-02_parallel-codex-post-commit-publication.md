---
decision_id: parallel-codex-post-commit-publication-2026-05-02
status: accepted
date: 2026-05-02
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-post-commit-origin-main-publication
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
  - docs/07-reference-implementation/README.md
  - agents/guardians/integrity-guardian.yaml
  - agents/guardians/integrity-guardian.policy.md
  - tests/unit/test_parallel_orchestration.py
  - tests/integration/test_parallel_orchestration_schema_contracts.py
  - tests/integration/test_reference_runtime.py
---

# Decision

Parallel Codex integration now emits a post-commit publication receipt before
the GitHub handoff is considered complete.

# Rationale

The execution receipt already proves batch readiness, dry-run evidence,
post-apply verification, checkout mutation, patch artifact cleanup, and commit
finalization. It did not, however, bind the final local commit to an actual
`origin/main` publication check. That made the automation handoff rely on an
operator-readable push status instead of a schema-bound receipt.

# Consequences

- `parallel_codex_post_commit_publication_receipt` records the source execution
  receipt digest, commit finalization readiness, local commit head, origin/main
  remote head, push command digest, remote verification command digest, and
  publication digest.
- Publication is `published` only when the source execution is ready, commit
  finalization is ready, the local head matches the execution head, the push
  command passes, and `git ls-remote origin refs/heads/main` returns the same
  commit.
- Push and remote verification output remain digest-only; raw execution,
  publication, push, and remote verification payloads are not stored.
- A blocked source execution or remote head mismatch remains schema-bound with
  `ready_for_github_handoff=false`.

# Revisit Triggers

- Replace command-bound push evidence with protected-branch provider receipts
  or signed merge-queue events when a live provider integration is added.
