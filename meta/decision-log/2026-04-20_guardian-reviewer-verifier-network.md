---
date: 2026-04-20
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/04-ai-governance/guardian-oversight.md
  - docs/07-reference-implementation/README.md
  - evals/safety/guardian_reviewer_verifier_network.yaml
  - specs/interfaces/governance.oversight.v0.idl
  - specs/schemas/guardian_reviewer_verification.schema
  - specs/schemas/guardian_verifier_network_receipt.schema
status: decided
---

# Decision: Guardian reviewer remote attestation transport を verifier network receipt として固定する

## Context

`docs/07-reference-implementation/README.md` の future work には
`Guardian oversight reviewer の remote attestation transport を actual verifier network に接続`
が残っていました。
既存 runtime は `verify_reviewer` による live-proof surrogate snapshot までは固定していましたが、
それがどの verifier endpoint / authority chain / trust root によって支えられているかは
machine-checkable ではありませんでした。

そのため、`oversight-demo` の reviewer verification は
proof binding と jurisdiction bundle までは説明できても、
actual verifier network 側の transport provenance を
event binding に渡す surface がありませんでした。

## Options considered

- A: verifier network は repo 外の future work のまま据え置き、surrogate snapshot だけを維持する
- B: 既存 `oversight-demo` をそのまま network-backed に置換し、surrogate path を消す
- C: surrogate path は `oversight-demo` として残しつつ、
  `verify_reviewer_from_network` / `oversight-network-demo` / `guardian_verifier_network_receipt`
  を追加して actual verifier transport を別 surface として materialize する

## Decision

**C** を採択。

## Consequences

- `governance.oversight.v0` に `verify_reviewer_from_network` を追加し、
  fixed endpoint registry から `verifier_endpoint / authority_chain_ref / trust_root_ref /
  trust_root_digest / freshness_window_seconds / observed_latency_ms` を持つ
  `guardian_verifier_network_receipt` を生成する
- `guardian_reviewer_verification` は optional な `network_receipt` を保持し、
  `oversight-network-demo` では network-backed verification を、
  `oversight-demo` では surrogate-only verification を引き続き確認する
- reviewer attestation event は network path の場合に
  `network_receipt_id / authority_chain_ref / trust_root_ref / trust_root_digest`
  を immutable reviewer binding として保持する
- raw network transcript や credential payload は repo に持ち込まず、
  ref / digest / authority-chain summary のみを保存する

## Revisit triggers

- verifier endpoint registry を multi-jurisdiction / multi-root rotation に拡張したい時
- distributed transport と reviewer verifier network を一体化したい時
- raw verifier payload や live mutual-auth channel transcript まで監査対象に上げたい時
