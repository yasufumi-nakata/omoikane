---
date: 2026-04-30
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/sensory-loopback.md
  - docs/02-subsystems/interface/biodata-transmitter.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.sensory_loopback.v0.idl
  - specs/schemas/sensory_loopback_biodata_arbitration_binding.schema
  - evals/interface/sensory_loopback_biodata_arbitration.yaml
status: decided
closes_next_gaps:
  - sensory-loopback-biodata-participant-arbitration
---

# Decision: shared loopback arbitration は participant ごとの BioData gate を digest-only に束縛する

## Context

BioData Transmitter は participant ごとの calibration confidence gate と
feature-window series drift gate を返せるようになった。一方、Sensory Loopback の
shared IMC / collective arbitration は participant map と owner handoff は検証していたが、
各 participant の BioData confidence / drift gate coverage を shared arbitration の入口で
過不足なく確認する contract を持っていなかった。

## Decision

`participant-biodata-gate-arbitration-v1` を Sensory Loopback に追加する。
shared session の `participant_identity_ids` と同じ集合の
`biodata-calibration-confidence-gate-v1` receipt だけを受け取り、各 receipt が
`sensory-loopback` target を pass し、feature-window series drift gate を `pass` として
束縛していることを確認する。

出力は `sensory_loopback_biodata_arbitration_binding.schema` に従う digest-only binding とし、
gate ref / gate digest、drift gate ref / digest、drift threshold digest、
target gate-set digest、binding digest だけを保持する。raw BioData、calibration、drift、
gate payload は保存しない。

## Consequences

- `sensory-loopback-demo --json` は self / peer の participant BioData gate artifacts と、
  shared arbitration binding、validation flags、ledger event を返す。
- public schema contract manifest は session / receipt / artifact family に加えて
  BioData arbitration binding を列挙する。
- IntegrityGuardian は shared loopback acceptance の前に participant gate coverage、
  drift gate pass、binding digest、raw payload redaction を監査できる。

## Revisit triggers

- 3-4 participant の shared sensory field で gate aggregation policy を weighted quorum にする時
- external clinical / jurisdiction threshold policy を drift gate threshold digest に署名束縛する時
- hardware-timing adapter が participant-specific latency drift を BioData gate と同じ arbitration に渡す時
