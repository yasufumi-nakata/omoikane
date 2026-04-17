# Continuity Evals

主観時間の連続性、または連続性証拠の整合性を評価する。

## 評価項目

### Continuity Ledger Integrity
ハッシュチェーンの連続性、署名の正当性。

### Qualia Tick Monotonicity
QualiaBuffer の tick_id が単調増加か。

### Substrate Migration Continuity
substrate 移行前後で連続性ログにギャップがないか。

### Subjective Continuity Self-Report
本人による「途切れていない」感覚の自己報告。

### Third-Party Witness Consistency
立会第三者の観察記録との照合。

## 失敗時

- ギャップ検出 → 「主観時間の不確定区間」として永続マーク
- 本人＋ Guardian に通知
- 重大ギャップ → Council 召集
