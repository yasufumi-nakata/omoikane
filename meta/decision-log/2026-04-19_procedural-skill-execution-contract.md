---
date: 2026-04-19
deciders: [yasufumi, codex-council]
related_docs:
  - docs/02-subsystems/mind-substrate/README.md
  - docs/02-subsystems/mind-substrate/memory-model.md
  - docs/02-subsystems/mind-substrate/procedural-memory.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.skill_execution.v0.idl
  - specs/schemas/procedural_skill_execution.schema
  - evals/continuity/procedural_skill_execution_contract.yaml
status: decided
---

# Decision: procedural memory の skill-execution は guardian-witnessed sandbox rehearsal として reference runtime へ昇格する

## Context

`procedural-writeback-demo` により bounded connectome delta と rollback token は固定できましたが、
`skill-execution` はなお docs 上の deferred surface として残っていました。
このままでは `MemoryCrystal -> preview -> writeback` の先が machine-readable にならず、
暗黙技能の enactment 境界が reference runtime 外に逃げ続けます。
一方で external actuation まで一気に開くと EWA や scheduler handoff と境界が混線するため、
まずは guardian witness 付き sandbox rehearsal に限定して contract を固定するのが安全でした。

## Options considered

- A: `skill-execution` は deferred のまま残し、writeback で止める
- B: `skill-execution` を guardian witness 付き sandbox rehearsal として昇格する
- C: `skill-execution` を external actuation まで含む実行 contract として一気に開く

## Decision

**B** を採択。

## Consequences

- `mind.skill_execution.v0` と `procedural_skill_execution.schema` を追加し、
  validated writeback から sandbox-only rehearsal receipt を生成する contract を固定する
- `procedural-skill-demo` で guardian witness、sandbox session、skill label、
  rollback token carryover、no external actuation を一度に確認する
- procedural preview の `deferred_surfaces` は `skill-execution` のみに縮小し、
  `weight-application` は既存 writeback contract 側で閉じた扱いに更新する
- 将来 actual actuation を足す場合も、
  sandbox rehearsal receipt と rollback-ready boundary を前提条件として再利用できる

## Revisit triggers

- sandbox rehearsal を超えて、実世界 actuation や device-specific motor semantics を扱いたくなった時
- guardian witness の実体証明や legal attestation を repo 内 artifact として束ねたくなった時
- execution step 数が 3 を超える staged rehearsal や multi-session enactment が必要になった時
