---
date: 2026-04-30
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/biodata-transmitter.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.biodata_transmitter.v0.idl
  - specs/schemas/biodata_feature_window_series_drift_gate.schema
  - specs/schemas/biodata_calibration_confidence_gate.schema
  - evals/interface/biodata_transmitter_roundtrip.yaml
status: decided
closes_next_gaps:
  - biodata-feature-window-series-drift-gate
---

# Decision: BioData feature-window series drift を calibration confidence gate の前段 hard gate にする

## Context

`biodata-feature-window-series-profile-v1` は複数日の adapter receipt と body-state latent を
ordered series に束ねられるが、calibration confidence gate はまだ calibration profile
だけを見ていた。current series の drift が大きい場合でも、古い calibration digest だけで
identity confirmation / sensory loopback へ confidence input を渡せてしまう。

## Decision

`biodata-feature-window-series-drift-gate-v1` を追加し、series profile digest、
calibration digest、source latent digest set、axis threshold policy、axis drift check set、
drift threshold digest を digest-only receipt として束縛する。

calibration confidence gate は、drift gate receipt が渡された場合に
drift gate ref / digest / threshold digest を target binding へ直接含める。
drift gate が `pass` でない場合、confidence gate は pass を出さない。

raw series payload、raw calibration payload、raw drift payload、raw gate payload は保存しない。

## Consequences

- `biodata-transmitter-demo --json` は feature-window series drift gate と、
  それを直接参照する calibration confidence gate を返す。
- public schema / IDL / eval / docs / IntegrityGuardian policy は drift gate digest、
  threshold digest、series-calibration latent set binding、raw drift payload redaction を検証する。
- Sensory Loopback 側の body-map threshold adjustment は、calibration confidence gate が
  current series drift gate を pass した時だけ confidence input として扱える。

## Revisit triggers

- external circadian clock / sleep diary / wearable verifier を drift threshold policy に束縛する時
- participant ごとに shared loopback へ BioData drift gate を分配する時
- threshold policy を jurisdiction / clinical reviewer signed policy に昇格する時
