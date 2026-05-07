---
decision_id: parallel-codex-integration-batch-conflict-arbitration-2026-05-01
status: accepted
date: 2026-05-01
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-integration-batch-conflict-arbitration
touchpoints:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_integration_batch_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_integration_batch.yaml
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
  - specs/schemas/parallel_codex_integration_batch_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_integration_batch.yaml
---

# Decision

Parallel Codex accept-ready worker receipts now pass through a batch conflict
arbitration receipt before main checkout integration.

# Rationale

Single worker-result receipts already bind worker identity, verification,
changed-file manifests, and remote source evidence. They did not yet define the
safe reduction step for multiple accept-ready receipts that arrive from
parallel workers in the same automation run. Without a batch receipt, the
integration order and changed-file overlap check could drift into ad hoc local
judgment.

# Consequences

- `parallel_codex_integration_batch_receipt` records the input receipt-set
  digest, deterministic digest/ref integration order, quarantined blocked
  receipt refs/digests, changed-file owner manifest digest, conflict digest,
  verification manifest digest, and batch decision.
- Only validated accept-ready receipts targeting the current main checkout head
  enter the ordered integration set.
- Blocked, stale, failed, marker-only, invalid, or stale-head receipts are
  quarantined from the integration order.
- Any changed-file overlap between accepted receipts keeps the batch
  schema-bound but blocked until the overlap is resolved.
- Raw worker receipt payloads, raw conflict payloads, raw stdout, and raw
  stderr remain out of the persisted artifact.

# Revisit Triggers

- Replace digest-only synthetic conflict evidence with live GitHub merge queue
  or provider compare evidence if Parallel Codex adopts a standardized remote
  integration backend.
