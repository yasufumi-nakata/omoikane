---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/substrate-broker.md
  - docs/07-reference-implementation/README.md
  - specs/schemas/substrate_allocation.schema
  - specs/schemas/substrate_dual_allocation_window.schema
  - evals/continuity/substrate_broker_dual_allocation_window.yaml
status: decided
closes_next_gaps:
  - kernel.broker.dual-allocation-open-window-schema
---

# Decision: Broker dual allocation schema は open/closed lifecycle を分ける

## Context

`broker-demo` の open dual allocation window は `window_status=shadow-active` の間、
`closed_at`、`close_reason`、`shadow_release`、`shadow_allocation.released_at` を
`null` として返します。

一方、公開 schema はそれらを文字列または release object として扱っており、
open receipt の machine validation と runtime 出力がずれていました。

## Options considered

- A: runtime から open window の nullable fields を省略する
- B: schema 側で open window は nullable、closed window は non-null release receipt 必須として表現する
- C: open window と closed window を別 schema に分ける

## Decision

**B** を採択。

## Consequences

- `substrate_allocation.schema` は active allocation の `released_at: null` を許容する
- `substrate_dual_allocation_window.schema` は
  `shadow-active` では close lifecycle fields を `null`、
  `closed` では `closed_at` / `close_reason` / `shadow_release` を non-null 必須として検証する
- broker schema contract test は
  standby probe、attestation chain、open/closed dual allocation window、
  attestation stream を `broker-demo` 実出力から検証する

## Revisit triggers

- dual allocation window の intermediate status が増える時
- shadow allocation release を別 ledger receipt family へ分離する時
