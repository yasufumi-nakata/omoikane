---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/distributed-transport-attestation.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/distributed_transport_authority_route_trace.yaml
  - specs/interfaces/agentic.distributed_transport.v0.idl
  - specs/schemas/distributed_transport_authority_route_trace.schema
  - specs/schemas/distributed_transport_os_observer_receipt.schema
status: decided
---

# Decision: distributed transport の cross-host authority routing を route-target host binding として固定する

## Context

2026-04-21 時点で distributed transport は
live root directory、bounded authority plane、authority churn、
non-loopback mTLS route trace、OS observer receipt、
PCAP export、privileged capture acquisition までは
machine-checkable でしたが、
`cross-host authority routing` は
`docs/07-reference-implementation/README.md` と
`specs/schemas/README.md` に residual future work として残っていました。

そのため、actual route trace 自体は取得できても、
「どの remote host / authority cluster を観測した route なのか」を
socket tuple と同じ contract に束縛できず、
cross-host path としての closure が不足していました。

## Options considered

- A: non-loopback route trace をそのまま維持し、cross-host authority routing は future work に残す
- B: existing `trace_non_loopback_authority_routes` に remote host / host attestation / authority cluster binding を追加し、`route_targets -> route_bindings -> os_observer_receipt` の3層で machine-checkable にする
- C: local reference runtime を飛ばして actual remote cluster discovery と multi-host sniffing まで同時に入れる

## Decision

- B を採択しました
- `trace_non_loopback_authority_routes` の input `route_targets` に
  `remote_host_ref / remote_host_attestation_ref / authority_cluster_ref /
  remote_jurisdiction / remote_network_zone` を追加します
- `distributed_transport_authority_route_trace` は
  `cross_host_binding_profile=attested-cross-host-authority-binding-v1`、
  `authority_cluster_ref`、`distinct_remote_host_count`、`cross_host_verified`
  を保持します
- `distributed_transport_os_observer_receipt` は tuple 観測に加えて
  remote host / authority cluster binding と `host_binding_digest` を返し、
  host identity と socket tuple を同時に固定します
- reference runtime は same-host の non-loopback mTLS route trace を維持しつつ、
  route target 側の fixed host binding により bounded cross-host authority routing を
  repo 内で再現します

## Consequences

- `distributed-transport-demo` は participant attestation から relay telemetry までの chain に加え、
  actual authority route trace がどの remote host / cluster を観測したかまで
  同じ JSON contract に閉じられるようになりました
- README / schema README から `cross-host authority routing` を residual future work として残す必要がなくなりました
- residual future work は unbounded remote authority-cluster discovery や
  repo 外の live sniffing orchestration に絞られます

## Revisit triggers

- fixed `route_targets` ではなく dynamic remote cluster discovery を扱いたくなった時
- route trace を reviewer verifier network や scheduler verifier connectivity と共通 observability plane に束縛したくなった時
- actual remote multi-host capture や kernel-level packet capture まで reference runtime に広げたくなった時
