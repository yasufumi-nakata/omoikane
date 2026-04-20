---
date: 2026-04-20
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/README.md
  - docs/02-subsystems/interface/sensory-loopback.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.sensory_loopback.v0.idl
status: decided
---

# Decision: Sensory Loopback を bounded guardian-recoverable surface として runtime 化する

## Context

2026-04-20 時点で L6 Interface は
`BDB / IMC / Collective / WMS / EWA` が reference runtime 化されていましたが、
`Sensory Loopback` だけは `docs/02-subsystems/interface/README.md` に
名称があるだけの docs-only surface でした。

この状態では avatar body への visual/audio/haptic feedback を
どの world anchor に束縛し、
どの drift / latency で Guardian が hold すべきか、
QualiaBuffer とどう接続するかを machine-checkable にできませんでした。

## Options considered

- A: Sensory Loopback は引き続き docs-only とし、Qualia/WMS 側の説明だけで済ませる
- B: digest-only artifact ref と body coherence guard に絞った `interface.sensory_loopback.v0` を追加する
- C: raw retinal/audio/haptic stream と hardware-specific timing まで同時に実装する

## Decision

- B を採択しました
- `SensoryLoopbackService` /
  `interface.sensory_loopback.v0` /
  `sensory_loopback_session.schema` /
  `sensory_loopback_receipt.schema` /
  `sensory-loopback-demo` を追加します
- loopback は `world_state_ref` と `body_anchor_ref` に必ず束縛し、
  `latency_budget_ms=90.0` /
  `coherence_drift_threshold=0.20` /
  `hold_drift_threshold=0.35` を固定します
- audit は `artifact_ref + digest + summary` のみを保持し、
  raw sensory payload は残しません
- degraded bundle は Guardian observe 必須とし、
  `guardian-hold` 後は `stabilize` でしか active に戻せない contract にします

## Consequences

- L6 の docs-only だった `Sensory Loopback` が runtime / schema / IDL / eval / tests / docs まで閉じます
- `QualiaBuffer` 側は raw stream を抱えず、
  `qualia_binding_ref` で surrogate tick と接続する bounded contract を得られます
- future work は raw stream capture、hardware timing、multi-self arbitration へ絞られます

## Revisit triggers

- retinal/audio/haptic hardware pipeline を actual device へ接続したい時
- proprioceptive calibration や richer avatar body map を入れたい時
- IMC / Collective 空間で loopback を shared transport と統合したい時
