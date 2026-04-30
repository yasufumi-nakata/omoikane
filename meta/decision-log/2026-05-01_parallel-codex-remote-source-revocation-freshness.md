---
decision_id: parallel-codex-remote-source-revocation-freshness-2026-05-01
status: accepted
date: 2026-05-01
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-remote-source-revocation-freshness-window
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
  - agents/guardians/integrity-guardian.policy.md
---

# Decision

Remote branch / PR Parallel Codex worker results now require a digest-bound
freshness window for the remote source-system revocation check.

# Rationale

The prior receipt required `current-not-revoked` and bound the revocation digest
into `remote_metadata_digest`, but it did not make the validity window of that
check explicit. A remote source could therefore keep a valid-looking
revocation digest after the check should have expired.

# Consequences

- Remote receipts now carry `remote_source_revocation_checked_at_ref`,
  `remote_source_revocation_freshness_window_seconds`,
  `remote_source_revocation_expires_at_ref`,
  `remote_source_revocation_freshness_status`, and
  `remote_source_revocation_freshness_digest`.
- `fresh` freshness status and a window no longer than 900 seconds are required
  for `accept-ready`.
- The freshness digest is included in both the revocation digest and the remote
  metadata digest, so source freshness cannot drift from revocation status.
- Raw remote freshness payloads are not stored.

# Revisit triggers

- Wire these freshness refs to a signed provider timestamp if a remote source
  system exposes a stable clock / revocation API.
