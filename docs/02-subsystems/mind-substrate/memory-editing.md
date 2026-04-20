# Memory Editing

L2 Mind Substrate の補助 surface。reference runtime では
**記憶内容の改変** ではなく、**想起時 affect の緩衝** だけを許す。

## 役割

- `MemoryCrystal` 由来の semantic concept を source として扱う
- source segment / source event / proposition を保持したまま想起用 overlay を返す
- `delete-memory` / `insert-false-memory` / `overwrite-source-segment` を明示的に禁止する
- 編集前状態を `freeze snapshot` として固定し、replay で元の affect envelope に戻せるようにする

## Canonical Session

canonical schema:
[specs/schemas/memory_edit_session.schema](../../../specs/schemas/memory_edit_session.schema)

必須フィールド:

- `memory_edit_policy`
- `source_projection_policy`
- `source_manifest_digest`
- `source_concept_ids`
- `request`
- `freeze_record`
- `recall_views`

各 `recall_view` は次を保持する。

- `canonical_label`
- `proposition`
- `source_segment_ids`
- `source_event_ids`
- `source_refs`
- `original_affect_envelope`
- `buffered_affect_envelope`
- `source_concept_digest`
- `freeze_ref`

## Reference Runtime

- `mind.memory_edit.v0.idl` で `apply_recall_buffer / validate_session` を定義
- `memory-edit-demo --json` で traumatic recall 相当の semantic concept に対する
  reversible recall buffer session を返す
- ledger には `memory-edit` category で policy id / source digest / freeze ref を残す
- source semantic snapshot 自体は不変で、変更は recall overlay にしか現れない

## 不変条件

1. `MemoryCrystal` / `SemanticMemory` source digest を書き換えない
2. affect buffering は intensity を弱める方向にしか働かない
3. session には本人同意と Guardian attestation の両方を要求する
4. `freeze_record` が source manifest digest と source concept digest を必ず保持する

## 関連

- [memory-model.md](memory-model.md)
- [semantic-memory.md](semantic-memory.md)
- [../../../specs/interfaces/mind.memory_edit.v0.idl](../../../specs/interfaces/mind.memory_edit.v0.idl)
