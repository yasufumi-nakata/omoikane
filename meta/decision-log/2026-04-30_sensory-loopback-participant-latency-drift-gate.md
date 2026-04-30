---
date: 2026-04-30
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/sensory-loopback.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.sensory_loopback.v0.idl
  - specs/schemas/sensory_loopback_biodata_arbitration_binding.schema
  - evals/interface/sensory_loopback_biodata_arbitration.yaml
status: decided
closes_next_gaps:
  - sensory-loopback-participant-latency-drift-gate
---

# Decision: shared loopback arbitration は participant latency drift gate も束縛する

## Context

`participant-biodata-gate-arbitration-v1` は shared Sensory Loopback の participant ごとに
BioData confidence gate と feature-window drift gate を確認していた。一方、hardware
timing 由来の participant-specific latency drift は、delivery receipt の latency 判定とは別に、
shared arbitration の入口で BioData gate と同じ participant set に束縛されていなかった。

## Decision

`participant-hardware-timing-latency-drift-gate-v1` を Sensory Loopback 側に追加し、
baseline latency、observed latency、absolute drift、`12.0ms` threshold digest を
participant ごとの digest-only gate にする。

shared BioData arbitration は `participant_latency_drift_gates` を必須にし、
`participant_identity_ids` と同じ集合・順序で coverage を確認する。BioData drift threshold
policy authority が bound の participant では、latency gate も同じ authority ref、
authority digest、source digest set を保持する。binding は latency gate digest set と
BioData gate digest set の両方を binding digest に含める。

raw timing payload、raw hardware adapter payload、raw latency threshold payload、
raw BioData / calibration / drift / gate payload は保存しない。

## Consequences

- `sensory-loopback-demo --json` は shared participant の latency drift gates と
  latency-bound BioData arbitration binding を返す。
- public schema / IDL / eval / docs / IntegrityGuardian policy は participant latency
  coverage、threshold authority digest sharing、latency digest set、raw timing redaction を検証する。
- delivery-level latency guard は残しつつ、shared arbitration の acceptance でも
  participant-specific hardware timing drift を fail-closed にできる。

## Revisit triggers

- 3-4 participant shared field で latency gate を weighted quorum に拡張する時
- repo 外 hardware capture adapter の raw timing acquisition を live verifier receipt に接続する時
- participant latency threshold policy を BioData drift threshold policy と別 authority に分離する時
