---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/procedural-memory.md
  - docs/02-subsystems/mind-substrate/memory-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.procedural_actuation.v0.idl
  - specs/schemas/procedural_actuation_bridge_session.schema
  - evals/continuity/procedural_actuation_bridge.yaml
status: decided
closes_next_gaps:
  - procedural.actuation.ewa-authorization-bridge
---

# Decision: Procedural enactment から EWA authorization への bridge を first-class 化する

## Context

`procedural-enactment-demo` は temp workspace 上の bounded command receipt と
cleanup / rollback token carryover までを証明していました。
一方、procedural skill を外界 actuation へ移す boundary は
EWA の `external_actuation_authorization` に委ねる設計でありながら、
source enactment と EWA authorization / approved command audit を
同一 receipt で束縛する public surface がありませんでした。

## Options considered

- A: `procedural-enactment-demo` を sandbox-only のまま維持し、EWA authorization との接続を docs の説明だけに留める
- B: `procedural_skill_enactment_session` に EWA fields を直接追加し、既存 enactment contract を拡張する
- C: `procedural_actuation_bridge_session` と `mind.procedural_actuation.v0` を追加し、sandbox-only enactment と EWA authorization の境界を別 receipt として固定する

## Decision

**C** を採択。

## Consequences

- `procedural-actuation-demo --json` は passed / cleaned-up な
  `procedural_skill_enactment_session` を source とし、
  EWA の `external_actuation_authorization`、approved command audit、
  legal execution、Guardian oversight gate、rollback token を
  `procedural_actuation_bridge_session` に digest-bound で束ねる
- `mind.skill_enactment.v0` の sandbox-only invariant は維持し、
  physical-world actuation は `mind.procedural_actuation.v0` の bridge receipt に分離する
- bridge receipt は `instruction_digest` と `intent_summary_digest` だけを保持し、
  raw instruction text と approved command の intent summary は `redacted_fields` へ退避する
- validator は source enactment digest、authorization digest、
  authorization validation、approved command authorization id、
  legal execution digest、Guardian oversight gate digest、
  rollback token preservation を同時に確認する
- schema / IDL / eval / CLI / unit test / integration test / docs / agents は
  procedural-to-EWA boundary contract に同期した

## Revisit triggers

- bridge 対象を reversible command 以外へ広げる時
- bridge receipt に emergency-stop postcondition や release receipt digest を含める時
- cross-host procedural executor から EWA authorization を発行する時
