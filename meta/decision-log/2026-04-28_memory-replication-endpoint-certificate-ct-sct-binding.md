---
date: 2026-04-28
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/03-protocols/memory-replication.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.memory_replication.v0.idl
  - specs/schemas/memory_replication_session.schema
  - evals/continuity/memory_replication_quorum.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
---

# Decision: MemoryReplication registry endpoint certificate を CT/SCT 証跡へ束縛する

## Context

`long-term-media-renewal-registry-endpoint-certificate-lifecycle-v1` は
registry endpoint の certificate fingerprint、chain digest、OCSP / revocation、
renewal event、previous certificate retirement digest を source proof set と
registry response quorum へ束縛していた。
一方で、certificate lifecycle が transparency-style readback、複数 log quorum、
SCT timestamp policy authority へ接続されていることは MemoryReplication 側の
first-class receipt として固定されていなかった。

## Decision

MemoryReplication の `endpoint_certificate_lifecycle` receipt に
`long-term-media-renewal-registry-endpoint-certificate-ct-log-readback-v1`、
`long-term-media-renewal-registry-endpoint-certificate-ct-log-quorum-v1`、
`long-term-media-renewal-registry-endpoint-certificate-sct-policy-authority-v1`
を追加する。

各 registry endpoint は CT-style readback digest、2-log quorum digest、
SCT timestamp window digest、SCT policy registry digest、SCT signer roster digest、
signer verifier quorum digest、SCT policy authority digest を持つ。
これらは certificate lifecycle quorum digest と session validation summary に束縛され、
raw CT log payload と raw SCT policy authority payload は保存しない。

## Consequences

- `memory-replication-demo --json` は CT readback / CT quorum / SCT policy authority binding と redaction flag を返す。
- `memory_replication_session.schema`、`mind.memory_replication.v0.idl`、
  continuity eval、IntegrityGuardian capability は同じ policy ids を共有する。
- `validate_session` は CT log raw payload または SCT authority raw payload が保存された場合に fail-closed する。

## Revisit triggers

- 実 CT log / SCT authority / registry endpoint の live response を検証対象に接続する時
- endpoint certificate rollover chain を 3 generation 以上へ拡張する時
