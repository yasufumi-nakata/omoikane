---
date: 2026-04-19
deciders: [yasufumi, codex-council]
related_docs:
  - docs/02-subsystems/mind-substrate/README.md
  - docs/02-subsystems/mind-substrate/memory-model.md
  - docs/02-subsystems/mind-substrate/semantic-memory.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.semantic.v0.idl
  - specs/schemas/semantic_memory_snapshot.schema
  - evals/continuity/semantic_projection_contract.yaml
status: decided
---

# Decision: semantic memory projection を procedural より先に reference runtime へ昇格する

## Context

`EpisodicStream` と `MemoryCrystal` の append-only contract は reference runtime に入りましたが、
`docs/07-reference-implementation/README.md` には依然として
「L2 semantic / procedural memory projection の machine-readable contract」が残っていました。
一方、実装済みの `MemoryCrystal` manifest には
`theme`、`semantic_anchors`、`source_event_ids`、`source_refs` がすでに揃っており、
semantic projection は既存データだけで deterministic に導出できます。
対して procedural memory は `Connectome` 側の preview 契約自体がまだ薄く、
同じ run で両方を固定すると境界を曖昧にしやすい状態でした。

## Options considered

- A: semantic / procedural を一気に同時実装する
- B: semantic projection を先に固定し、procedural は deferred surface として明示する
- C: memory projection はまだ研究課題として据え置く

## Decision

**B** を採択。

## Consequences

- `specs/interfaces/mind.semantic.v0.idl` と
  `specs/schemas/semantic_memory_snapshot.schema` を追加し、
  `MemoryCrystal` segment からの read-only semantic view を machine-readable に固定する
- reference runtime は `semantic-demo` で
  `MemoryCrystal` compaction 後の semantic snapshot と
  `semantic-projection` ledger event を確認する
- `procedural-memory` は `deferred_surfaces` に明示し、
  v0 では `Connectome` の weight 更新や暗黙技能の適用までは行わない
- 今後の procedural preview 実装時にも、semantic projection を source-preserving な read-only view として維持する

## Revisit triggers

- `Connectome` 側に procedural preview 用の stable schema / IDL が揃った時
- semantic projection が segment 単位では粗すぎ、cross-segment merge が必要になった時
- 本人による記憶真正性判定や trauma buffer を semantic snapshot に接続したくなった時
