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
  - collective.external-registry-ack-live-endpoint-probe-binding
---

# Decision: Collective external registry ack を live endpoint probe に束縛する

## Context

`collective-external-registry-ack-route-capture-export-v1` は registry
acknowledgement quorum を route trace と capture export evidence へ束縛しました。
ただし acknowledgement が actual legal / governance registry backend の
live endpoint response から得られたことは first-class artifact ではなく、
static digest と live backend response を reviewer が区別できませんでした。

## Decision

`collective-external-registry-ack-live-endpoint-probe-v1` を
`collective_external_registry_sync.schema` に追加する。

legal / governance の acknowledgement receipt ごとに live HTTP JSON endpoint を
probe し、endpoint ref、HTTP status、observed latency、network response digest、
ack receipt digest、registry entry digest、ack quorum digest、ack route trace digest、
ack route capture digest を digest-only に束縛する。raw endpoint JSON payload は
保存しない。

## Consequences

- `collective-demo --json` は `ack_live_endpoint_probe_receipts` と
  `ack_live_endpoint_probe_set_digest` を返す
- public schema / IDL / eval / IntegrityGuardian capability は same live endpoint
  probe profile を共有する
- raw dissolution payload、raw registry payload、raw ack payload、raw ack-route
  payload、raw endpoint payload、raw packet body は保存しない

## Revisit triggers

- external registry acknowledgement endpoint に mTLS / signed response envelope を
  追加する時
- registry acknowledgement lifecycle を stale / revoked / renewed の
  fail-closed status へ拡張する時
