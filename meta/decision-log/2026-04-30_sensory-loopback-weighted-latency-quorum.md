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
  - sensory-loopback-weighted-latency-quorum
---

# Decision: shared loopback latency gate は bounded weighted quorum を持つ

## Context

`participant-hardware-timing-latency-drift-gate-v1` は shared Sensory Loopback の
participant ごとに hardware timing drift を fail-closed できる。一方、3-4 participant の
shared sensory field では、1 participant の timing adapter が一時的に drift した時に、
raw timing payload を保存せず、かつ全員 pass 以外の bounded acceptance を表現する
machine-readable contract がなかった。

## Decision

`weighted-latency-quorum-v1` を `participant-biodata-gate-arbitration-v1` に追加する。
既定は従来どおり `all-participant-latency-pass-v1` で全 participant latency gate pass を
要求する。3-4 participant で明示 weight と threshold を渡した場合だけ、blocked latency
gate を `latency_quorum_failed_participant_ids` に残し、passing participant weight が
threshold 以上なら `latency_quorum_satisfied=true` として受理する。

binding は participant latency weight digest、latency quorum digest、failed participant id、
pass weight、threshold を保持するが、raw timing payload、raw hardware adapter payload、
raw threshold policy payload、raw authority payload は保存しない。

## Consequences

- `sensory-loopback-demo --json` は self + peer が pass、observer が blocked の
  3 participant weighted quorum path を返す。
- public schema / IDL / eval / tests は strict all-pass path と weighted quorum path の
  両方を検証する。
- weighted quorum は shared loopback acceptance の timing gate に限定され、BioData
  confidence gate / feature-window drift gate coverage 自体は全 participant pass のまま維持する。

## Revisit triggers

- 4 participant を超える federated sensory field へ拡張する時
- participant weight を external policy authority / live verifier receipt に束縛する時
- weighted quorum を latency 以外の BioData drift gate に広げる時
