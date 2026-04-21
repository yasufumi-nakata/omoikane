---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/04-ai-governance/guardian-oversight.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/governance.oversight.v0.idl
  - specs/schemas/guardian_verifier_network_receipt.schema
  - specs/schemas/guardian_verifier_transport_exchange.schema
  - evals/safety/guardian_reviewer_verifier_network.yaml
status: decided
---

# Decision: Guardian verifier network を digest-bound transport exchange まで固定する

## Context

2026-04-22 時点で `oversight-network-demo` は
`verifier_endpoint` / `authority_chain_ref` / `trust_root_ref` /
`trust_root_digest` を持つ `guardian_verifier_network_receipt`
まで machine-checkable でした。

一方 `governance.oversight.v0` には
`raw verifier transport payload exchange remain future work`
が残っており、reviewer verification が
どの request / response payload に基づいて成立したかを
repo 内 contract へ束縛できていませんでした。

この状態では verifier network receipt があっても、
transport 層の request / response digest と event binding が
切り離されたままです。

## Options considered

- A: verifier endpoint / root binding だけで止め、transport exchange は future work に残す
- B: verifier network receipt に digest-bound transport exchange artifact を追加し、request / response ref と digest を reviewer verification / attestation binding まで通す
- C: raw transcript body や credential payload 自体を repo に保存する

## Decision

Option B を採択します。

- `guardian_verifier_transport_exchange.schema` を追加し、
  `digest-bound-reviewer-transport-exchange-v1` を canonical profile に固定します
- `guardian_verifier_network_receipt` は
  `transport_exchange` を必須化し、
  `request_payload_ref` / `request_payload_digest` /
  `response_payload_ref` / `response_payload_digest` /
  `request_size_bytes` / `response_size_bytes`
  を同じ receipt digest に束縛します
- `reviewer_bindings` は
  `transport_exchange_id` / `transport_exchange_digest`
  を immutable binding として保持します
- raw payload body は repo に保存せず、
  sealed ref と digest のみを保持します

## Consequences

- `oversight-network-demo` は verifier endpoint / authority chain / trust root に加えて、
  digest-bound transport exchange まで JSON で可視化できます
- `governance.oversight.v0` の residual future work は
  raw verifier transport payload exchange ではなく、
  jurisdiction-specific legal execution へ縮小されます
- Guardian attestation event は
  verifier network receipt と transport exchange を
  同じ reviewer binding に焼き付けられるようになります

## Revisit triggers

- raw transport payload body を sealed external store と連動して再取得可能にしたくなった時
- verifier network を単一 endpoint registry から
  distributed authority plane へ広げたくなった時
- jurisdiction bundle 自体を legal execution receipt として
  actual regulator workflow に接続したくなった時
