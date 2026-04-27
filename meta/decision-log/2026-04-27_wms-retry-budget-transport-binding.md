---
date: 2026-04-27
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_remote_authority_retry_budget_receipt.schema
  - evals/interface/wms_remote_authority_retry_budget.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
---

# Decision: WMS retry budget を SLO quorum transport trace に束縛する

## Context

WMS authority SLO quorum は non-loopback route trace、cross-host binding、
OS observer digest set に束縛されていた。一方、retry budget receipt 自体は
primary SLO probe と registry/SLO-derived schedule を受け取るだけで、
同じ transport trace digest set を first-class に mirror していなかった。

## Decision

`wms_remote_authority_retry_budget_receipt` に
`authority-retry-budget-slo-quorum-transport-binding-v1` を追加し、
SLO quorum receipt の digest、primary probe digest、accepted probe digest set、
authority route trace digest、route binding refs、OS observer tuple digest set、
OS observer host-binding digest set を retry budget へ直接束縛する。

retry budget は `authority_slo_probe_quorum_bound=true` と
`retry_budget_transport_trace_bound=true` が両方成立しなければ
`budget_status=complete` にならない。raw remote transcript と raw route payload は保存しない。

## Consequences

- `wms-demo --json` の remote authority retry budget は SLO quorum transport binding を返す
- public schema / IDL / eval / Integrity Guardian capability は同じ policy id を共有する
- unit test は quorum digest drift と route binding ref drift を retry budget 側で検出する

## Revisit triggers

- retry budget を repo 外 live authority adapter へ接続する時
- SLO quorum と retry budget を別 transport plane に分離する必要が出た時
