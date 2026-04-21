---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/substrate-broker.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.broker.v0.idl
  - specs/schemas/standby_health_probe.schema
  - specs/schemas/substrate_attestation_chain.schema
  - evals/continuity/substrate_broker_attestation_chain.yaml
status: decided
---

# Decision: SubstrateBroker に standby probe と bounded attestation bridge を追加する

## Context

2026-04-20 時点の `SubstrateBrokerService` は
deterministic selection、neutrality rotation、
1 active lease + 1 standby candidate、
healthy attestation gate、energy-floor signal までは
machine-checkable でした。

一方で、standby candidate が migrate 直前にも本当に ready だったか、
また healthy source attestation がどの standby target / state digest と
結び付いていたかは repo 内で固定できていませんでした。
そのため residual future work として残っていた
`continuous cross-substrate attestation streaming`
へ進む前段の bounded contract が不足していました。

## Options considered

- A: broker は現状のまま据え置き、standby probe / attestation bridge は future work に残す
- B: second active lease は作らず、standby readiness probe と fixed 3-beat attestation bridge window を追加する
- C: いきなり live dual allocation と unbounded cross-substrate attestation streaming まで実装する

## Decision

Option B を採択します。

- `probe_standby` を追加し、
  `health_score` / `attestation_valid` / `energy_headroom_jps`
  で pre-bound standby candidate の migrate readiness を固定します
- `bridge_attestation_chain` を追加し、
  healthy source attestation と ready standby probe を
  `bounded-cross-substrate-attestation-window-v1`
  の 3-beat / 250ms window に束ねます
- bridge window は `expected_state_digest` と
  `expected_destination_substrate` を migrate 前に固定し、
  `handoff-ready` 以外では fail-closed とします

## Consequences

- `broker-demo` は selection / signal / attestation だけでなく、
  standby probe と attestation bridge まで repo 内で再現できます
- `kernel.broker.v0` / schema / eval / tests / docs が
  同じ standby readiness contract を共有します
- residual future work は live dual allocation と
  unbounded cross-substrate attestation streaming へ縮小されます

## Revisit triggers

- same identity の second active lease を bounded に許容したくなった時
- attestation bridge を 3 beat ではなく continuous stream へ拡張したくなった時
- broker の standby probe を actual remote substrate health service へ接続したくなった時
