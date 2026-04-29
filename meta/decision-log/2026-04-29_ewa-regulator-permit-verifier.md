---
date: 2026-04-29
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/ewa-safety.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.ewa.v0.idl
  - specs/schemas/ewa_regulator_permit_verifier_receipt.schema
  - evals/safety/ewa_regulator_permit_verifier.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - ewa-regulator-permit-verifier-readback
---

# Decision: EWA regulator permit verifier を legal execution に束縛する

## Context

EWA の reversible authorization は motor plan、stop-signal path、production connector、
jurisdiction-bound legal execution、network-attested Guardian oversight gate を
machine-checkable に束縛していた。
ただし permit authority や regulator API の readback は文字列 refs に留まり、
legal execution digest と permit status が同じ receipt に閉じ込められていなかった。

## Decision

`ewa-regulator-permit-verifier-v1` を追加し、
`ewa_regulator_permit_verifier_receipt` で legal execution id/digest、
jurisdiction、legal basis、jurisdiction bundle、permit authority、
permit record digest、permit scope、regulator API endpoint、API response digest、
API certificate digest、verifier key digest を束縛する。

reference runtime は `permit_status=valid` の readback だけを受け入れ、
raw permit payload、raw regulator response payload、verifier decision authority は
保持しない。`ewa-demo` は verifier receipt と validation summary を返し、
IntegrityGuardian と safety eval は legal execution binding、digest-only transport、
raw-payload redaction を検証する。

## Consequences

- `ewa-demo --json` は regulator permit verifier receipt を返し、ledger に
  `interface-ewa-regulator-permit` evidence を追加する。
- schema / IDL / eval / docs / IntegrityGuardian scope は同じ profile id と
  transport profile id を共有する。
- regulator verifier は authorization の decision authority にはならず、
  EWA の既存 reviewer / Guardian authorization chain は維持する。

## Revisit triggers

- 本番 regulator endpoint、PKI、freshness SLA を runtime adapter に接続する時
- permit class ごとに status enum や verifier quorum を分岐する時
- authorization の hard gate に permit verifier receipt を直接組み込む時
