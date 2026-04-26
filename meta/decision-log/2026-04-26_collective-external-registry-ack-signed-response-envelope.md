---
date: 2026-04-26
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
  - collective.external-registry-ack-signed-response-envelope
---

# Decision: Collective external registry ack endpoint response を署名 envelope に束縛する

## Context

`collective-external-registry-ack-live-endpoint-probe-v1` は legal / governance
registry acknowledgement を live HTTP JSON endpoint response digest に束縛しました。
ただし response が registry authority の signing key 由来であることは endpoint payload
digest の内側に閉じておらず、reviewer は static endpoint digest と signed envelope を
machine-checkable に区別できませんでした。

## Decision

`collective-external-registry-ack-signed-response-envelope-v1` を live endpoint probe
receipt に追加する。

ack endpoint response は response digest、registry authority / jurisdiction bound
signing key ref、response signature digest、raw response signature payload 非保存 flag を
持つ。external registry sync receipt は acknowledgement ごとの response signature
digest set とその set digest を registry digest set に入れ、signed response envelope が
全 probe で bound された時だけ complete になる。

## Consequences

- `collective-demo --json` は `ack_live_endpoint_response_signature_digests` と
  `ack_live_endpoint_signed_response_envelope_bound` を返す
- public schema / IDL / eval / IntegrityGuardian capability は live endpoint probe と
  signed response envelope を同じ closure point として共有する
- raw endpoint payload、raw acknowledgement payload、raw response signature payload、
  raw packet body は保存しない

## Revisit triggers

- registry acknowledgement endpoint に mTLS client certificate proof を追加する時
- registry acknowledgement lifecycle を stale / revoked / renewed の fail-closed status へ拡張する時
