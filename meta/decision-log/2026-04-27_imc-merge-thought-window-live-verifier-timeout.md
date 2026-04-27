---
date: 2026-04-27
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/imc-protocol.md
  - docs/03-protocols/inter-mind-comm.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.imc.v0.idl
  - specs/schemas/imc_merge_thought_ethics_receipt.schema
  - specs/schemas/imc_merge_thought_window_policy_verifier_receipt.schema
  - evals/interface/imc_merge_thought_ethics_gate.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - 2026-04-27_imc-merge-thought-window-live-verifier.md#request-timeout-validator
---

# Decision: IMC merge_thought live verifier timeout を authority digest に束縛する

## Context

`merge-thought-window-live-verifier-receipt-v1` は live HTTP verifier の response
digest と signature digest を束縛していたが、`request_timeout_ms` の runtime
validator と public schema の上限が一致していなかった。

## Decision

IMC merge_thought window policy verifier probe の request timeout を 250ms 以下に固定し、
`imc_merge_thought_window_policy_verifier_receipt.schema` で first-class schema にする。

`merge_window_policy_authority` は各 verifier receipt の request timeout set と
timeout budget binding flag を authority digest に含める。receipt validation は
`request_timeout_ms`、`request_timeout_budget_ms`、`request_timeout_budget_bound` を
検証し、timeout budget が外れた verifier receipt を fail-closed にする。

## Consequences

- `imc-demo --json` は `merge_thought_ethics_window_policy_timeout_bound=true` を返す
- public schema / IDL / eval / IntegrityGuardian capability は verifier timeout budget を検証する
- raw policy / verifier / response-signature payload は保存しない

## Revisit triggers

- production verifier network が 250ms より短い timeout tier を要求する時
- window policy verifier quorum を法域別 latency class へ分割する時
