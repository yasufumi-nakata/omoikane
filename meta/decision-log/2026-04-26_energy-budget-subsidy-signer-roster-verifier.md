---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/energy-budget.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.energy_budget.v0.idl
  - specs/schemas/energy_budget_subsidy_verifier_receipt.schema
  - specs/schemas/energy_budget_voluntary_subsidy_receipt.schema
  - evals/safety/energy_budget_subsidy_verifier.yaml
  - agents/guardians/ethics-guardian.yaml
closes_next_gaps:
  - 2026-04-25_energy-budget-subsidy-authority-binding.md#signer-roster-live-credential-verifier-network
status: decided
---

# Decision: EnergyBudget subsidy signer roster は verifier receipt に束縛する

## Context

`jurisdiction-bound-energy-subsidy-authority-v1` は signer roster ref/digest、
signer key ref、revocation registry、audit authority を固定していました。
ただし signer roster を live credential verifier network から取得する段階へ進めた時、
funding policy signature と signer roster digest を同じ verifier bridge に束縛する
first-class receipt がありませんでした。

## Options considered

- A: signer roster ref/digest だけを維持する
- B: raw verifier transcript を subsidy receipt に保存する
- C: loopback verifier receipt を追加し、challenge/response digest と authority chain ref だけを保存する

## Decision

**C** を採択。

`energy-subsidy-signer-roster-live-verifier-v1` を追加し、
`EnergyBudgetService.build_subsidy_signer_roster_verifier_receipt` が
signer roster digest、signer key ref、funding policy digest、funding policy signature digest、
verifier endpoint、authority chain ref、trust root ref を challenge/response digest に束縛する。
voluntary subsidy receipt は nested `signer_roster_verifier_receipt` と
`signer_roster_verifier_receipt_digest` を持ち、
authority binding digest も verifier receipt digest を含む。

raw verifier payload は保存せず、`raw_verifier_payload_stored=false` を固定する。

## Consequences

- `energy-budget-subsidy-demo --json` は signer roster verifier receipt と
  `signer_roster_verifier_bound=true` を返す
- public schema / IDL / eval / EthicsGuardian capability は
  signer roster verifier bridge を同じ closure point として共有する
- voluntary subsidy acceptance は donor consent、floor preservation、authority chain に加え、
  verifier receipt validation も通った時だけ成立する

## Revisit triggers

- verifier endpoint を actual remote network probe へ置き換える時
- subsidy authority を multi-jurisdiction quorum へ広げる時
