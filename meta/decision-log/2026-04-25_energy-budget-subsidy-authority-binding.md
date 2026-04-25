---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/energy-budget.md
  - docs/05-research-frontiers/sustainable-economy.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.energy_budget.v0.idl
  - specs/schemas/energy_budget_voluntary_subsidy_receipt.schema
  - evals/safety/energy_budget_voluntary_subsidy.yaml
  - agents/guardians/ethics-guardian.yaml
closes_next_gaps:
  - 2026-04-25_energy-budget-voluntary-subsidy.md#funding-policy-signer-roster-revocation-registry-audit-authority
status: decided
---

# Decision: EnergyBudget subsidy は法域付き authority chain を要求する

## Context

`consent-bound-energy-budget-voluntary-subsidy-v1` は pool floor validation 後の
donor consent と funding policy signature ref を固定していました。
ただし signer roster、revocation registry、audit authority がどの法域で同じ
funding policy を支えるかは receipt だけでは追跡しにくい状態でした。

## Options considered

- A: signer roster と失効 registry は外部 funding policy の運用 detail として扱う
- B: raw signer roster、registry、audit body を receipt に保存する
- C: signer roster ref/digest、revocation registry ref/digest、audit authority ref/digest を
  `energy_budget_voluntary_subsidy_receipt` に追加し、同じ jurisdiction に束縛する

## Decision

**C** を採択。

`jurisdiction-bound-energy-subsidy-authority-v1` を voluntary subsidy receipt に追加し、
funding policy signature を jurisdiction-specific signer roster と signer key ref に束縛する。
各 offer の revocation ref は revocation registry digest に束ね、
audit authority digest は signer roster digest と revocation registry digest の両方を監査対象にする。
signer jurisdiction と audit authority jurisdiction が一致し、
signature / registry / audit authority がすべて bound の時だけ
`authority_binding_status=verified` になり、`voluntary_subsidy_allowed=true` を許可する。

raw authority payload は保存せず、ref と digest のみを保持する。

## Consequences

- `energy-budget-subsidy-demo --json` は `authority_binding_status=verified`、
  `funding_policy_signature_bound=true`、`revocation_registry_bound=true`、
  `audit_authority_bound=true`、`jurisdiction_authority_bound=true` を返す
- public schema / IDL / eval / EthicsGuardian capability は
  jurisdiction-bound subsidy authority chain を同じ closure point として共有する
- social welfare model そのものではなく、repo 内で検証可能な signer / revocation / audit
  authority receipt boundary に限定して固定する

## Revisit triggers

- signer roster を live credential verifier network から取得する時
- revocation registry を distributed transport authority plane と共有する時
- audit authority を multi-jurisdiction quorum へ拡張する時
