---
date: 2026-04-19
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/distributed-transport-attestation.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/distributed_transport_rotation.yaml
  - specs/interfaces/agentic.distributed_transport.v0.idl
  - specs/schemas/distributed_participant_attestation.schema
  - specs/schemas/distributed_transport_envelope.schema
  - specs/schemas/distributed_transport_receipt.schema
status: decided
---

# Decision: distributed transport の key rotation / federated root quorum / multi-hop anti-replay を bounded contract に固定する

## Context

`agentic.distributed_transport.v0` は participant attestation / channel binding /
single-hop replay guard までは fixed でしたが、
`docs/07-reference-implementation/README.md` の future work には
transport key rotation / remote PKI federation / multi-hop anti-replay が残っていました。
このままだと rotated handoff や relay 経由 handoff を
repo 内 runtime で評価できませんでした。

## Options considered

- A: distributed transport は single-epoch / single-root のまま維持し、rotation は actual network 側の課題に残す
- B: key rotation だけを追加し、root federation と multi-hop anti-replay は後回しにする
- C: key epoch overlap、federated trust-root quorum、hop_nonce_chain replay guard を
  bounded contract として先に固定する

## Decision

**C** を採択。

## Consequences

- envelope は `key_epoch`、`accepted_key_epochs`、`trust_root_refs`、
  `trust_root_quorum`、`max_hops`、`previous_envelope_ref` を持つ
- participant attestation は `trust_root_ref` と `key_epoch` を持ち、
  rotated envelope では `transport_key_ref` を epoch-bound に更新する
- receipt は `verified_root_refs`、`key_epoch`、`hop_nonce_chain` を持ち、
  `federated_roots_verified && key_epoch_accepted` が無い限り `authenticated` にならない
- 別 envelope で同じ `hop_nonce_chain` を再利用した receipt も `replay-blocked` にする
- `distributed-transport-demo` は rotated federation handoff と
  multi-hop replay blocked を追加で可視化する

## Revisit triggers

- actual network PKI / key server / relay telemetry と live 接続したい時
- trust root を static quorum ではなく dynamic governance roster に束縛したい時
- relay path を latency / geography / jurisdiction-aware routing へ拡張したい時
