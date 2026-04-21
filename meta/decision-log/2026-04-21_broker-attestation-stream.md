---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/substrate-broker.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.broker.v0.idl
  - specs/schemas/substrate_attestation_stream.schema
  - evals/continuity/substrate_broker_attestation_stream.yaml
status: decided
---

# Decision: SubstrateBroker に sealed attestation stream を追加する

## Context

2026-04-21 時点の `SubstrateBrokerService` は
standby probe、bounded attestation chain、
bounded dual allocation window まで machine-checkable でした。

しかし `specs/schemas/README.md` には依然
`continuous cross-substrate attestation streaming`
が次段階として残っており、
`hot-handoff` migrate 直前の final state digest が
shadow-sync overlap 上で継続監視されていたかは repo 内で固定できていませんでした。

## Options considered

- A: dual allocation window だけを維持し、continuous keepalive は future work に残す
- B: shadow-active window に束縛された bounded keepalive stream を追加し、sealed receipt を `hot-handoff` migrate の前提にする
- C: cross-host dual allocation と remote substrate quorum まで一気に拡張する

## Decision

Option B を採択します。

- `seal_attestation_stream` を追加し、
  healthy source attestation、handoff-ready attestation chain、
  shadow-active dual allocation window を prerequisite に固定します
- keepalive stream は
  `bounded-cross-substrate-attestation-stream-v1`
  として `5 beats / 250ms cadence / drift<=0.08`
  を sealed receipt に落とします
- `hot-handoff` migrate は
  latest attestation stream の `expected_state_digest` と
  `expected_destination_substrate` が request と一致しない限り fail-closed にします

## Consequences

- `broker-demo` は `shadow-sync` overlap と `authority-handoff` state を
  別 digest として扱いながら、
  final handoff digest を keepalive stream で machine-checkable に固定できます
- `kernel.broker.v0` / schema / eval / docs / tests が
  同じ sealed attestation stream contract を共有します
- residual future work は broad な continuous streaming 一般論ではなく、
  cross-host dual allocation へ縮小されます

## Revisit triggers

- shadow-active keepalive を fixed 5 beat ではなく longer streaming session へ広げたくなった時
- broker keepalive source を local synthetic observation ではなく remote substrate quorum へ接続したくなった時
- cross-host dual allocation を repo 内 reference runtime へ取り込みたくなった時
