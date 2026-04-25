---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/energy-budget.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.energy_budget.v0.idl
  - specs/schemas/energy_budget_subsidy_verifier_receipt.schema
  - specs/schemas/energy_budget_subsidy_verifier_quorum_receipt.schema
  - specs/schemas/energy_budget_voluntary_subsidy_receipt.schema
  - evals/safety/energy_budget_subsidy_verifier.yaml
  - agents/guardians/ethics-guardian.yaml
closes_next_gaps:
  - energy-budget.subsidy-verifier.multi-jurisdiction-quorum
status: decided
---

# Decision: EnergyBudget subsidy verifier を multi-jurisdiction quorum に束縛する

## Context

`live-http-json-energy-subsidy-signer-roster-verifier-v1` は voluntary subsidy の
signer roster evidence を 1 つの live HTTP verifier response digest に束縛していました。
ただし reviewer は、同じ signer roster / funding policy evidence が複数 authority と
複数 verifier jurisdiction から独立に確認されたかを machine-checkable に判断できませんでした。

## Options considered

- A: primary live verifier receipt のみで `authority_binding_status=verified` を維持する
- B: raw verifier responses を複数保存して人間 reviewer が比較する
- C: digest-only の quorum receipt を追加し、accepted verifier digest set / authority refs / jurisdictions / route refs / response digests を束縛する

## Decision

**C** を採択。

`multi-jurisdiction-energy-subsidy-verifier-quorum-v1` は primary `JP-13` verifier と
backup `SG-01` verifier の live HTTP receipt を 1 つの quorum receipt に束ねる。
quorum は accepted verifier authority refs と verifier jurisdictions がそれぞれ 2 件以上で、
primary verifier digest が accepted digest set に含まれ、かつ signer roster / signer key /
funding policy digest / funding policy signature digest が全 accepted receipt で一致した時だけ
`quorum_status=complete` になる。

## Consequences

- `energy-budget-subsidy-demo --json` は nested `signer_roster_verifier_quorum_receipt` を返す
- voluntary subsidy acceptance は単一 live verifier だけでなく `signer_roster_verifier_quorum_bound=true` も要求する
- public schema / IDL / eval / EthicsGuardian capability は同じ quorum profile を共有する
- raw verifier payload は引き続き保存せず、endpoint response digest と accepted receipt digests だけを保存する

## Revisit triggers

- remote verifier endpoint に mTLS / signed response envelope を追加する時
- subsidy authority を quorum threshold policy registry から動的解決する時
