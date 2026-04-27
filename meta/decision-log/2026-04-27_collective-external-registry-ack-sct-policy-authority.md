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
  - 2026-04-27_collective-external-registry-ack-ct-log-quorum.md#sct-timestamp-policy-registry-signer-roster-quorum
---

# Decision: Collective SCT timestamp policy を authority quorum に束縛する

## Context

`collective-external-registry-ack-client-certificate-ct-log-quorum-v1` は
2 log CT quorum と 300 秒 SCT timestamp window を endpoint probe に束縛した。
一方で、その timestamp window がどの jurisdiction policy registry と signer roster
quorum から来たかは first-class receipt ではなかった。

## Decision

`collective-external-registry-ack-client-certificate-sct-policy-authority-v1`
を ack endpoint probe と external registry sync receipt に追加する。

各 probe は SCT policy registry digest、signer roster digest、2 signer verifier
response digest、verifier quorum digest、policy authority digest を持つ。
external registry sync receipt は probe ごとの policy authority digest set を
registry digest set に加え、CT quorum と SCT policy authority が両方 bound の時だけ
complete になる。

## Consequences

- `collective-demo --json` は `ack_live_endpoint_mtls_client_certificate_sct_policy_authority_*`
  fields と `ack_live_endpoint_mtls_client_certificate_sct_policy_authority_bound=true` を返す
- public schema / IDL / eval / IntegrityGuardian capability は SCT timestamp window の
  policy source と signer verifier quorum を同じ closure point で検証する
- raw SCT policy authority payload は保存しない

## Revisit triggers

- SCT policy authority を repo 外 live policy registry adapter へ接続する時
- signer roster verifier quorum に certificate transparency log operator の実 response を束ねる時
