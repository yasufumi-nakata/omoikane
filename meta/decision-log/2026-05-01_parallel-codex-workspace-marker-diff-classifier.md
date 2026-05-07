---
decision_id: parallel-codex-workspace-marker-diff-classifier-2026-05-01
status: accepted
date: 2026-05-01
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-workspace-marker-diff-classifier
touchpoints:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_worker_result_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_result_ingestion.yaml
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
  - specs/schemas/parallel_codex_worker_result_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_result_ingestion.yaml
---

# Decision

Parallel Codex workspace marker hygiene now has a repo-local diff classifier.

# Rationale

The prior receipt could block marker-only worker results, but it depended on
callers to pre-label marker-only files. Live enactment tests and automation runs
can leave `workspace-enacted` marker comments in the checkout, so the receipt
needs a bounded classifier that can distinguish marker-only diffs from
substantive changed files before main checkout integration.

# Consequences

- Worker result receipts carry `workspace_marker_classifier_profile`,
  digest-only diff summaries, summary count, and
  `workspace_marker_classifier_digest`.
- The classifier stores only file path, diff digest, added / removed line
  counts, marker-added line count, non-marker-added line count, and status.
- Files whose diff only adds `workspace-enacted:` marker comments are reflected
  in `workspace_marker_only_changed_files`; if every changed file is marker-only,
  the result remains schema-bound but blocked.
- Raw workspace marker diff text is not persisted.

# Revisit Triggers

- Replace line-based diff classification with structured patch segment
  manifests if live enactment begins emitting canonical segment-level evidence.
