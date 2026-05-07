---
decision_id: parallel-codex-remote-source-metadata-2026-05-01
status: accepted
date: 2026-05-01
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-remote-branch-pr-metadata-binding
touchpoints:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_worker_result_receipt.schema
  - evals/continuity/parallel_codex_result_ingestion.yaml
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/07-reference-implementation/README.md
  - agents/guardians/integrity-guardian.yaml
deciders: [yasufumi, codex-builder]
related_docs:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_worker_result_receipt.schema
  - evals/continuity/parallel_codex_result_ingestion.yaml
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/codex-as-builder.md
---

# Decision

Parallel Codex worker result receipts now accept remote branch / PR worker
results only when branch ref, PR ref, accepted source policy digest, and
integrity Guardian review authority digest are bound into
`remote_metadata_digest`.

# Rationale

Signed worker identity evidence closed the executor identity gap, but remote
worker handoff still lacked a digest-only source metadata surface. Without
branch / PR refs and accepted source policy evidence, a remote result could not
be reviewed as a concrete main-checkout integration candidate.

# Consequences

- `parallel-orchestration-demo` emits a `remote-branch-pr-worker-result`
  receipt that is ready only when remote metadata and worker identity evidence
  both validate.
- Direct and Yaoyorozu receipts mark remote metadata as `not-applicable` and
  cannot carry remote branch / PR refs.
- Raw remote metadata payloads are not stored; refs and digests are sufficient
  for review.

# Revisit triggers

- Add remote source-system revocation checks if stale or revoked remote branches
  become accepted worker sources.
