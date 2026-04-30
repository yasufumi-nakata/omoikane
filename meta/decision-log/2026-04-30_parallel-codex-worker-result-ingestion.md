---
decision_id: parallel-codex-worker-result-ingestion-2026-04-30
status: accepted
date: 2026-04-30
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-worker-result-ingestion
touchpoints:
  - references/parallel-codex-orchestration.md
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

Parallel Codex worker result ingestion is now a first-class L5
self-construction surface. Worker / subagent / `codex exec` results must be
reduced to `parallel-codex-worker-result-ingestion-v1` receipts before main
checkout integration.

# Rationale

The existing orchestration runbook fixed pull-first and worker-boundary
practice, but the runtime did not yet bind a worker result's patch digest,
changed file list, verification results, and base commit freshness into one
machine-checkable artifact. The receipt makes that handoff reviewable without
storing raw patch payloads, raw transcripts, or raw command output.

# Consequences

- `parallel-orchestration-demo` emits one ready receipt and one stale blocked
  receipt so acceptance and rejection paths remain schema-bound.
- Ready integration requires main checkout head and worker base commit to
  match, changed files to stay inside ownership scope, and unittest / gap-report
  verification commands to pass.
- IntegrityGuardian now has an explicit attestation capability for worker
  result ingestion receipts.
- The continuity eval protects receipt digest binding, verification manifest
  binding, and raw payload redaction.

# Revisit triggers

- The receipt may gain PR metadata when worker results are integrated from a
  remote branch rather than a local subagent handoff.
- The receipt may gain signed worker identity evidence when external worker
  executors are admitted.
