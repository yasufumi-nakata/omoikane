---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/substrate-broker.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.broker.v0.idl
  - specs/schemas/substrate_dual_allocation_window.schema
  - evals/continuity/substrate_broker_dual_allocation_window.yaml
status: decided
---

# Decision: SubstrateBroker に bounded live dual allocation window を追加する

## Context

2026-04-21 時点の `SubstrateBrokerService` は
`1 active lease + 1 standby candidate`、
`probe_standby`、
`bridge_attestation_chain`
まで machine-checkable でした。

その一方で `specs/schemas/README.md` には依然
`live dual allocation beyond the bounded standby probe / attestation window`
が次段階として残っており、
Method B の `shadow-sync -> authority-handoff`
を repo 内で materialize する surface が不足していました。

## Options considered

- A: broker を single-active のまま固定し、dual allocation は docs-only future work に残す
- B: Method B に限って bounded shadow-sync overlap window を追加し、second active allocation を fixed policy / schema / eval / demo まで落とす
- C: cross-host distributed broker や unbounded streaming handoff まで一気に実装する

## Decision

**B** を採択します。

## Consequences

- `substrate_dual_allocation_window.schema` を追加し、
  `bounded-live-dual-allocation-window-v1`
  を Method B shadow-sync の canonical policy とする
- `kernel.broker.v0` は
  `open_dual_allocation_window / close_dual_allocation_window`
  を公開し、
  ready standby probe・healthy attestation・handoff-ready attestation chain を
  prerequisite として second active allocation を fail-closed で materialize する
- overlap は `45s / 250ms cadence / max drift 0.08`
  に固定し、
  `shadow-sync` で開き `authority-handoff` で閉じる
- residual future work は generic な dual allocation 不在ではなく、
  cross-host dual allocation と continuous cross-substrate attestation streaming に縮小される

## Revisit triggers

- shadow allocation を same-host demo ではなく cross-host substrate へ広げたくなった時
- fixed 3 observation / 45s overlap ではなく continuous attestation streaming が必要になった時
- Method B dual allocation を scheduler の live stage execution と直接結び付けたくなった時
