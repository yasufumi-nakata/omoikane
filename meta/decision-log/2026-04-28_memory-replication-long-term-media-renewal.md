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

# Decision: MemoryReplication long-term media renewal を digest-only receipt に固定する

## Context

`memory-replication-demo` は four-target replication、Merkle audit、reconcile、
threshold key succession、multi-jurisdiction signer roster authority まで固定していた。
一方、protocol docs の 100-1000 年スケール保管メディアは repo 外研究領域として残り、
reference runtime では coldstore / trustee copy が長期 media refresh と readback proof に
束縛されていなかった。

## Decision

`long-term-media-renewal-proof-v1` を追加し、
`memory_replication_session.long_term_media_renewal` で `coldstore` / `trustee` の
renewed media proof、readback digest、migration attestation digest、3650 日 refresh interval、
1000 年 target horizon、Council review ref、Guardian attestation ref を digest-only に束縛する。

reference runtime は actual physical storage durability を主張しない。
raw media payload と raw readback payload は保存せず、実物理 media audit / HSM /
trustee network 接続は repo 外 frontier として残す。

## Consequences

- `memory-replication-demo --json` は long-term media renewal receipt と validation summary を返す。
- public schema / IDL / continuity eval / IntegrityGuardian capability は同じ policy id を共有する。
- `memory-replication` ledger event は renewal digest、target ids、readback ok を first-class evidence として残す。
