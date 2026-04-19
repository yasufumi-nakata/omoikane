---
date: 2026-04-19
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/04-ai-governance/guardian-oversight.md
  - docs/07-reference-implementation/README.md
  - evals/safety/guardian_reviewer_attestation_contract.yaml
  - specs/interfaces/governance.oversight.v0.idl
  - specs/schemas/guardian_oversight_event.schema
  - specs/schemas/guardian_oversight_snapshot.schema
  - specs/schemas/guardian_reviewer_record.schema
status: decided
---

# Decision: Guardian reviewer の proof binding と scoped liability を reference runtime に固定する

## Context

`docs/07-reference-implementation/README.md` の future work には
`Guardian oversight reviewer の実体証明と法的責任分担` が残っていました。
既存 runtime の `OversightService` は reviewer id を数えるだけで、
どの証明に基づく reviewer なのか、どの Guardian role / category まで責任を負うのかを
machine-checkable に保持していませんでした。
この状態では `oversight-demo` が human oversight の数合わせに留まり、
reviewer proof や legal ack を後段へ渡す contract が docs-only のままでした。

## Options considered

- A: reviewer 実体証明と責任分担は repo 外として維持し、runtime では reviewer 文字列だけを数える
- B: reviewer registry だけ追加し、attestation event には reviewer id だけを残す
- C: reviewer registry を追加し、attestation 時に `credential_id / proof_ref / legal_ack_ref / scope`
  を event 側へ immutable binding として焼き付ける

## Decision

**C** を採択。

## Consequences

- reference runtime は `guardian_reviewer_record` を登録してからでなければ
  `attest` を受け付けない
- reviewer は `identity_proof` と `responsibility` を持ち、
  `allowed_guardian_roles` / `allowed_categories` の外では fail-closed になる
- attestation 後の event は `reviewer_bindings` に
  `credential_id / proof_ref / liability_mode / legal_ack_ref / guardian_role / category`
  を保持し、reviewer revoke 後も過去 binding を監査できる
- `oversight-demo` は registered reviewer の veto attestation と
  pin-renewal scope mismatch reject を可視化する
- raw 身分証や契約書本文は repo に持ち込まず、`proof_ref` / `legal_ack_ref` に留める

## Revisit triggers

- live credential verification を external verifier と接続したい時
- jurisdiction ごとに異なる legal evidence package を runtime 内で切り替えたい時
- distributed oversight reviewer transport や remote attestation を扱いたい時
