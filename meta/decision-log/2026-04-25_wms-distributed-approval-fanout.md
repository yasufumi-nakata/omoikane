---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_distributed_approval_fanout_receipt.schema
  - evals/interface/wms_distributed_approval_fanout.yaml
status: decided
closes_next_gaps:
  - wms.physics-rules.distributed-approval-fanout
---

# Decision: WMS approval collection fan-out を distributed transport receipt へ束縛する

## Context

`bounded-wms-approval-collection-v1` は participant order と batch digest を
physics_rules change に束縛できるようにしました。
一方で `docs/02-subsystems/interface/wms-spec.md` には
distributed Council transport への approval fan-out 実装が未解決として残り、
complete collection が remote Council transport evidence と同じ digest family に
載っていることは machine-checkable ではありませんでした。

## Options considered

- A: IMC approval collection のみ維持し、distributed transport fan-out は research frontier に残す
- B: distributed Council transcript を WMS receipt に保存する
- C: Federation envelope digest、authenticated receipt digest、participant approval result digest を
  `wms_distributed_approval_fanout_receipt` に縮約する

## Decision

**C** を採択。

`distributed-council-approval-fanout-v1` を fixed profile とし、
`transport-result-bound-approval-fanout-v1` の digest profile で
complete approval collection digest、participant order、Federation envelope digest、
authenticated transport receipt digest、participant ごとの approval result digest を束縛する。

## Consequences

- `wms-demo --json` は 3 participant の fan-out receipt を返し、
  physics change receipt の `approval_fanout_digest` と同じ digest を共有する
- `interface.wms.v0` は `collect_distributed_approval_fanout` operation を持つ
- public schema / eval / tests は raw transcript ではなく digest-only distributed transport evidence を検証する

## Remaining scope

- actual remote multi-user engine の transaction log 統合は WMS engine adapter を持つ段階で再検討する
- distributed fan-out の retry / partial outage policy は、remote authority の operational profile が必要になった時に別 surface として扱う

## Revisit triggers

- WMS approval を Heritage Council returned result へも直接 fan-out したくなった時
- fan-out receipt を real remote authority route trace や packet capture export と同時に束縛したくなった時
