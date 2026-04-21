---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/distributed-transport-attestation.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/distributed_transport_authority_route_trace.yaml
  - specs/interfaces/agentic.distributed_transport.v0.idl
  - specs/schemas/distributed_transport_os_observer_receipt.schema
  - specs/schemas/distributed_transport_authority_route_trace.schema
status: decided
---

# Decision: distributed transport の authority route trace に OS observer receipt を束縛する

## Context

2026-04-21 時点の distributed transport は、
actual non-loopback mTLS route trace と socket-level trace までは
repo 内で machine-checkable でしたが、
OS 側がその TCP tuple をどう見ていたかは
`docs/07-reference-implementation/README.md` の residual future work として
残っていました。

この状態では authority plane の route trace が成功しても、
OS-native な観測面で同じ `local_ip:local_port -> remote_ip:remote_port`
が live connection として見えていたかを
reference runtime の contract に束縛できませんでした。

## Options considered

- A: socket trace だけを truth source に保ち、OS observer は future work に残す
- B: bounded な `netstat` / `lsof` observer receipt を追加し、
  authority route trace に同じ TCP tuple と connection state を束縛する
- C: いきなり privileged raw packet capture / tcpdump export まで実装する

## Decision

**B** を採択。

## Consequences

- `distributed_transport_os_observer_receipt.schema` を追加し、
  `observed_sources / connection_states / owning_pid / tuple_digest` を固定する
- `trace_non_loopback_authority_routes` は request 送信直後の live socket に対して
  `netstat` / `lsof` を走らせ、同じ TCP tuple を少なくとも 1 source で観測できた時だけ
  `os_observer_complete=true` とする
- `distributed_transport_authority_route_trace` は
  socket trace と OS observer receipt を同時に持ち、
  どちらかが欠けた場合は `trace_status=authenticated` にしない
- `distributed-transport-demo` は authority-plane per-server digest と
  socket trace に加えて、OS 側の tuple 観測結果も JSON で返す
- residual future work は broad な「OS-native packet capture」一般論ではなく、
  `cross-host authority routing` と
  `privileged raw packet capture export` に縮小される

## Revisit triggers

- route trace を single-host ではなく cross-host authority cluster へ拡張したい時
- netstat/lsof より下の raw packet metadata や tcpdump/pcap export が必要になった時
- authority route trace の OS observer receipt を reviewer network や governance attestation と共通化したい時
