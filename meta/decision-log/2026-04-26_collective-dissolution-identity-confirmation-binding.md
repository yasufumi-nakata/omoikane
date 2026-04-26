---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/collective-identity.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.collective.v0.idl
  - specs/schemas/collective_dissolution_receipt.schema
  - specs/schemas/identity_confirmation_profile.schema
  - evals/interface/collective_dissolution_receipt.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
---

# Decision: Collective dissolution を IdentityConfirmation digest proof に束縛する

## Context

`collective_dissolution_receipt.schema` は全 member confirmation と digest-only audit ref を
first-class artifact にしていました。ただし post-dissolution member recovery は boolean
confirmation だけで、既存の `multidimensional-identity-confirmation-v1` profile と
machine-checkable に接続されていませんでした。

## Options considered

- A: boolean member confirmation のまま維持する
- B: raw IdentityConfirmationProfile 全体を dissolution receipt に埋め込む
- C: member ごとの passed IdentityConfirmationProfile から confirmation digest、witness quorum status、self-report/witness consistency digest だけを receipt に束縛する

## Decision

**C** を採択。

`collective-dissolution-identity-confirmation-binding-v1` を dissolution receipt に追加し、
各 member の `multidimensional-identity-confirmation-v1` profile が `passed` かつ
`active_transition_allowed=true`、witness quorum `met`、self-report/witness consistency
`bound` である時だけ dissolution を成立させる。

receipt は member-keyed recovery proof、ordered confirmation digest set、
recovery binding digest、`raw_identity_confirmation_profiles_stored=false` を保持する。

## Consequences

- `collective-demo --json` は member recovery identity confirmation profiles と digest-only recovery proof を返す
- public dissolution schema、IDL、eval、IntegrityGuardian capability は同じ binding profile を共有する
- ledger event は raw IdentityConfirmation body ではなく recovery binding digest と confirmation digest set を保持する

## Revisit triggers

- Collective dissolution を external legal / governance registry へ同期する時
- post-dissolution recovery proof を remote reviewer verifier transport に束縛する時
