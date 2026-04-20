---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/ewa-safety.md
  - docs/02-subsystems/mind-substrate/procedural-memory.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.ewa.v0.idl
  - specs/schemas/external_actuation_authorization.schema
  - evals/safety/ewa_external_actuation_authorization.yaml
status: decided
---

# Decision: external actuation authorization artifact を EWA boundary に追加する

## Context

`gap-report --json` は clean でしたが、
`specs/schemas/README.md` には依然
`external-actuation authorization artifacts`
が次段階として残っていました。

2026-04-20 時点の procedural skill enactment は temp workspace / sandbox-only まで閉じており、
実物理 actuation へ進むときに
どの guardian-reviewed jurisdiction evidence と
どの command digest が結び付いていたかを
repo 内で machine-checkable に示す artifact がありませんでした。

EWA も reversible / partial-reversible / irreversible の gate は持っていましたが、
legal basis ref、guardian verification ref、jurisdiction bundle readiness を
digest-bound な authorization artifact として保持していませんでした。

## Options considered

- A: EWA command の approval_path flag だけで済ませ、authorization artifact は future work のまま残す
- B: non-read-only actuation の前段に bounded authorization artifact を追加し、jurisdiction evidence と command digest binding を schema/IDL/runtime/eval/test まで固定する
- C: device-specific legal execution engine や actual regulator API 連携まで一気に持ち込む

## Decision

**B** を採択。

## Consequences

- `external_actuation_authorization.schema` を追加し、
  `guardian-jurisdiction-bound-external-actuation-v1` を
  EWA v0 の canonical authorization policy とする
- `interface.ewa.v0` は `authorize / validate_authorization / command` の三段を持ち、
  non-read-only command では matching `authorization_id` を fail-closed で要求する
- authorization artifact は raw instruction を保持せず、
  `instruction_digest` / `intent_summary_digest` /
  `legal_basis_ref` / `guardian_verification_ref` /
  `jurisdiction_bundle_status=ready` を束縛する
- `procedural-memory.md` では、sandbox-only の次段で external actuation を行う場合に
  この artifact を経由することを明示できる
- device-specific motor semantics、full legal execution engine、
  emergency stop hardware protocol は引き続き future work に残る

## Revisit triggers

- EWA authorization を actual regulator / permit API と結び付けたくなった時
- procedural enactment を sandbox-only から real actuator dispatch へ接続したくなった時
- jurisdiction bundle を Guardian verifier network だけでなく distributed transport 側の authority plane と共通化したくなった時
