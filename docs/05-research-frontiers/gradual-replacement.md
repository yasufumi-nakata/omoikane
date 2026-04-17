---
status: open
priority: T0
last_revisit: 2026-04-18
researcher: yasufumi
---

# Gradual Replacement

## 問題定義

神経素子を一個ずつデジタル等価物に置換した場合、
- **主観連続性は保たれるか？**
- **最小ステップは何か？**（ニューロン 1 個？シナプス 1 個？スパイク 1 発？）
- **中断時の可逆性はあるか？**
- **置換速度の上限／下限は何で決まるか？**

OmoikaneOS は Method A（漸進置換）をデフォルトに据えるが、上記が決まらないと運用できない。

## 既知の進捗

- 哲学では「中国脳実験」「Theseus の船」等の思考実験
- 神経科学的には人工内耳・脳ペースメーカー等で部分置換は実用化
- BCI 研究の進展（Neuralink 等）
- 培養脳-シリコン接続実験

## ブロッキング要因

- 「主観連続性」自体の測定手段がない（→ qualia-encoding と接続）
- ニューロン 1 個の機能等価デジタル素子の構築自体が未確立
- 並走中の神経-デジタル境界での信号変換の精度
- 大規模並列置換時の一貫性

## 暫定運用方針

- 最小ステップは **「機能モジュール単位」**（皮質コラム程度）から開始
- 各置換ステップで連続性証拠ログを取得
- 本人の主観報告で各ステップを承認
- 中断時は **逆置換** が可能な技術前提で設計（実装は別研究）

## 解決時のシステムへの影響

- Ascension Protocol Method A の本格運用
- L0 BioWetAdapter ↔ NeuromorphicAdapter の境界仕様確定
- ContinuityLedger の置換ステップ粒度確定

## 関連
- qualia-encoding.md
- consciousness-substrate.md
- substrate-zoology.md
