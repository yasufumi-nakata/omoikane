---
date: 2026-04-20
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/procedural-memory.md
  - docs/02-subsystems/mind-substrate/README.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.skill_execution.v0.idl
status: decided
---

# Decision: procedural skill execution の次段として temp-workspace enactment surface を追加する

## Context

2026-04-20 時点の L2 procedural surface は
`procedural-demo` / `procedural-writeback-demo` / `procedural-skill-demo` により
preview、human-approved writeback、guardian-witnessed sandbox rehearsal までは
machine-checkable でしたが、
`specs/interfaces/README.md` には次段として
`L2 procedural skill execution enactment` が残っていました。

現行 `mind.skill_execution.v0` は `sandbox_action` / `evidence_ref` /
`rollback_token` を持つ rehearsal receipt であり、
temp workspace materialization、actual command 実行、cleanup receipt は持っていませんでした。

## Options considered

- A: `mind.skill_execution.v0` に command receipt と cleanup を直接足して contract を拡張する
- B: rehearsal receipt は維持し、その後段に `mind.skill_enactment.v0` と `procedural-enactment-demo` を新設する
- C: procedural surface を builder live enactment と統合し、L5 builder へ吸収する

## Decision

- B を採択しました
- `mind.skill_enactment.v0` / `procedural_skill_enactment_session.schema` /
  `evals/continuity/procedural_skill_enactment_execution.yaml` /
  `procedural-enactment-demo` を追加します
- enactment は temp workspace に限定し、
  `ProceduralSkillExecutor` の receipt を materialize して
  bounded command receipt と cleanup status を返します
- external actuation は引き続き禁止し、
  guardian witness と rollback token を enactment session へ carry します

## Consequences

- L2 procedural chain が `preview -> writeback -> skill execution -> skill enactment`
  まで reference runtime で閉じます
- `mind.skill_execution.v0` の rehearsal-only contract を濁さずに、
  actual command / cleanup receipt を別 surface で固定できます
- specs/interfaces/README.md の `L2 procedural skill execution enactment` 残件を外し、
  residual future work を external actuation authorization などへ絞れます

## Revisit triggers

- procedural enactment を actual external actuation authorization へ接続したい時
- sensory loopback artifact と connectome feedback を enactment session へ追加したい時
- builder live enactment と共通の temp workspace orchestration plane を切り出したい時
