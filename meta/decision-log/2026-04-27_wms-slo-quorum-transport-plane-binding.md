---
date: 2026-04-27
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_authority_slo_probe_quorum_receipt.schema
  - evals/interface/wms_authority_slo_probe_quorum.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - 2026-04-27_wms-slo-threshold-authority-binding.md#authority-slo-quorum-non-loopback-transport-plane
---

# Decision: WMS authority SLO quorum を non-loopback transport plane に束縛する

## Context

WMS authority SLO quorum は live SLO probe set と signed threshold policy を束縛していました。
一方、SLO probe の `route_ref` が WMS engine route binding と同じ authenticated
non-loopback distributed transport plane 上にあることは first-class receipt ではありませんでした。

## Decision

`wms_authority_slo_probe_quorum_receipt` に
`authority-slo-quorum-non-loopback-transport-binding-v1` を追加し、
`distributed_transport_authority_route_trace` の trace digest、authority plane digest、
route target discovery digest、route binding refs、remote host refs、OS observer tuple /
host-binding digest set を digest-only で mirror します。

quorum receipt は SLO probe の `route_refs` が route trace の `route_binding_refs` と一致し、
route trace が cross-host / non-loopback / OS observer complete の時だけ
`authority_slo_transport_trace_bound=true` と
`authority_slo_transport_cross_host_bound=true` になります。
この 2 つが true でなければ `quorum_status=complete` になりません。

## Consequences

- `wms-demo --json` は SLO quorum を engine authority route trace と同じ route binding refs に載せる
- public schema / IDL / eval / IntegrityGuardian capability は raw route trace payload 無しで
  transport-plane binding を検証する
- raw SLO payload、raw threshold payload、raw route payload は保存しない

## Revisit triggers

- authority SLO route trace を repo 外 live service adapter へ接続する時
- WMS retry budget 側も transport route trace の digest set を直接要求する時
