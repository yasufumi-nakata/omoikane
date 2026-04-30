---
decision_id: parallel-codex-worker-identity-evidence-2026-05-01
status: accepted
date: 2026-05-01
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-signed-worker-identity-evidence
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
---

# Decision

Parallel Codex worker result receipts now require signed worker identity
evidence. The receipt binds `worker_identity_ref`, `worker_identity_digest`,
and an integrity Guardian signature digest to the same patch digest and
main-checkout base/head evidence used for integration.

# Rationale

The prior result-ingestion receipt could prove changed files, patch digest,
verification evidence, and base commit freshness, but it did not bind the worker
identity as a digest-only artifact. That left the remote/external worker
revisit trigger under-specified even though the current runtime still accepts
only direct worker and Yaoyorozu dispatch sources.

# Consequences

- `parallel-orchestration-demo` now emits worker identity evidence on ready,
  stale-blocked, and Yaoyorozu bridge receipts.
- Main-checkout ingestion remains fail-closed if the identity signature digest
  no longer matches the worker identity digest, patch digest, or base/head
  commit evidence.
- Raw worker identity payloads are not stored; only refs and digests are kept.
- External worker execution is not broadened by this change. Remote branch / PR
  metadata remains a separate future extension.

# Revisit triggers

- Add branch / PR metadata only after remote worker identity, review authority,
  and accepted source-system policy are schema-bound.
