---
decision_id: yaoyorozu-research-evidence-verifier-timestamp-replay-2026-05-02
status: accepted
date: 2026-05-02
area: agentic/yaoyorozu
closes_next_gaps:
  - yaoyorozu-research-evidence-verifier-provider-timestamp-replay
touchpoints:
  - src/omoikane/agentic/yaoyorozu.py
  - src/omoikane/reference_os.py
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_research_evidence_verifier_receipt.schema
  - specs/schemas/yaoyorozu_research_evidence_exchange.schema
  - specs/catalog.yaml
  - evals/agentic/yaoyorozu_research_evidence_verifier.yaml
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/07-reference-implementation/README.md
  - agents/README.md
  - agents/guardians/integrity-guardian.yaml
  - agents/guardians/integrity-guardian.policy.md
  - tests/unit/test_agentic.py
  - tests/integration/test_yaoyorozu_schema_contracts.py
  - tests/integration/test_reference_runtime.py
  - tests/integration/test_cli.py
---

# Decision

Yaoyorozu researcher evidence verifier receipts now bind freshness to a
signed-current provider timestamp and replay-unique nonce guard.

# Rationale

The previous verifier receipt bound repo-local expected/observed evidence
digests, live verifier transport quorum, signed response envelopes, and a
900 second freshness window. It did not separately bind that freshness window
to a signed provider timestamp or replay guard, leaving a weaker contract than
the other live verifier surfaces that already require timestamp freshness and
replay uniqueness.

# Implementation

`yaoyorozu_research_evidence_verifier_receipt` now carries digest-only
provider timestamp fields, a timestamp signature digest, nonce evidence,
previous nonce digest, replay status, and replay guard digest. Runtime
validation requires `signed-current` timestamp status and `unique` replay
status before the verifier quorum remains bound. The exchange validation and
`yaoyorozu-demo --json` top-level validation expose the same two gates.

# Verification

Schema contracts, IDL, evals, docs, IntegrityGuardian policy, unit tamper tests,
reference runtime integration, and CLI integration all cover the timestamp and
replay guard fields. Raw evidence, raw verifier response, raw signature, and
decision authority remain absent.

# Revisit Triggers

- Replace the reference provider-clock timestamp refs with live external
  verifier timestamp fetches when the researcher evidence verifier becomes a
  network-backed integration.
