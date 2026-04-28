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
closes_next_gaps:
  - memory-replication-media-renewal-registry-endpoint-certificate-lifecycle
---

# Decision: MemoryReplication registry endpoint certificate lifecycle を verifier quorum に束縛する

## Context

`long-term-media-renewal-registry-verifier-v1` は JP-13 / SG-01 の registry
response digest、response signature digest、250ms timeout budget、quorum digest を
source proof set へ束縛していた。
ただし registry endpoint 自体の client-facing certificate freshness / revocation /
renewal lifecycle は verifier receipt の内側に first-class artifact として残っておらず、
endpoint 証明書が stale / revoked / rollover drift した場合の reviewer-facing evidence が
弱かった。

## Decision

`long-term-media-renewal-registry-endpoint-certificate-lifecycle-v1` を
`memory_replication_session.long_term_media_renewal.refresh_window.registry_verifier.endpoint_certificate_lifecycle`
に追加する。

この receipt は registry endpoint ref、current certificate fingerprint、certificate
chain digest、OCSP response digest、certificate revocation digest、renewal event digest、
previous certificate retirement digest を JP-13 / SG-01 response quorum と同じ
source media proof set に束縛する。

raw endpoint certificate payload、raw certificate freshness payload、raw certificate
lifecycle payload は保存しない。
reference runtime は実在 registry endpoint の TLS 到達性を主張せず、digest-only の
certificate lifecycle receipt と validation summary だけを返す。

## Consequences

- `memory-replication-demo --json` は registry verifier 内に endpoint certificate lifecycle receipt を返す。
- public schema / IDL / continuity eval / IntegrityGuardian capability は同じ policy id を共有する。
- `memory-replication` validation は stale certificate lifecycle と raw certificate payload 保存を fail-closed にする。
