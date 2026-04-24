---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_reconcile.schema
  - evals/interface/wms_time_rate_deviation_escape.yaml
status: decided
---

# Decision: WMS time_rate deviation を fixed private escape evidence へ束縛する

## Context

`interface.wms.v0` は time_rate deviation 時に private_reality escape を提示する
保証を持っていました。一方で public `wms_reconcile.schema` は
`requested_time_rate=1.0` だけを受理し、`wms-demo` も deviation scenario を
返していなかったため、fixed-time-rate boundary が schema/eval で検証できませんでした。

## Options considered

- A: `world_state.time_rate` を可変にして runtime state を直接変更する
- B: docs の「1.0 固定」だけを維持する
- C: requested deviation を `fixed-time-rate-private-escape-v1` の digest-bound
  reconcile evidence として返し、WorldState は 1.0 に固定する

## Decision

**C** を採択。

`baseline-requested-time-rate-delta-v1` digest profile で baseline 1.0、
requested value、delta、escape requirement、classification を束縛し、
deviation は `major_diff` / `offer-private-reality` へ deterministic に縮退する。

## Consequences

- `wms-demo --json` は `time_rate_deviation` scenario と
  `time_rate_deviation_escape_bound` validation を返す
- `wms_reconcile.schema` は non-1.0 requested time_rate を受理しつつ、
  baseline state lock と digest evidence を必須にする
- eval / unit / integration tests は WorldState.time_rate が 1.0 のまま保たれることを検証する

## Remaining scope

- substrate 間の実同期方式と知覚適応は research-frontier docs に残し、
  reference runtime では fixed boundary と escape evidence だけを扱う

## Revisit triggers

- WMS engine adapter が substrate-specific time_rate negotiation を実装する時
- remote participant の subjective-time attestation を transport receipt に束縛する時
