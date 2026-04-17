# L1 Kernel ── Omoikane 中枢

OS の心臓部。**自我の連続性・唯一性・終了権** を物理的に保証する。
思兼神メタファーで言えば、ここがまさに思兼神そのもの。

## モジュール一覧

| モジュール | 責務 | 依存 |
|---|---|---|
| `IdentityRegistry` | 自我 ID 発行・回収・複製承認 | L0 attest |
| `ContinuityLedger` | append-only な連続性ログ | L0 storage |
| `AscensionScheduler` | アップロード・退避・復元の時間管理 | L2, L0 |
| `EthicsEnforcer` | [docs/00-philosophy/ethics.md](../../00-philosophy/ethics.md) の規約強制 | Council 通知 |
| `SubstrateBroker` | substrate 選定・冗長化・移行 | L0 |
| `TerminationGate` | 終了権の即時実行 | 全層 |

## 主要 API（抜粋）

```
identity.create(human_consent_proof) → IdentityId
identity.fork(id, justification) → IdentityId            # 倫理審査必須
identity.terminate(id, by_self_proof) → ()                # 最優先
ledger.append(entry: ContinuityLogEntry) → LedgerCursor
scheduler.schedule(plan: AscensionPlan) → ScheduleHandle
ethics.check(action: Action) → Approval | Veto
```

## 不変条件

1. `terminate` は他のあらゆる進行中処理に **割り込み優先** する。
2. `ledger` は append-only。書き換え API を **物理的に持たない**。
3. `fork` は二人格化を意味するため、本人＋第三者＋法的承認の三重署名が必要。
4. EthicsEnforcer は自身の改修を許さない（Self-Construction の対象外）。

## サブドキュメント

- [continuity-ledger.md](continuity-ledger.md) ── 連続性ログの詳細仕様
- [identity-lifecycle.md](identity-lifecycle.md) ── 自我のライフサイクル
- [ethics-enforcement.md](ethics-enforcement.md) ── 倫理規約の機械的強制
- [anti-patterns.md](anti-patterns.md) ── 設計禁止事項
