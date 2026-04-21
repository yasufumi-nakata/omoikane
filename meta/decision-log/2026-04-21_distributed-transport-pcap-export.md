---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/distributed-transport-attestation.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/distributed_transport_packet_capture_export.yaml
  - specs/interfaces/agentic.distributed_transport.v0.idl
  - specs/schemas/distributed_transport_packet_capture_export.schema
status: decided
---

# Decision: distributed transport の authority route trace を trace-bound PCAP export へ落とす

## Context

2026-04-21 時点で distributed transport は
live root directory、authority plane、authority churn、
non-loopback mTLS route trace、OS observer receipt までは
machine-checkable でした。

一方で、authenticated な route trace を
packet-capture artifact として再利用できる contract はまだ無く、
`docs/07-reference-implementation/README.md` と
`specs/schemas/README.md` には
`privileged raw packet capture export` が residual gap として残っていました。

そのため、route trace が tuple / TLS / digest を保持していても、
packet-capture consumer に渡せる artifact 形式や
byte-count readback の基準は repo 内で固定されていませんでした。

## Options considered

- A: socket trace と OS observer のみを維持し、packet capture は future work のまま残す
- B: authenticated route trace を bounded な PCAP artifact へ export し、in-process readback と `tcpdump` readback を contract 化する
- C: いきなり cross-host authority routing と privileged live sniffing まで同時に扱う

## Decision

Option B を採択します。

`DistributedTransportService` は
`export_authority_route_packet_capture()` を持ち、
authenticated authority route trace から
`trace-bound-pcap-export-v1` artifact を生成します。

contract は次を必須にします。

- route ごとに `outbound-request` と `inbound-response` の 2 packet
- `local_ip / local_port / remote_ip / remote_port` と byte count の束縛
- in-process readback による tuple / payload length の再構成
- `tcpdump` がある環境では OS-native readback の追加確認

live privileged sniffing そのものではなく、
authenticated route trace を packet-capture artifact に落とし直す
bounded export として固定します。

## Consequences

- `distributed-transport-demo` は route trace の次段として
  `distributed_transport_packet_capture_export` を返し、
  PCAP artifact digest と readback digest を machine-checkable にします
- residual future work は broad な packet export 一般論ではなく、
  `cross-host authority routing` と
  `privileged live interface capture acquisition` へ縮小されます
- packet export は trace-derived synthetic PCAP に限定し、
  raw payload disclosure や privileged live capture は引き続き扱いません

## Revisit triggers

- authenticated route trace を cross-host authority cluster へ拡張したくなった時
- privileged interface capture を actual live acquisition として扱いたくなった時
- QUIC や non-TCP authority transport を packet export contract に追加したくなった時
