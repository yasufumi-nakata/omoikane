---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/energy-budget.md
  - docs/02-subsystems/kernel/anti-patterns.md
  - docs/05-research-frontiers/sustainable-economy.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.energy_budget.v0.idl
  - specs/schemas/energy_budget_pool_receipt.schema
  - evals/safety/energy_budget_pool_floor_guard.yaml
status: decided
---

# Decision: EnergyBudget pool でも per-identity floor を先に守る

## Context

`energy_budget_floor_receipt` は単一 identity の AP-1 economic pressure を
floor-protected receipt に束縛していました。
一方で `sustainable-economy` の scaling path では multi-identity pool が必要になります。
aggregate requested budget だけを見ると、ある identity の surplus が別 identity の
below-floor request を隠し、AP-1 violation が pool 内で相殺される危険があります。

## Options considered

- A: pool は social governance 側の未確定として残し、single-identity receipt だけを維持する
- B: aggregate budget が total floor を覆っていれば pool 全体を accepted とする
- C: pool receipt は member receipt を先に検証し、cross-identity offset を明示的に拒否する

## Decision

**C** を採択。

`kernel.energy_budget.v0` は `evaluate_pool_floor` と `validate_pool_receipt` を追加し、
各 member の `energy_budget_floor_receipt` を child receipt として束縛する。
pool receipt は ordered child digest set、total requested/granted/observed budget、
`cross_identity_subsidy_allowed=false`、
`cross_identity_floor_offset_blocked=true` を返す。

aggregate requested budget が total floor を覆っていても、member の requested budget が
floor 未満なら `pool_budget_status=floor-protected` とし、degradation を許可しない。

## Consequences

- `energy-budget-pool-demo --json` が migration member の below-floor request と
  council member の surplus request を同時に可視化する
- public schema / IDL / eval / EthicsGuardian capability は
  `ap1-protected-energy-budget-pool-floor-v1` を同じ closure point として共有する
- sustainable economy の外部財源モデルは引き続き research frontier だが、
  pool 化で AP-1 をすり抜けない機械境界は reference runtime で固定される

## Revisit triggers

- pool-level signed funding policy が外部 governance から渡される時
- identity 間で voluntary subsidy を本人同意付きで扱う必要が出た時
- measured substrate capacity が per-member ではなく shared fabric 単位でしか観測できない時
