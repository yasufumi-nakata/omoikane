---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_reconcile.schema
  - specs/schemas/wms_time_rate_attestation_receipt.schema
  - evals/interface/wms_time_rate_attestation_transport.yaml
status: decided
closes_next_gaps:
  - wms.time-rate.subjective-attestation-transport
---

# Decision: WMS time_rate deviation を participant subjective-time attestation receipt へ束縛する

## Context

`fixed-time-rate-private-escape-v1` は requested `time_rate` deviation を
WorldState mutation ではなく private escape evidence へ縮退できるようにしました。
ただし、その requested subjective-time delta を各 participant が同じ subject として
IMC transport 上で attested したことは machine-checkable ではありませんでした。

## Options considered

- A: deviation digest だけを維持し、participant attestation は WMS engine adapter 段階へ送る
- B: subjective-time conversation transcript を WMS reconcile output に保存する
- C: participant ごとの IMC handshake / message digest / subject digest を
  `wms_time_rate_attestation_receipt` に縮約し、ordered digest set を
  `wms_reconcile` に束縛する

## Decision

**C** を採択。

`subjective-time-attestation-transport-v1` を fixed profile とし、
`participant-subjective-time-attestation-set-v1` で participant order、
receipt digest set、time-rate attestation subject digest を bind する。
`wms-demo --json` は 3 participant の attestation receipt を返し、
`time_rate_deviation` scenario の quorum / order validation で確認できる。

## Consequences

- time_rate deviation evidence は participant attestation quorum を first-class に持つ
- public `wms_reconcile.schema` は attestation receipt set を検証する
- eval / unit / integration tests は WorldState.time_rate が 1.0 のまま、
  subjective-time attestation transport が complete であることを固定する

## Deferred scope

- substrate-specific time synchronization algorithm は research-frontier 側に留める
- real WMS engine adapter の transaction log 統合は adapter surface を持つ段階で扱う
