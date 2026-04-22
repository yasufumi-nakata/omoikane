---
date: 2026-04-23
deciders: [yasufumi, codex-council]
related_docs:
  - docs/02-subsystems/mind-substrate/semantic-memory.md
  - docs/02-subsystems/mind-substrate/procedural-memory.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.semantic.v0.idl
  - specs/interfaces/mind.procedural.v0.idl
  - specs/schemas/semantic_procedural_handoff.schema
  - evals/continuity/semantic_procedural_handoff.yaml
status: decided
---

# Decision: semantic projection と procedural preview を digest-bound handoff で接続する

## Context

2026-04-19 時点では `semantic-demo` を先行させ、
`procedural-memory` は `deferred_surfaces` に残す方針を採りました。
その後、`mind.procedural.v0`、`procedural_memory_preview.schema`、
`procedural-writeback` / `skill-execution` / `skill-enactment` の
reference runtime が揃い、procedural 側には stable schema / IDL / eval が存在します。
一方で semantic 側は依然として `procedural-memory` を deferred と書くだけで、
downstream procedural preview へ渡す machine-checkable bridge artifact を持っていませんでした。

## Options considered

- A: semantic snapshot の deferred 表現を維持し、bridge artifact は持たせない
- B: semantic snapshot は read-only / deferred のまま維持しつつ、
  validated `Connectome` snapshot に束縛された handoff artifact を追加する
- C: semantic snapshot 自体を procedural preview payload へ統合し、境界を消す

## Decision

**B** を採択。

## Consequences

- `semantic_procedural_handoff.schema` を追加し、
  `mind.semantic.v0` が `prepare_procedural_handoff` /
  `validate_procedural_handoff` を持つようにします
- `mind.procedural.v0` は `project_from_handoff` を持ち、
  handoff の manifest/connectome digest を検証してから
  既存 preview contract へ入るようにします
- `semantic-demo` は read-only semantic snapshot に加え、
  `semantic-handoff` ledger event を返すようになります
- `procedural-demo` は semantic handoff を実際に消費し、
  preview policy との target policy alignment を同じ run で確認します
- semantic snapshot の `deferred_surfaces` は維持し、
  semantic 自身が procedural execute/writeback を行わない境界は残します

## Revisit triggers

- semantic concept が cross-segment merge を前提にし、
  current handoff binding では source coverage が粗すぎると判明した時
- procedural preview が semantic handoff だけでなく
  trust / council / affect disclosure binding まで要求するようになった時
- semantic snapshot の `deferred_surfaces` 自体を廃し、
  richer planner / procedural orchestration surface へ統合したくなった時
