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

semantic handoff schema:
[specs/schemas/semantic_procedural_handoff.schema](../../../specs/schemas/semantic_procedural_handoff.schema)

writeback receipt schema:
[specs/schemas/procedural_writeback_receipt.schema](../../../specs/schemas/procedural_writeback_receipt.schema)

skill execution receipt schema:
[specs/schemas/procedural_skill_execution.schema](../../../specs/schemas/procedural_skill_execution.schema)

skill enactment session schema:
[specs/schemas/procedural_skill_enactment_session.schema](../../../specs/schemas/procedural_skill_enactment_session.schema)

procedural actuation bridge schema:
[specs/schemas/procedural_actuation_bridge_session.schema](../../../specs/schemas/procedural_actuation_bridge_session.schema)

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

- `mind.procedural.v0.idl` で `project / project_from_handoff / validate_snapshot` を定義
- `mind.procedural_writeback.v0.idl` で `apply_preview / validate_receipt` を定義
- `mind.skill_execution.v0.idl` で `execute / validate_receipt` を定義
- `mind.skill_enactment.v0.idl` で `execute / validate_session` を定義
- `mind.procedural_actuation.v0.idl` で `authorize_bridge / validate_bridge` を定義
- `procedural-demo --json` で `semantic_procedural_handoff` を消費しつつ
  `MemoryCrystal` manifest と `Connectome` snapshot から preview を生成する
- `procedural-writeback-demo --json` で preview を human-approved writeback に昇格し、
  copied `Connectome` snapshot、writeback receipt、continuity diff metadata を確認する
- `procedural-skill-demo --json` で writeback 後の selected recommendation を
  guardian witness 付き sandbox rehearsal へ昇格し、
  `skill-execution` receipt、sandbox evidence ref、rollback token carryover を確認する
- `procedural-enactment-demo --json` で `skill-execution` receipt を temp workspace に materialize し、
  actual command receipt、cleanup、rollback token carryover を確認する
- `procedural-actuation-demo --json` で passed / cleaned-up な
  `procedural_skill_enactment_session` を EWA の
  `external_actuation_authorization` と approved command audit に
  digest-bound で接続し、raw instruction text を保持せずに
  PLC / firmware stop-signal adapter receipt / legal execution /
  Guardian oversight gate / rollback token を確認する
- ledger には `procedural-preview` category で source manifest / connectome digest と target path 一覧を残す
- ledger には `procedural-writeback` category で output connectome digest、human reviewer quorum、rollback token を残す
- ledger には `procedural-execution` category で executed skill label、sandbox session、rollback token を残す
- ledger には `procedural-enactment` category で materialized skill count、command receipt、cleanup status、rollback token を残す
- ledger には `procedural-actuation-bridge` category で source enactment digest、
  EWA authorization digest、command id、delivery scope、rollback token を残す
- `weight-application` は reference runtime で bounded writeback まで固定し、
  `skill-execution` と `skill-enactment` も sandbox-only / no external actuation の範囲で固定する
- external actuation へ接続する場合は `mind.procedural_actuation.v0` の
  bridge receipt を介し、`interface.ewa.v0` の
  `external_actuation_authorization` artifact、guardian-reviewed jurisdiction evidence、
  stop-signal adapter receipt binding、command digest binding、raw instruction redaction を満たす必要がある

## 不変条件

1. preview は `Connectome` を直接変更しない
2. `proposed_weight_delta` は `max_weight_delta=0.08` を超えない
3. すべての recommendation は source segment / event の trace を保持する
4. writeback は self / council / guardian に加えて 2 名以上の human reviewer を要する
5. すべての writeback は continuity diff と rollback token を残す
6. skill execution は guardian witness 付き sandbox-only rehearsal に限り、external actuation を禁止する
7. skill enactment は temp workspace cleanup と actual command receipt を必須とし、external actuation を禁止する
8. procedural actuation bridge は passed enactment と EWA authorization / approved command / stop-signal adapter receipt の digest が一致する場合だけ成立する

## 関連

- [memory-model.md](memory-model.md)
- [semantic-memory.md](semantic-memory.md)
- [../../../specs/interfaces/mind.procedural.v0.idl](../../../specs/interfaces/mind.procedural.v0.idl)
- [../../../specs/interfaces/mind.procedural_writeback.v0.idl](../../../specs/interfaces/mind.procedural_writeback.v0.idl)
- [../../../specs/interfaces/mind.skill_execution.v0.idl](../../../specs/interfaces/mind.skill_execution.v0.idl)
- [../../../specs/interfaces/mind.skill_enactment.v0.idl](../../../specs/interfaces/mind.skill_enactment.v0.idl)
- [../../../specs/interfaces/mind.procedural_actuation.v0.idl](../../../specs/interfaces/mind.procedural_actuation.v0.idl)
