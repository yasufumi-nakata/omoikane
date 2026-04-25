---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_distributed_approval_fanout_receipt.schema
  - evals/interface/wms_distributed_approval_fanout_retry.yaml
status: decided
closes_next_gaps:
  - wms.physics-rules.distributed-approval-fanout-retry
---

# Decision: WMS distributed approval fan-out partial outage を bounded retry receipt へ縮約する

## Context

`distributed-council-approval-fanout-v1` は complete collection を
Federation transport evidence に束縛できるようにしました。
ただし partial transport outage が起きた場合、retry attempt と最終 recovered
fan-out result が同じ digest family に載っていることは machine-checkable ではありませんでした。

## Options considered

- A: partial outage は operational layer のみで扱い、fan-out receipt には残さない
- B: failed transport transcript を WMS receipt に保存する
- C: retry attempt を `bounded-distributed-approval-fanout-retry-v1` として
  outage observation digest、retry window、recovery result digest、
  recovery transport receipt digest へ縮約する

## Decision

**C** を採択。

`max_retry_attempts=2`、`retry_window_ms=1500` を fixed profile とし、
`participant-retry-outage-digest-v1` で retry attempt digest set を作る。
recovered retry の `recovery_result_digest` と `recovery_transport_receipt_digest` が
最終 participant fan-out result に一致する時だけ、
`partial_outage_status=recovered` の complete fan-out receipt として扱う。

## Consequences

- `wms-demo --json` は observer participant の timeout retry を 1 件返す
- public `wms_distributed_approval_fanout_receipt.schema` は retry attempt set と
  partial outage recovery status を検証する
- physics_rules change は retry-recovered fan-out digest をそのまま束縛する

## Remaining scope

- real remote authority の exponential backoff や adaptive retry budget は、
  external operational profile を持つ段階で別 contract として扱う
