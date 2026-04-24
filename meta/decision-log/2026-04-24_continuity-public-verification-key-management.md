---
date: 2026-04-24
surface:
  - src/omoikane/kernel/continuity.py
  - specs/schemas/continuity_public_verification_bundle.schema
  - evals/continuity/continuity_public_verification_key_management.yaml
closes_next_gaps:
  - docs/02-subsystems/kernel/continuity-ledger.md#public-verification-key-management
---

# Decision: ContinuityLedger の public verification key roster を固定する

## Context

ContinuityLedger は `sha256` chain と `hmac-sha256` role signature で
reference runtime の deterministic bootstrap を満たしていました。
一方で docs には、公開検証可能な署名方式と key management への移行待ちが残り、
Integrity Guardian や外部 verifier が最初に検証する machine-readable artifact が
ありませんでした。

## Decision

`continuity-public-verification-key-management-v1` を追加し、
`continuity-demo --json` が digest-only public verification bundle を返すようにします。
bundle は次を固定します。

- ledger head / entry count / ledger verification digest
- role ごとの verifier key ref / key digest / verification scope
- entry ごとの required role / present role / signature digest / verifier key ref
- raw key material と raw signature payload を公開しない flag

実運用の公開鍵暗号へ飛ばず、まず reference runtime で key roster と signature evidence の
公開 contract を閉じます。

## Consequence

- `kernel.continuity.v0` は bundle compile / validation operation を持つ
- `continuity_public_verification_bundle.schema` は `continuity-demo --json` の出力を直接検証できる
- `evals/continuity/continuity_public_verification_key_management.yaml` が
  ledger head、key roster、per-entry signature digest、非公開 flag を守る
- HMAC secret は runtime 内部に残し、公開 artifact は digest / ref だけに縮約する
