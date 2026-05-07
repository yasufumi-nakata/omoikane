---
decision_id: parallel-codex-status-check-poll-budget-2026-05-02
status: accepted
date: 2026-05-02
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-status-check-poll-budget
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

Parallel Codex post-commit publication now binds a bounded status/check polling
budget before GitHub handoff.

# Rationale

The publication receipt already required a successful post-push status/check
suite and a fresh, signed provider snapshot. It still lacked an explicit
attempt and interval budget for how long the handoff was allowed to wait for
queued or in-progress checks. Without that receipt field, an exhausted polling
loop could be collapsed into a generic missing-check failure without showing
the retry budget that was consumed.

# Implementation

`parallel_codex_post_commit_publication_receipt` now includes a
`post-push-status-check-poll-budget-v1` profile with attempt count, max
attempts, interval seconds, terminal status, digest, digest-bound flag, and a
raw payload redaction flag. The publication digest includes the poll digest,
and the runtime blocks GitHub handoff unless polling reaches the `completed`
terminal state within the default 5-attempt / 30-second interval budget.

# Verification

The reference runtime, schema contract tests, continuity eval, IDL, catalog,
docs, and IntegrityGuardian policy all require the poll digest, completed
terminal state, bounded attempt budget, and raw polling payload redaction.

# Revisit Triggers

- Replace reference polling budget receipts with live GitHub check polling
  receipts when provider integration is available.
