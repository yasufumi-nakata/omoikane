---
decision_id: parallel-codex-quarantine-manifest-digest-2026-05-01
status: accepted
date: 2026-05-01
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-blocked-receipt-quarantine-manifest-digest
touchpoints:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_integration_batch_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_integration_batch.yaml
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
  - specs/schemas/parallel_codex_integration_batch_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_integration_batch.yaml
---

# Decision

Parallel Codex integration batches now bind quarantined blocked worker receipts
to `blocked-receipt-quarantine-manifest-v1`.

# Rationale

The batch receipt already kept blocked, stale, marker-only, and invalid worker
receipts out of the ordered integration set, but the quarantine set itself was
only represented as parallel ref and digest arrays. A reviewer could verify the
ordered integration digest and changed-file conflict digest while the blocked
receipt quarantine manifest had no first-class digest.

# Consequences

- `parallel_codex_integration_batch_receipt` carries
  `quarantine_profile` and `quarantined_receipt_set_digest`.
- The digest is computed from sorted blocked receipt ref/digest pairs and is
  validated alongside the receipt-set, ordered integration, owner manifest,
  conflict, verification, and final receipt digests.
- The reference demo and eval now assert both ready and conflict batches bind
  the quarantined receipt set.
- Raw blocked worker receipt payloads remain redacted; only refs, digests, and
  the quarantine manifest digest are retained.

# Revisit Triggers

- Add dependency / topological ordering only when disjoint changed-file batches
  need semantic ordering beyond deterministic receipt digest order.
