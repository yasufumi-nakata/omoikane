# 2026-04-19 AscensionScheduler Reference Runtime

## Decision

- `AscensionScheduler` を L1 の独立 surface として reference runtime へ昇格する。
- execution を Method A の 4 stage
  (`scan-baseline` → `bdb-bridge` → `identity-confirmation` → `active-handoff`)
  に固定し、Method B/C は plan 受理のみで実行対象から外す。
- timeout 超過時は active stage の `rollback_to` に従って自動 rollback し、
  rollback 先が無い stage は `failed` として閉じる。
- scheduler state は `schedule_handle` と append-only continuity history を正本とし、
  pause / resume / rollback / cancel の全遷移を ledger event 付きで保存する。

## Rationale

- `docs/07-reference-implementation/README.md` に残っていた最大の runtime gap が
  AscensionScheduler の stage machine と rollback 実行面だった。
- 既に `docs/02-subsystems/kernel/ascension-scheduler.md`、
  `ascension_plan.schema`、`schedule_handle.schema` の草案があり、
  runtime / CLI / IDL / eval / tests を一気に揃える条件が整っていた。
- `TerminationGate` だけ先に実装されている状態では、
  upload sequence の順序保証と timeout rollback が docs-only のまま残っていた。

## Consequences

- `scheduler-demo` で Method A の固定 blueprint、順序違反 reject、
  timeout rollback、pause / resume、最終 completion を 1 回で smoke できる。
- `kernel.scheduler.v0.idl` と
  `evals/continuity/scheduler_stage_rollback.yaml` が追加され、
  scheduler contract が machine-readable になった。
- 大きな残課題は Method B/C の execution 面と
  SubstrateBroker-triggered pause/failover hook であり、
  distributed substrate orchestration は引き続き future work に残る。
