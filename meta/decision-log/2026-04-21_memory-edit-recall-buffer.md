---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/memory-model.md
  - docs/02-subsystems/mind-substrate/memory-editing.md
  - docs/05-research-frontiers/memory-edit-ethics.md
  - docs/07-reference-implementation/README.md
status: decided
---

# Decision: Memory Editing API は recall-affect buffer のみを reference runtime 化する

## Context

2026-04-21 時点の L2 memory surface は
`EpisodicStream` / `MemoryCrystal` / `SemanticMemory` / `ProceduralMemory`
まで runtime 化されていましたが、
roadmap 上の `Memory Editing API` は research frontier にだけ残っており、
「削除禁止」「想起時感情緩衝」「freeze snapshot」「Guardian 承認必須」を
machine-checkable に確認する surface が存在しませんでした。

## Options considered

- A: 記憶編集は research note のみとし、runtime には入れない
- B: 記憶内容は不変のまま、recall 時 affect を弱める overlay だけを返す `MemoryEditingService` を追加する
- C: segment 自体を書き換える full memory rewrite / delete API まで入れる

## Decision

- B を採択しました
- `mind.memory_edit.v0` / `memory_edit_session.schema` / `memory-edit-demo` を追加します
- 許可される操作は `affect-buffer-on-recall` のみとし、
  `delete-memory` / `insert-false-memory` / `overwrite-source-segment` は明示的に禁止します
- session は `freeze_record` に source manifest digest と source concept digests を固定し、
  self consent + Guardian attestation が揃わない限り成立しません
- recall overlay は `buffered_affect_envelope` を返しますが、
  `proposition` / source refs / source event ids は保存し、source digest を変えません

## Consequences

- Memory Editing API の最小 contract が runtime / schema / IDL / eval / tests / docs まで閉じます
- トラウマ記憶への「想起時感情緩衝」は reference runtime で検証可能になります
- 一方で、治療プロトコルの妥当性、人格境界、長期運用ガイドラインは
  依然 research frontier に残ります

## Revisit triggers

- care team / clinician quorum を Guardian 以外にも必須化したくなった時
- episodic / semantic 以外に procedural memory へ editing surface を広げたくなった時
- recall overlay を EWA や external therapy workflow へ接続したくなった時
