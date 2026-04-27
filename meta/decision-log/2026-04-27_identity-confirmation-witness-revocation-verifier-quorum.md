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
closes_next_gaps:
  - identity-confirmation-witness-revocation-live-verifier-quorum
---

# Decision: Identity confirmation witness revocation を live verifier quorum に束縛する

## Context

`identity-witness-registry-binding-v1` は accepted witness の registry entry、
verifier key ref、revocation ref、revocation status を digest-only に束縛していた。
ただし、その revocation ref set が複数 verifier の fresh response により
`not-revoked` と確認されたことは first-class artifact ではなかった。

## Decision

`identity-witness-revocation-live-verifier-quorum-v1` を
`witness_registry_binding` に追加する。

各 confirmation profile は accepted witness revocation refs、registry snapshot digest、
JP-13 / US-CA verifier response digest set、freshness window、quorum digest を保持する。
Active transition は witness registry binding と self-report consistency に加え、
dual-jurisdiction verifier quorum が `complete` の時だけ pass する。

## Consequences

- `identity-confirmation-demo --json` は complete verifier quorum を含む pass profile と、
  verifier quorum incomplete で fail-closed する profile を返す
- public schema / IDL / eval / IdentityGuardian は raw verifier payload を保存せず、
  response digest set と quorum digest だけを検証する
- `identity-fidelity` ledger event は witness registry binding digest に加え、
  revocation verifier quorum digest を束縛する

## Revisit Triggers

- verifier jurisdictions を policy-driven roster へ広げる時
- actual external revocation service adapter を追加する時
