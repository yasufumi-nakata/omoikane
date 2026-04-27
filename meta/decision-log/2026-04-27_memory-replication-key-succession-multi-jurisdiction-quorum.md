---
date: 2026-04-27
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/03-protocols/memory-replication.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.memory_replication.v0.idl
  - specs/schemas/memory_replication_session.schema
  - evals/continuity/memory_replication_quorum.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - memory-replication.key-succession-multi-jurisdiction-signer-roster-quorum
---

# Decision: Memory replication key succession を multi-jurisdiction quorum に束縛する

## Context

`threshold-key-succession-guarded-recovery-v1` は JP-13 signer roster policy まで
束縛済みだったが、successor key preparation を単一 jurisdiction の signer roster
だけで complete と判定していた。repo 外 authority / HSM へ接続する前でも、複数
jurisdiction の signer roster policy digest を同じ session に束縛しておく必要があった。

## Decision

`memory_replication_session.key_succession` に
`key-succession-multi-jurisdiction-signer-roster-quorum-v1` を追加する。

receipt は JP-13 と SG-01 の required / accepted jurisdiction set、各 jurisdiction の
signer roster policy digest、signer roster digest set、identity-guardian /
integrity-guardian signature digest set、quorum status を保持する。raw jurisdiction
policy payload と raw signer roster payload は保存しない。

## Consequences

- `memory-replication-demo --json` は単一 JP-13 signer roster policy と
  JP-13 / SG-01 multi-jurisdiction quorum の両方を返す
- validation は missing jurisdiction、policy digest drift、raw jurisdiction policy payload
  storage を fail-closed にする
- public schema / IDL / eval / IntegrityGuardian capability は同じ quorum policy id を共有する

## Revisit triggers

- actual signer roster authority / HSM / trustee network を live verifier に接続する時
- JP-13 / SG-01 以外の jurisdiction を policy registry から動的に解決する時
