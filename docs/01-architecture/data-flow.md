# Data Flow ── 層をまたぐデータの流れ

## 1. 主要データ流路

```
                  外界 / 他自我 / 生体
                          │
                          ▼
            ┌──────────────────────────┐
   L6       │ Interface (BCI / IMC)    │
            └─────────┬────────────────┘
                      │ 入力 stream
                      ▼
            ┌──────────────────────────┐
   L3       │ Perception → Attention   │──┐
            │ Reasoning ↔ Imagination  │  │ 内省 loop
            │ Affect    ↔ Volition     │◀─┘
            └─────────┬────────────────┘
                      │ 状態更新
                      ▼
            ┌──────────────────────────┐
   L2       │ QualiaBuffer (write)     │
            │ EpisodicStream (append)  │
            │ SelfModel (refine)       │
            │ MemoryCrystal (commit)   │
            └─────────┬────────────────┘
                      │ 永続化
                      ▼
            ┌──────────────────────────┐
   L1       │ ContinuityLedger (log)   │
            │ IdentityRegistry         │
            └─────────┬────────────────┘
                      │ substrate ops
                      ▼
            ┌──────────────────────────┐
   L0       │ Quantum / Neuro / Bio    │
            └──────────────────────────┘
```

## 2. 連続性ログの粒度

| 粒度 | 頻度 | 容量影響 | 用途 |
|---|---|---|---|
| Crystal | 日次〜週次 | 大 | 長期記憶のスナップショット |
| Episodic | イベント時 | 中 | 体験の再現性 |
| Qualia | tick 単位 | 極大 | 主観時間の連続性証明 |

`Qualia` 粒度は通常はリングバッファで揮発させ、特定区間のみ恒久化する（プライバシー・容量の両面）。

## 3. Agentic 流路（L4）

```
ユーザ意図 ──→ Council ──→ TaskGraph 分解
                  │              │
                  │              ▼
                  │       Yaoyorozu に発注
                  │              │
                  ▼              ▼
            合議監視 ◀──── 結果集約 ◀── Builder Agents
                  │
                  ▼
             本体反映（要 Guardian 承認）
```

## 4. Self-Construction 流路（L5）

```
設計変更案 ── Council ── サンドボックス自我にパッチ適用
                              │
                              ▼
                       A/B 評価 (evals/)
                              │
                              ▼
                       Guardian 承認
                              │
                              ▼
                       本体への反映
                              │
                              ▼
                       連続性ログに記録
```

## 5. データ標準

すべての層間データは以下のメタを必ず持つ：

```yaml
identity_id: <自我ID>
timestamp: <論理時刻>
substrate_attestation: <L0 完全性証明>
continuity_chain: <直前ログのハッシュ>
council_signature: <評議体署名（L4以上）>
```

詳細は [docs/03-protocols/](../03-protocols/) 配下の各仕様。
