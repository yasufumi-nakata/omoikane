---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/trust-management.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.trust.v0.idl
  - specs/schemas/trust_redacted_destination_lifecycle.schema
  - specs/schemas/trust_transfer_receipt.schema
  - evals/agentic/trust_cross_substrate_transfer.yaml
status: decided
closes_next_gaps:
  - 2026-04-24_trust-redacted-verifier-federation-summary.md#agentic.trust.redacted-destination-lifecycle-summary
next_gap_ids:
  - agentic.trust.destination-revoked-recovery-branch
---

# Decision: Trust redacted export では destination lifecycle を summary/commitment surface に縮約する

## Context

2026-04-24 時点で `trust-transfer-demo --export-profile bounded-trust-transfer-redacted-export-v1`
は `trust_redacted_snapshot` と `trust_redacted_verifier_federation` までは
public contract 化されていましたが、
`destination_lifecycle` は export profile に関係なく
full append-only ledger のまま公開していました。

このままでは redacted export が snapshot / verifier federation だけを縮約しつつ、
destination 側の entry ref、covered verifier receipt ids、rationale を
そのまま露出する非対称 surface に留まり、
public disclosure floor を lifecycle 側まで machine-checkable に閉じられません。

## Options considered

- A: destination lifecycle は full ledger のまま維持し、redaction は verifier federation までで止める
- B: destination lifecycle 全体を opaque digest 1 本に畳み、status transition や timing も公開しない
- C: `trust_redacted_destination_lifecycle` を追加し、
  status transition / timing / digest commitments だけを public summary として残す

## Decision

**C** を採択。

## Consequences

- redacted export profile では full `destination_lifecycle.history` を公開せず、
  `trust_redacted_destination_lifecycle` が
  `sequence` / `event_type` / `status` / `recorded_at` / `valid_until` /
  `federation_digest` / `cadence_digest` /
  `covered_verifier_receipt_commitment_digest` /
  `destination_snapshot_digest`
  だけを public summary として返す
- entry ref、latest federation/cadence ref、covered verifier receipt ids、
  rationale は `redacted_fields` へ退避し、
  full append-only ledger 全体は `sealed_lifecycle_digest` に束縛する
- `validate_transfer_receipt()` は
  `destination_lifecycle_disclosure_bound` を追加し、
  full profile では full ledger、redacted profile では summary/commitment surface が
  selected export profile と一致することを継続検証する
- schema / IDL / docs / eval / integration test / schema contract test は
  lifecycle disclosure floor を verifier disclosure floor と同列に継続検証する

## Revisit triggers

- destination lifecycle を single current path から
  actual `revoked -> recovered` branch へ拡張したくなった時
- verifier federation を fixed 2-receipt pair から
  multi-root / cross-jurisdiction quorum へ拡張したくなった時
- cadence 自体も summary/commitment surface へさらに縮約したくなった時
