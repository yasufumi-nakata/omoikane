---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/sensory-loopback.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.sensory_loopback.v0.idl
  - specs/schemas/sensory_loopback_artifact_family.schema
  - evals/interface/sensory_loopback_artifact_family.yaml
status: decided
---

# Decision: sensory loopback の multi-scene artifact family を reference runtime に昇格する

## Context

`gap-report --json` は clean でしたが、
`specs/schemas/README.md` には依然
`multi-scene sensory loopback artifact families`
が次段階として残っていました。

2026-04-21 時点の `sensory-loopback-demo` は
coherent delivery、guardian hold、stabilize recovery までは
machine-checkable でしたが、
それら複数 scene を「同一 session の回復経路」として
1 つの bounded artifact に束ねる contract がありませんでした。

そのため、raw payload を残さずに
どの scene sequence が guardian intervention を経て active session へ戻ったかを
repo 内で再監査する surface が欠けていました。

## Options considered

- A: receipt 単位のまま維持し、multi-scene family は future work に残す
- B: 同一 session 内の 2-4 receipt を digest-only family に束ね、schema/IDL/runtime/eval/test まで固定する
- C: sensory loopback を multi-self arbitration や richer avatar map まで一気に拡張する

## Decision

**B** を採択。

## Consequences

- `sensory_loopback_artifact_family.schema` を追加し、
  `multi-scene-artifact-family-v1` を canonical family policy とする
- `SensoryLoopbackService.capture_artifact_family(...)` は
  coherent / held / stabilized scene を同一 session に束ね、
  `guardian_intervention_count`、`stabilization_delivery_ids`、
  `final_session_status` を digest-bound に返す
- session snapshot は `artifact_family_count` と latest `family_ref` を保持し、
  sensory-loopback demo は recovery chain を 1 つの family として監査へ残せる
- residual future work は raw stream timing、richer avatar map、
  collective / IMC 空間での multi-self loopback arbitration へ絞られる

## Revisit triggers

- sensory loopback family を collective / IMC 共有空間の multi-self arbitration と束ねたくなった時
- raw retinal/audio/haptic payload を artifact family と併走させたくなった時
- richer avatar body map や proprioceptive calibration を family policy に反映したくなった時
