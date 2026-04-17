---
status: open
priority: T1
last_revisit: 2026-04-18
researcher: yasufumi
---

# Long-Term Storage

## 問題定義

100 年・1000 年・10000 年スケールで MemoryCrystal を保管できるメディアは何か。
ビット腐敗、メディア劣化、フォーマット陳腐化に対抗する方法は。

## 既知の進捗

- 5D 光学ガラス (University of Southampton)
- DNA storage
- 石英ガラス (Microsoft Project Silica)
- 中性子捕獲書込み（理論）
- 月面・地球軌道アーカイブ構想

## ブロッキング要因

- 容量と耐久性のトレードオフ
- 読み出しデバイスの陳腐化（フォーマットが残っても読めない）
- コスト

## 暫定運用方針

- 多メディア併用（一種の劣化に他種で対抗）
- 定期的な再書き込み（migration）
- フォーマット定義そのものを共に保管（self-describing media）
- 月面・地球軌道分散保管の検討

## 解決時のシステムへの影響

- Ascension の保証期間が事実上無限化
- 「不死」の物理的根拠が強化

## 関連
- memory-replication.md
- substrate-zoology.md
