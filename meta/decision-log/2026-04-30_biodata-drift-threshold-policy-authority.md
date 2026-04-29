---
date: 2026-04-30
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/biodata-transmitter.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.biodata_transmitter.v0.idl
  - specs/schemas/biodata_drift_threshold_policy_authority_receipt.schema
  - specs/schemas/biodata_feature_window_series_drift_gate.schema
  - specs/schemas/biodata_calibration_confidence_gate.schema
  - evals/interface/biodata_transmitter_roundtrip.yaml
status: decided
closes_next_gaps:
  - biodata-drift-threshold-policy-authority
---

# Decision: BioData drift threshold policy を authority digest に束縛する

## Context

`biodata-feature-window-series-drift-gate-v1` は current series drift を
bounded threshold で検査し、calibration confidence gate の前段 hard gate にできる。
しかし threshold set 自体が clinical reviewer、jurisdiction policy、Guardian のどの
authority ref に由来するかは、drift gate digest の外側に残っていた。

## Decision

`biodata-drift-threshold-policy-authority-v1` を追加し、axis threshold set を
clinical reviewer、jurisdiction policy、Guardian の 3 authority source digest へ束縛する。
各 source は authority ref、policy ref、signer key ref、signature ref、jurisdiction を
digest-only に保持する。

drift gate は authority ref、authority receipt digest、authority source digest set、
quorum status を直接保持し、confidence gate へも authority digest を伝播する。
raw threshold policy payload、raw signature payload、raw authority payload、
raw reviewer payload は保存しない。authority refs は threshold provenance であり、
BioData の clinical diagnosis authority や identity decision authority へ昇格しない。

## Consequences

- `biodata-transmitter-demo --json` は threshold policy authority receipt と
  authority-bound drift gate / confidence gate を返す。
- public schema / IDL / eval / docs / IntegrityGuardian policy は axis threshold digest、
  authority source digest set、required role coverage、raw policy/signature redaction を検証する。
- shared Sensory Loopback 側は既存の drift threshold digest を受け取り続けられるが、
  upstream BioData receipt は threshold provenance を追跡できる。

## Revisit triggers

- jurisdiction policy を live verifier endpoint に接続する時
- clinical reviewer quorum を複数 reviewer / multi-jurisdiction policy に拡張する時
- participant-specific latency drift threshold と同じ authority receipt を共有する時
