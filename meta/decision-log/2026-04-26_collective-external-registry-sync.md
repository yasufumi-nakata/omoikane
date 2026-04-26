---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/collective-identity.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.collective.v0.idl
  - specs/schemas/collective_external_registry_sync.schema
  - specs/schemas/collective_recovery_capture_export_binding.schema
  - evals/interface/collective_external_registry_sync.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - collective.dissolution.external-legal-governance-registry-sync
---

# Decision: Collective dissolution を external registry sync へ束縛する

## Context

直前の Collective recovery capture export binding は recovery route trace を
verified pcap export と delegated privileged capture acquisition へ束縛しました。
ただし Revisit trigger に残っていた external legal / governance registry への同期は、
collective recovery chain の first-class artifact ではありませんでした。

## Options considered

- A: capture export binding digest だけを維持し、external registry sync は運用メモに残す
- B: raw dissolution payload や registry payload を receipt に保存する
- C: capture export binding digest、legal registry digest、governance registry digest、registry entry digest、submission digest、ack digest を別 artifact として束縛する

## Decision

**C** を採択。

`collective-dissolution-external-registry-sync-v1` を追加し、
`collective-demo --json` が recovery capture export binding digest、external legal
registry digest、governance registry digest、registry entry digest、submission receipt
digest、ack receipt digest を返す。

raw dissolution payload、raw registry payload、raw packet body は保存しない。

## Consequences

- collective recovery proof chain は dissolution -> verifier transport -> route trace ->
  capture export -> external registry sync まで digest-only に接続される
- public schema / IDL / eval / IntegrityGuardian capability は同じ registry sync
  profile を共有する
- `interface-collective-dissolution` ledger category は dissolution、verifier transport、
  route trace、capture export、external registry sync の 5 event を持つ

## Revisit triggers

- external registry を actual jurisdiction API / governance registry backend へ差し替える時
- registry acknowledgement を multi-jurisdiction quorum へ拡張する時
