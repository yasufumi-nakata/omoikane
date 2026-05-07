---
decision_id: parallel-codex-remote-source-content-identity-2026-05-01
status: accepted
date: 2026-05-01
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-remote-branch-pr-content-identity-binding
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

Remote branch / PR worker result receipts now carry a source content identity gate.

# Rationale

Remote branch and PR refs are mutable. The existing receipt bound the source
system, review authority, revocation freshness, signed provider timestamp, and
timestamp replay guard, but it did not make the exact remote head / tree / diff
identity first-class. A current-looking remote ref could therefore be reviewed
and then shift content before main checkout integration.

# Consequences

- Remote receipts include `remote_source_content_profile`,
  `remote_source_content_ref`, `remote_source_content_status`,
  `remote_source_head_commit`, `remote_source_tree_digest`,
  `remote_source_diff_digest`, `remote_source_content_digest`, and
  `remote_source_content_bound`.
- The content digest is included in `remote_metadata_digest`.
- Remote content identity whose status is not `bound` remains schema-bound but
  blocked from main checkout integration.
- Raw remote source content payloads are not stored.

# Revisit Triggers

- Replace digest-only synthetic head / tree refs with live GitHub compare API
  evidence if the automation standardizes remote branch or PR ingestion through
  a stable signed source endpoint.
