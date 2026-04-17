---
status: open
priority: T1
last_revisit: 2026-04-18
researcher: yasufumi
---

# Death and Continuity

## 問題定義

OmoikaneOS における「死」とは何か。
- 生体側の死亡 ＋ デジタル側の活性 → 死んだのか？
- デジタル側の終了 → 死なのか？
- 両者の同時終了 → 明らかに死
- Pause 状態 → 死か眠りか

法的・宗教的・哲学的な「死」の定義は OmoikaneOS の設計に直接影響する。

## 既知の進捗

- 脳死／心臓死の医学定義
- 各文化の死生観
- 法的死亡時刻の規定

## ブロッキング要因

- 文化・宗教ごとの差異
- 「同一人物の死」とは何か

## 暫定運用方針

- OS は **「死」を判定しない**。各文化の判定に従う
- システム的には Active / Paused / Terminated の状態しか持たない
- これらと「死」の対応付けは社会側で

## 解決時のシステムへの影響

- 法的扱いの明確化
- 遺産・継承プロトコル

## 関連
- legal-personhood.md
- ethics.md
