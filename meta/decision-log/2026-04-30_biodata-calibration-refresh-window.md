---
date: 2026-04-30
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/biodata-transmitter.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.biodata_transmitter.v0.idl
  - specs/schemas/biodata_calibration_refresh_receipt.schema
  - specs/schemas/biodata_calibration_confidence_gate.schema
  - evals/interface/biodata_transmitter_roundtrip.yaml
status: decided
closes_next_gaps:
  - biodata-calibration-refresh-window
---

# Decision: BioData calibration 再利用を freshness window receipt に束縛する

## Context

`biodata-calibration-confidence-gate-v1` は calibration profile と
feature-window series drift gate を identity confirmation / sensory loopback の
confidence input へ渡せるようになっていた。一方で、同じ calibration を後続 run で
再利用する時に、current drift gate、本人同意、Guardian review、freshness window が
同時に揃っていることを示す独立 receipt はなかった。

## Decision

`biodata-calibration-refresh-window-v1` を追加し、calibration digest、
feature-window drift gate digest、threshold policy authority digest、
current drift gate evidence、self consent、Guardian review、refresh deadline、
refreshed-at ref、1-90 日 freshness window を digest-only receipt として束縛する。

calibration confidence gate は refresh receipt が渡された場合に
refresh ref / digest / source digest set / status を target gate binding へ直接含める。
refresh receipt が `fresh` でない場合、confidence gate は pass を出さない。

raw calibration payload、raw drift payload、raw threshold policy payload、
raw refresh payload、raw gate payload は保存しない。

## Consequences

- `biodata-transmitter-demo --json` は calibration refresh receipt と、
  それを直接参照する calibration confidence gate を返す。
- public schema / IDL / eval / docs / IntegrityGuardian policy は refresh source digest set、
  freshness window、drift gate binding、threshold authority binding、raw refresh redaction を検証する。
- Sensory Loopback 側へ渡る confidence gate は、current BioData calibration が
  freshness window 内で再確認されたことを digest-only に追跡できる。

## Revisit triggers

- freshness window を live scheduler / external verifier cadence と接続する時
- multi-jurisdiction Guardian review quorum を calibration refresh source に拡張する時
- participant-specific shared loopback calibration refresh を group arbitration に伝播する時
