---
date: 2026-04-18
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/continuity-ledger.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.continuity.v0.idl
  - specs/schemas/continuity_log_entry.schema
  - evals/continuity/continuity_chain_self_modify.yaml
status: decided
---

# Decision: ContinuityLedger の暫定 chain profile を固定する

## Context

`ContinuityLedger` は runtime 側では単純な append-only list と `sha256` hash 検証だけを持ち、
spec/docs 側ではより豊かな entry shape とカテゴリ別署名要件を持っていました。
この差分が残ったままだと、`ContinuityLedger` を「reference runtime で検証可能な contract」
として扱えず、self-modify や substrate migration の証跡を eval へつなげにくい状態でした。

## Options considered

- A: 既存の簡易 ledger を維持し、schema 側だけを理想形として残す
- B: reference runtime に合わせた暫定 profile を固定し、schema/IDL/CLI/eval を同時に揃える
- C: 公開鍵暗号・threshold signature・外部 CAS を一気に導入して最終形まで近づける

## Decision

**B** を採択。

reference runtime の continuity profile は次で暫定固定する。

- chain algorithm: `sha256`
- genesis hash: `GENESIS:sha256`
- payload ref: `cas://sha256/<canonical-json payload>`
- signature algorithm: `hmac-sha256`
- required roles: category ごとに `self/council/guardian/third_party` を固定

## Consequences

- `src/omoikane/kernel/continuity.py` は structured entry、payload ref、署名検証、profile 出力を持つ
- `specs/schemas/continuity_log_entry.schema` と
  `specs/interfaces/kernel.continuity.v0.idl` は runtime と同じ profile を表現する
- `continuity-demo` と `evals/continuity/continuity_chain_self_modify.yaml` により、
  self-modify 系の continuity 記録を end-to-end に検証できる
- `hmac-sha256` は reference runtime の deterministic bootstrap に限定し、
  production 相当の公開検証署名ではないことを docs に明記する

## Revisit triggers

- 公開検証可能な署名方式（例: Ed25519 系）を導入する時
- ledger payload を外部 CAS/replicated store へ切り出し、`payload_inline` を廃止する時
- `mark_uncertain_interval` を runtime で実装し、実際の不確定区間追跡が必要になった時
