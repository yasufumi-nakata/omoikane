---
date: 2026-04-30
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/sensory-loopback.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.sensory_loopback.v0.idl
  - specs/schemas/sensory_loopback_biodata_arbitration_binding.schema
  - evals/interface/sensory_loopback_biodata_arbitration.yaml
status: decided
closes_next_gaps:
  - sensory-loopback-weighted-latency-policy-authority
---

# Decision: weighted latency quorum weight は policy authority digest に束縛する

## Context

`weighted-latency-quorum-v1` は 3-4 participant の shared Sensory Loopback で、
blocked latency gate を failed participant id として残したまま bounded acceptance できる。
しかし participant weight と threshold は binding digest に含まれるだけで、
どの外部 policy authority がその重み付けを承認したかを machine-readable に束縛していなかった。

## Decision

weighted quorum path に `weighted-latency-quorum-authority-v1` を追加する。
`participant_latency_weights` または `latency_quorum_threshold` を渡す場合は、
`latency_weight_policy_authority_ref`、
`latency_weight_policy_authority_digest`、
`latency_weight_policy_source_digest_set` を必須にする。

binding は participant latency weight digest と policy authority digest を別々に保持し、
さらに `latency_weight_policy_digest` を `latency_quorum_digest` に混ぜる。
strict all-pass path は `latency_weight_policy_profile=not-bound` のまま残し、
weight policy authority ref / digest / source digest set は空にする。

## Consequences

- `sensory-loopback-demo --json` は weighted quorum の authority ref / digest /
  source digest set を返し、public schema validation で確認する。
- unit / integration / eval は weighted path の `latency_weight_policy_bound` と
  `latency_weight_policy_digest_bound` を検証する。
- raw latency weight policy payload と raw authority payload は保存しない。

## Revisit triggers

- weight policy authority を live verifier quorum で freshness 判定する時
- 4 participant を超える federated sensory field へ拡張する時
- participant weight を session 内で動的更新する時
