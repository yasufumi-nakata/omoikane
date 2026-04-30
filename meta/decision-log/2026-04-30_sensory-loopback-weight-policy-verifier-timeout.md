---
date: 2026-04-30
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/sensory-loopback.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.sensory_loopback.v0.idl
  - specs/schemas/sensory_loopback_biodata_arbitration_binding.schema
  - specs/schemas/sensory_loopback_latency_weight_policy_verifier_quorum.schema
  - evals/interface/sensory_loopback_biodata_arbitration.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - sensory-loopback-weight-policy-verifier-timeout
---

# Decision: weighted latency policy verifier は request timeout budget を束縛する

## Context

`weighted-latency-policy-live-verifier-quorum-v1` は weighted Sensory Loopback の
latency weight policy authority が fresh であることを 2 verifier quorum へ束縛していた。
しかし verifier response がどの request timeout budget で取得されたかは
machine-readable な digest set ではなく、fresh だが unbounded な verifier response を
weighted quorum acceptance に混ぜる余地が残っていた。

## Decision

latency weight policy verifier quorum の request timeout を `250ms` 以下に固定し、
各 verifier receipt へ `request_timeout_ms`、`request_timeout_budget_ms`、
`request_timeout_budget_bound`、`observed_latency_ms` を追加する。

quorum は `verifier_request_timeout_digest_set` と
`verifier_request_timeout_budget_bound=true` を持ち、response digest と quorum digest の
両方に timeout budget evidence を束縛する。weighted arbitration binding は
`latency_weight_policy_verifier_timeout_bound=true` を保持し、weighted quorum acceptance は
fresh verifier quorum だけでなく timeout-bound verifier quorum も要求する。

## Consequences

- `sensory-loopback-demo --json` は weighted latency path で
  `latency_weight_policy_verifier_timeout_bound=true` を返す。
- public schema / IDL / eval / IntegrityGuardian policy は 250ms request timeout budget と
  raw verifier / response / signature payload redaction を検証する。
- strict all-pass latency path は verifier profile / timeout binding を `not-bound` / `false` のまま維持する。

## Revisit triggers

- production verifier network が 250ms より短い latency tier を要求する時
- weighted latency verifier quorum を jurisdiction-specific timeout class へ分割する時
- 4 participant を超える federated sensory field の weighted quorum を導入する時
