---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/sensory-loopback.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.sensory_loopback.v0.idl
  - specs/schemas/sensory_loopback_session.schema
  - specs/schemas/sensory_loopback_receipt.schema
  - specs/schemas/sensory_loopback_artifact_family.schema
  - evals/interface/sensory_loopback_guard.yaml
status: decided
---

# Decision: sensory loopback に avatar body-map calibration contract を追加する

## Context

2026-04-22 時点の `gap-report --json` は
`specs/interfaces/interface.sensory_loopback.v0.idl` の residual line として
`richer avatar-body maps` を最優先 gap に挙げていました。

既存の `SensoryLoopbackService` は
`world_state_ref` と単一 `body_anchor_ref`、`body_coherence_score` のみを扱い、
どの canonical body segment map に対する drift なのか、
どの proprioceptive calibration snapshot に束縛された receipt なのかを
machine-checkable に残していませんでした。

## Options considered

- A: sensory loopback は現状の scalar `body_coherence_score` のまま維持し、body map は repo 外メモに留める
- B: `avatar_body_map_ref` / `proprioceptive_calibration_ref` / `body_map_alignment_ref` を session / receipt / artifact family に追加し、weighted drift を runtime で導出する
- C: raw retinal/audio/haptic payload capture と device-driver timing まで同時に実装する

## Decision

- B を採択しました
- `SensoryLoopbackService.open_session(...)` は
  `avatar_body_map_ref` と `proprioceptive_calibration_ref` を必須入力にします
- `deliver_bundle(...)` は scalar `body_coherence_score` を外し、
  canonical 4 segment (`core` / `left-hand` / `right-hand` / `stance`) の
  `body_map_alignment` から weighted drift を導出します
- receipt と multi-scene artifact family は
  `avatar_body_map_ref` / `proprioceptive_calibration_ref` /
  `body_map_alignment_ref` を保持し、
  recovery chain 全体で calibration continuity を追跡できるようにします

## Consequences

- `sensory-loopback-demo` は body-map calibration bound な coherent / held / stabilized path を返します
- `gap-report --json` の truth-source に残っていた sensory loopback の residual future-work line は解消されます
- raw payload capture や device-driver timing は
  in-repo bootstrap runtime の deterministic boundary 外として扱われ、
  digest-only contract を維持します

## Revisit triggers

- sensory loopback を actual capture pipeline や hardware driver と結びたい時
- collective / IMC 空間で multi-self body-map arbitration を扱いたい時
- avatar body-map を 4 segment より細かい proprioceptive topology へ拡張したい時
