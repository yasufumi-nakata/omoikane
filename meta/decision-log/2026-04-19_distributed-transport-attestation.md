---
date: 2026-04-19
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/distributed-council-resolution.md
  - docs/02-subsystems/agentic/distributed-transport-attestation.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/distributed_transport_authenticity.yaml
  - specs/interfaces/agentic.distributed_transport.v0.idl
  - specs/schemas/distributed_participant_attestation.schema
  - specs/schemas/distributed_transport_envelope.schema
  - specs/schemas/distributed_transport_receipt.schema
status: decided
---

# Decision: distributed council remote handoff を participant-attested transport envelope に固定する

## Context

`distributed-council-demo` により Federation / Heritage の returned result 自体は
machine-readable になっていましたが、README future-work の先頭に残っていた
`participant attestation / transport authenticity` はまだ docs-only でした。
この状態では remote endpoint へ渡す前段の handoff bundle が
誰の credential / proof に基づくのか、どの channel binding と route nonce に
束縛されているのかを reference runtime で検証できませんでした。

## Options considered

- A: remote handoff は repo 外として維持し、distributed result policy だけを truth source にする
- B: envelope だけ作り、receipt verification と replay guard は future work に残す
- C: participant attestation、channel binding、receipt verification、replay guard を
  1 つの `agentic.distributed_transport.v0` contract に固定する

## Decision

**C** を採択。

## Consequences

- Federation handoff は `federation-mtls-quorum-v1` として
  `self-liaison x2 + guardian x1` の attested envelope を要求する
- Heritage handoff は `heritage-attested-review-v1` として
  `cultural-representative x2 + legal-advisor + ethics-committee` の
  fixed reviewer roles を要求する
- receipt は `channel_authenticated && required_roles_satisfied && quorum_attested` を
  満たした場合のみ `authenticated` になる
- 同一 `route_nonce` の再利用は `replay-blocked` になり、
  remote result を二重取り込みしない
- `distributed-transport-demo` が Federation accepted / Heritage accepted /
  Federation replay blocked を JSON で可視化する

## Revisit triggers

- live PKI federation や transport key rotation を actual network に接続したい時
- multi-hop relay をまたぐ replay detection を runtime 内で扱いたい時
- distributed oversight reviewer transport をこの handoff contract に統合したい時
