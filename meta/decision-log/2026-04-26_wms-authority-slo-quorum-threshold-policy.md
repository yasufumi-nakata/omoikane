---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_authority_slo_probe_quorum_receipt.schema
  - specs/schemas/wms_authority_slo_quorum_threshold_policy_receipt.schema
  - evals/interface/wms_authority_slo_probe_quorum.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - 2026-04-26_wms-authority-slo-probe-quorum.md#signed-threshold-policy
---

# Decision: WMS authority SLO quorum threshold を signed policy receipt に束縛する

## Context

`multi-authority-slo-probe-quorum-v1` は primary / backup authority の live SLO
probe を 2 authority / 2 jurisdiction の quorum receipt へ束ねていました。
ただし `required_quorum_count=2` と jurisdiction threshold は runtime 側の固定値で、
reviewer はその threshold が jurisdiction policy registry 由来かを
machine-checkable に確認できませんでした。

## Decision

`signed-authority-slo-quorum-threshold-policy-v1` を追加し、WMS quorum receipt は
signed threshold policy receipt を内包する。
threshold policy は jurisdiction policy registry refs / digests、remote jurisdiction set、
required authority count、required jurisdiction count、signer key ref、
policy body digest、signature digest を raw policy payload 無しで束縛する。

quorum は live probe set だけでなく、threshold policy の registry refs / digests と
jurisdiction set が accepted probe set と一致した時だけ `quorum_status=complete` になる。

## Consequences

- `wms-demo --json` は `remote_authority_slo_quorum_threshold_policy` と validation flag を返す
- `wms_authority_slo_probe_quorum_receipt.schema` は threshold policy digest と signature digest を必須にする
- IntegrityGuardian は SLO quorum threshold が signed registry policy 由来であることを検証対象にする

## Revisit triggers

- authority SLO quorum を distributed transport route trace と同じ non-loopback transport plane に載せる時
- threshold policy signer roster / revocation registry も live verifier quorum へ昇格する時
