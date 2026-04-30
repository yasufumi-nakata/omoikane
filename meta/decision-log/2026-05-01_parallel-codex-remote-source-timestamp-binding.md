---
decision_id: parallel-codex-remote-source-timestamp-binding-2026-05-01
status: accepted
date: 2026-05-01
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-remote-source-revocation-provider-timestamp-binding
touchpoints:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_worker_result_receipt.schema
  - specs/schemas/README.md
  - evals/continuity/parallel_codex_result_ingestion.yaml
  - evals/continuity/README.md
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/07-reference-implementation/README.md
  - agents/guardians/integrity-guardian.yaml
  - agents/guardians/integrity-guardian.policy.md
---

# Decision

Remote branch / PR Parallel Codex worker results now bind the revocation
freshness refs to signed provider timestamp evidence before they can become
`accept-ready`.

# Rationale

The prior receipt made the freshness window explicit, but the checked-at and
expires-at refs were not themselves tied to a signed clock source. A remote
source could therefore present a current-looking freshness digest while the
timestamp authority was stale, invalid, or unbound.

# Consequences

- Remote receipts carry `remote_source_revocation_timestamp_ref`,
  `remote_source_revocation_timestamp_status`,
  `remote_source_revocation_timestamp_digest`, and
  `remote_source_revocation_timestamp_signature_digest`.
- `signed-current` timestamp status is required for `accept-ready`; stale or
  invalid timestamps remain schema-bound but blocked.
- The timestamp signature digest is included in the freshness digest, and the
  timestamp evidence is included in `remote_metadata_digest`.
- Raw remote timestamp payloads are not stored.

# Revisit triggers

- Replace the reference provider timestamp digest with a live provider clock
  verifier only when a remote source system exposes a stable signed API.
