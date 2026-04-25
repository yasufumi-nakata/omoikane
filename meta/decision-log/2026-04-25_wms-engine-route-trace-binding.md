---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_engine_route_binding_receipt.schema
  - evals/interface/wms_engine_route_binding.yaml
status: decided
closes_next_gaps:
  - 2026-04-25_wms-engine-transaction-log.md#wms.engine.cross-host-route-binding
---

# Decision: WMS engine transaction log を authority route trace へ束縛する

## Context

`digest-bound-wms-engine-transaction-log-v1` は WMS source artifacts と
external engine adapter transaction entry を digest-only に束縛していました。
一方で、その engine adapter boundary がどの authenticated distributed transport
authority route 上で観測されたかは WMS 側の first-class receipt ではありませんでした。

## Options considered

- A: route trace binding は distributed transport demo の責務に留め、WMS engine log は単独で完結させる
- B: raw route transcript や packet body を WMS receipt に保存する
- C: completed engine log digest と authenticated cross-host authority-route trace digest、
  route binding refs、remote host refs、OS observer tuple / host-binding digest を
  `wms_engine_route_binding_receipt` に縮約する

## Decision

**C** を採択。

`distributed-transport-bound-wms-engine-adapter-route-v1` は
completed `wms_engine_transaction_log`、`non-loopback-mtls-authority-route-v1`、
`attested-cross-host-authority-binding-v1`、OS observer tuple digest を同じ receipt へ束縛する。
raw engine payload、raw route payload、packet body は保存しない。

## Consequences

- `wms-demo --json` は `engine_route_binding` scenario と
  `engine_route_binding_bound` validation を返す
- public schema / IDL / eval / Integrity Guardian capability は同じ policy id を共有する
- WMS engine adapter の external transport evidence は distributed transport surface への
  digest-only reference として reviewer-facing になる

## Revisit triggers

- real WMS engine adapter が route trace と signed engine transaction body hash を同時に返す時
- WMS engine route binding を live packet-capture export / privileged capture acquisition へ直接束縛する時
