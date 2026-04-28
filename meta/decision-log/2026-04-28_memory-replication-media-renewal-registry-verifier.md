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

# Decision: MemoryReplication media renewal registry verifier を refresh window に束縛する

## Context

`long-term-media-renewal-refresh-window-v1` は media proof set を
current-not-revoked status、90 日 revocation check window、次回 refresh ref、
stale / revoked source fail-closed flag へ束縛していた。
ただし coldstore / trustee の registry status response を digest-only evidence として
same refresh window に固定する reviewer-facing artifact はまだ無かった。

## Decision

`long-term-media-renewal-registry-verifier-v1` を
`memory_replication_session.long_term_media_renewal.refresh_window.registry_verifier`
に追加する。

この receipt は JP-13 / SG-01 の registry endpoint ref、request payload digest、
response digest set、response signature digest set、250ms timeout budget、
registry quorum digest、current-not-revoked status を source proof digest set と
revocation registry digest set に束縛する。

raw registry payload と raw response payload は保存しない。
reference runtime は物理 media 耐久性や外部 registry 接続の成立を主張せず、
digest-only verifier receipt と validation summary だけを返す。

## Consequences

- `memory-replication-demo --json` は refresh window 内に registry verifier receipt を返す。
- public schema / IDL / continuity eval / IntegrityGuardian capability は同じ policy id を共有する。
- `memory-replication` ledger event は registry verifier digest と quorum result を first-class evidence として残す。

## Revisit triggers

- 実在 coldstore / trustee registry の transport route trace を registry verifier に接続する時
- registry endpoint の freshness / certificate lifecycle を別 receipt として分ける時
