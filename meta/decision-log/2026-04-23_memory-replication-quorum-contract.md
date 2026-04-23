---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/README.md
  - docs/02-subsystems/mind-substrate/memory-model.md
  - docs/03-protocols/memory-replication.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.memory_replication.v0.idl
  - specs/schemas/memory_replication_session.schema
  - evals/continuity/memory_replication_quorum.yaml
status: decided
---

# Decision: MemoryCrystal replication を quorum-bound reference contract へ昇格する

## Context

2026-04-23 時点で `MemoryCrystal` は
`append-only-segment-rollup-v1` compaction までは runtime 化されていましたが、
`docs/03-protocols/memory-replication.md` にある
`Primary / Mirror / ColdStore / Trustee` の四重保管、
Merkle root 比較、
不一致時の rollback / Council escalation は
まだ machine-checkable artifact を持っていませんでした。

このままでは長期記憶の durability policy が docs-only のまま残り、
semantic / procedural handoff より手前の
保管・整合性・reconcile boundary を reference runtime で検証できません。

## Options considered

- A: `memory_crystal_manifest` のみを維持し、replication protocol は docs-only のまま残す
- B: four-target placement だけを追加し、Merkle audit と reconcile は future work に残す
- C: four-target placement、plaintext metadata + encrypted payload transfer、Merkle audit、council-escalated reconcile を同じ session artifact に閉じる

## Decision

**C** を採択。

## Consequences

- `mind.memory_replication.v0` と `memory_replication_session.schema` を追加し、
  `primary` / `mirror` / `coldstore` / `trustee` の fixed target set を公開 contract に固定する
- `memory-replication-demo` は
  source manifest digest、plaintext metadata digest、random-block Merkle audit、
  `trustee` mismatch、Guardian alert、Council escalation、resync requirement を
  1 session で返す
- `evals/continuity/memory_replication_quorum.yaml` と unit/integration test により、
  quorum loss や digest drift を継続検出できる
- residual gap は generic な replication policy 不在ではなく、
  geo-distributed storage media や long-horizon key succession のような
  repo 外 research frontier へ縮小する

## Revisit triggers

- four-target fixed policy を超えて dynamic replica admission / retirement を扱いたくなった時
- Merkle audit を random-block から actual remote storage proof へ拡張したくなった時
- Shamir catalog ref を abstract binding ではなく
  hardware-backed custody workflow まで materialize したくなった時
