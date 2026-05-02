---
decision_id: yaoyorozu-research-evidence-verifier-roster-freshness-2026-05-03
status: accepted
date: 2026-05-03
area: agentic/yaoyorozu
closes_next_gaps:
  - yaoyorozu-research-evidence-verifier-roster-freshness-revocation
touchpoints:
  - src/omoikane/agentic/yaoyorozu.py
  - src/omoikane/reference_os.py
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_research_evidence_verifier_receipt.schema
  - specs/schemas/yaoyorozu_research_evidence_exchange.schema
  - specs/schemas/yaoyorozu_research_evidence_synthesis.schema
  - specs/catalog.yaml
  - evals/agentic/yaoyorozu_research_evidence_verifier.yaml
  - evals/agentic/yaoyorozu_research_evidence_exchange.yaml
  - evals/agentic/yaoyorozu_research_evidence_synthesis.yaml
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/07-reference-implementation/README.md
  - agents/README.md
  - agents/guardians/integrity-guardian.policy.md
  - tests/unit/test_agentic.py
  - tests/integration/test_yaoyorozu_schema_contracts.py
  - tests/integration/test_reference_runtime.py
  - tests/integration/test_cli.py
---

# Decision

Yaoyorozu researcher evidence verifier receipts now bind the policy-bound
verifier roster digest to an explicit freshness window and not-revoked status
before the live verifier quorum can validate.

# Rationale

The roster policy binding made the accepted verifier classes, jurisdictions,
threshold, and transport profile auditable, but it did not separately state
whether that roster snapshot was current or revoked. Because this surface is
digest-only and must not store the external roster payload, freshness and
revocation state need their own small digest payload and validation flag.

# Implementation

The verifier receipt now carries `verifier_roster_freshness_profile`,
`verifier_roster_freshness_ref`, `verifier_roster_freshness_window_seconds`,
`verifier_roster_freshness_status`, `verifier_roster_revocation_ref`,
`verifier_roster_revocation_status`, `verifier_roster_freshness_digest`, and
`verifier_roster_freshness_bound`. Exchange validation exposes
`evidence_verifier_roster_freshness_bound`, and synthesis requires every source
exchange to carry the same flag before advisory Council input validates.

# Verification

Runtime, schemas, IDL, evals, docs, IntegrityGuardian policy, unit tamper tests,
reference runtime integration, and CLI integration now cover the roster
freshness / revocation gate. Raw roster freshness payloads remain redacted.

# Revisit Triggers

- Replace the deterministic freshness and revocation refs with signed provider
  receipts when the verifier roster becomes network-backed.
- Shorten or parameterize the 86400 second roster freshness window when a real
  roster provider publishes a stricter service-level policy.
