# Semantic Memory

L2 Mind Substrate のサブシステム。`MemoryCrystal` の append-only segment を、
本人が参照しやすい **read-only semantic concept view** に投影する。

## 役割

- `MemoryCrystal` の `theme` / `semantic_anchors` / `source_event_ids` を失わずに概念化する
- 体験記憶そのものを改変せず、参照用の semantic snapshot だけを生成する
- procedural memory へ越境実行せず、validated `Connectome` snapshot に束縛された
  digest-bound handoff だけを準備する

## Canonical Snapshot

canonical schema:
[specs/schemas/semantic_memory_snapshot.schema](../../../specs/schemas/semantic_memory_snapshot.schema)

semantic handoff schema:
[specs/schemas/semantic_procedural_handoff.schema](../../../specs/schemas/semantic_procedural_handoff.schema)

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

- `mind.semantic.v0.idl` で
  `project / prepare_procedural_handoff / validate_snapshot / validate_procedural_handoff`
  を定義
- `semantic-demo --json` で `MemoryCrystal` manifest から semantic snapshot を生成し、
  validated `Connectome` snapshot に束縛された `semantic_procedural_handoff` を返す
- ledger には `semantic-projection` category で source manifest digest と concept label を残す
- ledger には `semantic-handoff` category で handoff digest と target namespace を残す
- `procedural-memory` は snapshot contract 上では v0 の deferred surface として明示する

## 不変条件

1. source segment の digest と support 参照を失わない
2. projection は read-only であり `MemoryCrystal` を上書きしない
3. `deferred_surfaces` から procedural memory を外さない
4. concept digest は payload から決定論的に再計算できる
5. handoff は validated `Connectome` snapshot と target namespace を digest-bound に固定する

## 関連

- [memory-model.md](memory-model.md)
- [episodic-stream.md](episodic-stream.md)
- [../../../specs/interfaces/mind.semantic.v0.idl](../../../specs/interfaces/mind.semantic.v0.idl)
