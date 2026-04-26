---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/collective-identity.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.collective.v0.idl
  - specs/schemas/collective_recovery_capture_export_binding.schema
  - specs/schemas/distributed_transport_packet_capture_export.schema
  - specs/schemas/distributed_transport_privileged_capture_acquisition.schema
  - evals/interface/collective_recovery_capture_export_binding.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - collective.recovery-route-trace.capture-export-binding
---

# Decision: Collective recovery route trace を capture export に束縛する

## Context

直前の Collective recovery route trace binding は post-dissolution recovery verifier
transport を authenticated non-loopback authority-route trace へ束縛しました。
ただし Revisit trigger に残っていた packet capture export / privileged capture
acquisition は、collective recovery chain の first-class artifact ではありませんでした。

## Options considered

- A: route trace binding digest だけを維持する
- B: raw packet capture body や verifier transcript を collective receipt に保存する
- C: route trace binding digest、verified pcap export digest、delegated-broker privileged capture digest、member ごとの capture binding digest を別 artifact として束縛する

## Decision

**C** を採択。

`collective-recovery-route-trace-capture-export-v1` を追加し、
`collective-demo --json` が recovery route trace binding digest、packet capture export
digest、privileged capture acquisition digest、route binding ref set、member capture
binding digest set を返す。

raw verifier payload、raw route payload、raw packet body は保存しない。

## Consequences

- collective recovery proof chain は verifier transport -> route trace -> pcap export /
  delegated capture acquisition まで digest-only に接続される
- public schema / IDL / eval / IntegrityGuardian capability は同じ capture export binding
  profile を共有する
- `interface-collective-dissolution` ledger category は dissolution、verifier transport、
  route trace、capture export の 4 event を持つ

## Revisit triggers

- Collective dissolution を external legal / governance registry へ同期する時
- packet capture export を actual privileged OS capture backend へ差し替える時
