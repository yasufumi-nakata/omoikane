---
date: 2026-04-27
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_authority_slo_quorum_threshold_policy_receipt.schema
  - specs/schemas/wms_authority_slo_probe_quorum_receipt.schema
  - evals/interface/wms_authority_slo_probe_quorum.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - 2026-04-26_wms-authority-slo-quorum-threshold-policy.md#threshold-policy-signer-roster-revocation
---

# Decision: WMS authority SLO quorum threshold を signer roster / revocation verifier に束縛する

## Context

`signed-authority-slo-quorum-threshold-policy-v1` は WMS remote authority SLO quorum の
required authority / jurisdiction count を signed jurisdiction policy registry receipt へ
束縛していました。一方、その threshold policy signer がどの signer roster に属し、
revoked ではないことをどの live verifier quorum が確認したかは first-class receipt ではありませんでした。

## Decision

WMS authority SLO quorum threshold policy receipt に
`authority-slo-quorum-threshold-signer-roster-v1`、
`authority-slo-threshold-signer-roster-live-verifier-quorum-v1`、
`authority-slo-quorum-threshold-revocation-registry-v1` を追加します。

threshold policy は signer roster digest、verifier response digest set、
revocation registry digest、`threshold_authority_binding_status=verified` を持ちます。
SLO quorum receipt は同じ digest を mirror し、threshold policy source / signature に加えて
signer roster verifier quorum と revocation registry が bound の時だけ complete になります。

## Consequences

- `wms-demo --json` は threshold policy と SLO quorum receipt の両方で
  signer roster / verifier quorum / revocation registry binding を返す
- public schema / IDL / eval / IntegrityGuardian capability は threshold signer authority chain を
  同じ closure point で検証する
- raw threshold policy payload、raw signer roster payload、raw revocation registry payload、
  raw authority verifier payload は保存しない

## Revisit triggers

- authority SLO quorum を distributed transport route trace と同じ non-loopback transport plane に載せる時
- threshold policy signer roster / revocation verifier を repo 外 live service adapter へ接続する時
