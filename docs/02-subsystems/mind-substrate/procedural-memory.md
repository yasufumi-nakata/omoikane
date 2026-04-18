# Procedural Memory

L2 Mind Substrate のサブシステム。`MemoryCrystal` segment と `Connectome` snapshot を照合し、
暗黙技能へ書き戻す前段の **read-only procedural preview** を生成する。

## 役割

- `MemoryCrystal` の反復 event から connectome へ反映候補を抽出する
- `Connectome` 本体を変更せず、bounded な `weight-delta-preview` のみを返す
- 本適用前に self / council / guardian の承認境界を machine-readable に固定する

## Canonical Snapshot

canonical schema:
[specs/schemas/procedural_memory_preview.schema](../../../specs/schemas/procedural_memory_preview.schema)

必須フィールド:

- `preview_policy`
- `source_manifest_digest`
- `source_segment_ids`
- `connectome_snapshot_id`
- `connectome_snapshot_digest`
- `recommendations`
- `preview_only`
- `deferred_surfaces`

各 recommendation は次を保持する。

- `target_edge_id`
- `target_path`
- `plasticity_rule`
- `proposed_weight_delta`
- `target_weight_after_preview`
- `source_segment_ids`
- `source_event_ids`
- `guardrails`
- `source_segment_digest`

## Reference Runtime

- `mind.procedural.v0.idl` で `project / validate_snapshot` を定義
- `procedural-demo --json` で `MemoryCrystal` manifest と `Connectome` snapshot から preview を生成する
- ledger には `procedural-preview` category で source manifest / connectome digest と target path 一覧を残す
- `weight-application` と `skill-execution` は v0 では deferred のままにする

## 不変条件

1. preview は `Connectome` を直接変更しない
2. `proposed_weight_delta` は `max_weight_delta=0.08` を超えない
3. すべての recommendation は source segment / event の trace を保持する
4. apply path に進む前に self / council / guardian の三者承認が必要

## 関連

- [memory-model.md](memory-model.md)
- [semantic-memory.md](semantic-memory.md)
- [../../../specs/interfaces/mind.procedural.v0.idl](../../../specs/interfaces/mind.procedural.v0.idl)
