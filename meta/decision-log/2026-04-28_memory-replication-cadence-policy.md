---
date: 2026-04-28
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/03-protocols/memory-replication.md
  - docs/02-subsystems/mind-substrate/memory-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.memory_replication.v0.idl
  - specs/schemas/memory_replication_session.schema
  - evals/continuity/memory_replication_quorum.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
---

# Decision: MemoryReplication media renewal cadence を identity / jurisdiction policy に束縛する

## Context

`long-term-media-renewal-refresh-window-v1` は renewed media proof set を
current-not-revoked status、90 日 revocation check、registry verifier quorum、
endpoint certificate CT / SCT evidence に束縛していた。
一方、refresh cadence は固定値 `3650` 日として読めるだけで、identity class や
JP-13 / SG-01 の jurisdiction policy digest による reviewer-facing な根拠は
machine-readable ではなかった。

## Decision

`long-term-media-renewal-cadence-policy-v1` を
`memory_replication_session.long_term_media_renewal.cadence_policy` として追加する。
receipt は selected identity cadence class、identity cadence class digest、
JP-13 / SG-01 jurisdiction cadence policy refs / digests、
target 別 refresh interval、effective refresh interval、effective revocation check window、
Council review ref、IntegrityGuardian attestation ref を
`cadence_commit_digest` に束縛する。

`long-term-media-renewal-refresh-window-v1` は `cadence_policy_digest` を持ち、
refresh window が cadence policy と別々に drift しないことを検証する。
raw identity cadence payload と raw jurisdiction cadence payload は保存しない。

## Consequences

- `memory-replication-demo --json` は cadence policy receipt と validation summary を返す。
- public schema / IDL / continuity eval / IntegrityGuardian policy は同じ policy id を共有する。
- `memory-replication` ledger event は cadence policy digest と effective refresh interval を first-class evidence として残す。
- 実在 registry や physical media の endurance audit は引き続き repo 外の実運用接続問題として扱う。
