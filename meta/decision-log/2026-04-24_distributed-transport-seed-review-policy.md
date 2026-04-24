---
decision_id: distributed-transport-seed-review-policy
date: 2026-04-24
surface:
  - src/omoikane/agentic/distributed_transport.py
  - specs/schemas/distributed_transport_authority_seed_review_policy.schema
  - specs/interfaces/agentic.distributed_transport.v0.idl
  - evals/agentic/distributed_transport_authority_seed_review_policy.yaml
closes_next_gaps:
  - 2026-04-21_distributed-transport-privileged-capture-acquisition.md#gap-1
---

# Decision: remote authority-cluster seed review policy を first-class artifact にする

`gap-report --json` は clean でしたが、
`distributed-transport-attestation.md` には remote seed review の budget policy と
accepted cluster selection の厳格化が次の実装候補として残っていました。
既存 runtime は `discover_remote_authority_clusters` 内で review budget と accepted cluster
条件を検査していましたが、policy 自体は downstream や schema contract で独立検証できませんでした。

## 採用案

- `distributed_transport_authority_seed_review_policy` を追加し、
  `budget-bound-authority-seed-review-policy-v1` を固定する
- `review_budget`、`seed_count`、active authority-plane member、
  `single-accepted-cluster-after-budget-review-v1`、fail-closed 条件を digest-bound にする
- `distributed_transport_authority_cluster_discovery` は同じ policy を埋め込み、
  candidate cluster review に `review_policy_ref` / `review_policy_digest` を残す
- `distributed-transport-demo --json` は policy を top-level にも返し、
  public schema test が policy と discovery の digest binding を検証する

## 退けた案

- A: `review_budget` integer のまま維持する
  - budget は見えるが、active member coverage や accepted cluster mode が証跡化されない
- B: discovery schema の説明だけを更新する
  - runtime と CLI 出力が同じ contract を共有できない

## 残すもの

- 実 remote seed 運用、external trust anchor 運用、実ネットワーク上の seed lifecycle は
  repo 外の operational surface として残す
