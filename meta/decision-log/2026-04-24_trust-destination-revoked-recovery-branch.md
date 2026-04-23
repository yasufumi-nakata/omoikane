---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/trust-management.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.trust.v0.idl
  - specs/schemas/trust_transfer_receipt.schema
  - specs/schemas/trust_redacted_destination_lifecycle.schema
  - evals/agentic/trust_cross_substrate_transfer.yaml
status: decided
closes_next_gaps:
  - 2026-04-24_trust-redacted-destination-lifecycle-summary.md#agentic.trust.destination-revoked-recovery-branch
next_gap_ids:
  - agentic.trust.multi-root-recovery-quorum
---

# Decision: Trust destination lifecycle に revoked/recovered branch を固定する

## Context

2026-04-24 時点で `trust-transfer-demo` は
redacted lifecycle summary まで public contract 化されていましたが、
destination lifecycle 自体は
`imported -> renewed -> revocation-cleared` の single current path に留まり、
一度 fail-closed に落ちた trust が
どの verifier federation / cadence を根拠に復帰したかを
repo 内 runtime で machine-checkable に監査できませんでした。

このままでは destination-side revocation が
単なる「cleared 済み check」の説明に圧縮され、
actual `revoked -> recovered` branch を
full / redacted の両 export profile で同一 digest family に残せません。

## Options considered

- A: current path を維持し、revoked/recovered branch は docs 上の説明に留める
- B: `revoked` terminal branch だけを追加し、recovery は別 surface に分離する
- C: `trust_transfer_receipt` / `trust_redacted_destination_lifecycle` の両方で
  `imported -> renewed -> revoked -> recovered` を固定し、
  recovery を renewed verifier federation/cadence に再束縛する

## Decision

**C** を採択。

## Consequences

- full profile の `destination_lifecycle.history` は
  `imported -> renewed -> revoked -> recovered` の fixed 4-entry branch を返す
- `revoked` entry は renewal 済み federation/cadence を保持したまま
  `status=revoked` で fail-closed 化し、
  `recovered` entry はさらに 1 回 renewed した verifier federation/cadence を
  top-level current state として束縛する
- redacted profile の `trust_redacted_destination_lifecycle` も
  同じ 4-entry branch を summary/commitment surface に縮約し、
  revoked/recovered ordering を reviewer-facing に監査できる
- `TrustService.validate_transfer_receipt()` は
  `destination_recovery_history_bound` を追加し、
  renewal / revocation / recovery が
  export profile と top-level current federation/cadence に整合することを検証する
- schema / IDL / eval / CLI demo / unit test / integration test / decision log を
  同一 branch contract に同期した

## Revisit triggers

- verifier federation を fixed 2-receipt pair から
  multi-root / cross-jurisdiction recovery quorum へ拡張したくなった時
- recovered ではなく terminal `revoked` export を
  reviewer-facing surface として固定したくなった時
- recovery reviewer の scoped rationale / legal execution proof を
  redacted export にも summary として残したくなった時
