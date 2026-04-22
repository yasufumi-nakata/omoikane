# Decision: AscensionScheduler の cancel を execution receipt まで昇格する

## Context

`AscensionScheduler.cancel()` 自体は public API として存在していましたが、
`scheduler-demo`、`evals/continuity`、integration/unit test、
および reviewer-facing `scheduler_execution_receipt` には
cancel 経路が明示的に出ていませんでした。

この状態では `cancelled` status が schema 上は許容されていても、
実際に protected handoff 前の operator cancel が
digest-bound artifact として閉じることを継続検証できません。

## Decision

- `scheduler-demo` に Method A cancel scenario を追加する
- `scheduler_execution_receipt` に `cancel_count` と
  `outcome_summary.cancelled` を追加し、`scenario_labels` に `cancelled` を固定語彙として載せる
- `evals/continuity/scheduler_cancellation.yaml` を追加し、
  current stage を保持したまま handle が閉じる contract を明文化する
- docs/IDL/test も同じ cancel semantics に同期する

## Consequences

- reviewer は `completed` / `failed` だけでなく `cancelled` も
  first-class execution outcome として機械的に追跡できます
- protected handoff 前に external termination governance へ切り替える運用が
  runtime / schema / eval / test の同一 contract で確認できます
- 残る論点は generic cancellation policy ではなく、
  cancel を termination gate や外部 notice flow とどう束ねるかです
