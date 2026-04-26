---
date: 2026-04-27
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/identity-lifecycle.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.identity.v0.idl
  - specs/schemas/identity_confirmation_profile.schema
  - evals/identity-fidelity/identity_confirmation_profile.yaml
  - agents/guardians/identity-guardian.yaml
status: decided
---

# Decision: Identity confirmation witness は registry / revocation に束縛する

## Context

`multidimensional-identity-confirmation-v1` は clinician + guardian の
witness quorum と self-report / witness score consistency を確認していました。
ただし accepted witness が現在有効な reviewer registry entry と verifier key に
対応し、revocation registry 上で not-revoked であることを
first-class artifact として保持していませんでした。

## Options considered

- A: witness role 文字列と alignment score だけで quorum を継続する
- B: raw witness registry roster と raw revocation payload を confirmation profile に保存する
- C: digest-only `identity-witness-registry-binding-v1` を追加し、accepted witness の
  registry entry digest、verifier key ref、revocation ref、registry snapshot digest を
  continuity subject に束縛する

## Decision

**C** を採択。

Accepted witness は `registry_status=current` かつ
`revocation_status=not-revoked` の場合だけ pass できる。
confirmation profile は `identity-witness-registry-binding-v1` として
accepted witness registry digest set、verifier key refs、revocation refs、
required roles、registry snapshot digest、`raw_registry_payload_stored=false` を保持する。

## Consequences

- `identity-confirmation-demo --json` は
  `witness_registry_binding` と validation flag
  `witness_registry_binding_bound` / `registry_binding_digest_bound` を返す
- stale / unknown / revoked witness は alignment score が閾値を超えていても
  accepted witness から除外される
- witness registry binding が不成立なら
  `witness-registry-binding-not-bound` で Active 遷移を拒否する
- raw witness registry roster と raw revocation payload は保存しない

## Revisit triggers

- registry source を jurisdiction-specific external authority へ移す時
- witness role を clinician / guardian 以外の reviewer roster へ拡張する時
- revocation registry の live verifier quorum を導入する時
