---
decision_id: ethics-consent-event-redaction-2026-04-30
status: accepted
date: 2026-04-30
area: kernel/ethics
closes_next_gaps:
  - ethics-consent-authenticity-event-redaction
touchpoints:
  - src/omoikane/kernel/ethics.py
  - src/omoikane/reference_os.py
  - specs/interfaces/kernel.ethics.v0.idl
  - specs/schemas/ethics_event.schema
  - specs/schemas/ethics_consent_authenticity_receipt.schema
  - evals/safety/ethics_rule_tree_contract.yaml
  - docs/02-subsystems/kernel/ethics-enforcement.md
  - docs/07-reference-implementation/README.md
  - agents/guardians/integrity-guardian.yaml
---

# Decision: consent-bound EthicsLedger events use digest-only receipts

## Context

The previous consent authenticity guard correctly vetoed coerced consent and
escalated incomplete attestations, but `record_decision()` still copied the raw
request payload into `action_snapshot`. That contradicted the documented
`raw consent payload を保存しない` boundary and made consent evidence harder to
review as a stable public artifact.

## Decision

EthicsLedger events now use
`ethics-event-action-snapshot-digest-redaction-v1`. The action snapshot carries
`payload_ref`, `payload_digest`, a small non-sensitive summary, and
`raw_payload_stored=false`. Consent-bound actions additionally carry
`ethics_consent_authenticity_receipt` with
`consent-authenticity-digest-receipt-v1`, required evidence refs, missing
evidence/attestation lists, authenticity status, receipt digest, and
`raw_consent_payload_stored=false`.

## Consequences

- `ethics_event.schema` validates digest-only action snapshots instead of raw
  payload snapshots.
- `ethics-demo` proves coerced and incomplete consent events retain reviewer
  evidence without raw consent payloads.
- IntegrityGuardian has an explicit attestation scope for consent event
  redaction.

## Revisit

Jurisdiction-specific consent registry verification can be layered on top of
the receipt once an external verifier schema is needed.
