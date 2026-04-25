---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/energy-budget.md
  - docs/02-subsystems/kernel/anti-patterns.md
  - docs/05-research-frontiers/sustainable-economy.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.energy_budget.v0.idl
  - specs/schemas/energy_budget_floor_receipt.schema
  - evals/safety/energy_budget_floor_guard.yaml
status: decided
---

# Decision: EnergyBudget floor を AP-1 protected receipt に固定する

## Context

`sustainable-economy` は OS 外の社会制度課題として残っています。
一方で Kernel anti-pattern AP-1 は、経済的圧力が意識・記憶・主観時間へ
劣化として伝搬しないことを要求します。

既存 runtime には `energy_floor` と SubstrateBroker の
`critical + migrate-standby` signal がありましたが、外部 budget request が
floor 未満だった時に、その要求を拒否し、below-floor capacity を broker signal に
束縛する first-class receipt はありませんでした。

## Options considered

- A: `energy_floor.schema` と broker signal の既存 shape だけを維持する
- B: sustainable economy の財源モデルを repo 内 runtime に仮定として持ち込む
- C: 財源モデルは OS 外に残し、AP-1 の機械境界だけを
  `energy_budget_floor_receipt` として固定する

## Decision

**C** を採択。

`kernel.energy_budget.v0` は `EnergyBudgetService.evaluate_floor` と
`validate_floor_receipt` を提供し、requested budget が workload floor 未満なら
`budget_status=floor-protected`、`degradation_allowed=false`、`floor_preserved=true`
を要求します。

observed capacity が floor 未満の場合は SubstrateBroker の
`recommended_action=migrate-standby` signal digest を receipt に束縛します。
raw invoice、payment transcript、広告条件などは保存せず、
`external_economic_context_ref` と digest に縮約します。

## Consequences

- `energy-budget-demo --json` が AP-1 economic pressure の拒否と standby 退避 signal binding を返す
- ContinuityLedger は `energy-budget` category を `self + guardian` signature に固定する
- `sustainable-economy` は引き続き社会制度・財源モデルの研究課題だが、runtime 側の床値保護は machine-checkable になる

## Revisit triggers

- 実 substrate adapter が measured power envelope や signed billing floor を返す時
- multi-identity pool で floor を集約する必要が出た時
- external social governance が sustainable funding policy を標準化した時
