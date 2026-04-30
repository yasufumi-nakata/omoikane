---
decision_id: parallel-codex-remote-source-timestamp-replay-guard-2026-05-01
status: accepted
date: 2026-05-01
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-remote-source-revocation-provider-timestamp-replay-guard
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

Remote branch / PR Parallel Codex worker results now bind signed provider
timestamp evidence to a replay guard before `accept-ready`.

# Rationale

The prior contract required a signed-current provider timestamp, but it did not
force that timestamp evidence to be unique for the specific remote branch / PR
source. A replayed timestamp could therefore make an old revocation freshness
window appear current.

# Consequences

- Remote receipts carry `remote_source_revocation_timestamp_nonce_ref`,
  `remote_source_revocation_timestamp_previous_nonce_digest`,
  `remote_source_revocation_timestamp_replay_status`, and
  `remote_source_revocation_timestamp_replay_guard_digest`.
- `unique` replay status is required for `accept-ready`; replayed timestamps
  remain schema-bound but blocked.
- The replay guard digest is included in the freshness digest and the remote
  metadata digest, so timestamp freshness cannot drift from replay protection.
- Raw replay guard payloads are not stored.

# Revisit triggers

- Replace the deterministic nonce chain with a live provider anti-replay API
  when remote source systems expose stable signed nonce or audit-log endpoints.
