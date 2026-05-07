---
decision_id: parallel-codex-remote-source-ancestry-binding-2026-05-01
status: accepted
date: 2026-05-01
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-remote-branch-pr-main-head-ancestry-binding
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

Remote branch / PR worker result receipts now carry a main-head ancestry gate.

# Rationale

Remote content identity binds the mutable branch or PR ref to head, tree, and
diff digests, but it does not prove the reviewed remote head is based on the
same main checkout base commit that the worker used. A remote result could be
content-bound and still represent an unrelated history, making integration
unsafe even when revocation and timestamp evidence are current.

# Consequences

- Remote receipts include `remote_source_ancestry_profile`,
  `remote_source_base_commit`, `remote_source_merge_base_commit`,
  `remote_source_ancestry_status`, `remote_source_ancestry_digest`, and
  `remote_source_ancestry_bound`.
- The ancestry digest is included in `remote_metadata_digest` together with
  remote source content identity.
- Remote ancestry whose status is not `ancestor-bound`, or whose base /
  merge-base commits do not match `worker_base_commit`, remains schema-bound
  but blocked from main checkout integration.
- Raw remote ancestry payloads are not stored.

# Revisit Triggers

- Replace digest-only synthetic ancestry evidence with live GitHub compare API
  evidence if remote branch / PR ingestion standardizes a signed source
  endpoint.
