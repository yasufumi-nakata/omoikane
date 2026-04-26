---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/collective-identity.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.collective.v0.idl
  - specs/schemas/collective_dissolution_receipt.schema
  - evals/interface/collective_dissolution_receipt.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - collective.dissolution-receipt-public-contract
---

# Decision: Collective dissolution receipt を public schema contract に昇格する

## Context

L6 Collective Identity は formation と merge session を public schema で検証していましたが、
`dissolve_collective` の返却値は IDL inline schema と `collective_record.last_dissolution`
の nested object に留まっていました。

そのため reviewer は CLI 出力の dissolution artifact を単独 schema と eval で確認できず、
member recovery confirmation と digest-only audit ref が closure point として薄い状態でした。

## Options considered

- A: 既存 inline schema を維持し、record snapshot の validation に任せる
- B: `collective_dissolution_receipt.schema` を追加し、runtime / IDL / eval / tests で単独 contract にする
- C: dissolution を merge session の `completed` status に吸収し、別 receipt を返さない

## Decision

**B** を採択。

`collective_dissolution_receipt.schema` を追加し、`dissolve_collective` は
`schema_version=1.0`、全 member confirmation、`member_recovery_required=true`、
digest-only `audit_event_ref` を持つ receipt を返す。

`collective-demo --json` は同 receipt を `interface-collective-dissolution` ledger event にも残し、
schema contract test と eval が public artifact として検証する。

## Consequences

- Collective teardown は formation / merge と同じ粒度で reviewer-visible になる
- `interface.collective.v0` の `dissolve_collective` output と `collective.dissolved` event は
  inline schema ではなく同じ public schema を参照する
- Integrity Guardian は `collective.dissolution-receipt.attest` capability で
  member recovery confirmation と digest-only audit binding を確認できる

## Revisit triggers

- collective dissolution を external legal / governance registry へ同期する時
- post-dissolution member recovery を IdentityConfirmationService の multi-dimension proof と束ねる時
