---
decision_id: parallel-codex-remote-source-revocation-check-2026-05-01
status: accepted
date: 2026-05-01
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-remote-source-system-revocation-check
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

Remote branch / PR Parallel Codex worker results now require a digest-bound
remote source-system revocation check before they can be accepted into the main
checkout.

# Rationale

Remote source metadata already bound branch refs, PR refs, accepted source
policy digests, and IntegrityGuardian review authority. That still left a
hidden handoff gap: a branch or PR could become revoked or stale after metadata
capture but before main-checkout integration.

# Consequences

- Remote receipts carry `remote_source_revocation_ref`,
  `remote_source_revocation_status`, and `remote_source_revocation_digest`.
- `current-not-revoked` is required for `accept-ready`; revoked or stale sources
  remain schema-bound but blocked.
- The revocation digest is included in `remote_metadata_digest`, so branch / PR
  metadata and source freshness cannot drift independently.
- Raw remote revocation payloads are not stored.

# Revisit triggers

- Replace the deterministic revocation receipt with live provider checks if a
  remote source system exposes a stable, signed revocation API.
