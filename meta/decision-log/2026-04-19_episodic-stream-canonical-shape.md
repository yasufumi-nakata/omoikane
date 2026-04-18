---
date: 2026-04-19
deciders: [yasufumi, codex-council]
related_docs:
  - docs/02-subsystems/mind-substrate/README.md
  - docs/02-subsystems/mind-substrate/episodic-stream.md
  - docs/02-subsystems/mind-substrate/memory-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.memory.v0.idl
  - specs/schemas/episodic_event.schema
  - specs/schemas/episodic_stream_snapshot.schema
  - evals/continuity/episodic_stream_handoff.yaml
status: decided
---

# Decision: EpisodicStream の canonical shape を固定して MemoryCrystal handoff を実装する

## Context

`MemoryCrystal` compaction 自体は reference runtime に入った一方で、
その入力となる `EpisodicStream` は docs 上の概念に留まり、
canonical event shape・IDL・CLI・eval・handoff window が未整備でした。
このままでは L2 memory surface が
「圧縮後の manifest はあるが、何をどう流し込むかは未定」という
中途半端な状態のままでした。

## Options considered

- A: `EpisodicStream` は research frontier のまま据え置き、`MemoryCrystal` だけを reference runtime とする
- B: append-only episodic stream の canonical event shape と compaction handoff window を reference runtime に昇格する
- C: semantic / procedural まで含む L2 全面の memory contract を一気に固定する

## Decision

**B** を採択。

## Consequences

- `specs/schemas/episodic_event.schema` と `episodic_stream_snapshot.schema` を canonical schema とする
- `specs/interfaces/mind.memory.v0.idl` で `append / snapshot / prepare_compaction` を固定する
- reference runtime は `episodic-demo` で append-only snapshot と `MemoryCrystal` handoff を確認する
- `memory-demo` も static source list ではなく `EpisodicStream` handoff window を入力に使う
- continuity eval は `evals/continuity/episodic_stream_handoff.yaml` で snapshot と manifest の両方を守る

## Revisit triggers

- semantic memory projection を独立 schema / service として固定する時
- procedural memory や connectome update を episodic event へ正規流入させる時
- event 数や narrative role が `5 event handoff window` では不足すると判明した時
