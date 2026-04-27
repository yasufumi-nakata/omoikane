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
  - 2026-04-27_identity-confirmation-witness-revocation-verifier-quorum.md#policy-driven-verifier-roster
---

# Decision: Identity revocation verifier quorum を roster policy に束縛する

## Context

`identity-witness-revocation-live-verifier-quorum-v1` は accepted witness
revocation refs を複数 verifier の fresh response に束縛していた。
ただし、その verifier jurisdiction set がどの policy roster から要求されたかは
first-class artifact ではなく、quorum count が満たされても意図した roster と違う
jurisdiction pair を受け入れる余地があった。

## Decision

`identity-witness-revocation-verifier-roster-policy-v1` を
`witness_registry_binding` に追加する。

roster policy は roster ref、required jurisdiction set、quorum threshold、
roster digest、`raw_revocation_verifier_roster_payload_stored=false` を持つ。
Active transition は revocation verifier quorum が `complete` で、かつ observed
jurisdiction set が required roster を覆う時だけ pass する。

## Consequences

- `identity-confirmation-demo --json` は pass profile と、quorum は complete だが
  roster jurisdiction mismatch で fail-closed する profile を返す
- public schema / IDL / eval / IdentityGuardian は raw roster payload を保存せず、
  roster digest と required jurisdiction set を検証する
- `identity-fidelity` ledger event は revocation verifier quorum digest に加えて
  revocation verifier roster digest を束縛する

## Revisit Triggers

- actual external revocation service adapter へ接続する時
- verifier roster の authority source を jurisdiction policy registry へ移す時
