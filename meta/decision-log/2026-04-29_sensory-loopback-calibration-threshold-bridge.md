---
date: 2026-04-29
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/biodata-transmitter.md
  - docs/02-subsystems/interface/sensory-loopback.md
  - docs/05-research-frontiers/biosignal-transmitter.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.sensory_loopback.v0.idl
  - specs/schemas/sensory_loopback_session.schema
  - specs/schemas/sensory_loopback_receipt.schema
  - specs/schemas/sensory_loopback_artifact_family.schema
  - evals/interface/sensory_loopback_guard.yaml
status: decided
closes_next_gaps:
  - sensory-loopback-calibration-confidence-threshold-bridge
---

# Decision: BioData calibration gate を sensory loopback drift threshold に限定接続する

## Context

BioData Transmitter は complete な calibration profile を
`biodata-calibration-confidence-gate-v1` として sensory loopback target へ渡せる。
ただし Sensory Loopback 側はまだその confidence input を body-map drift threshold へ
反映しておらず、2026-04-29 の BioData decision log にも次段 trigger として残っていた。

## Decision

`biodata-calibration-gated-drift-threshold-v1` を Sensory Loopback session / receipt /
artifact family scene summary に追加する。
`sensory-loopback` target が pass し、`confidence_score >= 0.7` の時だけ
coherent / hold drift threshold を最大 `0.04` まで補正する。

この補正は confidence input であり、`avatar_body_map_ref`、
`proprioceptive_calibration_ref`、Guardian observation、Guardian hold、
stabilization を置き換えない。gate ref、gate digest、confidence score、
applied threshold だけを保存し、raw calibration payload と raw gate payload は保存しない。

## Consequences

- `sensory-loopback-demo --json` は BioData calibration confidence gate と threshold adjustment validation を返す。
- public schema / IDL / eval / docs / IntegrityGuardian policy が gate digest、applied threshold、raw payload redaction を検証する。
- Sensory Loopback は BioData calibration を使えるが、主観同一性や body-map calibration 完了の証明にはしない。

## Revisit triggers

- 実 dataset adapter から calibration confidence を受け取る時
- participant ごとの calibration gate を shared loopback arbitration に分配する時
- body-map drift threshold 以外の timing / haptic gain 補正へ広げる時
