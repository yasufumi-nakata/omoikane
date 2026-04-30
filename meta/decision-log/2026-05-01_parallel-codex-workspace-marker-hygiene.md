---
decision_id: parallel-codex-workspace-marker-hygiene-2026-05-01
status: accepted
date: 2026-05-01
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-workspace-enacted-marker-only-result-hygiene
touchpoints:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_worker_result_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_result_ingestion.yaml
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/07-reference-implementation/README.md
  - agents/guardians/integrity-guardian.yaml
  - agents/guardians/integrity-guardian.policy.md
---

# Decision

Parallel Codex worker result receipts now carry a workspace marker hygiene gate.

# Rationale

The repo can contain `workspace-enacted` marker comments from live enactment
tests or prior automation runs. Without an explicit receipt field, a worker
result could present marker-only file changes as if they were substantive
implementation output.

# Consequences

- Receipts include `workspace_marker_hygiene_profile`,
  `workspace_marker_only_changed_files`,
  `workspace_marker_only_change_count`,
  `workspace_marker_hygiene_status`, and
  `workspace_marker_hygiene_digest`.
- Marker-only results are schema-bound but blocked from main checkout
  integration.
- Results that include a marker comment plus substantive changed files remain
  accept-ready when every other gate passes.
- Raw marker payload text is not stored.

# Revisit Triggers

- Replace caller-supplied marker-only file classification with a repo-local diff
  classifier if the live enactment layer starts emitting structured patch
  segment manifests.
