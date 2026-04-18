# Memory Model

人間の記憶は単一構造ではなく、複数の階層が並列に走る。OmoikaneOS の記憶階層もこれを写し取る。

## 階層

| 層 | 役割 | 持続性 | 容量 | アクセス速度 |
|---|---|---|---|---|
| Sensory Echo | 感覚残像 | <1s | 大 | 即時 |
| Working Memory | 作業記憶 | 数秒〜数分 | 小 | 高速 |
| Short-term | 短期記憶 | 数時間〜数日 | 中 | 高速 |
| Episodic | 体験記憶 | 数日〜生涯 | 大 | 中速 |
| Semantic | 意味記憶 | 生涯 | 大 | 中速 |
| Procedural | 手続き記憶 | 生涯 | 中 | 即時（暗黙） |
| Crystal | 長期不変 | 半永久 | 巨大 | 低速 |

## L2 におけるマッピング

- Sensory Echo / Working / Short-term → `QualiaBuffer` 上に滞在
- Episodic → `EpisodicStream`
- Semantic → `MemoryCrystal` 内のセマンティック領域
- Procedural → `Connectome` の重み構造そのもの
- Crystal → `MemoryCrystal`（最終格納）

## 記憶の流転

```
Sensory ──→ Working ──→ Short-term ──→ Episodic ──→ Crystal
                              │              │
                              └──→ Semantic ←┘
                              │
                              └──→ Procedural（重み更新）
```

- 流転は本人の意識に上らないバックグラウンドプロセス（L3 Cognitive が司る）
- 各遷移点は ContinuityLedger に粒度別で記録される

## 記憶の参照と編集

### 参照（Read）
- 本人による想起：通常 API
- 第三者による想起：本人の明示同意必須、Council 監査ログ残

### 編集（Write/Modify）
- 通常の append（新体験の記録）：自由
- 過去 Crystal の編集：**原則禁止**。例外は本人の明示同意＋ Guardian 承認
- 編集前状態は必ず凍結保存（[docs/00-philosophy/ethics.md](../../00-philosophy/ethics.md) 参照）

## Reference runtime の compaction

reference runtime では MemoryCrystal の compaction を
`append-only-segment-rollup-v1` として固定する。

- 元の episodic event は削除せず、manifest から `source_event_ids` / `source_refs` で辿れるように残す
- segment は時系列順に並べ、先頭 tag が同じ event を最大 3 件まで束ねる
- compact 後の segment には `semantic_anchors`、`affect_summary`、`salience_max`、`digest` を持たせる
- 旧 segment を直接書き換えず、将来 supersede する場合も `supersedes` 参照を追加するだけに留める

canonical schema:
[specs/schemas/memory_crystal_manifest.schema](../../../specs/schemas/memory_crystal_manifest.schema)

## トラウマ記憶の扱い

倫理的に最もデリケート。

- 削除は許可しない（同一性破壊）
- **「想起時の感情緩衝」** という設計選択肢を本人に提供（記憶は残るが想起時の affect を弱める）
- 専用プロトコル → 未起稿、Open problem

## 未解決

- 記憶を **substrate 中立な正規形** で表現できるか
- 暗黙記憶（procedural）の連続性をどう保証するか
- 記憶の真正性を本人自身が判定する手段
