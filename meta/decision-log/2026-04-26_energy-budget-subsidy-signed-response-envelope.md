---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/energy-budget.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.energy_budget.v0.idl
  - specs/schemas/energy_budget_subsidy_verifier_receipt.schema
  - specs/schemas/energy_budget_subsidy_verifier_quorum_receipt.schema
  - evals/safety/energy_budget_subsidy_verifier.yaml
  - agents/guardians/ethics-guardian.yaml
status: decided
closes_next_gaps:
  - energy-budget.subsidy-verifier.signed-response-envelope
---

# Decision: EnergyBudget subsidy verifier response を signed envelope に束縛する

## Context

`multi-jurisdiction-energy-subsidy-verifier-quorum-v1` は primary / backup の
live HTTP verifier receipt を quorum に束ねていました。ただし endpoint response が
どの verifier signing key により発行されたか、また response signature payload を保存せずに
どの digest へ縮約するかは first-class contract ではありませんでした。

## Decision

`signed-energy-subsidy-verifier-response-envelope-v1` を
`energy_budget_subsidy_verifier_receipt` に追加します。
response signature digest は response digest、challenge digest、verifier authority、
verifier jurisdiction、route ref、response signing key ref、trust root digest を
`energy-subsidy-verifier-response-signature-digest-v1` で束縛します。

quorum receipt は accepted live verifier receipt から
`accepted_verifier_response_signature_digests` と
`signed_response_envelope_quorum_bound=true` を派生し、
accepted response digest だけでなく signed envelope の集合も machine-checkable にします。

## Consequences

- `energy-budget-subsidy-demo --json` は signed response envelope と quorum binding を返す
- voluntary subsidy acceptance は `signer_roster_verifier_bound` と
  `signer_roster_verifier_quorum_bound` の内側で signed response envelope を必須にする
- public schema / IDL / eval / EthicsGuardian capability は同じ signed envelope profile を共有する
- raw verifier payload と raw response signature payload は保存しない

## Revisit triggers

- verifier signing key rotation を separate roster policy として独立させる時
- subsidy authority を quorum threshold policy registry から動的解決する時
