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
  - collective.external-registry-ack-mtls-client-certificate-proof
---

# Decision: Collective external registry ack endpoint を mTLS client certificate proof に束縛する

## Context

`collective-external-registry-ack-signed-response-envelope-v1` は legal / governance
registry acknowledgement endpoint response を registry authority の signing key digest
へ束縛した。一方、probe 側がどの mTLS client certificate で endpoint に到達したかは
first-class receipt になっておらず、response signature と client-auth proof を
machine-checkable に分離できなかった。

## Decision

`collective-external-registry-ack-mtls-client-certificate-proof-v1` を
ack live endpoint probe receipt に追加する。

各 probe は registry acknowledgement endpoint ref、ack receipt digest、response digest、
mTLS client certificate ref、certificate fingerprint、certificate chain digest、
client CA ref、certificate proof digest を持つ。external registry sync receipt は
probe ごとの certificate proof digest set と set digest を registry digest set に追加し、
live probe、signed response envelope、mTLS client certificate proof がすべて bound の時だけ
complete になる。

## Consequences

- `collective-demo --json` は `ack_live_endpoint_mtls_client_certificate_*` fields と
  `ack_live_endpoint_mtls_client_certificate_bound=true` を返す
- public schema / IDL / eval / IntegrityGuardian capability は endpoint response signature と
  client certificate proof を同じ closure point で検証する
- raw endpoint payload、raw response signature payload、raw client certificate payload、
  raw packet body は保存しない

## Revisit triggers

- registry acknowledgement lifecycle を stale / revoked / renewed の fail-closed status へ拡張する時
- client certificate revocation registry / OCSP-style freshness proof を endpoint probe に追加する時
