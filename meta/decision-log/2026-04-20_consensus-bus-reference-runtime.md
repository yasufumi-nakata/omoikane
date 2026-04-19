---
date: 2026-04-20
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/consensus-bus.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.consensus_bus.v0.idl
  - specs/schemas/consensus_message.schema
  - evals/agentic/consensus_bus_delivery_guard.yaml
status: decided
---

# Decision: ConsensusBus を audited delivery surface として昇格する

## Context

`ConsensusBus` は L4 Agentic Orchestration の主要コンポーネントとして
docs に現れていた一方、repo には `consensus_message.schema` の断片参照しかなく、
runtime / CLI / eval / test まで閉じていませんでした。
この状態では「直接合意禁止」「Builder は bus 経由でのみ dispatch」という
L4 の不変条件を machine-checkable にできません。

## Options considered

- A: `consensus_message.schema` を Council side effect のまま据え置き、専用 runtime は持たない
- B: ConsensusBus を専用 service に昇格し、dispatch / report / gate / resolve と direct handoff block を固定する
- C: YaoyorozuRegistry / AmenoUzumePool まで同時に起こし、bus はその一部として実装する

## Decision

**B** を採択。

## Consequences

- `agentic.consensus_bus.v0` と `consensus-bus-demo` を追加し、
  Council dispatch brief、Builder report、Guardian gate、final resolve を
  `consensus-bus-only` で監査可能にする
- `reject_direct_message` を surface として持ち、
  bus bypass attempt を `blocked` として transcript 外に明示記録する
- `evals/agentic/consensus_bus_delivery_guard.yaml` で
  phase order / guardian gate / resolve completion / direct handoff block を継続検証する

## Revisit triggers

- YaoyorozuRegistry / AmenoUzumePool を実 worker roster 付きで materialize する時
- ConsensusBus transcript を distributed transport や live verifier network と束ねる時
- session transcript の署名 policy を Builder / Guardian 別に強化したい時
