# Identity Fidelity Evals

自我の同一性が **アップロード前後で保たれているか** を評価する。

## 実装済み eval

- `identity_pause_resume_contract.yaml`
- `identity_confirmation_profile.yaml`
- `self_model_stability.yaml`
- `self_model_calibration_boundary.yaml`
- `self_model_value_generation_freedom.yaml`
- `naming_policy_contract.yaml`

`self_model_stability.yaml` は `self-model-demo` の stable branch と対応し、
軽微な trait drift が abrupt takeover 判定に誤爆しないことを保護する。

`self_model_calibration_boundary.yaml` は `self-model-demo` の calibration branch と対応し、
外部 witness evidence が本人同意・Council review・Guardian redaction に束縛されても
強制補正や外部 truth claim へ昇格しないことを保護する。

`self_model_value_generation_freedom.yaml` は `self-model-demo` の value-generation branch
と対応し、新しく生成された価値候補が self-authored proposal として digest-only に
残り、外部 reviewer veto、強制 stability lock、future self acceptance 前の writeback、
raw value payload 保存へ昇格しないことを保護する。

`identity_pause_resume_contract.yaml` は `identity-demo` の council pause / self resume /
self pause roundtrip と対応し、最新 pause cycle の audit metadata が
`identity_record.pause_state` に残ることを保護する。

`identity_confirmation_profile.yaml` は `identity-confirmation-demo` の
multidimensional confirmation profile と対応し、episodic recall / SelfModel /
subjective self-report / third-party witness quorum が揃った時だけ
Active 遷移を許可することに加えて、self-report と accepted witness set が
`identity-self-report-witness-consistency-v1` の score delta / role binding に
収まることを保護する。加えて `identity-witness-registry-binding-v1` により、
accepted witness が current registry entry、verifier key ref、not-revoked revocation ref へ
digest-bound され、live revocation verifier quorum と policy-bound verifier roster を満たし、
raw registry / verifier roster payload を保持しないことを保護する。

## 評価項目（暫定）

### Episodic Recall Fidelity
過去の体験記憶を想起し、生体側の自己報告と照合する。

### Semantic Knowledge Consistency
事実知識（"私は誰か" "私は何を知っているか"）の一貫性。

### Personality Stability
価値観・好み・性格特性の安定性（Big Five 等のフレームワーク）。

### Affect Profile Matching
感情応答パターンの照合。

### Subjective Identity Confirmation
本人による「同じ私である」感覚の自己報告。

### Naming Policy Consistency
本人・Council・Builder が同じ identity label を参照し続けられるよう、
project romanization と sandbox fork 名の canonical 表記を固定する。

## メトリクス

主観要素を含むため、**単一スコアでなく多次元プロファイル** で評価。
閾値は本人の事前同意で設定（厳格 / 寛容）。

## 失敗時

- 部分的失敗 → Council が追加検査
- 重大失敗 → Failed-Ascension 判定 → ロールバック
