---
date: 2026-04-25
deciders:
  - codex
  - integrity-guardian
status: decided
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_remote_authority_retry_budget_receipt.schema
  - evals/interface/wms_remote_authority_retry_budget.yaml
closes_next_gaps:
  - 2026-04-25_wms-remote-authority-retry-budget.md#signed-jurisdiction-rate-limit
---

# Decision: WMS remote authority retry budget を signed jurisdiction rate limit へ束縛する

## Context

`bounded-remote-authority-adaptive-retry-budget-v1` は recovered fan-out retry を
route-health observation、fixed exponential schedule、engine transaction log の
fan-out entry に束縛していました。一方で、remote authority が返す signed retry
budget や jurisdiction-specific rate limit は first-class evidence ではなく、retry
schedule がどの法域の rate limit と signer key に従ったかを machine-checkable に
検証できませんでした。

## Decision

`signed-jurisdiction-rate-limit-retry-budget-v1` を retry budget receipt に追加します。
route-health observation は `remote_jurisdiction`、`jurisdiction_rate_limit_ref`、
`jurisdiction_retry_limit_ms`、`signer_key_ref`、`jurisdiction_rate_limit_digest`、
`authority_signature_digest` を持ち、schedule entry は同じ evidence を複写します。
`within_budget` は fixed exponential backoff と jurisdiction retry limit の両方を
満たした時だけ true になります。

## Consequences

- `wms-demo --json` の `remote_authority_retry_budget` は
  `signature_policy_id=signed-jurisdiction-rate-limit-retry-budget-v1` と
  `remote_jurisdictions=["JP-13"]` を返す
- public schema / IDL / eval / Integrity Guardian capability は同じ signed jurisdiction
  retry budget contract を共有する
- raw remote authority transcript は保存せず、rate limit payload と authority signature は
  digest / ref だけで束縛する

## Revisit Triggers

- jurisdiction policy registry を distributed transport authority plane と共通化する時
- retry budget を authority health SLO や participant cardinality に応じて可変化する時
