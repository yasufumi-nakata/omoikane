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

# Decision: MemoryReplication media renewal proof を refresh / revocation window に束縛する

## Context

`long-term-media-renewal-proof-v1` は `coldstore` / `trustee` の renewed media proof、
readback digest、migration attestation、3650 日 refresh interval、1000 年 target horizon
を digest-only に固定した。
ただし初回 proof が current なまま扱われる条件、失効確認 window、次回 refresh ref、
stale / revoked proof の fail-closed 条件は reviewer-facing artifact として明示されていなかった。

## Options considered

- A: 既存 `next_refresh_due_ref` だけを維持し、失効確認は repo 外 frontier に置く
- B: `memory_replication_session.long_term_media_renewal.refresh_window` を nested receipt として追加し、source proof digest set と readback digest set を current-not-revoked / revocation check / next refresh ref に束縛する
- C: long-term media renewal を別 demo に分離し、replication session から切り離す

## Decision

B を採用する。
`long-term-media-renewal-refresh-window-v1` は source proof digest set、
source readback digest set、source media proof set digest、90 日 revocation check window、
revocation registry refs / digest set、next required refresh ref、Council review ref、
Guardian attestation ref、stale / revoked source fail-closed flag を
`refresh_commit_digest` へ束縛する。

raw revocation payload と raw refresh payload は保存しない。
reference runtime は actual physical media durability や external registry 接続を主張せず、
bounded digest-only receipt と validation summary だけを返す。

## Consequences

- `memory-replication-demo --json` は renewal proof に加えて refresh-window receipt と validation summary を返す。
- public schema / IDL / continuity eval / IntegrityGuardian capability は同じ policy id を共有する。
- `memory-replication` ledger event は renewal digest に加えて refresh commit digest と revocation check result を first-class evidence として残す。

## Revisit triggers

- 実在 coldstore / trustee media registry の live response を refresh window に接続する時
- long-term media refresh cadence や revocation check window を identity / jurisdiction ごとに変える時
