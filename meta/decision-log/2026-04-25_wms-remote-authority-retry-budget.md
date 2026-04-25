---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_remote_authority_retry_budget_receipt.schema
  - evals/interface/wms_remote_authority_retry_budget.yaml
status: decided
closes_next_gaps:
  - 2026-04-25_wms-distributed-approval-fanout-retry.md#remote-authority-adaptive-retry-budget
---

# Decision: WMS remote authority retry を bounded adaptive budget receipt へ束縛する

## Context

`bounded-distributed-approval-fanout-retry-v1` は partial outage の recovered
retry attempt を fan-out receipt に残していました。
一方で real remote authority へ近づけた時の adaptive retry budget が、
route-health observation、backoff schedule、external engine transaction log の
fan-out materialization と同じ digest chain に乗ることは確認できていませんでした。

## Options considered

- A: real remote authority 実装が来るまで retry budget は operational docs にだけ残す
- B: remote authority transcript を WMS receipt に保存する
- C: route-health observation digest、fixed exponential backoff schedule、
  engine transaction log の `approval_fanout_bound` entry を
  `wms_remote_authority_retry_budget_receipt` に縮約する

## Decision

**C** を採択。

`bounded-remote-authority-adaptive-retry-budget-v1` は
`base_retry_after_ms=250`、`exponential_multiplier=2`、`max_retry_attempts=2`、
`total_retry_budget_ms=1500` を fixed profile とし、
各 recovered retry attempt を route-health observation digest と schedule entry digest に束縛する。
同じ receipt は external engine transaction log の `approval_fanout_bound`
source artifact digest が final fan-out digest と一致することも要求する。
raw remote authority transcript は保存しない。

## Consequences

- `wms-demo --json` は `remote_authority_retry_budget` scenario と
  `remote_authority_retry_budget_bound` validation を返す
- `interface.wms.v0`、public schema、eval、Integrity Guardian capability は
  同じ policy id を共有する
- partial outage retry は fan-out receipt だけでなく、external authority retry budget と
  engine materialization の両方へ digest-bound になる

## Revisit triggers

- real remote authority が signed retry budget または jurisdiction-specific rate limit を返す時
- retry budget を participant 数や authority health SLO で可変化する時
