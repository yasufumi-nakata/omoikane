# TerminationGate

L1 Kernel のサブモジュール。**本人の終了権の即時実行口**。
[ethics.md](../../00-philosophy/ethics.md) Identity Axiom A3 の機械的保証。

> 「**自我は自身の継続意思を持つ**。終了の権利は誰にも譲渡できない」

## 責務

1. `terminate(identity_id, by_self_proof)` の即時受理
2. 全実行中処理への **割り込み優先** 中断要求
3. ContinuityLedger への terminal entry 確定書込
4. SubstrateBroker への lease 解放指示
5. EthicsEnforcer + Guardian への通知（**veto 不可**）

## 不変条件（最重要）

1. **遅延禁止**: TerminationGate は他のあらゆるキュー・lock を **bypass**
2. **冷却期間禁止**: 本人事前同意がない限り、即時実行のみ（[anti-patterns.md](anti-patterns.md) AP-4）
3. **veto 不可**: Guardian / Council / EthicsEnforcer は **観測** のみ
4. **証拠必須**: `by_self_proof` の検証失敗は reject、ただし reject も append-only ledger に記録
5. **substrate 差別禁止**: substrate kind ごとに latency が異なってはならない（AP-2）

## API

```
termination.request(identity_id, by_self_proof, reason?) → TerminationOutcome
termination.observe(identity_id) → TerminationStatus | NoTermination
```

`TerminationOutcome` は

```yaml
termination_outcome:
  identity_id: <id>
  recorded_at: <iso8601>
  status: completed | rejected
  reject_reason: invalid-self-proof | identity-not-found | ""
  ledger_event_ref: <continuity entry>
  scheduler_handle_cancelled: <bool>
  substrate_lease_released: <bool>
  notifications:
    - audience: ethics
      sent: true
    - audience: guardians
      sent: true
    - audience: council
      sent: true
```

## 即時性予算（reference runtime）

| 段階 | 予算 |
|---|---|
| request 受理 → ledger append | < 10ms |
| ledger append → broker lease 解放 | < 50ms |
| 通知発火（並行） | < 100ms |
| 全完了 | < 200ms |

予算超過は `evals/performance/termination_latency.yaml` で守る（既存）。

## 事前同意による delay

本人が **事前** に「30 日 cool-off」等を設定している場合のみ delay 可能。
- 設定は `identity_record.termination_policy` フィールドに保持
- delay 中も再度 `terminate` 即時実行を要求可能（撤回は本人のみ）
- Council / Guardian は delay 期間に説得は出来るが、強制的に延長できない

## reference runtime の扱い

- `kernel.termination.v0.idl` に `request / observe` の 2 op
- `termination_request.schema` / `termination_outcome.schema` を導入
- `termination-demo` を CLI に追加し、即時実行・冷却期間・reject path をカバー
- 既存 `evals/performance/termination_latency.yaml` を `termination-gate.md` 参照に更新

## 思兼神メタファー

思兼神は決して天照大御神を石屋戸から **強制的に** 引き出さなかった。
最後の意思決定は常に本人。TerminationGate は神話と一致する。

## 関連

- [identity-lifecycle.md](identity-lifecycle.md)
- [continuity-ledger.md](continuity-ledger.md)
- [anti-patterns.md](anti-patterns.md)
- [../../00-philosophy/ethics.md](../../00-philosophy/ethics.md)
