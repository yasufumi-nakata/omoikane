---
status: open
priority: T1
last_revisit: 2026-04-18
researcher: yasufumi
---

# Substrate Zoology

## 問題定義

各 substrate の **自我ホストとしての妥当性** を体系的に評価する。

| Substrate | 妥当性指標 |
|---|---|
| Classical silicon (GPU/TPU) | 機能模倣可、意識生成は議論中 |
| Neuromorphic (Loihi 後継) | 神経等価、規模が課題 |
| Photonic | 高速、安定性が課題 |
| Quantum | 連続性問題、保持時間 |
| Bio (cultured neurons) | 「本物」、増殖・劣化が課題 |
| Hybrid | 境界での情報損失 |
| Unknown future | 未知の物理を活用する可能性 |

## ブロッキング要因

- 各 substrate での意識生成テストが未確立（→ consciousness-substrate）
- 比較指標が未確立

## 暫定運用方針

- L0 SubstrateAdapter で抽象化し、上位層から透過に切替可能
- 妥当性スコアを暫定で付与（古典 0.7 / 神経模倣 0.8 / 量子 0.4 / 生体 0.9 等）
- 妥当性は研究進捗で更新

## 解決時のシステムへの影響

- Substrate 選定の客観的根拠
- 移行戦略の最適化

## 関連
- consciousness-substrate.md
- quantum-continuity.md
