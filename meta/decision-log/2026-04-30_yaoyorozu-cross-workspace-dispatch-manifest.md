---
decision_id: yaoyorozu-cross-workspace-dispatch-manifest-2026-04-30
status: accepted
date: 2026-04-30
area: agentic/yaoyorozu
closes_next_gaps:
  - yaoyorozu-cross-workspace-dispatch-manifest
touchpoints:
  - src/omoikane/agentic/yaoyorozu.py
  - src/omoikane/reference_os.py
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_cross_workspace_dispatch_manifest.schema
  - specs/schemas/yaoyorozu_worker_dispatch_plan.schema
  - specs/schemas/yaoyorozu_worker_dispatch_receipt.schema
  - evals/agentic/yaoyorozu_local_worker_dispatch.yaml
  - agents/guardians/integrity-guardian.yaml
---

# Decision

Yaoyorozu worker dispatch now emits a
`yaoyorozu-cross-workspace-dispatch-manifest-v1` artifact before the dispatch
plan digest is finalized. The manifest binds the workspace discovery ref/digest,
accepted workspace digest set, dispatch-unit workspace selections, Guardian
preseed gates, dependency materialization requirements, and source manifest
public verification bundle into one digest-only reviewer-facing contract.

# Rationale

The previous source-manifest carry-forward proved that executable agent sources
were public-verification-bound, but it did not provide one reviewer-facing
manifest for the cross-workspace execution decision itself. Reviewers had to
join workspace discovery, convocation binding, dispatch units, and receipt
counts manually. The manifest makes that join explicit without exposing raw
workspace, source, or dispatch payloads.

# Consequences

- `prepare_worker_dispatch()` builds and validates the manifest before storing
  it in `yaoyorozu_worker_dispatch_plan`.
- `execute_worker_dispatch()` echoes the same manifest ref/digest/body into
  `yaoyorozu_worker_dispatch_receipt` and receipt validation recomputes the
  dispatch workspace bindings from executed worker results.
- `council_convocation_session` now carries accepted workspace digests and a
  coverage summary digest so downstream manifest construction can remain
  digest-only.
- The local worker dispatch eval protects plan/receipt carry-forward of the
  new manifest.

# Revisit

Future cross-host transport work should extend this manifest with transport
receipt digests only after the transport schema itself is reviewer-facing and
raw network payload handling is specified.
