---
date: 2026-05-03
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/07-reference-implementation/README.md
  - src/omoikane/reference_os.py
  - tests/unit/test_builders.py
status: decided
---

# Decision: Yaoyorozu execution-chain fixture isolation

## Context

`yaoyorozu-demo` materializes a reviewer-facing L5 execution chain by running
live enactment and rollback witness services. Those services intentionally
exercise checkout-bound mutation receipts, but when the demo used the repository
root directly, repeated test or automation runs could leave `workspace-enacted`
marker residue in the main checkout before rollback cleanup completed.

## Decision

Keep the execution-chain receipt shape, reviewer-network gates, and rollback
witness semantics, but run the Yaoyorozu demo's live enactment / rollback
witness against a temporary git fixture repo seeded with only the patch targets
and eval refs needed by the generated build artifact.

## Consequences

- `yaoyorozu-demo --json` remains machine-checkable for build artifact,
  sandbox apply, live enactment, staged rollout, and rollback witness binding.
- The main checkout is no longer used as the mutable target for that demo path,
  so hourly automation can run the full suite without producing tracked marker
  residue.
- The lower-level `rollback-demo` and rollback service tests continue to cover
  checkout-bound mutation receipts; tests now use fixture checkouts where they
  need direct mutation semantics.

## Revisit Triggers

- The rollback receipt schema distinguishes source checkout from fixture
  checkout explicitly.
- Yaoyorozu execution-chain demos need to prove mutation against a separately
  provisioned long-lived repository instead of a temporary fixture.
