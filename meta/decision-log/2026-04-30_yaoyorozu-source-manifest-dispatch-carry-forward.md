---
decision_id: yaoyorozu-source-manifest-dispatch-carry-forward-2026-04-30
status: accepted
date: 2026-04-30
area: agentic/yaoyorozu
closes_next_gaps:
  - yaoyorozu-source-manifest-public-verification-dispatch-carry-forward
touchpoints:
  - src/omoikane/agentic/yaoyorozu.py
  - src/omoikane/reference_os.py
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_worker_dispatch_plan.schema
  - specs/schemas/yaoyorozu_worker_dispatch_receipt.schema
  - evals/agentic/yaoyorozu_local_worker_dispatch.yaml
  - agents/guardians/integrity-guardian.yaml
---

# Decision

Yaoyorozu worker dispatch now treats the source manifest public verification
bundle as a launch prerequisite. `prepare_worker_dispatch()` accepts the
already ledger-bound source manifest binding, carries its public verification
bundle ref/digest/body into the dispatch plan, and `execute_worker_dispatch()`
echoes the same bundle into the receipt.

# Rationale

The source manifest public projection was previously reviewer-facing but
stopped at the registry/ledger boundary. Worker dispatch selected executable
agents from that registry without making the public bundle part of the launch
and receipt contract, so reviewers could not verify that the source manifest
provenance survived into the execution path.

# Consequences

- Dispatch plan and receipt schemas require
  `source_manifest_public_verification_bundle_ref`,
  `source_manifest_public_verification_bundle_digest`, and the digest-only
  bundle body.
- Runtime validation checks that the bundle is ready, digest-bound, raw-payload
  redacted, and tied to the same registry snapshot before worker launch.
- The local worker dispatch eval now protects this carry-forward path.

# Revisit

Workspace discovery and future cross-workspace dispatch manifests can reuse the
same public bundle fields, but should only do so after their own reviewer-facing
schema contracts are introduced.
