# Episodic Stream

L2 Mind Substrate のサブシステム。体験を **時系列の episodic event** として保持し、
`MemoryCrystal` へ渡す直前の canonical handoff window を固定する。

## 役割

- Qualia / Council / Substrate など複数由来の出来事を substrate-neutral に並べる
- event を削除せず append-only で保持する
- `MemoryCrystal` compaction が受ける source event shape を固定する

## Canonical Event Shape

canonical schema:
[specs/schemas/episodic_event.schema](../../../specs/schemas/episodic_event.schema)

必須フィールド:

- `summary`
- `tags`
- `salience`
- `valence`
- `arousal`
- `source_refs`
- `attention_target`
- `narrative_role`
- `self_coherence`
- `continuity_ref`

`narrative_role` は reference runtime では
`observation | deliberation | resolution | verification | handoff`
の 5 種に固定する。

## Snapshot And Handoff

canonical schema:
[specs/schemas/episodic_stream_snapshot.schema](../../../specs/schemas/episodic_stream_snapshot.schema)

reference runtime は snapshot ごとに:

1. append-only policy
2. `compaction_candidate_ids`
3. `ready_for_compaction`
4. `target_compaction_strategy=append-only-segment-rollup-v1`

を明示し、`MemoryCrystal` へ渡す直前 window を機械可読で固定する。

## Reference Runtime

- `mind.memory.v0.idl` で `append / snapshot / prepare_compaction` を定義
- `episodic-demo --json` で 5 event の reference stream と compaction handoff を確認
- `memory-demo --json` でも same handoff window を使って manifest を生成する

## 不変条件

1. event は削除・上書きしない
2. `continuity_ref` を持たない event は受理しない
3. `source_refs` が空の event は受理しない
4. compaction は最新 window を参照し、event の本文を書き換えない

## 関連

- [memory-model.md](memory-model.md)
- [qualia-buffer.md](qualia-buffer.md)
- [../../../specs/interfaces/mind.memory.v0.idl](../../../specs/interfaces/mind.memory.v0.idl)
