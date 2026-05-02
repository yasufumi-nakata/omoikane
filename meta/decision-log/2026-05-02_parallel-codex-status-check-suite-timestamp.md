---
decision_id: parallel-codex-status-check-suite-timestamp-2026-05-02
status: accepted
date: 2026-05-02
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-status-check-suite-provider-timestamp
touchpoints:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_post_commit_publication_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_post_commit_publication.yaml
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
---

# Decision

Parallel Codex post-commit publication now binds the status/check suite
provider timestamp and replay guard before GitHub handoff.

# Rationale

The prior publication receipt bound the status/check suite freshness window,
but it did not independently require a signed provider timestamp for the suite
snapshot or a replay guard for that timestamp. A replayed or stale provider
timestamp could therefore remain digest-bound while still weakening the
publication decision.

# Implementation

`parallel_codex_post_commit_publication_receipt` now includes a
`post-push-provider-status-check-suite-signed-timestamp-v1` profile and a
`post-push-provider-status-check-suite-timestamp-replay-guard-v1` profile.
The runtime records digest-only timestamp evidence, requires the timestamp
status to be `signed-current`, requires the replay status to be `unique`, folds
both digests into the publication digest, and blocks handoff if either raw
timestamp payload is stored.

# Verification

The reference runtime, schema contract tests, CLI integration test, continuity
eval, IDL, catalog, docs, and IntegrityGuardian policy all require the signed
status/check suite timestamp, replay guard, digest binding, and raw payload
redaction.

# Revisit Triggers

- Replace reference timestamp refs with live GitHub check-suite provider
  timestamp fetches when network integration is available.
