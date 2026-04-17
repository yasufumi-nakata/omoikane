---
status: open
priority: T0
last_revisit: 2026-04-18
researcher: yasufumi
---

# Scan Fidelity

## 問題定義

Connectome を「十分な精度で」スキャンするとは何か。
- 何を測定すべきか（神経構造／重み／動的状態／神経修飾物質濃度／？）
- 解像度はどこまで必要か（μm? nm? Å?）
- 動的情報（スパイクパターン）の測定窓
- 測定誤差が同一性に与える影響

## 既知の進捗

- Electron microscopy による connectome（C. elegans 完全マップ等）
- Expansion microscopy
- Tissue clearing + light sheet microscopy
- 高速 Calcium imaging
- 機械学習による神経追跡

## ブロッキング要因

- 高解像度と広範囲の両立
- 動的状態（神経修飾物質・gene expression）の同時測定
- 破壊的測定 vs 非破壊的測定のトレードオフ
- 全脳スケールでの実用的時間

## 暫定運用方針

- Method A（漸進置換）では一回のフルスキャンを必須としない
- Method B/C を選ぶ本人には「現状のスキャン精度」を明示し、informed consent を強化
- 精度向上の進捗を本ドキュメントで追う

## 解決時のシステムへの影響

- Method C（破壊スキャン）の実用化
- 高精度 Connectome を持つ MemoryCrystal の運用

## 関連
- gradual-replacement.md
- consciousness-substrate.md
