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
  - memory-replication.key-succession-jurisdiction-signer-roster
---

# Decision: Memory replication key succession を signer roster policy に束縛する

## Context

`threshold-key-succession-guarded-recovery-v1` は 3-of-5 share、2 Guardian
attestation、successor key digest、rotation ledger ref までを session に封入していた。
ただし successor key preparation を承認する signer set がどの jurisdiction roster に
由来するかは first-class receipt ではなく、raw roster payload を保存せずに検証できる
contract が不足していた。

## Decision

`memory_replication_session.key_succession` に
`key-succession-jurisdiction-signer-roster-policy-v1` を追加する。

receipt は `JP-13` の policy ref、signer roster ref、signer roster digest、
identity-guardian / integrity-guardian の required role set、2 signature digest、
quorum status、raw signer roster payload redaction を保持する。
`memory-replication-demo --json` は signer roster policy bound / quorum ok / raw roster
payload 非保存 flag を返し、ledger event も signer roster digest を key succession
evidence として同じ L2 event に束縛する。

## Consequences

- key succession は Guardian quorum だけでなく jurisdiction-specific signer roster
  quorum にも束縛される
- public schema / IDL / eval / IntegrityGuardian capability は同じ policy id を共有する
- repo 外 signer roster authority へ接続する前でも、raw roster payload を保存しない
  digest-only contract を machine-checkable に維持できる

## Revisit triggers

- actual signer roster authority / HSM / trustee network を live verifier に接続する時
- jurisdiction set を JP-13 固定から multi-jurisdiction quorum へ拡張する時
