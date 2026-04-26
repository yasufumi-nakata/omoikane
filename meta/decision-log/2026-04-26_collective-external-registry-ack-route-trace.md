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
  - collective.external-registry-ack-route-trace-binding
---

# Decision: Collective external registry ack quorum を authority route trace に束縛する

## Context

`collective-external-registry-ack-quorum-v1` は legal / governance registry の
acknowledgement を 2 jurisdiction quorum として束縛しました。
ただし ack quorum が reviewer-facing な network / host evidence のどの route に載ったかは
first-class artifact ではなく、ack digest が registry authority plane と同じ観測可能経路で
確認されたことを machine-checkable に示せませんでした。

## Decision

`collective-external-registry-ack-route-trace-v1` を
`collective_external_registry_sync.schema` に追加する。

ack quorum の legal / governance ack receipt は、authenticated non-loopback
authority-route trace の route binding ref、remote host attestation ref、
OS observer host binding digest、socket response digest にそれぞれ束縛される。
`ack_route_trace_binding_digest` は ack quorum digest、authority route trace digest、
ack authority refs、route binding refs をまとめる。

## Consequences

- `collective-demo --json` は `ack_route_trace_bindings` と
  `ack_route_trace_binding_digest` を返す
- public schema / IDL / eval / IntegrityGuardian capability は同じ route-trace-bound
  ack profile を共有する
- raw dissolution payload、raw registry payload、raw ack payload、raw ack-route payload、
  raw packet body は保存しない

## Revisit triggers

- external registry acknowledgement を actual jurisdiction API / governance registry backend
  の live endpoint へ差し替える時
- registry ack route trace を delegated packet capture export まで拡張する時
