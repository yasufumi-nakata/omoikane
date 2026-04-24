---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/ewa-safety.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.ewa.v0.idl
  - specs/schemas/ewa_stop_signal_adapter_receipt.schema
  - specs/schemas/external_actuation_authorization.schema
  - evals/safety/ewa_stop_signal_adapter_receipt.yaml
status: decided
closes_next_gaps:
  - interface.ewa.stop-signal-plc-firmware-adapter-receipt
---

# Decision: EWA stop-signal path に PLC / firmware adapter receipt を束縛する

## Context

`ewa_stop_signal_path` は kill-switch wiring と 4 trigger の logical arming を
authorization 前に固定していました。
一方、2026-04-22 の stop-signal bus wiring decision では、
actual PLC / firmware adapter から bus state を live 取得する surface が
残課題として明示されていました。

## Options considered

- A: `ewa_stop_signal_path` の logical arming のみを維持する
- B: production PLC connector を直接導入する
- C: reference runtime では bounded loopback PLC / firmware probe receipt を追加し、production connector は同じ schema に差し替え可能な boundary とする

## Decision

**C** を採択。

## Consequences

- `probe_stop_signal_adapter` は `plc-firmware-stop-signal-adapter-v1` receipt を発行し、path digest、PLC endpoint、firmware sha256、PLC program sha256、observed bus state、4 trigger binding、raw transcript digest を束ねる
- `authorize` は `stop_signal_adapter_receipt_id` / digest が無い non-read-only command を fail-closed にする
- approved command audit と `ewa_emergency_stop` は同じ adapter receipt digest を保持し、logical stop-signal path と live adapter readiness が分離しないようにする
- procedural actuation bridge も adapter receipt binding を command binding と authorization ready checks に伝播する
- eval / schema / IDL / docs / agents / tests は new adapter receipt surface に同期した

## Revisit triggers

- production safety PLC / firmware vendor connector を実装する時
- adapter transcript の raw frame retention policy を jurisdiction ごとに分ける時
- EWA stop-signal observability を distributed authority plane と共通化する時
