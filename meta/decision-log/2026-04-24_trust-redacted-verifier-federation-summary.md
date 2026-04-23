---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/trust-management.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.trust.v0.idl
  - specs/schemas/trust_redacted_verifier_receipt_summary.schema
  - specs/schemas/trust_redacted_verifier_federation.schema
  - specs/schemas/trust_transfer_receipt.schema
  - evals/agentic/trust_cross_substrate_transfer.yaml
status: decided
closes_next_gaps:
  - 2026-04-24_trust-redacted-export-profile.md#agentic.trust.redacted-verifier-federation-summary
next_gap_ids:
  - agentic.trust.redacted-destination-lifecycle-summary
---

# Decision: Trust redacted export profile では verifier federation を summary/commitment surface に縮約する

## Context

2026-04-24 時点で `trust-transfer-demo --export-profile bounded-trust-transfer-redacted-export-v1`
は snapshot 側の `trust_redacted_snapshot` までは public contract 化されていましたが、
`remote_verifier_federation` は依然として full verifier receipt 2 本をそのまま露出していました。

このままでは redacted export が snapshot payload だけを縮約しつつ、
reviewer challenge / transport exchange detail はそのまま公開する非対称 surface に留まり、
public disclosure floor を verifier federation 側まで machine-checkable に閉じられません。

## Options considered

- A: redacted export でも verifier federation は full receipt のまま維持する
- B: verifier federation 全体を opaque digest 1 本に畳み、freshness timing も公開しない
- C: `trust_redacted_verifier_receipt_summary` と
  `trust_redacted_verifier_federation` を追加し、
  freshness timing / transport digest / sealed receipt digest だけを summary として公開する

## Decision

**C** を採択。

## Consequences

- redacted export profile では `remote_verifier_federation` が
  full `verifier_receipts` ではなく
  `trust_redacted_verifier_federation` summary を返す
- 各 verifier は `trust_redacted_verifier_receipt_summary` として
  `receipt_id` / `verifier_ref` / `verifier_endpoint` / `jurisdiction` /
  `recorded_at` / `freshness_window_seconds` / `transport_exchange_digest` /
  `sealed_receipt_digest` だけを公開する
- cadence / destination lifecycle は summary surface の `receipt_digest` ではなく
  `sealed_federation_digest` を binding target に使い、
  public summary と hidden full federation の commitment chain を分離する
- `validate_transfer_receipt()` は
  `remote_verifier_disclosure_bound` を公開 validation surface に追加し、
  full profile と redacted profile の disclosure floor が
  selected export profile と一致することを継続検証する
- schema / IDL / docs / eval / CLI / integration test / unit test は
  redacted verifier summary surface を継続検証する

## Revisit triggers

- redacted export でも destination lifecycle を summary/commitment へ縮約したくなった時
- verifier federation を single-jurisdiction fixed pair から
  multi-root / cross-jurisdiction quorum へ拡張したくなった時
- verifier summary に latency aggregate や revocation branch summary を追加したくなった時
