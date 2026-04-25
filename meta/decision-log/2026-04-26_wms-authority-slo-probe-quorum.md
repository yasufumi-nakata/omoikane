---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_authority_slo_probe_receipt.schema
  - specs/schemas/wms_authority_slo_probe_quorum_receipt.schema
  - evals/interface/wms_authority_slo_probe_quorum.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - 2026-04-26_wms-authority-slo-live-probe.md#multi-jurisdiction-authority-slo-quorum
---

# Decision: WMS authority SLO probe を quorum receipt に束縛する

## Context

`live-authority-slo-snapshot-probe-v1` は authority SLO snapshot を live HTTP
endpoint response digest に束縛しました。ただし primary retry probe だけでは、
reviewer は同じ WMS retry evidence が別 authority / remote jurisdiction からも
独立に live 観測されたかを machine-checkable に確認できませんでした。

## Decision

`multi-authority-slo-probe-quorum-v1` を追加し、primary SLO probe と backup
authority SLO probe を 1 つの digest-only quorum receipt へ束ねます。
receipt は accepted probe digests、authority refs、remote jurisdictions、
route refs、jurisdiction policy registry digests、SLO snapshot digests、
network response digests を set digest に固定し、raw SLO payload は保存しません。

quorum は 2 authority / 2 remote jurisdiction を満たし、かつ primary retry probe
digest が accepted probe set に含まれる場合だけ `quorum_status=complete` になります。

## Consequences

- `wms-demo --json` は `remote_authority_slo_probe_quorum_receipt` と validation flag を返す
- `interface.wms.v0` / public schema / eval / IntegrityGuardian capability は同じ quorum profile を共有する
- remote authority SLO evidence は single live endpoint ではなく、multi-authority quorum として reviewer に提示される

## Revisit triggers

- authority SLO quorum を distributed transport route trace と同じ non-loopback transport plane に載せる時
- quorum threshold を jurisdiction policy registry 側の signed policy から取得する時
