---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/trust-management.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.trust.v0.idl
  - specs/schemas/trust_redacted_snapshot.schema
  - specs/schemas/trust_transfer_receipt.schema
  - evals/agentic/trust_cross_substrate_transfer.yaml
status: decided
closes_next_gaps:
  - 2026-04-24_trust-destination-lifecycle.md#agentic.trust.redacted-transfer-export-profile
next_gap_ids:
  - agentic.trust.redacted-verifier-federation-summary
---

# Decision: Trust transfer receipt に redacted export profile を追加する

## Context

2026-04-24 時点で `trust-transfer-demo` は
guardian / human quorum、live verifier federation、
re-attestation cadence、destination lifecycle まで
machine-checkable でしたが、
public receipt 自体は `source_snapshot` / `destination_snapshot` を
full clone のまま露出していました。

このままでは cross-substrate trust transfer に対して
「internal destination seed は保ちつつ、
reviewer-facing export では trust event payload を縮約する」
という disclosure floor を repo 内 runtime で検証できません。

## Options considered

- A: full clone receipt のみを維持し、redacted export は docs の説明に留める
- B: trust transfer と別 artifact に redacted export を分離する
- C: 既存 `trust_transfer_receipt` に `export_profile_id` を追加し、
  full clone / redacted を同一 receipt family で分岐する

## Decision

**C** を採択。

## Consequences

- `trust_transfer_receipt` は
  `export_profile_id=snapshot-clone-with-history | bounded-trust-transfer-redacted-export-v1`
  を持つ
- full-clone profile では既存どおり
  `source_snapshot` / `destination_snapshot` を公開し、
  `history_commitment_digest` と `trust-transfer-no-redaction-v1`
  を追加して export/import digest family を固定する
- redacted profile では raw snapshot を公開せず、
  `trust_redacted_snapshot` が sealed snapshot ref / digest、
  thresholds、eligibility、score surface、
  `history_commitment_digest`、`redacted_fields`
  を public projection として返す
- destination 側 seed mode は引き続き
  `snapshot-clone-with-history` に固定し、
  public export profile と internal import policy を分離する
- CLI / docs / schema / IDL / eval / tests は
  `trust-transfer-demo --export-profile bounded-trust-transfer-redacted-export-v1`
  を継続検証する

## Revisit triggers

- public redacted profile でも live verifier federation receipt を
  summary / commitment へ縮約したくなった時
- verifier federation を single-jurisdiction fixed pair から
  multi-root / cross-jurisdiction quorum へ拡張したくなった時
- destination lifecycle を current path だけでなく
  revoked / recovered branch まで公開 export に含めたくなった時
