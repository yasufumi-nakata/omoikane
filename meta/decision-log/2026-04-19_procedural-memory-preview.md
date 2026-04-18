---
date: 2026-04-19
deciders: [yasufumi, codex-council]
related_docs:
  - docs/02-subsystems/mind-substrate/README.md
  - docs/02-subsystems/mind-substrate/memory-model.md
  - docs/02-subsystems/mind-substrate/procedural-memory.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.procedural.v0.idl
  - specs/schemas/procedural_memory_preview.schema
  - evals/continuity/procedural_preview_contract.yaml
status: decided
---

# Decision: procedural memory は apply 前の connectome-coupled preview から reference runtime へ昇格する

## Context

`semantic-demo` により `MemoryCrystal` からの read-only semantic view は固定できましたが、
`docs/07-reference-implementation/README.md` にはなお
「L2 procedural memory projection と connectome-coupled preview contract」が残っていました。
一方で reference runtime には `ConnectomeDocument` と `MemoryCrystal` manifest がすでにあり、
両者を突き合わせた bounded な preview なら destructive write を入れずに機械可読化できます。
直接 apply path まで入れると consent / oversight / continuity diff の境界が急に広がるため、
まず preview-only contract を切り出すのが安全でした。

## Options considered

- A: procedural memory も即座に connectome write まで実装する
- B: procedural memory は preview-only contract として昇格し、apply path は deferred に残す
- C: procedural memory は引き続き設計メモだけに留める

## Decision

**B** を採択。

## Consequences

- `specs/interfaces/mind.procedural.v0.idl` と
  `specs/schemas/procedural_memory_preview.schema` を追加し、
  `MemoryCrystal` segment と `Connectome` snapshot から
  `weight-delta-preview` を導く contract を固定する
- reference runtime は `procedural-demo` で
  `crystal-commit` 後の manifest、`Connectome` snapshot、
  `procedural-preview` ledger event をまとめて確認する
- preview 自体は read-only に留め、
  `weight-application` と `skill-execution` は deferred surface として残す
- 将来 apply path を追加する時も、
  self / council / guardian 三者承認と continuity diff 記録を前提にできる

## Revisit triggers

- preview だけでは不足で、human-approved writeback contract を昇格したくなった時
- `Connectome` の対象 edge 選定が segment ごと preview では粗すぎる時
- procedural memory を qualia / self-model / affect 系の runtime と横断統合したくなった時
