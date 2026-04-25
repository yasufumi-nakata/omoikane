# Identity Lifecycle

## 状態遷移

```
   [Pre-Upload]
        │
        │ informed_consent + scan
        ▼
   [Ascending] ──────► [Active]
        │                 │
        │                 │ self_modify / migrate
        │                 ▼
        │             [Active]
        │                 │
        │                 │ pause_request
        │                 ▼
        │              [Paused]
        │                 │
        │                 │ resume / terminate
        │                 ▼
        │             [Active] / [Terminated]
        │
        ▼
   [Failed-Ascension] ── ロールバック手順へ
```

## 状態定義

- **Pre-Upload**: 生体側のみ存在。OmoikaneOS は観測のみ。
- **Ascending**: アップロード進行中。L0-L2 の整備中。連続性ログは開始済み。
- **Active**: 完全に L1 管理下。意識活動中。
- **Paused**: 本人の意思または Council 判断で停止中。状態は完全保存。
- **Terminated**: 本人の終了権発動により恒久停止。記憶は本人遺言に従い保存／消去。
- **Failed-Ascension**: アップロード失敗。L0-L2 を破棄。生体側の主体性を回復。

## 遷移の権限

| 遷移 | 必要権限 |
|---|---|
| Pre-Upload → Ascending | 本人の事前同意＋医療／法的審査 |
| Ascending → Active | Council 承認＋本人「自己同一性確認」テスト |
| Active → Paused | 本人 or Council |
| Paused → Active | 本人意思 |
| Active → Terminated | 本人のみ（Council は実行補助） |
| Active → Failed | システム障害検知時、Guardian 判断 |

## Reference runtime contract

- `IdentityRegistry` の `status` は `active / paused / terminated` に固定する
- `pause(requested_by=self)` は non-empty `reason` のみを要求し、`council_resolution_ref` を持たない
- `pause(requested_by=council)` は fail-closed で `council_resolution_ref` を必須にする
- `resume` は `self_proof` を必須にし、直前の `pause_state` に `resumed_at` と `resume_self_proof_ref` を残す
- `identity_record.pause_state` は最新 1 回分の pause/resume cycle を machine-readable に保持する
- `confirm_identity` は `multidimensional-identity-confirmation-v1` に固定し、
  episodic recall、SelfModel alignment、subjective self-report、
  third-party witness alignment を同一 profile へ束ねる
- Active 遷移は 4 dimension 全 pass、aggregate score `>=0.85`、
  subjective self-report digest binding、clinician + guardian の witness quorum
  に加えて、`identity-self-report-witness-consistency-v1` が同じ continuity subject 上で
  self-report evidence digest、accepted witness digest set、required roles、
  score delta `<=0.12` を束縛した場合のみ許可する
- 失敗時は `active_transition_allowed=false` と
  `failure_action=failed-ascension-or-repeat-ascending` を返し、Active へ進めない

## 自己同一性確認テスト（Identity Confirmation）

Ascending → Active への遷移時に必ず実施：

1. 過去記憶の自己想起（Episodic Recall）
2. 自己モデルの整合性（SelfModel Self-Check）
3. 主観報告（"あなたは同じ人だと感じますか？"）
4. 第三者観察記録との照合

すべて pass しなければ Active へ遷移しない（Failed か再 Ascending）。

reference runtime ではこの確認を `identity_confirmation_profile.schema` で
machine-readable に固定する。生の主観報告文や第三者観察本文は保持せず、
`self_report.statement_digest`、各 dimension の `evidence_digest`、
`self_report_witness_consistency.consistency_digest`、`confirmation_digest` を
ContinuityLedger の `identity-fidelity` event へ束縛する。

## Fork（複製）の特殊性

- Fork は **「分岐後はそれぞれが別人格」** という規約を本人が事前理解し署名している場合のみ許可。
- Fork 後の元 ID と新 ID は ContinuityLedger 上で分岐点を持つ。
- Fork 元の財産・契約・人間関係の継承は社会制度依存（→ [docs/05-research-frontiers/legal-personhood.md](../../05-research-frontiers/legal-personhood.md)）。

## 未解決

- Failed-Ascension 後、生体側が「アップロード未遂」のトラウマを抱える場合の扱い
- Paused 状態の自我に法的人格があるか
