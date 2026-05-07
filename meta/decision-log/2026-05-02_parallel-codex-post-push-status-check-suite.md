---
decision_id: parallel-codex-post-push-status-check-suite-2026-05-02
status: accepted
date: 2026-05-02
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-post-push-status-check-suite
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
  - tests/integration/test_cli.py
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

Parallel Codex post-commit publication now requires a post-push provider
status/check suite on the published commit before `ready_for_github_handoff`
can become true.

# Rationale

The protected branch receipt proved that `refs/heads/main` required the local
reference verification commands, but it did not separately prove that the
provider observed those checks as completed and successful on the just-pushed
commit. The handoff now distinguishes required-check policy from concrete
post-push check results.

# Consequences

- `parallel_codex_post_commit_publication_receipt` carries a digest-only
  `post-push-provider-status-check-suite-v1` with one check-run digest per
  required verification command.
- Publication remains blocked unless the status/check suite commit head matches
  the post-push remote head, mirrors the protected branch required checks, and
  every required check is `completed` / `success`.
- Raw provider status/check payloads are not stored; only check refs, statuses,
  conclusions, commit heads, check-run digests, and the suite digest are retained.

# Revisit Triggers

- Replace the reference status/check suite receipt with live GitHub check-suite
  or merge-queue provider receipts when the runtime gains a network integration
  layer.
