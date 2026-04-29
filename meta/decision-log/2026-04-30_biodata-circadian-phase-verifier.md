---
date: 2026-04-30
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/biodata-transmitter.md
  - docs/05-research-frontiers/biosignal-transmitter.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.biodata_transmitter.v0.idl
  - specs/schemas/biodata_circadian_phase_verifier_receipt.schema
  - specs/schemas/biodata_feature_window_series_profile.schema
  - evals/interface/biodata_transmitter_roundtrip.yaml
status: decided
closes_next_gaps:
  - biodata-circadian-phase-verifier
---

# Decision: BioData circadian phase refs を verifier quorum に束縛する

## Context

`biodata-feature-window-series-profile-v1` は longitudinal / circadian profile を
構築できるが、phase refs 自体は series 内の文字列 ref だけだった。series drift gate が
calibration confidence gate の前段 hard gate になると、phase refs が外部 clock、
sleep diary、wearable summary のどの evidence に由来するかを raw payload なしで
監査する contract が必要になった。

## Decision

`biodata-circadian-phase-verifier-v1` を追加し、ordered circadian phase refs を
external clock、sleep diary、wearable evidence refs の 3 source digest へ束縛する。
feature-window series profile は phase verifier ref / digest / source digest set /
status を直接保持し、series profile digest に verifier digest も含める。

raw clock payload、raw sleep diary payload、raw wearable payload、raw phase payload、
raw verifier payload は保存しない。verifier は日内位相の evidence quorum であり、
主観同一性、semantic thought recovery、clinical circadian diagnosis の証明ではない。

## Consequences

- `biodata-transmitter-demo --json` は circadian phase verifier receipt と、
  verifier-bound feature-window series profile を返す。
- public schema / IDL / eval / docs / IntegrityGuardian policy は phase ref digest set、
  verifier source digest set、quorum status、raw verifier payload redaction を検証する。
- feature-window series drift gate は、phase evidence が digest-bound された series
  profile を calibration confidence gate の current-series evidence として扱える。

## Revisit triggers

- 実 wearable / sleep diary / clock source を live verifier endpoint に接続する時
- circadian phase verifier quorum を participant ごとの shared loopback arbitration に分配する時
- phase evidence policy を clinical reviewer signed policy に昇格する時
