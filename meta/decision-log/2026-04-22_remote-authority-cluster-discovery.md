---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/distributed-transport-attestation.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/distributed_transport_authority_cluster_discovery.yaml
  - specs/interfaces/agentic.distributed_transport.v0.idl
  - specs/schemas/distributed_transport_authority_cluster_discovery.schema
  - specs/schemas/distributed_transport_authority_route_target_discovery.schema
status: decided
---

# Decision: remote authority-cluster discovery を review-capped contract に縮約する

## Context

2026-04-22 時点の distributed transport reference runtime は
live root directory、bounded authority plane、authority churn、
bounded route-target discovery、non-loopback mTLS route trace、
PCAP export、privileged capture acquisition まで
machine-checkable でした。

一方で remote authority-cluster discovery 自体は未実装で、
authority route trace の upstream には reviewed `route_catalog` しかありませんでした。
この状態では route trace 前の authority-cluster 選定が
repo 外の live seed に対して first-class artifact 化されず、
future-work hit として残っていました。

## Options considered

- A: reviewed `route_catalog` 前提を維持し、remote authority-cluster discovery は引き続き未実装にする
- B: live remote seed をそのまま open-world discovery として trace に流し込み、選定 contract を持たない
- C: live remote seed を probe しつつ、candidate cluster と accepted route catalog を review-capped discovery artifact に縮約してから downstream へ渡す

## Decision

Option C を採択します。

`DistributedTransportService` は
`discover_remote_authority_clusters` を持ち、
`review-capped-authority-cluster-discovery-v1` を canonical profile に固定します。

この artifact は次を必須化します。

- `seed_refs` ごとの `candidate_targets` / `candidate_clusters` を記録すること
- `review_budget` が全 seed を覆えない場合は fail-closed にすること
- active authority-plane member 全件を cover し、`remote_host_attestation_ref` が complete な cluster だけを accepted にすること
- accepted cluster が 1 件に定まらない場合は fail-closed にすること
- downstream には `accepted_route_catalog_ref / digest` と authority-plane-bound route catalog だけを渡すこと

## Consequences

- `distributed-transport-demo` は
  `authority_plane -> authority_cluster_discovery -> authority_route_target_discovery -> authority_route_trace`
  の chain を JSON で machine-checkable に示せます
- gap-report truth source から
  remote authority-cluster discovery の future-work line を外せます
- reviewed `route_catalog` は curated ingress として残しつつ、
  live remote seed からの ingress も同じ downstream discovery contract に揃えられます

## Revisit triggers

- accepted cluster を 1 件ではなく ranked shortlist として残したくなった時
- review budget を Council / Guardian policy と動的連携したくなった時
- seed transport を HTTP JSON 以外へ拡張したくなった時
