---
date: 2026-04-29
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/self-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.self_model.v0.idl
  - specs/schemas/self_model_care_trustee_registry_binding_receipt.schema
  - evals/identity-fidelity/self_model_care_trustee_registry_binding.yaml
  - agents/guardians/identity-guardian.yaml
status: decided
---

# Decision: SelfModel care trustee registry binding に live revocation verifier quorum を接続する

## Context

`self-model-care-trustee-registry-binding-v1` は care trustee handoff refs を current
external registry entry、verifier key ref、not-revoked revocation ref へ digest-only に
束縛した。一方で、revocation refs が live verifier response として freshness window 内に
確認されていることは registry binding 自身の first-class contract ではなかった。

## Decision

care trustee registry binding receipt に
`self-model-care-trustee-registry-revocation-live-verifier-quorum-v1` を追加し、
accepted revocation refs を JP-13 / US-CA の required jurisdiction set、signed
response envelope、response signing key、trust root、route ref、freshness window、
verifier receipt digest set、quorum digest に束縛する。

reference runtime は quorum が `complete` で、各 verifier response が `not-revoked`、
freshness window が正、covered revocation refs が accepted revocation refs と一致する場合だけ
`revocation_live_verifier_bound=true` とする。stale / revoked verifier response は
fail-closed し、raw verifier payload や raw response signature payload は保存しない。

## Consequences

- `build_care_trustee_registry_binding_receipt` は `revocation_verifier_receipts` を必須入力にする
- `self-model-demo --json` は care trustee registry binding validation に quorum status と live verifier binding を返す
- schema / IDL / eval / IdentityGuardian は stale または revoked verifier response を受理しない条件を共有する

## Revisit triggers

- revocation verifier endpoint の real transport、certificate chain、OCSP/CRL 相当の実在 authority を導入する時
- JP-13 / US-CA 以外の jurisdiction quorum や threshold policy を registry binding ごとに分岐する時
