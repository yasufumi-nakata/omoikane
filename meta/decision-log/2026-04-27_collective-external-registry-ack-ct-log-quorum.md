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
  - collective.external-registry-ack-client-certificate-ct-log-quorum-sct-timestamp-policy
---

# Decision: Collective external registry ack CT readback を quorum / SCT policy に束縛する

## Context

`collective-external-registry-ack-client-certificate-ct-log-readback-v1` は
acknowledgement endpoint probe の mTLS client certificate lifecycle chain を
certificate transparency-style readback evidence に束縛した。ただし、前回の
decision log は CT inclusion proof を複数 log quorum や SCT timestamp policy へ
広げることを次段の見直し条件として残していた。

## Decision

`collective-external-registry-ack-client-certificate-ct-log-quorum-v1` と
`collective-external-registry-ack-client-certificate-sct-timestamp-policy-v1`
を ack live endpoint probe と external registry sync receipt に追加する。

各 probe は primary / witness の 2 CT log refs、log ごとの leaf digest、
inclusion proof digest、readback digest、quorum set digest、SCT timestamp digest、
`within-window` status、`quorum-met` status、CT quorum digest を持つ。
external registry sync receipt は probe ごとの CT quorum digest set を
registry digest set に追加し、endpoint probe、signed response envelope、mTLS
certificate proof、freshness proof、lifecycle proof、lifecycle chain proof、
CT readback、CT quorum がすべて bound の時だけ complete になる。

## Consequences

- `collective-demo --json` は `ack_live_endpoint_mtls_client_certificate_ct_log_quorum_*`
  fields と `ack_live_endpoint_mtls_client_certificate_ct_log_quorum_bound=true` を返す
- public schema / IDL / eval / IntegrityGuardian capability は CT-style readback に加え、
  2 log quorum と 300 秒 SCT timestamp window を同じ closure point で検証する
- raw endpoint payload、raw response signature payload、raw client certificate payload、
  raw freshness payload、raw lifecycle payload、raw lifecycle chain payload、
  raw CT log payload、raw packet body は保存しない

## Revisit triggers

- CT quorum を repo 外 live service adapter や実 CT log inclusion proof API へ接続する時
- SCT timestamp window を jurisdiction-specific policy registry や signer roster quorum へ広げる時
