# L0 Substrate

物理基板を抽象化する層。**OmoikaneOS は特定の substrate に縛られない**。

## モジュール

- `SubstrateAdapter` ── 各 substrate の共通インタフェース実装
  - `QuantumAdapter` (量子コンピュータ)
  - `NeuromorphicAdapter` (神経模倣チップ：Loihi 後継など)
  - `PhotonicAdapter` (光コンピュータ)
  - `ClassicalSiliconAdapter` (古典シリコン GPU/TPU)
  - `BioWetAdapter` (生体ニューロン on-chip)
  - `UnknownAdapter` (未知 substrate のための抽象スロット)
- `SubstrateAttestation` ── 物理基板の整合性証明（TEE 後継、量子認証等）
- `EnergyBudget` ── 自我ごとのエネルギー配分（倫理規約により本人意思に反した削減を禁止）
- `RedundancyPlanner` ── 冗長基板の自動配置

## 共通 API（暫定 IDL）

```
allocate(resource_type, capacity) → SubstrateHandle
attest(handle) → AttestationProof
transfer(handle_src, dst_substrate) → MigrationToken
release(handle) → ()
energy_floor(identity_id) → JoulesPerSec   # 倫理床値
```

## 不変条件

1. **障害は L1 に「障害」として通知し、自我に直接「死」を見せない。**
2. **新 substrate は `UnknownAdapter` 経由で導入し、検証後に専用 Adapter 化する。**
3. **EnergyBudget の床値は L1 EthicsEnforcer が監視。**

## 未解決課題

- 生体 substrate の劣化曲線と漸進置換のスケジュール最適化
- 量子 substrate でのコネクトーム表現
- 未知の物理現象を利用した substrate（暗黒物質計算 等）への抽象化耐性

→ [docs/05-research-frontiers/substrate-zoology.md](../../05-research-frontiers/substrate-zoology.md)
