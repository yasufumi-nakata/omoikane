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
  - collective.external-registry-ack-client-certificate-rollover-chain
---

# Decision: Collective external registry ack certificate lifecycle を rollover chain proof に束縛する

## Context

`collective-external-registry-ack-client-certificate-lifecycle-v1` は acknowledgement
endpoint probe の current certificate と previous certificate の renewal / retirement
edge を first-class receipt にしていました。一方、単一の previous edge だけでは、
複数世代の certificate rollover が同じ chain として継続していることを
machine-checkable に確認できませんでした。

## Decision

`collective-external-registry-ack-client-certificate-rollover-chain-v1` を
external registry acknowledgement endpoint probe と registry sync receipt に追加します。

各 probe は ancestor -> previous -> current の 3 generation certificate refs、
3 fingerprint、2 retirement digest、2 renewal event digest、terminal lifecycle proof digest、
chain set digest、chain proof digest、`chain_status=complete` を持ちます。
external registry sync receipt は probe ごとの lifecycle chain proof digest set を
registry digest set に追加し、live probe、signed response envelope、mTLS certificate proof、
freshness proof、lifecycle proof、lifecycle chain proof がすべて bound の時だけ complete になります。

## Consequences

- `collective-demo --json` は `ack_live_endpoint_mtls_client_certificate_lifecycle_chain_*`
  fields と `ack_live_endpoint_mtls_client_certificate_lifecycle_chain_bound=true` を返す
- public schema / IDL / eval / IntegrityGuardian capability は current/previous renewal だけでなく
  3 generation rollover chain を同じ closure point で検証する
- raw endpoint payload、raw response signature payload、raw client certificate payload、
  raw freshness payload、raw lifecycle payload、raw lifecycle chain payload、raw packet body は保存しない

## Revisit triggers

- chain depth を 3 generation から policy-driven variable depth に広げる時
- live OCSP / CRL endpoint retrieval と certificate transparency log readback を
  repo 外 adapter へ接続する時
