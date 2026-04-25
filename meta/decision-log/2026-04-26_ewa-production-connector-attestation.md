---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/ewa-safety.md
  - docs/02-subsystems/mind-substrate/procedural-memory.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.ewa.v0.idl
  - specs/interfaces/mind.procedural_actuation.v0.idl
  - specs/schemas/ewa_production_connector_attestation.schema
  - evals/safety/ewa_production_connector_attestation.yaml
  - evals/continuity/procedural_actuation_bridge.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - ewa.production-connector-attestation
---

# Decision: EWA production connector attestation を authorization に束縛する

## Context

EWA は stop-signal path と PLC / firmware adapter receipt を authorization と
emergency stop に束縛していました。ただし実機 vendor API connector certificate、
設置証明、safety PLC installation ref は digest-only の first-class receipt ではなく、
production connector を実デバイスへ接続する境界が docs-only に残っていました。

## Decision

`ewa_production_connector_attestation` を追加し、
`vendor-api-safety-plc-installation-attestation-v1` profile で
vendor API certificate digest、production connector ref、installation proof digest、
safety PLC ref、firmware / PLC program digest を stop-signal adapter receipt に束縛します。

authorization、approved command audit、emergency stop、procedural actuation bridge は
同じ `production_connector_attestation_id` /
`production_connector_attestation_digest` を保持し、raw vendor payload と raw
installation payload は reference runtime に保存しません。

## Consequences

- `ewa-demo --json` は production connector attestation と validation flag を返す
- `procedural-actuation-demo --json` は bridge session の command binding に同じ attestation digest を保持する
- public schema / IDL / eval / IntegrityGuardian capability は同じ production connector profile を共有する
- stop-signal adapter receipt だけでは authorization が成立せず、production connector attestation まで必須になる

## Revisit triggers

- 実 vendor API connector を live transport / remote PKI federation に接続する時
- installation proof を site-specific regulator permit workflow と統合する時
- safety PLC firmware attestation を hardware root-of-trust へ移す時
