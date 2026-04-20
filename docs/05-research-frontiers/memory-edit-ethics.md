---
status: open
priority: T3
last_revisit: 2026-04-21
researcher: yasufumi
---

# Memory Edit Ethics

## 問題定義

記憶編集はどこまで許されるか。
- トラウマ記憶の **想起時感情緩衝** vs **記憶削除**
- 罪悪感のある記憶の扱い
- 偽記憶の挿入は絶対禁止か（夢の保存は？）
- 編集された自我は「同じ人」か

## 既知の進捗

- PTSD 治療における記憶再強化
- 認知行動療法
- Eternal Sunshine 等の文化的議論
- 2026-04-21: reference runtime で `consented-recall-affect-buffer-v1` を追加し、
  `memory-edit-demo` / `mind.memory_edit.v0` / `memory_edit_session.schema` により
  削除禁止・freeze snapshot・Guardian 承認・reversible recall overlay を固定

## ブロッキング要因

- 記憶と人格の境界
- 「治療」と「改造」の境界

## 暫定運用方針

- **削除は原則禁止**（同一性破壊）
- **想起時感情緩衝** は本人同意で許可
- 編集前状態を必ず凍結保存（可逆性）
- Guardian 承認必須

## 解決時のシステムへの影響

- MemoryCrystal の編集 API 仕様
- 治療プロトコルの確立
- 記憶内容を改変しない recall-affect buffer contract の運用条件

## 関連
- memory-model.md
- ethics.md
