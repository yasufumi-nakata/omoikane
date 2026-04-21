---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/substrate-broker.md
  - docs/02-subsystems/substrate/README.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.broker.v0.idl
  - specs/interfaces/substrate.adapter.v0.idl
  - specs/schemas/substrate_attestation_chain.schema
  - specs/schemas/substrate_dual_allocation_window.schema
  - specs/schemas/substrate_attestation_stream.schema
  - specs/schemas/substrate_transfer.schema
  - evals/continuity/substrate_broker_attestation_chain.yaml
  - evals/continuity/substrate_broker_dual_allocation_window.yaml
  - evals/continuity/substrate_broker_attestation_stream.yaml
status: decided
---

# Decision: SubstrateBroker の Method B dual allocation を cross-host host-bound contract に昇格する

## Context

2026-04-21 時点で `SubstrateBrokerService` は
standby probe、attestation chain、bounded dual allocation window、
sealed attestation stream まで machine-checkable でした。

一方で `kernel.broker.v0.idl` には
`Cross-host dual allocation remains future work` が残っており、
Method B `shadow-sync -> authority-handoff` が
「どの host pair 上で成立した handoff なのか」を
repo 内 contract に束縛できていませんでした。

4/22 に distributed transport 側で
cross-host authority binding が閉じたため、
L1 broker 側も substrate handoff を host-bound に揃える準備が整いました。

## Options considered

- A: 現状の same-shape dual allocation を維持し、cross-host binding は future work に残す
- B: 既存 broker surface を拡張し、attestation chain / dual allocation window / attestation stream / transfer に distinct host pair と cluster binding を追加する
- C: Broker を飛ばして scheduler から distributed substrate orchestration を直接実装する

## Decision

Option B を採択します。

Method B の broker handoff は
`attested-cross-host-substrate-handoff-v1` を canonical profile に固定し、
次を必須化します。

- source / standby が同一 `substrate_cluster_ref` に属すること
- source / standby が distinct `host_ref` を持つこと
- `bridge_attestation_chain` が `expected_destination_host_ref` と `host_binding_digest` を先に固定すること
- `open_dual_allocation_window` / `seal_attestation_stream` / `migrate` が同じ host binding を引き継ぐこと
- `SubstrateAllocation` / `SubstrateTransfer` も host metadata を first-class field として保持すること

## Consequences

- `broker-demo` は substrate-kind rotation だけでなく、
  actual Method B handoff の distinct-host pair を JSON で示せるようになります
- `substrate_attestation_chain` / `substrate_dual_allocation_window` /
  `substrate_attestation_stream` / `substrate_transfer` が同じ host-bound handoff contract を共有します
- `kernel.broker.v0` の residual future work から
  `cross-host dual allocation` を外せます
- 残課題は broad な dual allocation 不在ではなく、
  distributed scheduler orchestration や longer-running multi-host streaming のような
  さらに上位の coordination に縮小されます

## Revisit triggers

- Method B handoff を固定 cluster pair ではなく dynamic substrate discovery へ広げたくなった時
- scheduler の live stage execution と broker host binding を 1 つの orchestration receipt に統合したくなった時
- host binding を verifier network や external authority plane と共通 attestation にしたくなった時
