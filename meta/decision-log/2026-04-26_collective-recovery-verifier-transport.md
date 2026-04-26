---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/collective-identity.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.collective.v0.idl
  - specs/schemas/collective_recovery_verifier_transport_binding.schema
  - evals/interface/collective_recovery_verifier_transport.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - collective.recovery-proof.remote-verifier-transport
---

# Decision: Collective recovery proof を remote verifier transport に束縛する

## Context

`collective_dissolution_receipt.schema` は member recovery proof を
IdentityConfirmation digest として保持していました。ただし直前の再訪条件に残っていた
「post-dissolution recovery proof を remote reviewer verifier transport に束縛する」
面は、dissolution receipt の外側にまだ first-class artifact がありませんでした。

## Options considered

- A: dissolution receipt の digest-only recovery proof だけで止める
- B: raw verifier request / response payload を receipt に保存する
- C: dissolution receipt digest、member recovery binding digest、per-member verified
  transport receipt digest set を別 artifact として束縛する

## Decision

**C** を採択。

`collective-dissolution-recovery-verifier-transport-v1` を追加し、
`collective-demo --json` が dissolution receipt digest、member recovery binding digest、
member ごとの verified remote reviewer transport receipt、transport exchange digest、
request / response payload digest、raw verifier payload 非保存 flag を返す。

## Consequences

- dissolution receipt 本体は raw IdentityConfirmation profile 非保存のまま維持される
- remote verifier transport evidence は
  `collective_recovery_verifier_transport_binding.schema` で直接検証できる
- `interface-collective-dissolution` ledger category は dissolution receipt と
  verifier transport binding の 2 event を持つ

## Revisit triggers

- Collective dissolution を external legal / governance registry へ同期する時
- verifier transport binding を actual non-loopback distributed authority route trace へ接続する時
