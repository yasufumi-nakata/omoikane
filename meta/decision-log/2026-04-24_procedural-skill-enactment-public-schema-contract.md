---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/procedural-memory.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.skill_enactment.v0.idl
  - specs/schemas/procedural_skill_enactment_session.schema
  - evals/continuity/procedural_skill_enactment_execution.yaml
status: decided
---

# Decision: procedural skill enactment session は public schema contract で検証する

## Context

`procedural-enactment-demo` は temp workspace materialization、
actual command receipt、cleanup、rollback token carryover を runtime で返していました。
ただし hidden gap として、demo 出力が
`procedural_skill_enactment_session.schema` に直接照合されず、
command receipt の `eval_ref` が session の `eval_refs` に束縛されることも
public contract として弱いままでした。

## Options considered

- A: runtime validation のみ維持する
- B: schema validation test だけを追加する
- C: schema / IDL / eval / docs / builder policy / tests を同期し、mandatory eval と command receipt eval binding を public contract にする

## Decision

**C** を採択。

## Consequences

- `validate_session()` は mandatory eval binding、command receipt eval refs、
  temp workspace cleanup を machine-checkable な validation result として返す
- `procedural_skill_enactment_session.schema` は
  `evals/continuity/procedural_skill_enactment_execution.yaml` を必須化し、
  passed session の command receipt を all-pass に制限する
- integration test は `procedural-enactment-demo` の session を
  public schema に直接通す
- eval / docs / CodexBuilder policy は schema-backed verification を前提にする

## Revisit triggers

- enactment が複数 eval を並列実行する時
- failed / blocked enactment の retained workspace forensic receipt を追加する時
- external actuation へ接続する範囲を sandbox-only から広げる時
