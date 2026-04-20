---
date: 2026-04-20
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/distributed-transport-attestation.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/distributed_transport_authority_plane.yaml
  - specs/interfaces/agentic.distributed_transport.v0.idl
  - specs/schemas/distributed_transport_authority_plane.schema
status: decided
---

# Decision: distributed transport の bounded authority plane を key-server fleet contract として追加する

## Context

`probe_live_root_directory` によって rotated envelope へ trusted root quorum を
束縛できるようになっていましたが、
README future-work と schema README には依然
`non-loopback distributed PKI authority plane / external key server fleet`
が残っていました。

この状態では、どの external key server がどの trusted root を実際に広告し、
その endpoint が reachable だったのか、
root-directory snapshot とどう結び付いたのかが repo 内で machine-checkable ではありませんでした。

## Options considered

- A: root-directory probe のみで止め、key-server fleet は future work のまま据え置く
- B: bounded key-server fleet probe を追加し、authority-plane digest と per-server connectivity receipt を rotated receipt 前に固定する
- C: actual non-loopback mTLS routing と dynamic server churn handling まで同時に入れる

## Decision

**B** を採択。

## Consequences

- `probe_authority_plane` を `agentic.distributed_transport.v0` に追加し、
  `distributed_transport_authority_plane` schema を新設する
- `distributed-transport-demo` は loopback key-server fleet を使い、
  `root-directory -> authority-plane -> rotated receipt` の束縛を 1 シナリオで再現する
- rotated receipt は root-directory 直結ではなく authority-plane が返した
  `trusted_root_refs` を使って authenticate する
- residual future work は actual non-loopback mTLS authority routing、
  dynamic remote key-server churn、socket-level tracing へ絞られる

## Revisit triggers

- authority plane を actual non-loopback mTLS endpoint や remote socket telemetry へ接続したい時
- key-server membership を dynamic governance roster と reviewer network へ結び付けたい時
- root-directory / authority-plane / relay telemetry を共通 observability plane に統合したい時
