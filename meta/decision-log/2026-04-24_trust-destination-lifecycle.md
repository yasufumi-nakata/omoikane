---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/trust-management.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.trust.v0.idl
  - specs/schemas/trust_transfer_receipt.schema
  - evals/agentic/trust_cross_substrate_transfer.yaml
status: decided
closes_next_gaps:
  - 2026-04-24_trust-verifier-federation-cadence.md#agentic.trust.destination-revocation-renewal-history
next_gap_ids:
  - agentic.trust.redacted-transfer-export-profile
---

# Decision: Trust transfer receipt に destination lifecycle ledger を内包する

## Context

2026-04-24 時点で `trust-transfer-demo` は
guardian/human quorum、live remote verifier federation、
fixed re-attestation cadence までは public contract 化されていましたが、
destination 側でその trust が
「renew 済みか」「revocation check を通ったか」を
append-only に追える ledger がありませんでした。

このままでは cross-substrate trust transfer が
current な cadence snapshot を 1 点返すだけに留まり、
post-import の renewal / revocation gate を
repo 内 runtime で machine-checkable に監査できません。

## Options considered

- A: `re_attestation_cadence` だけを維持し、destination lifecycle は docs 上の説明に留める
- B: 別 artifact を追加し、trust transfer receipt からは参照だけ張る
- C: 既存 `trust_transfer_receipt` に `destination_lifecycle` を追加し、
  `imported -> renewed -> revocation-cleared` history を同じ digest family に束ねる

## Decision

**C** を採択。

## Consequences

- `trust_transfer_receipt` は `destination_lifecycle` を持ち、
  latest federation/cadence binding、active entry ref、
  fail-closed revocation action を公開 contract とする
- reference runtime は initial federation/cadence に続いて
  renewed federation/cadence を合成し、
  `imported -> renewed -> revocation-cleared`
  の append-only history を `destination_current=true` で返す
- `TrustService.validate_transfer_receipt()` は
  `destination_lifecycle_bound` /
  `destination_renewal_history_bound` /
  `destination_revocation_history_bound` /
  `destination_current`
  を public validation surface として返す
- schema / IDL / eval / CLI / runtime integration test / unit test は
  snapshot preserve を崩さず destination-side history を継続検証する

## Revisit triggers

- trust transfer を full clone ではなく redacted export profile に分岐したくなった時
- destination lifecycle を single current path から
  actual revoked / recovered branch へ拡張したくなった時
- verifier federation を cross-jurisdiction multi-root へ広げたくなった時
