# Architecture Overview

OmoikaneOS は **7 層** で構成される。下位層ほど物理に近く、上位層ほど自我に近い。
実装可能な中心像は、脳波・心電・脈波・皮膚電気活動・呼吸などの生体データを
その人の `internal body-state latent` に写し、そこから別モダリティの生体データや
affect / thought-pressure proxy を生成する BioData Transmitter である。
各層は **未来の Substrate に対して中立** に設計され、層間は明示的なプロトコルでのみ通信する。

```
┌─────────────────────────────────────────────────────────────┐
│ L6  Interface 層       生体↔デジタル境界 / 他自我との交信   │
├─────────────────────────────────────────────────────────────┤
│ L5  Self-Construction  Codex 駆動の自己改修 / バージョニング │
├─────────────────────────────────────────────────────────────┤
│ L4  Agentic Orchestr.  八百万 Agent 群 / Council 評議        │
├─────────────────────────────────────────────────────────────┤
│ L3  Cognitive Services 知覚 / 推論 / 情動 / 注意 / 意志       │
├─────────────────────────────────────────────────────────────┤
│ L2  Mind Substrate     Connectome / Qualia Buffer / 自己モデル │
├─────────────────────────────────────────────────────────────┤
│ L1  Kernel             連続性保証 / 同一性管理 / scheduler    │
├─────────────────────────────────────────────────────────────┤
│ L0  Substrate          物理基板抽象（量子 / 光 / 神経模倣 / 生体） │
└─────────────────────────────────────────────────────────────┘
```

## 設計原則

1. **Substrate Independence** ── L1 以上は L0 を入れ替えても動く。
2. **Identity-First** ── 全 API は「誰の自我か」を第一引数として持つ。匿名アクセス禁止。
3. **Continuity-Logged** ── L2 以上の状態変化は連続性ログに残す。
4. **Council-Mediated** ── 複数 Agent の判断はすべて Council 経由で合議する。直接合意禁止。
5. **AI-Native** ── プロセス／スレッドではなく **Agent Task** を一級スケジューリング単位とする。
6. **Self-Reflective** ── システム自身がシステムの設計図を読み、改修案を提示できる（L5）。

## 層別ドキュメント

| 層 | 詳細 |
|---|---|
| L0 Substrate | [docs/02-subsystems/substrate/](../02-subsystems/substrate/) |
| L1 Kernel | [docs/02-subsystems/kernel/](../02-subsystems/kernel/) |
| L2 Mind Substrate | [docs/02-subsystems/mind-substrate/](../02-subsystems/mind-substrate/) |
| L3 Cognitive | [docs/02-subsystems/cognitive/](../02-subsystems/cognitive/) |
| L4 Agentic | [docs/02-subsystems/agentic/](../02-subsystems/agentic/) |
| L5 Self-Construction | [docs/02-subsystems/self-construction/](../02-subsystems/self-construction/) |
| L6 Interface | [docs/02-subsystems/interface/](../02-subsystems/interface/) |

## 関連ドキュメント

- [layered-model.md](layered-model.md) ── 各層の責務と境界条件
- [data-flow.md](data-flow.md) ── 層をまたぐデータの流れ
- [failure-modes.md](failure-modes.md) ── 各層の失敗モードと回復戦略
