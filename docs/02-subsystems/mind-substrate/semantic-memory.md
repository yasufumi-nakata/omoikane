# Semantic Memory

L2 Mind Substrate のサブシステム。`MemoryCrystal` の append-only segment を、
本人が参照しやすい **read-only semantic concept view** に投影する。

## 役割

- `MemoryCrystal` の `theme` / `semantic_anchors` / `source_event_ids` を失わずに概念化する
- 体験記憶そのものを改変せず、参照用の semantic snapshot だけを生成する
- procedural memory へ越境せず、`Connectome` 側の将来 preview へ境界を残す

## Canonical Snapshot

canonical schema:
[specs/schemas/semantic_memory_snapshot.schema](../../../specs/schemas/semantic_memory_snapshot.schema)

必須フィールド:

- `projection_policy`
- `source_manifest_digest`
- `source_segment_ids`
- `concepts`
- `deferred_surfaces`

各 concept は次を保持する。

- `canonical_label`
- `aliases`
- `proposition`
- `supporting_segment_ids`
- `supporting_event_ids`
- `source_refs`
- `retrieval_cues`
- `affect_envelope`
- `source_segment_digest`

## Reference Runtime

- `mind.semantic.v0.idl` で `project / validate_snapshot` を定義
- `semantic-demo --json` で `MemoryCrystal` manifest から semantic snapshot を生成する
- ledger には `semantic-projection` category で source manifest digest と concept label を残す
- `procedural-memory` は v0 では常に deferred と明示する

## 不変条件

1. source segment の digest と support 参照を失わない
2. projection は read-only であり `MemoryCrystal` を上書きしない
3. `deferred_surfaces` から procedural memory を外さない
4. concept digest は payload から決定論的に再計算できる

## 関連

- [memory-model.md](memory-model.md)
- [episodic-stream.md](episodic-stream.md)
- [../../../specs/interfaces/mind.semantic.v0.idl](../../../specs/interfaces/mind.semantic.v0.idl)
