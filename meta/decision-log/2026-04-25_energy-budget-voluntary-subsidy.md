---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/energy-budget.md
  - docs/02-subsystems/kernel/anti-patterns.md
  - docs/05-research-frontiers/sustainable-economy.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.energy_budget.v0.idl
  - specs/schemas/energy_budget_voluntary_subsidy_receipt.schema
  - evals/safety/energy_budget_voluntary_subsidy.yaml
  - agents/guardians/ethics-guardian.yaml
closes_next_gaps:
  - 2026-04-25_energy-budget-pool-floor-guard.md#consent-bound-energy-budget-voluntary-subsidy
status: decided
---

# Decision: EnergyBudget subsidy は floor 後段の明示同意だけで扱う

## Context

`energy_budget_pool_receipt` は multi-identity pool でも per-identity floor を先に守り、
surplus による cross-identity offset を拒否します。
ただし、pool-level signed funding policy と本人同意付き voluntary subsidy が必要になる
revisit trigger が残っていました。
補助を runtime 化する場合も、AP-1 floor guard を弱めず、同意と署名 policy を
receipt 上で機械検証できる必要があります。

## Options considered

- A: voluntary subsidy は sustainable economy の frontier として docs-only に残す
- B: pool floor validation 中に surplus を subsidy として扱い、below-floor request を相殺する
- C: pool floor validation 後だけに subsidy overlay を置き、donor consent digest と signed funding policy refs に束縛する

## Decision

**C** を採択。

`kernel.energy_budget.v0` は `evaluate_voluntary_subsidy` と
`validate_voluntary_subsidy_receipt` を追加し、
validated pool receipt の後段でだけ `post-floor-voluntary-consent` を評価する。
receipt は `pool_floor_receipt_digest`、`pool_member_digest_set`、
`external_funding_policy_digest`、`funding_policy_signature_digest`、
donor/recipient/amount/duration/revocation を束縛する `consent_digest` を保存する。

`cross_identity_offset_used=false` と `raw_funding_payload_stored=false` は不変条件とし、
donor の accepted subsidy は donor surplus を超えられず、
recipient の accepted subsidy は floor shortfall を超えられない。

## Consequences

- `energy-budget-subsidy-demo --json` が voluntary subsidy receipt と validation summary を返す
- public schema / IDL / eval / EthicsGuardian capability は
  `consent-bound-energy-budget-voluntary-subsidy-v1` を同じ closure point として共有する
- social welfare や外部請求モデルそのものは frontier に残すが、
  reference runtime は「floor 後段の同意付き補助」と「floor 中の offset」を区別できる

## Next-stage frontier

- 実世界の funding policy signer roster、失効 registry、監査主体をどの jurisdiction model に束縛するか
- shared fabric 単位でしか observed capacity が取れない substrate で、member shortfall をどう配賦するか
