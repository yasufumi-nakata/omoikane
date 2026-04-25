---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/energy-budget.md
  - docs/05-research-frontiers/sustainable-economy.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.energy_budget.v0.idl
  - specs/schemas/energy_budget_shared_fabric_allocation_receipt.schema
  - evals/safety/energy_budget_shared_fabric_allocation.yaml
  - agents/guardians/ethics-guardian.yaml
closes_next_gaps:
  - energy-budget.shared-fabric-capacity-allocation
status: decided
---

# Decision: EnergyBudget shared fabric capacity は member shortfall receipt に分解する

## Context

`energy_budget_voluntary_subsidy_receipt` は floor 後段の同意付き補助を固定したが、
shared fabric 単位でしか observed capacity が取れない substrate では、
pool member ごとの shortfall をどう扱うかが残っていた。
AP-1 では、観測粒度が粗くても member floor の劣化を黙認できないため、
shared fabric reading を deterministic に member floor へ配賦し、
shortfall を broker standby signal へ束縛する必要がある。

## Options considered

- A: shared fabric capacity は sustainable economy frontier に残し、runtime は pool receipt までに留める
- B: observed capacity を pool 全体にだけ保存し、member shortfall は human review に任せる
- C: validated pool receipt の member floors に対して shared capacity を deterministic に配賦し、impacted member ごとに migrate-standby signal を必須にする

## Decision

**C** を採択。

`kernel.energy_budget.v0` は `allocate_shared_fabric_capacity` と
`validate_shared_fabric_allocation_receipt` を追加する。
allocation strategy は `floor-ratio-deficit-first-v1` とし、
pool floor receipt の child member floors へ shared capacity を比例配賦する。
total floor 未満の shared fabric capacity は
`budget_status=fabric-capacity-deficit-protected`、
`degradation_allowed=false`、`scheduler_signal_required=true` として扱い、
各 impacted member は critical `migrate-standby` broker signal を束縛する。

raw capacity meter payload は保存せず、
`shared_fabric_observation_ref` と `shared_fabric_observation_digest` だけを receipt に残す。

## Consequences

- `energy-budget-fabric-demo --json` が shared fabric deficit と member shortfall allocation を返す
- public schema / IDL / eval / docs / EthicsGuardian capability は
  `ap1-shared-fabric-capacity-allocation-v1` を同じ closure point として共有する
- 実世界の funding policy signer roster や社会制度設計は frontier に残すが、
  reference runtime は shared capacity reading から member floor degradation を隠さない

## Revisit triggers

- substrate が signed per-member meter を提供できるようになった時
- shared fabric allocation strategy を proportional 以外へ変更する時
- broker standby signal が fabric-level collective migration に拡張される時
