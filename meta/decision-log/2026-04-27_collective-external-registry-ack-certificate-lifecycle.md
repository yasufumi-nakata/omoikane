---
date: 2026-04-27
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/collective-identity.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.collective.v0.idl
  - specs/schemas/collective_external_registry_sync.schema
  - evals/interface/collective_external_registry_sync.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - collective.external-registry-ack-client-certificate-renewal-lifecycle
---

# Decision: Collective external registry ack client certificate lifecycle を renewed rollover proof に束縛する

## Context

`collective-external-registry-ack-client-certificate-freshness-revocation-v1`
は acknowledgement endpoint probe の mTLS client certificate が freshness window 内で
`not_revoked` であることを証明した。一方、その certificate が renewal / rollover により
どの previous certificate を退役させたのか、また stale / revoked lifecycle signal が来た時に
fail-closed するかは first-class artifact ではなかった。

## Decision

`collective-external-registry-ack-client-certificate-lifecycle-v1` を
ack live endpoint probe と external registry sync receipt に追加する。

各 probe は current certificate proof digest と freshness proof digest に加え、
previous certificate ref / fingerprint、previous certificate retirement ref / digest、
renewal event ref / digest、172800 秒 lifecycle window、`renewed` status、
`accept-renewed-client-certificate` action、lifecycle proof digest を持つ。
external registry sync receipt は probe ごとの lifecycle proof digest set と set digest を
registry digest set に追加し、live probe、signed response envelope、mTLS certificate proof、
freshness proof、lifecycle proof がすべて bound の時だけ complete になる。

## Consequences

- `collective-demo --json` は
  `ack_live_endpoint_mtls_client_certificate_lifecycle_*` fields と
  `ack_live_endpoint_mtls_client_certificate_lifecycle_bound=true` を返す
- public schema / IDL / eval / IntegrityGuardian capability は certificate freshness と
  certificate lifecycle renewal を同じ closure point で検証する
- stale / revoked lifecycle status は `renewed` contract から外れ、validation が fail-closed する
- raw endpoint payload、raw response signature payload、raw client certificate payload、
  raw freshness payload、raw lifecycle payload、raw packet body は保存しない

## Revisit triggers

- certificate rollover を複数世代の chain receipt に広げる時
- live OCSP / CRL endpoint retrieval を repo 外 adapter へ接続する時
