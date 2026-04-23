---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/trust-management.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.trust.v0.idl
  - specs/schemas/trust_snapshot.schema
  - specs/schemas/trust_transfer_receipt.schema
  - evals/agentic/trust_cross_substrate_transfer.yaml
status: decided
closes_next_gaps:
  - 2026-04-23_trust-provenance-anti-tamper-guard.md#gap-1
next_gap_ids:
  - agentic.trust.remote-attestation-federation
---

# Decision: Trust の substrate 跨ぎ移送を digest-bound receipt として固定する

## Context

2026-04-23 時点で `agentic.trust.v0` と `TrustService` は
provenance-bound anti-tamper guard と human pin freeze までは
machine-checkable でしたが、
trust snapshot を substrate 境界の向こうへ carry over する public artifact がなく、
policy / thresholds / eligibility / history を保った export/import を
repo 内 runtime で検証できませんでした。

このままでは TrustRegistry が source substrate 上だけの local state に留まり、
standby substrate や reviewed destination host へ移る際の
guardian / human attestation と snapshot preserve を
reference runtime で reviewer-facing に監査できません。

## Options considered

- A: trust update surface のみを維持し、cross-substrate transfer は docs 上の説明に留める
- B: snapshot clone を追加するが、guardian/human attestation や digest binding は持ち込まない
- C: source/export, guardian+human federation attestation, destination/import を 1 receipt に閉じる

## Decision

**C** を採択。

## Consequences

- `agentic.trust.v0` は `transfer_snapshot` / `validate_transfer_receipt` を持ち、
  `trust_transfer_receipt` を public contract にする
- reference runtime は `trust-transfer-demo` により
  `source-guardian` / `destination-guardian` / `human-reviewer` の fixed quorum、
  source / destination `trust_snapshot` digest、
  route digest、
  `snapshot-clone-with-history` import を同一 receipt に束ねる
- `TrustService.import_snapshot()` と `transfer_snapshot_to()` は
  history / thresholds / provenance policy / eligibility を preserve した clone import を固定する
- schema / CLI / integration test / schema contract test / eval は
  digest binding と preserve 条件を継続検証する
- 次段の frontier は fixed three-party quorum を超える
  live remote verifier federation と re-attestation cadence の materialization へ移る

## Revisit triggers

- guardian / human attestation を live remote verifier network に拡張したくなった時
- trust transfer に expiry, lease renewal, destination-side revocation を持ち込みたくなった時
- history preserve を full clone ではなく redacted export profile に分岐したくなった時
