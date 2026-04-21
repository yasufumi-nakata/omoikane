---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/ascension-scheduler.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.scheduler.v0.idl
  - specs/schemas/scheduler_execution_receipt.schema
  - evals/continuity/scheduler_execution_receipt.yaml
status: decided
---

# Decision: AscensionScheduler の実行経路を compiled execution receipt として固定する

## Context

2026-04-22 時点で `AscensionScheduler` は
Method A/B/C の stage machine、artifact sync、verifier rotation、
Method B broker handoff まで machine-checkable でした。

一方で `scheduler-demo` が返すのは scenario JSON の寄せ集めであり、
「1 本の schedule handle がどの execution profile に従ってどの gate を通り、
どの continuity refs を残したか」を
first-class artifact として再利用できませんでした。

この状態では runtime と docs/evals が豊富でも、
reviewer-facing には handle history を毎回読み解く必要があり、
automation が次回の gap 選定時に実行結果を digest-bound な contract として扱いにくいままでした。

## Options considered

- A: `schedule_handle` と `scheduler-demo` の scenario JSON だけを維持し、execution receipt は作らない
- B: `schedule_handle` history から compile する `scheduler_execution_receipt` を追加し、Method A/B/C の protected gate/outcome を first-class summary にする
- C: generic scheduler executor DSL を新設し、compile ではなく execution 全体を別 surface に移す

## Decision

Option B を採択します。

`AscensionScheduler` は `compile_execution_receipt(handle)` を持ち、
`schedule_handle` から次を固定的に抽出します。

- method ごとの `execution_profile_id`
- fixed `stage_blueprint` と `visited_stages`
- `continuity_event_refs` と transition count
- `artifact_bundle_status` / `verifier_rotation_state` /
  `verifier_connectivity_status` / `broker_handoff_status`
- timeout recovery、protected gate pause、live verifier connectivity、
  verifier rotation cutover、Method B broker handoff、Method C fail-closed を
  `outcome_summary` と `scenario_labels` へ要約した結果
- digest-less payload に対する `receipt_digest`

## Consequences

- `scheduler-demo` は handle 群に加えて
  `execution_receipts` と validation を返し、
  Method A/B/C の run outcome を reviewer-facing に再利用できます
- `scheduler_execution_receipt.schema` と
  `kernel.scheduler.v0` が、
  stage machine の「状態」だけでなく「実行結果 summary」も
  machine-checkable に扱います
- residual future work は generic な execution summary 不在ではなく、
  distributed scheduler orchestration や
  external verifier / broker / transport を跨いだ複合 receipt の統合へ縮小されます

## Revisit triggers

- scheduler execution を live distributed orchestration receipt と統合したくなった時
- execution receipt に reviewer / guardian attestation を追加したくなった時
- Method A/B/C 以外の profile を reference runtime に導入したくなった時
