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
  - collective.external-registry-ack-client-certificate-ct-log-readback
---

# Decision: Collective external registry ack certificate chain を CT-style readback に束縛する

## Context

`collective-external-registry-ack-client-certificate-rollover-chain-v1` は
acknowledgement endpoint probe の mTLS client certificate を ancestor -> previous ->
current の 3 generation rollover chain に束縛した。一方、その chain が
certificate transparency-style の readback evidence に含まれていることは
first-class receipt ではなかった。

## Decision

`collective-external-registry-ack-client-certificate-ct-log-readback-v1` を
ack live endpoint probe と external registry sync receipt に追加する。

各 probe は CT log ref、certificate leaf digest、inclusion proof digest、
chain proof digest、`included` status、CT readback digest を持つ。
external registry sync receipt は probe ごとの CT readback digest set を
registry digest set に追加し、endpoint probe、signed response envelope、mTLS
certificate proof、freshness proof、lifecycle proof、lifecycle chain proof、CT readback
がすべて bound の時だけ complete になる。

## Consequences

- `collective-demo --json` は `ack_live_endpoint_mtls_client_certificate_ct_log_*`
  fields と `ack_live_endpoint_mtls_client_certificate_ct_log_bound=true` を返す
- public schema / IDL / eval / IntegrityGuardian capability は 3 generation
  rollover chain と CT-style readback を同じ closure point で検証する
- raw endpoint payload、raw response signature payload、raw client certificate payload、
  raw freshness payload、raw lifecycle payload、raw lifecycle chain payload、
  raw CT log payload、raw packet body は保存しない

## Revisit triggers

- CT log readback を repo 外 live service adapter へ接続する時
- CT inclusion proof を複数 log quorum や SCT timestamp policy へ広げる時
