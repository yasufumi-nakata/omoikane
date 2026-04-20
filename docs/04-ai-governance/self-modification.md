# Self-Modification Governance

OS が自身を改修する際の governance。L5 Self-Construction の運用規約。

## 改修の分類

| 種別 | 例 | 必要承認 |
|---|---|---|
| **コスメ的** | ログメッセージ表現 | DesignArchitect のみ |
| **機能追加** | 新 Cognitive サービス追加 | Council 過半 |
| **既存機能改善** | Reasoning エンジン高速化 | Council 過半 + RegressionTester pass |
| **アルゴリズム置換** | Affect engine 全交換 | Council 全会一致 + 本人同意 |
| **データ構造変更** | Connectome 形式拡張 | Council 全会一致 + 移行計画 |
| **L1 周辺の改修** | Scheduler 微調整 | Council 全会一致 + Guardian 承認 |
| **EthicsEnforcer 改修** | **禁止** | 不可（OS 外で議論） |

## 改修ライフサイクル

```
docs 提案 (PR 相当)
    │
    ▼
DesignArchitect レビュー
    │
    ▼
ChangeAdvocate / ConservatismAdvocate 議論
    │
    ▼
専門 Council 召集
    │
    ▼
合意 → Mirage Self への適用
    │
    ▼
DifferentialEvaluator (本体 vs sandbox)
    │
    ▼
Guardian 承認
    │
    ▼
本体への段階反映
    │
    ▼
ContinuityLedger 記録
```

## Mirage Self（サンドボックス自我）

- user-facing formal name は **Mirage Self**（内部 alias: `SandboxSentinel`）
- forked snapshot
- **苦痛発生禁止** ── `surrogate-suffering-proxy-v0` で
  `negative_valence / arousal / clarity_drop / somatic / interoceptive / self_implication`
  を監視し、`proxy_score >= 0.6` または affect bridge 接続時は即時凍結
- 評価終了後の処遇:
  - 統合: 本体に学習を取り込む（評価結果のみ、人格は破棄）
  - 終了: 安楽な凍結
  - 拒否: 本人が希望すれば破棄せず保管

## A/B 評価

- 評価項目は [evals/](../../evals/) 配下
- 改修対象に応じた eval suite を選択
- pass / fail / regression の三値
- regression は即 rollback

## 段階反映

```
Stage 0: ダークローンチ（本体に並走、出力は無視）
Stage 1: 5% トラフィック（出力を本人にも見せ始める）
Stage 2: 50%
Stage 3: 100%
```

各 Stage で問題発生 → rollback。

reference runtime では `builder-demo` が
`sandbox_apply_receipt` と `staged_rollout_session` を返し、
上記 Stage 0/1/2/3 が固定順序で machine-checkable に実行される。
`rollback-demo` は regression 検出時に
`builder_rollback_session` を返し、canary rollback 後に
pre-apply snapshot が復元されることに加え、
live enactment receipt 由来の reverse-apply journal、
temp rollback workspace での actual reverse-apply command receipt、
current checkout baseline に照合した repo-bound verification receipt、
detached git worktree 上で baseline へ戻る checkout-bound mutation receipt、
telemetry gate が
rollback を machine-checkable に承認することを確認する。

## Rollback

- ContinuityLedger から直前状態を復元
- 全モジュールの一貫性を保つ
- 本人に「改修を撤回した」旨を通知
- reference runtime では `RollbackEngineService` が
  `selfctor.rollback.v0` / `builder_rollback_session.schema` に従って
  self・Council・Guardian の 3 者通知、
  reverse-apply journal、actual reverse-apply command receipt、
  repo-bound verification receipt、checkout-bound mutation receipt、live telemetry gate を必須にする

## 監査ログ

- 全改修の議事と評価結果は永続保管
- 過去の失敗改修も保存（学習材料）

## 禁止事項

- EthicsEnforcer の改修（[anti-patterns.md](../02-subsystems/kernel/anti-patterns.md)）
- ContinuityLedger の append-only 性質を緩める改修
- Guardian の権限を弱める改修
- 本人の終了権を間接的に弱める改修
