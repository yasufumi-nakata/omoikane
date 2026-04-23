---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/trust-management.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.trust.v0.idl
  - specs/schemas/trust_transfer_receipt.schema
  - specs/schemas/trust_redacted_verifier_federation.schema
  - specs/schemas/trust_redacted_destination_lifecycle.schema
  - evals/agentic/trust_cross_substrate_transfer.yaml
status: decided
closes_next_gaps:
  - 2026-04-24_trust-destination-revoked-recovery-branch.md#agentic.trust.multi-root-recovery-quorum
next_gap_ids:
  - agentic.trust.recovery-rationale-redaction-summary
---

# Decision: Trust recovery branch を multi-root / cross-jurisdiction quorum に引き上げる

## Context

2026-04-24 時点で `trust-transfer-demo` は
`imported -> renewed -> revoked -> recovered` の destination lifecycle と
redacted export floor までは machine-checkable でしたが、
`recovered` branch 自体は
single-jurisdiction / fixed 2 receipt の verifier pair に留まっていました。

このままでは recovered branch が
「revocation 後に本当に quorum を取り直したか」を
repo 内 runtime で reviewer-facing に監査できず、
multi-root / cross-jurisdiction recovery への拡張が
docs 上の次段メモに留まっていました。

## Options considered

- A: recovery でも fixed 2 receipt pair を維持し、multi-root quorum は future work に残す
- B: remote verifier federation に root 数だけを追加し、destination lifecycle までは束縛しない
- C: recovered federation / cadence / destination lifecycle / redacted export を同時に multi-root quorum へ拡張する

## Decision

**C** を採択。

## Consequences

- `remote_verifier_federation` は `quorum_policy_id`、`jurisdictions`、
  `trust_root_quorum`、`jurisdiction_quorum` を公開し、
  baseline の fixed pair と recovered branch の multi-root quorum を同一 family で表現する
- reference runtime は recovered branch で
  `required_verifier_count=3`、
  `trust_root_quorum=2`、
  `jurisdiction_quorum=2` の verifier federation を構成し、
  `JP-13` / `US-CA` / `EU-DE` の distinct verifier を
  reviewer-binding digest に束ねる
- destination lifecycle は full / redacted の両 profile で
  `quorum_policy_id` と quorum counts を保持し、
  `recovery_quorum_bound=true` により
  recovered branch の quorum materialization を継続検証する
- schema / IDL / eval / CLI / integration test / unit test は
  fixed 2 receipt 前提を外し、
  recovered branch だけが stronger quorum を要求する contract に同期した

## Revisit triggers

- redacted export に recovery rationale / legal proof の summary floor も追加したくなった時
- recovery quorum を fixed 3 verifier から lease / expiry 付きの rotating quorum へ広げたくなった時
- multi-root quorum を verifier receipt だけでなく destination-side legal execution proof へも束縛したくなった時
