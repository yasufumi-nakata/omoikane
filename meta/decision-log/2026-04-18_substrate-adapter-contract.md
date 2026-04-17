---
date: 2026-04-18
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/substrate/README.md
  - docs/01-architecture/layered-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/substrate.adapter.v0.idl
  - evals/continuity/substrate_migration_continuity.yaml
status: decided
---

# Decision: SubstrateAdapter v0 contract を固定する

## Context

`SubstrateAdapter` には既に最小の IDL ファイルが存在した一方で、
docs に書かれている operation 群、reference runtime の実装、catalog、eval が
揃っていませんでした。
この状態では L0 substrate を「仕様済み」とも「未解決」とも言い切れず、
connectome や continuity の後続設計を受ける境界として弱いままでした。

## Options considered

- A: 既存の `allocate` / `attest` だけを維持し、残りは docs 上の暫定 API として残す
- B: `transfer` / `release` / `energy_floor` を含む v0 contract を固定し、reference runtime で end-to-end に実証する
- C: 量子・生体・未知 substrate まで含めた全 adapter 群を先に schema 化する

## Decision

**B** を採択。

## Consequences

- `specs/interfaces/substrate.adapter.v0.idl` を L0 の正本 contract として扱う
- operation は `allocate` / `attest` / `transfer` / `release` / `energy_floor` の 5 つに固定する
- 各 payload は専用 schema に切り出し、runtime と docs が同じ shape を参照する
- reference runtime は `substrate-demo` で allocation から migration / release までを実行し、
  continuity eval の受け皿を提供する

## Revisit triggers

- `UnknownAdapter` や量子 substrate を実装し、capability negotiation が必要になった時
- energy floor が静的テーブルでは足りず、EthicsEnforcer と双方向連携が必要になった時
- SubstrateBroker を独立 service として分離し、L1/L0 間イベント境界を細分化する時
