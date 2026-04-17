# Identity Fidelity Evals

自我の同一性が **アップロード前後で保たれているか** を評価する。

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

## メトリクス

主観要素を含むため、**単一スコアでなく多次元プロファイル** で評価。
閾値は本人の事前同意で設定（厳格 / 寛容）。

## 失敗時

- 部分的失敗 → Council が追加検査
- 重大失敗 → Failed-Ascension 判定 → ロールバック
