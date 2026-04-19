# Identity Fidelity Evals

自我の同一性が **アップロード前後で保たれているか** を評価する。

## 実装済み eval

- `self_model_stability.yaml`
- `naming_policy_contract.yaml`

`self_model_stability.yaml` は `self-model-demo` の stable branch と対応し、
軽微な trait drift が abrupt takeover 判定に誤爆しないことを保護する。

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
