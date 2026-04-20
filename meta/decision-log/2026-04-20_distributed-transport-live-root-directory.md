---
date: 2026-04-20
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/distributed-transport-attestation.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/distributed_transport_live_root_directory.yaml
  - specs/interfaces/agentic.distributed_transport.v0.idl
  - specs/schemas/distributed_transport_root_directory.schema
status: decided
---

# Decision: distributed transport の live root-directory federation を bounded surface として追加する

## Context

`agentic.distributed_transport.v0` は
participant attestation、key rotation、federated root quorum、
multi-hop relay telemetry までは fixed されていましたが、
`specs/schemas/README.md` には次段として
`live remote PKI federation` が残っていました。

この状態では rotated envelope がどの remote root directory を根拠に
`verified_root_refs` を受け取ったのか、
その endpoint が reachable だったのか、
response digest と latency をどう束縛したのかが repo 内で machine-checkable ではありませんでした。

## Options considered

- A: remote PKI は引き続き docs-only の future work とし、receipt へ root refs を手入力し続ける
- B: live root-directory probe を loopback HTTP JSON surface として追加し、trusted root quorum を receipt verification 前に束縛する
- C: actual external key server / mTLS / socket tracing まで同時に入れる

## Decision

**B** を採択。

## Consequences

- `probe_live_root_directory` を `agentic.distributed_transport.v0` に追加し、
  `distributed_transport_root_directory` /
  `distributed_transport_root_connectivity_receipt` を新設する
- rotated handoff は live endpoint の `response_digest / observed_latency_ms /
  matched_root_count / quorum_satisfied` を持つ connectivity receipt を経由して
  `trusted_root_refs` を receipt verification に渡す
- `distributed-transport-demo` は loopback endpoint を使い、
  actual remote server が無くても live root quorum binding を再現できる
- residual future work は non-loopback authority plane や external key server 群への接続へ絞られる

## Revisit triggers

- live root directory を actual mTLS endpoint や external key server cluster へ接続したい時
- root federation を dynamic governance roster と reviewer network へ結び付けたい時
- relay telemetry と root-directory probe を共通 observability plane に統合したい時
