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
  - collective.external-registry-ack-client-certificate-freshness-revocation
---

# Decision: Collective external registry ack mTLS client certificate を freshness / revocation proof に束縛する

## Context

`collective-external-registry-ack-mtls-client-certificate-proof-v1` は
ack endpoint probe が利用した mTLS client certificate ref、fingerprint、
certificate chain digest、client CA ref を first-class receipt にした。
ただし、その certificate が probe 時点で失効していないこと、また freshness window
内に検証されたことは digest-bound artifact ではなかった。

## Decision

`collective-external-registry-ack-client-certificate-freshness-revocation-v1`
を ack live endpoint probe receipt に追加する。

各 probe は client certificate proof digest に加え、revocation registry ref、
revocation registry digest、OCSP-style responder ref、OCSP-style response digest、
`not_revoked` status、24h freshness window、checked_at、freshness proof digest を持つ。
external registry sync receipt は probe ごとの freshness proof digest set と set digest
を registry digest set に追加し、live probe、signed response envelope、mTLS client
certificate proof、freshness/revocation proof がすべて bound の時だけ complete になる。

## Consequences

- `collective-demo --json` は
  `ack_live_endpoint_mtls_client_certificate_freshness_*` fields と
  `ack_live_endpoint_mtls_client_certificate_freshness_bound=true` を返す
- public schema / IDL / eval / IntegrityGuardian capability は endpoint response signature、
  client certificate proof、freshness / revocation proof を同じ closure point で検証する
- raw endpoint payload、raw response signature payload、raw client certificate payload、
  raw freshness / revocation payload、raw packet body は保存しない

## Revisit triggers

- live OCSP / CRL endpoint retrieval を repo 外 adapter へ接続する時
- certificate renewal / rollover lifecycle を stale / renewed / revoked の fail-closed
  status に広げる時
