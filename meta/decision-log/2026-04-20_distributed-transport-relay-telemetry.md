---
date: 2026-04-20
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/distributed-transport-attestation.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/distributed_transport_relay_telemetry.yaml
  - specs/interfaces/agentic.distributed_transport.v0.idl
  - specs/schemas/distributed_transport_relay_telemetry.schema
status: decided
---

# Decision: distributed transport の multi-hop relay telemetry を bounded surface として固定する

## Context

`agentic.distributed_transport.v0` は participant attestation、key rotation、
federated trust-root quorum、multi-hop anti-replay までは fixed されていましたが、
`docs/07-reference-implementation/README.md` の future work 先頭には
`multi-hop anti-replay の telemetry` が残っていました。
この状態では receipt verdict は machine-checkable でも、
どの relay hop がどの jurisdiction / network zone を通り、
どの latency と trust-root visibility を観測したのかを
reference runtime 内で一貫して追跡できませんでした。

## Options considered

- A: telemetry は actual network 側の責務として残し、receipt status だけを truth source にする
- B: ledger event だけ追加し、IDL / schema / eval は増やさない
- C: relay hop telemetry を `capture_relay_telemetry` と専用 schema で固定し、
  receipt の anti-replay / root quorum verdict を mirror する

## Decision

**C** を採択。

## Consequences

- `distributed_transport_relay_telemetry.schema` を追加し、
  `relay_hops[]` に `relay_id / relay_endpoint / jurisdiction / network_zone /
  hop_nonce / observed_latency_ms / root_refs_seen / route_binding_ref` を保持する
- `capture_relay_telemetry` は `receipt.hop_nonce_chain` と同順の telemetry を返し、
  最終 hop `delivery_status` を `receipt_status` と一致させる
- `anti_replay_status` と `replay_guard_status` は receipt authenticity checks を mirror し、
  replay-blocked path でも telemetry artifact 自体は残す
- `distributed-transport-demo` は rotated federation path と
  replay-blocked heritage path の relay telemetry を JSON で可視化する
- README future-work から `multi-hop anti-replay telemetry` を外し、
  残課題を `actual network PKI / key server` に絞る

## Revisit triggers

- relay telemetry を real network sockets / tracing backend / packet capture へ接続したい時
- relay policy を latency だけでなく geography / jurisdiction-aware routing へ拡張したい時
- distributed oversight reviewer transport と共通 observability plane に統合したい時
