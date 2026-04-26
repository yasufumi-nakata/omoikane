---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/collective-identity.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.collective.v0.idl
  - specs/schemas/collective_external_registry_sync.schema
  - evals/interface/collective_external_registry_sync.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - collective.external-registry-ack-route-capture-export-binding
---

# Decision: Collective external registry ack route trace を capture export に束縛する

## Context

`collective-external-registry-ack-route-trace-v1` は legal / governance registry
acknowledgement quorum を authenticated non-loopback authority-route trace へ束縛しました。
ただし Revisit trigger に残っていた delegated packet capture export は、
external registry ack route の first-class artifact ではありませんでした。

## Decision

`collective-external-registry-ack-route-capture-export-v1` を
`collective_external_registry_sync.schema` に追加する。

ack route trace binding digest、verified pcap export digest、
delegated-broker privileged capture digest、ack ごとの route capture binding digest を
同じ external registry sync receipt に束縛する。ack route は jurisdiction 優先で選ばれるため、
capture artifact との照合は route ordering ではなく route binding ref set で固定する。

## Consequences

- `collective-demo --json` は `ack_route_packet_capture_digest`、
  `ack_route_privileged_capture_digest`、`ack_route_capture_binding_digest` を返す
- public schema / IDL / eval / IntegrityGuardian capability は同じ ack route capture
  profile を共有する
- raw dissolution payload、raw registry payload、raw ack payload、raw ack-route payload、
  raw packet body は保存しない

## Revisit triggers

- external registry acknowledgement を actual jurisdiction API / governance registry backend
  の live endpoint へ差し替える時
- ack route packet capture を actual privileged OS capture backend へ差し替える時
