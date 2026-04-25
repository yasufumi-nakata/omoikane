---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_authority_slo_probe_receipt.schema
  - specs/schemas/wms_remote_authority_retry_budget_receipt.schema
  - evals/interface/wms_remote_authority_retry_budget.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - 2026-04-25_wms-registry-slo-retry-budget.md#authority-slo-live-endpoint
---

# Decision: WMS authority SLO snapshot を live probe receipt に束縛する

## Context

`registry-bound-authority-retry-slo-v1` は remote authority retry schedule を
jurisdiction policy registry digest と authority SLO snapshot digest へ束縛していました。
一方で、authority SLO snapshot が live endpoint から取得されたことは first-class
artifact ではなく、reviewer は SLO retry window が static fixture 由来か live probe
由来かを machine-checkable に区別できませんでした。

## Decision

`live-authority-slo-snapshot-probe-v1` を追加し、WMS demo は bounded local HTTP JSON
endpoint から authority SLO payload を取得してから retry budget を作ります。
probe receipt は endpoint ref、HTTP status、observed probe latency、network response
digest、authority SLO snapshot digest、jurisdiction policy registry digest を保存し、
raw SLO payload は保存しません。

remote authority retry budget は `authority_slo_live_probe_bound=true` と
`authority_slo_probe_digests` を持つ場合だけ complete になります。

## Consequences

- `wms-demo --json` は `remote_authority_slo_probe_receipt` を返す
- `wms_remote_authority_retry_budget_receipt.schema` は live SLO probe receipt coverage を必須にする
- IntegrityGuardian は remote authority SLO live probe receipt を retry schedule の前提 evidence として検証する

## Revisit triggers

- cross-host authority SLO endpoint を distributed transport authority route trace と同じ transport plane に載せる時
- authority SLO probe を複数 jurisdiction /複数 authority の quorum へ拡張する時
