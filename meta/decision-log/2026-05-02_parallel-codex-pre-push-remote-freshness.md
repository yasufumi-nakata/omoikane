---
decision_id: parallel-codex-pre-push-remote-freshness-2026-05-02
status: accepted
date: 2026-05-02
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-post-commit-pre-push-remote-freshness
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
---

# Decision

Parallel Codex post-commit publication now binds a pre-push origin/main
freshness receipt before treating a push result as GitHub handoff evidence.

# Rationale

The previous publication receipt proved that the final remote head matched the
local commit after push, but it did not separately prove that origin/main still
matched the source execution checkout head immediately before the push. A remote
advance between execution planning and publication therefore lacked a dedicated
schema-bound fail-closed reason.

# Consequences

- `parallel_codex_post_commit_publication_receipt` carries the source execution
  current checkout head, pre-push remote head, command-bound pre-push
  `git ls-remote origin refs/heads/main` receipt, and observed head/ref digest.
- Publication remains blocked unless the pre-push remote head matches the source
  execution current checkout head.
- Pre-push stdout/stderr remains digest-only; raw remote verification payloads
  are not stored.
- The reference demo, eval, docs, Guardian policy, IDL, schema, and tests now
  expose this gate alongside the existing post-push remote-head verification.

# Revisit Triggers

- Replace command-bound pre-push freshness evidence with provider-native branch
  lease or merge-queue receipts when a live provider integration is added.
