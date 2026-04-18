---
date: 2026-04-18
deciders: [yasufumi, codex-council]
related_docs:
  - docs/02-subsystems/mind-substrate/README.md
  - docs/02-subsystems/mind-substrate/memory-model.md
  - docs/03-protocols/memory-replication.md
  - docs/07-reference-implementation/README.md
  - specs/schemas/memory_crystal_manifest.schema
  - evals/continuity/memory_crystal_compaction.yaml
status: decided
---

# Decision: MemoryCrystal compaction は append-only segment rollup で始める

## Context

`MemoryCrystal` は設計文書に存在していた一方で、reference runtime には
runtime・schema・eval・CLI のいずれも存在せず、
`meta/open-questions.md` でも compaction 戦略が未確定のままでした。
このままでは L2 memory surface が connectome/qualia に比べて薄く、
hourly builder が具体的な未実装ギャップとして前進させにくい状態でした。

## Options considered

- A: compaction は未解決のまま維持し、研究フロンティアへ据え置く
- B: 元イベントを保持した append-only segment rollup を reference runtime の暫定方針として固定する
- C: 削除や再配置を含む aggressive compaction を最初から認める

## Decision

**B** を採択。

## Consequences

- `specs/schemas/memory_crystal_manifest.schema` を canonical schema とする
- reference runtime は `memory-demo` で source event を最大 3 件ずつ segment 化した manifest を生成・検証する
- compaction は `chronological-primary-tag` で束ね、元 event は `source_event_ids` / `source_refs` で必ず追跡可能に残す
- supersede が必要になっても、旧 segment を書き換えず `supersedes` 参照を append する
- continuity eval は `evals/continuity/memory_crystal_compaction.yaml` で append-only と source retention を守る

## Revisit triggers

- MemoryCrystal と EpisodicStream の canonical schema を同時に固定する時
- source event 数や semantic density が `max_source_events_per_segment=3` では不十分になった時
- 暗号化 metadata や trustee replication の都合で manifest shape を広げる必要が出た時
