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
  - memory-replication.key-succession-quorum-threshold-policy-authority
---

# Decision: Memory replication key succession quorum threshold を policy authority に束縛する

## Context

`threshold-key-succession-guarded-recovery-v1` は JP-13 と SG-01 の signer roster
policy digest を multi-jurisdiction quorum に束ねていた。一方で、その quorum threshold
`2` がどの policy registry と signer authority に由来するかは first-class receipt ではなく、
reviewer 側固定値だけで complete と判定できる余地が残っていた。

## Decision

`memory_replication_session.key_succession.signer_roster_quorum` に
`key-succession-multi-jurisdiction-quorum-threshold-policy-v1` authority receipt を追加する。

receipt は policy registry ref / digest、policy body digest、required jurisdiction set、
quorum threshold、jurisdiction policy digest set、signer roster digest set、
authority signature digest set、verifier quorum digest を保持する。raw threshold policy
payload と raw policy registry payload は保存しない。

`MemoryReplicationService.validate_session` は threshold authority の digest drift、
quorum threshold drift、raw policy payload storage を fail-closed にする。

## Consequences

- `memory-replication-demo --json` は `key_succession_quorum_threshold_policy_bound`
  と `key_succession_quorum_threshold_policy_ok` を返す
- public schema / IDL / eval / IntegrityGuardian capability は同じ policy id を共有する
- ledger event は threshold policy authority digest を memory replication evidence として残す

## Revisit triggers

- actual signer roster authority / HSM / trustee network を live verifier に接続する時
- JP-13 / SG-01 以外の jurisdiction を policy registry から動的に解決する時
