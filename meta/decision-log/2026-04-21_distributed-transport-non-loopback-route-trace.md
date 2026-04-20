---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/distributed-transport-attestation.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/distributed_transport_authority_route_trace.yaml
  - specs/interfaces/agentic.distributed_transport.v0.idl
  - specs/schemas/distributed_transport_authority_route_trace.schema
status: decided
---

# Decision: distributed transport の authority plane を non-loopback mTLS route trace まで固定する

## Context

2026-04-20 時点の distributed transport は
live root directory、bounded authority plane、authority churn までは
machine-checkable でしたが、
actual non-loopback mTLS authority routing と socket-level tracing は
`docs/07-reference-implementation/README.md` と
`specs/interfaces/agentic.distributed_transport.v0.idl`
に future work として残っていました。

そのため、authority plane が「reachable」と主張していても、
どの local/remote socket tuple で接続し、
どの peer/client certificate fingerprint で mTLS が成立し、
返ってきた payload digest が authority plane snapshot と一致したかは
repo 内で検証できませんでした。

## Options considered

- A: authority plane は live HTTP probe のまま維持し、non-loopback mTLS route trace は future work に残す
- B: stable authority plane に対して local non-loopback address 上の mTLS route trace を追加し、socket-level evidence を schema/IDL/eval/test まで固定する
- C: local machine を飛ばして cross-host authority cluster と OS packet capture まで同時に入れる

## Decision

- B を採択しました
- `trace_non_loopback_authority_routes` と
  `distributed_transport_authority_route_trace` を追加し、
  route ごとの `local_ip / remote_ip / tls_version / cipher_suite /
  peer_certificate_fingerprint / client_certificate_fingerprint /
  request_bytes / response_bytes / response_digest`
  を authority plane に束縛します
- reference runtime は static test certificate bundle を temp directory に materialize し、
  local machine の non-loopback IPv4 address に bind した mTLS authority server へ
  actual route trace を実行します
- route trace は authority plane の current key server set 全体を cover し、
  per-server response digest が一致したときだけ `trace_status=authenticated`
  になります

## Consequences

- distributed transport surface は loopback HTTP probe だけでなく、
  actual non-loopback mTLS route と socket trace まで repo 内で再現できるようになりました
- `distributed-transport-demo` は rotated authority plane に対する
  stable route trace を返し、authority-plane digest と socket-level evidence を
 同じ JSON contract に閉じられます
- residual future work は cross-host authority routing と
  OS-native packet capture へ縮小されます

## Revisit triggers

- local machine 内ではなく cross-host authority cluster を trace したくなった時
- packet capture / kernel telemetry / QUIC など socket より下の observability を扱いたくなった時
- authority route trace を reviewer network や governance attestation plane へ束縛したくなった時
