# Procedural Memory

L2 Mind Substrate のサブシステム。`MemoryCrystal` segment と `Connectome` snapshot を照合し、
暗黙技能へ書き戻す前段の **read-only procedural preview** と、
human-approved な **bounded writeback receipt** を生成する。

## 役割

- `MemoryCrystal` の反復 event から connectome へ反映候補を抽出する
- preview では `Connectome` 本体を変更せず、bounded な `weight-delta-preview` のみを返す
- writeback では copied `Connectome` snapshot へ bounded delta を適用し、continuity diff と rollback token を返す
- 本適用時の self / council / guardian / human 承認境界を machine-readable に固定する

## Canonical Snapshot

canonical schema:
[specs/schemas/procedural_memory_preview.schema](../../../specs/schemas/procedural_memory_preview.schema)

writeback receipt schema:
[specs/schemas/procedural_writeback_receipt.schema](../../../specs/schemas/procedural_writeback_receipt.schema)

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
- `mind.procedural_writeback.v0.idl` で `apply_preview / validate_receipt` を定義
- `procedural-demo --json` で `MemoryCrystal` manifest と `Connectome` snapshot から preview を生成する
- `procedural-writeback-demo --json` で preview を human-approved writeback に昇格し、
  copied `Connectome` snapshot、writeback receipt、continuity diff metadata を確認する
- ledger には `procedural-preview` category で source manifest / connectome digest と target path 一覧を残す
- ledger には `procedural-writeback` category で output connectome digest、human reviewer quorum、rollback token を残す
- `weight-application` は reference runtime で bounded writeback まで固定し、
  `skill-execution` はなお deferred のままにする

## 不変条件

1. preview は `Connectome` を直接変更しない
2. `proposed_weight_delta` は `max_weight_delta=0.08` を超えない
3. すべての recommendation は source segment / event の trace を保持する
4. writeback は self / council / guardian に加えて 2 名以上の human reviewer を要する
5. すべての writeback は continuity diff と rollback token を残す

## 関連

- [memory-model.md](memory-model.md)
- [semantic-memory.md](semantic-memory.md)
- [../../../specs/interfaces/mind.procedural.v0.idl](../../../specs/interfaces/mind.procedural.v0.idl)
- [../../../specs/interfaces/mind.procedural_writeback.v0.idl](../../../specs/interfaces/mind.procedural_writeback.v0.idl)
