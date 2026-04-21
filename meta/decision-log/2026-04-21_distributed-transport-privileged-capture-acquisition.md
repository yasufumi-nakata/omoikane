---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/distributed-transport-attestation.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/distributed_transport_privileged_capture_acquisition.yaml
  - specs/interfaces/agentic.distributed_transport.v0.idl
  - specs/schemas/distributed_transport_privileged_capture_acquisition.schema
status: decided
---

# Decision: distributed transport の privileged live interface capture acquisition を delegated lease として固定する

## Context

2026-04-21 時点で distributed transport は
authority route trace と trace-bound PCAP export までは
machine-checkable でしたが、
`docs/07-reference-implementation/README.md` と
`specs/schemas/README.md` には
`privileged live interface capture acquisition` が
residual future work として残っていました。

そのため、authenticated route trace と verified packet export を
実際の live capture handoff へ進める時に、
どの interface を対象にし、
どの filter を束縛し、
どの権限 broker が lease を発行したかを
repo 内で固定できていませんでした。

## Options considered

- A: privileged capture acquisition は future work のまま残し、synthetic PCAP export だけを維持する
- B: route trace + packet export から interface / filter / broker lease / command preview を返す delegated acquisition receipt を追加する
- C: いきなり root 権限の live sniffing と cross-host route capture まで同時に扱う

## Decision

Option B を採択します。

`DistributedTransportService` は
`acquire_privileged_interface_capture()` を持ち、
authenticated authority route trace と
verified packet-capture export を入力に、
`bounded-live-interface-capture-acquisition-v1` receipt を返します。

contract は次を必須にします。

- traced local IP 全てが 1 つの host interface に解決されること
- capture filter が traced route の双方向 tuple をすべて束縛すること
- delegated broker が interface / filter digest / route binding set を echo して lease を返すこと
- capture command preview が `tcpdump`、resolved interface、exact filter を保持すること

reference runtime は actual live packet sniffing ではなく、
delegated broker から lease と command preview を受け取る bounded acquisition として固定します。

## Consequences

- `distributed-transport-demo` は packet export の次段として
  `distributed_transport_privileged_capture_acquisition` を返し、
  interface / filter / lease / broker attestation を machine-checkable にします
- residual future work は `cross-host authority routing` へさらに絞られます
- live capture 実行そのものは broker 外部の責務として残しつつ、
  repo 内では acquisition handoff の shape を固定できます

## Revisit triggers

- cross-host authority routing を actual remote cluster へ広げる時
- delegated broker ではなく OS-native privilege handoff まで同じ contract に入れたくなった時
- `tcpdump` 以外の capture backend を canonical command preview に含めたくなった時
