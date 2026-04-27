---
date: 2026-04-27
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
closes_next_gaps:
  - memory-replication.key-management-generational-succession
---

# Decision: Memory replication key succession を threshold receipt に束縛する

## Context

`docs/03-protocols/memory-replication.md` には、本人が一時的に key を失った場合の
世代継承が未解決として残っていた。既存 runtime は 3-of-5 Shamir policy を
profile に持っていたが、successor key epoch、Guardian attestation、rotation ledger ref、
raw key material redaction を machine-checkable に確認できなかった。

## Decision

`memory_replication_session` に
`threshold-key-succession-guarded-recovery-v1` receipt を追加する。
receipt は source manifest digest、previous / successor key epoch、3 accepted share refs、
5 share commitment digests、2 Guardian attestation digests、successor key digest、
rotation ledger ref を保持する。

raw key material と raw shard material は保存しない。

## Consequences

- `memory-replication-demo --json` は `key_succession` receipt と validation flags を返す
- public schema / IDL / eval / IntegrityGuardian capability は同じ policy id を共有する
- ledger event は replication reconcile と key succession digest を同じ L2 evidence に束縛する

## Revisit triggers

- repo 外 HSM / trustee network / live key ceremony adapter へ接続する時
- key succession policy を jurisdiction-specific signer roster に束縛する時
