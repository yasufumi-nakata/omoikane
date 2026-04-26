---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/energy-budget.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.energy_budget.v0.idl
  - specs/schemas/energy_budget_subsidy_verifier_quorum_threshold_policy_receipt.schema
  - specs/schemas/energy_budget_subsidy_verifier_quorum_receipt.schema
  - evals/safety/energy_budget_subsidy_verifier.yaml
  - agents/guardians/ethics-guardian.yaml
status: decided
closes_next_gaps:
  - 2026-04-26_energy-budget-subsidy-verifier-quorum.md#quorum-threshold-policy-registry
---

# Decision: EnergyBudget subsidy verifier quorum threshold を signed policy receipt に束縛する

## Context

`multi-jurisdiction-energy-subsidy-verifier-quorum-v1` は primary `JP-13` verifier と
backup `SG-01` verifier の live receipt を 2 authority / 2 jurisdiction の quorum へ
束ねていました。ただし required authority / jurisdiction count は runtime 定数で、
reviewer は threshold が jurisdiction policy registry 由来かを machine-checkable に確認できませんでした。

## Decision

`signed-energy-subsidy-verifier-quorum-threshold-policy-v1` を追加し、
subsidy verifier quorum receipt は signed threshold policy receipt を内包する。
threshold policy は jurisdiction policy registry refs / digests、verifier jurisdiction set、
required authority count、required jurisdiction count、signer key ref、policy body digest、
signature digest を raw policy payload 無しで束縛する。

quorum は live verifier receipt set だけでなく、threshold policy の jurisdiction set と
required counts が accepted verifier set と一致し、policy body digest と signature digest が
検証できる時だけ `quorum_status=complete` になる。

## Consequences

- `energy-budget-subsidy-demo --json` は nested `threshold_policy_receipt` と validation flag を返す
- `energy_budget_subsidy_verifier_quorum_receipt.schema` は threshold policy digest と signature digest を必須にする
- EthicsGuardian は subsidy verifier quorum threshold が signed registry policy 由来であることを検証対象にする
- raw threshold policy payload は保存せず、registry digest / policy body digest / signature digest のみ保持する

## Revisit triggers

- threshold policy signer roster / revocation registry も live verifier quorum へ昇格する時
- subsidy verifier quorum を distributed transport route trace と同じ non-loopback transport plane に載せる時
