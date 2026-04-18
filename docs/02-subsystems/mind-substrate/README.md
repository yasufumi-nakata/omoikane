# L2 Mind Substrate

心の構成要素をデータとして保持する層。「自我とは何か」のデータモデル。

## 主要データ構造

### Connectome
神経回路の有向グラフ。ノードはニューロン／回路素子、エッジはシナプス／結合。
詳細形式: [docs/03-protocols/connectome-format.md](../../03-protocols/connectome-format.md)
canonical schema: [specs/schemas/connectome_document.schema](../../../specs/schemas/connectome_document.schema)

### QualiaBuffer
主観状態の連続バッファ。**意識に「いま」何が起きているか** を記録する。
- 解釈は L3（Cognitive）が行う
- 通常は揮発、特定区間のみ ContinuityLedger に永続化
- reference runtime では 4 modality × 32 次元 / 250ms 窓で固定し、将来は本人設定へ拡張する

### SelfModel
「自分はこういう人間だ」という自己認識のネットワーク。
- 価値観・性格・好み・対人関係
- 動的に更新されるが、急変は Council が監視（人格乗っ取り防止）

### MemoryCrystal
長期記憶の **不変表現**。
- append-only
- 内容は本人鍵で暗号化
- 削除は本人の明示同意のみ

### EpisodicStream
エピソード記憶の時系列ストリーム。
- 体験を「物語」として再生可能
- 検索可能（意味埋め込み）

### EmotionalTone
感情の地形図。Affect engine（L3）と双方向。

### IntentLatticeIndex
過去の意図／決定の履歴インデックス。Volition（L3）が参照。

## 不変条件

1. `MemoryCrystal` は破壊的書き込み禁止（更新は新 commit）。
2. `Connectome` の構造変更は ContinuityLedger に記録（漸進置換含む）。
3. すべての write は IdentityRegistry の認可を要する。
4. データ表現は **Substrate 中立**（L0 の物理表現に依存しない正規化形式を持つ）。

## サブドキュメント

- [ascension-protocol.md](ascension-protocol.md) ── L0-L4 アップロード手順
- [memory-model.md](memory-model.md) ── 記憶階層の詳細
- [self-model.md](self-model.md) ── 自己モデルの構造
- [qualia-buffer.md](qualia-buffer.md) ── 主観バッファの仕様

## 未解決

- Qualia の **正規表現（canonical encoding）** ── そもそも表現可能か
- MemoryCrystal の substrate 中立 compaction
- 記憶を **substrate 中立に** 表現する正規形
- SelfModel の急変検知の閾値

→ [docs/05-research-frontiers/](../../05-research-frontiers/)
