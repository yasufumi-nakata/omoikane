---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/collective-identity.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.collective.v0.idl
  - specs/schemas/collective_recovery_route_trace_binding.schema
  - specs/schemas/distributed_transport_authority_route_trace.schema
  - evals/interface/collective_recovery_route_trace_binding.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - collective.recovery-verifier.actual-route-trace-binding
---

# Decision: Collective recovery verifier を non-loopback route trace に束縛する

## Context

直前の Collective recovery verifier transport では、dissolution receipt digest と
member recovery proof を remote reviewer verifier transport receipt へ束縛しました。
ただし Revisit trigger として残っていた「verifier transport binding を actual
non-loopback distributed authority route trace へ接続する」面は、まだ
first-class artifact になっていませんでした。

## Options considered

- A: verifier transport receipt の digest set だけを維持する
- B: distributed transport の route trace payload を raw transcript として保存する
- C: verifier transport binding digest、authenticated route trace digest、member ごとの route binding ref / socket response digest / remote host attestation ref を別 artifact として束縛する

## Decision

**C** を採択。

`collective-recovery-non-loopback-route-trace-binding-v1` は
recovery verifier transport binding digest と
`distributed_transport_authority_route_trace.schema` に合う authenticated
non-loopback authority-route trace digest を束縛する。
member ごとに verifier transport receipt digest、route binding ref、
remote host attestation ref、OS observer host binding digest、socket response digest を
member route binding digest に縮約する。

## Consequences

- `collective-demo --json` は recovery verifier transport に加えて
  `recovery_route_trace_binding` を返す
- `interface.collective.v0` は `bind_recovery_verifier_route_trace` operation を持つ
- IntegrityGuardian は collective recovery proof の remote verifier chain が
  actual non-loopback route trace まで到達していることを digest-only に監査できる
- raw verifier payload と raw route payload は保存しない

## Revisit triggers

- Collective dissolution を external legal / governance registry へ同期する時
- route trace binding を packet capture export / privileged capture acquisition まで拡張する時
