---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/distributed-transport-attestation.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/distributed_transport_authority_route_target_discovery.yaml
  - specs/interfaces/agentic.distributed_transport.v0.idl
  - specs/schemas/distributed_transport_authority_route_target_discovery.schema
  - specs/schemas/distributed_transport_authority_route_trace.schema
status: decided
---

# Decision: distributed transport の authority route targets を discovery receipt 化する

## Context

2026-04-21 までの distributed transport reference runtime は
live root directory、bounded authority plane、authority churn、
non-loopback mTLS route trace、OS observer receipt、
PCAP export、privileged capture acquisition まで
machine-checkable でした。

一方で authority route trace 直前は
`trace_non_loopback_authority_routes(route_targets=...)` に
raw な `route_targets` list を直接渡しており、
「stable authority plane と reviewed route catalog の対応関係」を
独立した receipt として残せていませんでした。

この状態では trace 自体は成立しても、
どの active authority-plane member を trace 対象として確定したのかを
前段 contract として監査できません。

## Options considered

- A: 既存 trace input を維持し、`route_targets` を ad hoc list のまま使い続ける
- B: stable authority plane と reviewed route catalog を束ねる `discover_authority_route_targets` receipt を追加し、trace はその receipt に束縛する
- C: reviewed catalog を飛ばして unbounded remote authority-cluster discovery まで一気に実装する

## Decision

Option B を採択します。

`DistributedTransportService` は
`discover_authority_route_targets` を持ち、
`bounded-authority-route-target-discovery-v1` を canonical profile に固定します。

この receipt は次を必須化します。

- stable authority plane の active member 全件を `key_server_ref` 単位で cover すること
- `server_endpoint / server_name / remote_host_ref / remote_host_attestation_ref /
  authority_cluster_ref / remote_jurisdiction / remote_network_zone` を target ごとに保持すること
- authority plane 由来の `server_role / authority_status / matched_root_refs` を retain すること
- trace receipt が `route_target_discovery_ref / route_target_discovery_digest` に束縛されること

## Consequences

- `distributed-transport-demo` は
  `authority_plane -> route_target_discovery -> authority_route_trace`
  の chain を JSON で machine-checkable に示せるようになります
- non-loopback authority trace は raw list ではなく discovery receipt provenance を持つため、
  reviewer-facing にも「どの active member を trace したか」が明確になります
- residual future work は raw `route_targets` 不在ではなく、
  reviewed catalog の外側にある unbounded remote authority-cluster discovery に縮小されます

## Revisit triggers

- route catalog 自体を reviewer verifier network や live root directory と統合したくなった時
- active-only ではなく draining member を含む alternate discovery scope を扱いたくなった時
- repo 外の dynamic authority-cluster discovery を bounded に持ち込みたくなった時
