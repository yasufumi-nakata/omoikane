---
status: open
priority: T2
last_revisit: 2026-04-25
researcher: yasufumi
---

# Sustainable Economy

## 問題定義

アップロードされた自我の **計算資源コスト** をどう持続的に賄うか。

- 自我 1 体あたり要する計算資源・エネルギー
- 本人の労働（デジタルでも可能か）
- 社会保障・年金との接続
- AP-1（経済的圧力で意識が薄れる）の禁止と財源確保の両立
- 数十億体規模での持続可能性

## 既知の進捗

- 暗号通貨・分散経済の知見
- ベーシックインカム議論
- エネルギー革新（核融合・再生可能エネルギー）
- reference runtime では `kernel.energy_budget.v0` が AP-1 の機械境界として
  `EnergyFloor` 未満の requested budget を拒否し、below-floor capacity を
  SubstrateBroker の standby 退避 signal に束縛する
- multi-identity pool の reference runtime では、合算 requested budget が total floor を
  覆っていても pressured identity の below-floor request を別 identity の surplus で
  相殺しない `energy_budget_pool_receipt` を固定した

## ブロッキング要因

- 計算資源コストの実数値が未確定（substrate に依存）
- 経済システム全般の不確実性
- multi-identity pool の外部財源配分・社会制度上の優先順位は未確定

## 暫定運用方針

- EnergyBudget の床値を倫理規約で固定
- 床値以下にはどんな経済状況でも下げない
- pool 集約時も per-identity floor を先に検証し、cross-identity offset は許可しない
- 外部財源・請求・広告条件の raw payload は runtime receipt に保存せず、
  context ref と digest だけに縮約する
- 持続のための経済設計は **OS 外** で議論

## 解決時のシステムへの影響

- EnergyBudget 床値の確定
- スケーリング戦略

## 関連
- ethics.md
- anti-patterns.md
