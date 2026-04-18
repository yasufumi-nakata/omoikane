# AscensionScheduler

L1 Kernel のサブモジュール。アップロード・退避・復元の **時間管理** と
**段階遷移の整合** を担う。Identity の状態遷移（[identity-lifecycle.md](identity-lifecycle.md)）の
**実行系**。

## 責務

1. AscensionPlan の受理と検証
2. 各 Stage（Pre → Ascending → Active → Paused → Active / Terminated / Failed）の遷移実行
3. Stage 遷移の ContinuityLedger 記録
4. SubstrateBroker / EthicsEnforcer / Council との同期
5. Pause / Resume / Rollback の即時実行

## AscensionPlan の構造

```yaml
ascension_plan:
  plan_id: <uuid>
  identity_id: <id>
  method: A | B | C            # Method A 漸進置換 / B 並走 / C 破壊スキャン
  stages:
    - stage_id: scan-baseline
      precondition: pre-upload-consent
      timeout_ms: 7_776_000_000   # 90 日
      rollback_to: null
    - stage_id: bdb-bridge
      precondition: scan-baseline:done
      timeout_ms: 600_000          # 10 分
      rollback_to: scan-baseline
    - stage_id: identity-confirmation
      precondition: bdb-bridge:done
      timeout_ms: 1_800_000        # 30 分
      rollback_to: bdb-bridge
    - stage_id: active-handoff
      precondition: identity-confirmation:passed
      timeout_ms: 300_000          # 5 分
      rollback_to: bdb-bridge
  ethics_attestation_required: true
  council_attestation_required: true
```

reference runtime は Method ごとに固定 profile を持つ。

- Method A: 上記 4 stage を固定実装し、timeout 超過時は `rollback_to` へ戻す
- Method B: `shadow-sync → dual-channel-review → authority-handoff → bio-retirement`
  を固定実装し、degraded substrate signal では pause、critical signal では
  `dual-channel-review` へ rollback する
- Method C: `consent-lock → scan-commit → activation-review` を固定実装し、
  `scan-commit` 以降は rollback を持たず、critical substrate signal で fail-closed する

## 不変条件

1. stage の遷移は **ContinuityLedger に append** されるまで完了とみなさない
2. timeout 超過は自動 rollback。即時に `Failed-Ascension` か前段 stage に戻す
3. `Active → Terminated` は scheduler を **割り込み優先** で停止する
4. SubstrateBroker からの degraded signal は scheduler の Pause に直結し、
   critical signal は stage policy に従って rollback または fail-closed する
5. Method A の stage 順序を入れ替える self-modify は禁止（T-Kernel）

## API

```
scheduler.schedule(plan: AscensionPlan) → ScheduleHandle
scheduler.advance(handle, stage_id) → StageResult
scheduler.pause(handle, reason) → ScheduleHandle
scheduler.resume(handle) → ScheduleHandle
scheduler.rollback(handle, to_stage_id) → ScheduleHandle
scheduler.enforce_timeout(handle, elapsed_ms) → TimeoutResult
scheduler.handle_substrate_signal(handle, severity, source_substrate, reason) → SignalResult
scheduler.cancel(handle, reason) → ScheduleHandle
```

## reference runtime の扱い

- `kernel.scheduler.v0.idl` で機械可読に
- `ascension_plan.schema` / `schedule_handle.schema` を導入
- `scheduler-demo` を CLI に追加し、Method A の順序遷移＋ forced rollback、
  Method B の reversible substrate failover、
  Method C の fail-closed destructive scan を ContinuityLedger に記録
- `evals/continuity/scheduler_stage_rollback.yaml` と
  `evals/continuity/scheduler_method_profiles.yaml` で Method A/B/C の contract を守る

## 思兼神メタファー

思兼神は天の石屋戸を開ける **段取り** を組んだ。スケジューラはまさに
「順序」と「中断時の戻し方」を司る。

## 関連

- [identity-lifecycle.md](identity-lifecycle.md)
- [continuity-ledger.md](continuity-ledger.md)
- [substrate-broker.md](substrate-broker.md)
- [termination-gate.md](termination-gate.md)
- [../mind-substrate/ascension-protocol.md](../mind-substrate/ascension-protocol.md)
