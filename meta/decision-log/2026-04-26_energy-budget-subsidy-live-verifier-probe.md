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
  - 2026-04-26_energy-budget-subsidy-signer-roster-verifier.md#verifier-endpoint-actual-remote-network-probe
status: decided
---

# Decision: EnergyBudget subsidy verifier は live HTTP probe receipt にする

## Context

`energy-subsidy-signer-roster-live-verifier-v1` は signer roster digest、
signer key ref、funding policy digest、funding policy signature digest を
digest-only verifier receipt に束縛していました。
ただし `energy-budget-subsidy-demo` の verifier receipt は loopback 生成であり、
actual endpoint response digest と timeout budget を同じ receipt に残していませんでした。

## Options considered

- A: loopback verifier receipt を維持し、endpoint probing は運用文脈に残す
- B: raw verifier JSON response を voluntary subsidy receipt に保存する
- C: live HTTP verifier endpoint を probe し、response digest / timeout / latency / endpoint URL だけを receipt に保存する

## Decision

**C** を採択。

`EnergyBudgetService.probe_subsidy_signer_roster_verifier_endpoint` を追加し、
endpoint JSON が expected signer roster、signer key、funding policy digest、
funding policy signature digest、authority chain、trust root を返した時だけ
`live-http-json-energy-subsidy-signer-roster-verifier-v1` receipt を発行する。
receipt は `network_response_digest`、`request_timeout_ms`、
`observed_latency_ms`、`network_probe_bound=true` を保持し、
raw verifier payload は保存しない。

`evaluate_voluntary_subsidy` は caller-supplied verifier receipt を受け取り、
same funding policy / signer roster digest と一致する時だけ
`authority_binding_status=verified` を維持する。

## Consequences

- `energy-budget-subsidy-demo --json` は actual local HTTP verifier endpoint を probe した
  nested verifier receipt を返す
- public schema / IDL / eval / EthicsGuardian capability は
  loopback だけでなく live HTTP verifier receipt を検証対象に含める
- subsidy authority binding は signer roster digest に加えて
  endpoint response digest と latency budget でも reviewer が追跡できる

## Revisit triggers

- subsidy authority を multi-jurisdiction quorum へ広げる時
- remote verifier endpoint に mTLS / signed response envelope を追加する時
