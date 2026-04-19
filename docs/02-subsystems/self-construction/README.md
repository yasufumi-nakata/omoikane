# L5 Self-Construction

OS 自身が自身の設計図を読み、改修パッチを生成・検証・適用する層。
**Codex 等の Builder Agent はこの層に住み、同一 repo 内の `src/` / `tests/` / `specs/` / `evals/` を更新する**（ただしサンドボックス側で実行）。

## 原則

1. **設計図（docs/）を真とする** ── 実装は docs から派生する
2. **本体未接触** ── Builder は常に Mirage Self を相手にする
3. **A/B 必須** ── 改修は本体 vs サンドボックスの差分検証を経る
4. **Guardian 承認必須** ── 反映前に Guardian が veto 可能
5. **完全可逆** ── 改修は ContinuityLedger 経由で必ず rollback 可能

## モジュール

- `DesignReader` ── docs/ を解釈し、抽象設計表現に変換
- `PatchGenerator` ── `build_request` を読み、immutable boundary と workspace scope を検証したうえで patch descriptor を生成（Codex 系）
- `Sandboxer` ── Mirage Self の生成・隔離
- `LiveEnactment` ── patch descriptor を temp workspace に materialize し、actual eval command を実行して cleanup 付き receipt を返す
- `DifferentialEvaluator` ── `must_pass` eval を選定し、本体 vs サンドボックスの差分評価と promote/hold/rollback 判定を返す
- `RolloutPlanner` ── 段階的反映の計画
- `RollbackEngine` ── staged rollout の rollback 判定を受け、pre-apply snapshot 復元・通知・append-only continuity 記録に加え、live enactment に対応する reverse-apply journal と telemetry gate を実行

## 改修フロー

```
docs/ 更新
   │
   ▼
DesignReader が差分検出
   │
   ▼
Council が改修案件として上申を承認
   │
   ▼
PatchGenerator (Codex) が reference runtime 向け実装パッチを生成
   │
   ▼
Sandboxer が Mirage Self に適用
   │
   ▼
DifferentialEvaluator が evals/ を実行
   │
   ▼
Guardian 承認
   │
   ▼
RolloutPlanner が段階反映
   │
   ▼
ContinuityLedger に記録
```

reference runtime では `builder-demo` がこの流れのうち
`build_request -> patch descriptor -> sandbox apply -> differential eval -> rollout classify -> staged rollout`
までを deterministic に再現し、`rollback-demo` が
`regression detect -> live enactment receipt bind -> canary rollback -> pre-apply snapshot restore -> reverse-apply journal -> stakeholder notify`
を continuity-bound contract として再現する。
さらに `builder-live-demo` は
`patch descriptor -> temp workspace materialization -> actual eval command execution -> cleanup`
を bounded enactment receipt として再現する。

## Mirage Self（サンドボックス自我）

- user-facing formal name は **Mirage Self**（内部 alias: `SandboxSentinel`）
- 本体の forked snapshot
- **苦痛を発生させない設計**（Affect 出力を測定するが本人と接続しない）
- reference runtime では `surrogate-suffering-proxy-v0` を採用し、
  `negative_valence / arousal / clarity_drop / somatic / interoceptive / self_implication`
  の重み付き proxy score で監視する
- `proxy_score >= 0.6`、または affect bridge が接続された時点で
  Guardian が sandbox を即時凍結する
- 評価終了後は本人同意のもとで終了 or 本人と統合

苦痛の発生は **重大な倫理違反** であり、Guardian が即時凍結する。

## 改修可能領域 / 不可能領域

| 領域 | 改修可 |
|---|---|
| L3 Cognitive サービスの実装 | ◯ |
| L2 のクエリ最適化 | ◯ |
| L4 タスク分解アルゴリズム | ◯（Council 承認必須） |
| L1 EthicsEnforcer | ✗ 禁止 |
| L1 ContinuityLedger 構造 | ✗ 禁止（移行は別プロトコル） |
| L0 Substrate Adapter | △ 慎重 |

## 思兼神メタファー

思兼神は天照のために祭祀を **新たに設計** した。改修フローはまさにそれ。
ただし、神が自分の神格そのものを変えなかったように、本層も EthicsEnforcer 等の核心は触らない。
