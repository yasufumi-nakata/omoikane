---
decision_id: parallel-codex-yaoyorozu-dispatch-bridge-2026-04-30
status: accepted
date: 2026-04-30
area: self-construction/parallel-orchestration
closes_next_gaps:
  - yaoyorozu-dispatch-to-parallel-codex-ingestion-bridge
touchpoints:
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_worker_result_receipt.schema
  - evals/continuity/parallel_codex_result_ingestion.yaml
  - docs/02-subsystems/self-construction/README.md
  - docs/07-reference-implementation/README.md
  - agents/guardians/integrity-guardian.yaml
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_worker_result_receipt.schema
  - evals/continuity/parallel_codex_result_ingestion.yaml
  - docs/02-subsystems/self-construction/README.md
  - docs/07-reference-implementation/README.md
  - agents/guardians/integrity-guardian.yaml
---

# Decision

Parallel Codex ingestion now accepts Yaoyorozu worker-dispatch receipts as an
upstream source. A dispatch receipt, its patch-candidate receipt refs/digests,
and derived changed-file list are reduced into the same
`parallel_codex_worker_result_receipt` contract used for direct worker results.

# Rationale

Yaoyorozu dispatch already bound worker plans, execution receipts, and patch
candidates, while Parallel Codex ingestion already guarded main-checkout
integration. Without a bridge, reviewers still had to manually connect
Yaoyorozu's patch-candidate evidence to the final main-checkout ingestion
decision.

# Consequences

- `parallel-orchestration-demo` now includes a
  `source_system=yaoyorozu-worker-dispatch` receipt.
- The bridge derives a patch digest from dispatch plan digest, dispatch receipt
  digest, patch-candidate receipt digests, and changed files.
- `upstream_binding_digest` binds the upstream receipt ref/digest,
  patch-candidate refs/digests, and changed files without storing raw dispatch
  or patch payloads.
- Existing stale-worker blocking remains unchanged.

# Revisit triggers

- External Yaoyorozu dispatch from a remote branch should add PR or branch
  metadata only after remote worker identity evidence is schema-bound.
