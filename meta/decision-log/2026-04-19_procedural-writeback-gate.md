---
date: 2026-04-19
deciders: [yasufumi, codex-council]
related_docs:
  - docs/02-subsystems/mind-substrate/README.md
  - docs/02-subsystems/mind-substrate/procedural-memory.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.procedural.v0.idl
  - specs/interfaces/mind.procedural_writeback.v0.idl
  - specs/schemas/procedural_writeback_receipt.schema
  - evals/continuity/procedural_writeback_contract.yaml
status: decided
---

# Decision: procedural memory writeback は human-approved bounded connectome delta として reference runtime へ昇格する

## Context

`procedural-demo` により connectome-coupled preview は固定できましたが、
`docs/07-reference-implementation/README.md` にはなお
「L2 procedural memory apply path と human-approved writeback contract」が残っていました。
preview のみでは writeback に必要な reviewer quorum、continuity diff、rollback token の
境界が機械可読にならず、README 上の durable gap も残り続けます。
一方で reference runtime には preview recommendation、`ConnectomeDocument`、
ContinuityLedger の event path がすでにあり、
copied snapshot への bounded delta 適用なら destructive risk を抑えつつ
writeback contract を具体化できます。

## Options considered

- A: writeback はまだ docs 上の TODO として残し、preview-only を維持する
- B: writeback を self / council / guardian / human reviewer quorum 付きの bounded contract として reference runtime へ昇格する
- C: full skill execution まで一気に実装し、writeback と enactment を同時に閉じる

## Decision

**B** を採択。

## Consequences

- `mind.procedural_writeback.v0` と
  `procedural_writeback_receipt.schema` を追加し、
  validated preview から copied `Connectome` snapshot へ
  bounded `weight-application` を行う contract を固定する
- reference runtime は `procedural-writeback-demo` で
  preview、updated connectome、writeback receipt、
  human reviewer quorum、continuity diff metadata、rollback token を一度に確認する
- `skill-execution` 自体は deferred のまま残し、
  writeback surface を connectome delta と ledger evidence に限定する
- 今後 richer enactment を足す際も、
  reviewer quorum と rollback-ready boundary を前提条件として再利用できる

## Revisit triggers

- human reviewer の実体証明や法的証跡を repo 内 artifact として扱う必要が出た時
- preview からの選択的 apply だけでは不足で、staged rollout や multi-step rehearsal が必要になった時
- `skill-execution` を reference runtime へ昇格し、writeback 後の enactment contract まで閉じたくなった時
