---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/collective-identity.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.collective.v0.idl
  - specs/schemas/collective_external_registry_sync.schema
  - evals/interface/collective_external_registry_sync.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - collective.external-registry-acknowledgement-quorum
---

# Decision: Collective external registry ack を 2 jurisdiction quorum に束縛する

## Context

`collective-dissolution-external-registry-sync-v1` は recovery capture export binding を
external legal / governance registry の entry、submission、ack receipt へ束縛しました。
ただし acknowledgement は単一 digest で、legal registry と governance registry が別法域で
独立に accepted したことを reviewer が machine-checkable に確認できませんでした。

## Decision

`collective-external-registry-ack-quorum-v1` を追加し、legal registry ack と
governance registry ack の 2 receipt を authority ref / jurisdiction / registry digest /
submission digest に束縛します。

quorum は `required_authority_count=2`、`required_jurisdiction_count=2` を満たし、
ack digest set と quorum digest が `collective_external_registry_sync.schema` に残る場合だけ
`complete` になります。

## Consequences

- `collective-demo --json` は `ack_quorum_digest`、ack receipt set、
  accepted authority refs、jurisdiction set を返す
- public schema / IDL / eval / IntegrityGuardian capability は同じ ack quorum profile を共有する
- raw dissolution payload、raw registry payload、raw ack payload、raw packet body は保存しない

## Revisit triggers

- external registry を actual jurisdiction API / governance registry backend へ差し替える時
- registry acknowledgement を remote verifier transport と同じ authority route trace plane へ載せる時
