---
decision_id: yaoyorozu-research-evidence-verifier-roster-policy-2026-05-03
status: accepted
date: 2026-05-03
area: agentic/yaoyorozu
closes_next_gaps:
  - yaoyorozu-research-evidence-verifier-roster-policy
touchpoints:
  - src/omoikane/agentic/yaoyorozu.py
  - src/omoikane/reference_os.py
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_research_evidence_verifier_receipt.schema
  - specs/schemas/yaoyorozu_research_evidence_exchange.schema
  - specs/schemas/yaoyorozu_research_evidence_synthesis.schema
  - specs/catalog.yaml
  - evals/agentic/yaoyorozu_research_evidence_verifier.yaml
  - evals/agentic/yaoyorozu_research_evidence_synthesis.yaml
  - docs/07-reference-implementation/README.md
  - agents/guardians/integrity-guardian.policy.md
  - tests/unit/test_agentic.py
  - tests/integration/test_yaoyorozu_schema_contracts.py
  - tests/integration/test_reference_runtime.py
  - tests/integration/test_cli.py
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/agentic/yaoyorozu.py
  - src/omoikane/reference_os.py
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_research_evidence_verifier_receipt.schema
  - specs/schemas/yaoyorozu_research_evidence_exchange.schema
  - specs/schemas/yaoyorozu_research_evidence_synthesis.schema
  - specs/catalog.yaml
  - evals/agentic/yaoyorozu_research_evidence_verifier.yaml
---

# Decision

Yaoyorozu researcher evidence verifier receipts now bind the live verifier
quorum to a policy-bound verifier roster digest before the evidence can flow
into advisory Council synthesis.

# Rationale

The previous receipt already bound repo-local evidence readback, live verifier
transport quorum, signed responses, timestamp freshness, and replay guard
evidence. It did not separately prove that the accepted verifier classes,
jurisdictions, quorum threshold, and transport profile came from the current
roster policy. That left the quorum complete but weaker than the roster-bound
verifier surfaces used elsewhere in the reference runtime.

# Implementation

The verifier receipt now carries `verifier_roster_policy_id`,
`verifier_roster_profile`, `verifier_roster_ref`, `verifier_roster_digest`,
`verifier_roster_status`, and `verifier_roster_bound`. The quorum digest
includes the roster digest, validation rejects stale or tampered roster fields,
and multi-researcher synthesis explicitly requires every source exchange to
carry `evidence_verifier_roster_bound=true`.

# Verification

Schema contracts, IDL, evals, docs, IntegrityGuardian policy, unit tamper tests,
reference runtime integration, and CLI integration cover the roster-bound gate.
Raw evidence, raw verifier response, raw verifier roster, raw signature payloads,
and researcher decision authority remain absent.

# Revisit Triggers

- Replace the deterministic reference roster ref with a live external verifier
  roster fetch when the researcher evidence verifier becomes network-backed.
