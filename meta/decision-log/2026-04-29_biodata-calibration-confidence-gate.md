---
date: 2026-04-29
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/biodata-transmitter.md
  - docs/02-subsystems/kernel/identity-lifecycle.md
  - docs/02-subsystems/interface/sensory-loopback.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.biodata_transmitter.v0.idl
  - specs/schemas/biodata_calibration_confidence_gate.schema
  - evals/interface/biodata_transmitter_roundtrip.yaml
status: decided
closes_next_gaps:
  - biodata-calibration-confidence-gate-bridge
---

# Decision: BioData calibration を confidence gate として接続する

## Context

BioData Transmitter は multi-day calibration profile を作成できるが、その結果を
identity confirmation や sensory loopback の入口へ渡す digest-only contract が無かった。
既存の Revisit trigger では calibration profile を confidence gate に渡すことが次段として残っていた。

## Decision

`biodata-calibration-confidence-gate-v1` を追加し、complete な calibration profile を
identity confirmation と sensory loopback の target gate refs へ束縛する。
receipt は calibration digest、source latent digest set、full modality coverage、
target 別 threshold、target gate set digest、gate receipt digest を持つ。

identity confirmation gate は `confidence_score >= 0.8`、sensory loopback gate は
`confidence_score >= 0.7` を要求する。gate は confidence input であり、self-report、
witness quorum、registry verifier、body-map calibration、Guardian hold を置き換えない。
raw calibration payload と raw gate payload は保存しない。

## Consequences

- `biodata-transmitter-demo --json` は `calibration_confidence_gate` と validation flags を返す。
- public schema / IDL / eval / docs / IntegrityGuardian policy が confidence gate digest と raw payload redaction を検証する。
- BioData calibration は identity / loopback へ接続されたが、主観同一性や semantic thought recovery の証明にはしない。

## Revisit triggers

- 実 EEG/ECG/PPG/EDA/respiration dataset adapter を接続する時
- identity confirmation 側が body-state latent を独立 dimension として扱う時
- sensory loopback 側が calibration confidence を body-map drift threshold の動的補正に使う時
