---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/ascension-scheduler.md
  - docs/02-subsystems/kernel/substrate-broker.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.scheduler.v0.idl
  - specs/interfaces/kernel.broker.v0.idl
  - specs/schemas/schedule_handle.schema
  - specs/schemas/scheduler_method_b_handoff_receipt.schema
  - evals/continuity/scheduler_method_b_broker_handoff.yaml
status: decided
---

# Decision: Method B の scheduler protected stage を broker orchestration receipt で gate する

## Context

2026-04-22 時点で `SubstrateBrokerService` は
standby probe、attestation chain、dual allocation window、
sealed attestation stream、cross-host host binding まで
machine-checkable でした。

一方 `AscensionScheduler` の Method B は
`shadow-sync -> dual-channel-review -> authority-handoff -> bio-retirement`
という stage machine だけを持ち、
`authority-handoff` / `bio-retirement` を開く時に
actual broker handoff 証跡を repo 内 contract として要求していませんでした。

この状態では docs で「SubstrateBroker と同期する」と書いていても、
Method B protected stage が host-bound handoff evidence なしで進めてしまいます。

## Options considered

- A: scheduler は stage machine のまま維持し、broker orchestration は repo 外 future work に残す
- B: Method B 専用 receipt を導入し、prepare / confirm の 2 段で broker handoff を scheduler handle に束縛する
- C: scheduler を飛ばして broker が Method B stage を直接実行する

## Decision

Option B を採択します。

`AscensionScheduler` は `scheduler_method_b_handoff_receipt` を持ち、
`method-b-host-bound-broker-orchestration-v1` を canonical policy に固定します。

この receipt は次を必須化します。

- `dual-channel-review` 中に `prepare_method_b_handoff` を通して
  `broker_signal` / `standby_probe` / `attestation_chain` /
  `dual_allocation_window` / `attestation_stream`
  を 1 つの prepared receipt へ束ねること
- prepared receipt が無いまま `authority-handoff` を開けないこと
- `authority-handoff` 中に `confirm_method_b_handoff` を通して
  hot-handoff `migration` と closed dual allocation cleanup を束縛すること
- confirmed receipt が無いまま `bio-retirement` を開けないこと
- receipt 自体が source/destination substrate、distinct host pair、
  host binding digest、cluster ref、cleanup release status を保持すること

## Consequences

- `scheduler-demo` は Method B signal pause / rollback だけでなく、
  actual broker evidence による prepare gate と confirm gate を JSON で示せるようになります
- `schedule_handle` は governance artifact sync / verifier roster に加えて
  Method B broker handoff receipt も first-class に保持します
- residual future work は generic な broker/scheduler 連携不在ではなく、
  distributed scheduler orchestration や longer-running multi-host streaming のような
  より上位の coordination に縮小されます

## Revisit triggers

- scheduler が live distributed substrate discovery を直接扱いたくなった時
- Method B receipt を verifier network や distributed transport observability plane と統合したくなった時
- `bio-retirement` の完了判定に source release 以上の multi-party witness を追加したくなった時
