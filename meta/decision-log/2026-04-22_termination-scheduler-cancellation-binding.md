---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/termination-gate.md
  - docs/02-subsystems/kernel/ascension-scheduler.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.termination.v0.idl
  - specs/schemas/termination_request.schema
  - specs/schemas/termination_outcome.schema
  - evals/continuity/termination_scheduler_cancellation.yaml
status: decided
---

# Decision: TerminationGate は bound scheduler handle の cancel receipt まで outcome に束縛する

## Context

2026-04-22 時点で `TerminationGate.request()` は
`scheduler_handle_ref` を受け取っていましたが、
completed path でも実際には `AscensionScheduler.cancel()` を呼ばず、
public `termination_outcome` には `scheduler_handle_cancelled` の bool しか出ていませんでした。

この状態では termination surface が
「どの handle を止めたのか」「cancel が実際に execution receipt へ閉じたのか」を
machine-checkable に示せず、
`scheduler.cancel` と `TerminationGate` の contract が repo 内で分断されていました。

## Options considered

- A: current bool field を維持し、scheduler receipt binding は future work に残す
- B: `TerminationGate` が actual scheduler cancel と execution receipt compile を行い、結果を `termination_outcome.scheduler_cancellation` に束縛する
- C: termination request 自体を scheduler / oversight / notice flow の複合 orchestration へ拡張する

## Decision

Option B を採択します。

- `termination_request` は optional `scheduler_handle_ref` / `active_allocation_id` を public input として持ちます
- completed path は bound handle があれば `AscensionScheduler.cancel()` と
  `compile_execution_receipt()` を実行し、
  `result=cancelled` / `cancel_count` / `execution_receipt_digest` を
  `termination_outcome.scheduler_cancellation` に保持します
- `cool-off-pending` は `result=deferred`、
  invalid self proof の reject は `result=not-requested` として残し、
  non-cancel を completed path と区別します
- `termination-demo` は実際の Method A handle を bind し、
  completed / cool-off / reject の scheduler fate を sidecar JSON で返します

## Consequences

- TerminationGate と AscensionScheduler の cancel contract が
  runtime / schema / docs / eval / tests の同一 surface へ揃います
- completed path の `scheduler_handle_cancelled=true` が
  abstract flag ではなく execution receipt digest に裏付けられた artifact になります
- 残る論点は generic な scheduler cancel 不足ではなく、
  termination を Guardian notice flow や外部 legal escalation とどう束ねるかです

## Revisit triggers

- termination outcome に Guardian notice authority / legal execution binding を追加したくなった時
- 複数 scheduler handle の一括中断や task-graph level cancel まで拡張したくなった時
- termination surface を IMC / collective / external notice orchestration と統合したくなった時
