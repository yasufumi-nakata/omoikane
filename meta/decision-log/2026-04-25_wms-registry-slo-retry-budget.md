---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_remote_authority_retry_budget_receipt.schema
  - evals/interface/wms_remote_authority_retry_budget.yaml
  - agents/guardians/integrity-guardian.yaml
closes_next_gaps:
  - 2026-04-25_wms-engine-adapter-signature-binding.md#registry-bound-retry-schedule
status: decided
---

# Decision: WMS retry budget は registry / SLO snapshot 由来の schedule にする

## Context

`signed-jurisdiction-rate-limit-retry-budget-v1` は remote jurisdiction、
jurisdiction-specific rate limit、signer key ref、authority signature digest を
route-health observation と schedule entry に束縛していました。
ただし schedule がどの jurisdiction policy registry と authority SLO snapshot から
導出されたかは、rate limit ref だけでは reviewer が機械的に追跡しにくい状態でした。

## Options considered

- A: signed rate-limit ref だけを維持し、registry と SLO は運用側の外部文脈に残す
- B: raw registry / SLO payload を receipt に保存する
- C: registry ref/digest と SLO snapshot ref/digest を route-health observation と schedule entry に複写し、schedule limit を digest-only に導出する

## Decision

**C** を採択。

`registry-bound-authority-retry-slo-v1` を retry budget の追加 policy とし、
`jurisdiction-policy-registry-bound-retry-v1` と
`authority-slo-snapshot-retry-window-v1` の digest を observation に束縛する。
schedule entry は `registry-slo-derived-retry-schedule-v1` として、
fixed exponential backoff、jurisdiction retry limit、registry/SLO derived limit の
全てを満たす場合だけ `budget_decision=retry` になる。

raw registry body、raw SLO snapshot body、raw remote transcript は保存しない。

## Consequences

- `wms-demo --json` の `remote_authority_retry_budget` scenario は
  `jurisdiction_policy_registry_bound`、`authority_slo_snapshot_bound`、
  `registry_slo_schedule_bound`、`registry_bound_retry_budget_bound` を返す
- public schema / IDL / eval / IntegrityGuardian capability は
  registry / SLO derived schedule を同じ closure point として共有する
- retry schedule の説明責任は rate-limit signature だけでなく、
  registry snapshot と SLO snapshot の digest chain でも検証できる

## Revisit triggers

- 複数 jurisdiction の registry snapshot が同一 retry schedule に混在する時
- authority SLO snapshot を live endpoint 取得に昇格する時
