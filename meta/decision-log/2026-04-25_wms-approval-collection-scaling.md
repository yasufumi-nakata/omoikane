---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_approval_collection_receipt.schema
  - evals/interface/wms_approval_collection_scaling.yaml
status: decided
---

# Decision: WMS approval collection を bounded batch receipt へ昇格する

## Context

`wms_participant_approval_transport_receipt` は participant ごとの live IMC
approval を証明できるようになりました。
一方で shared_reality の participant 数が増えた時に、receipt set が
どの participant order / digest set / batch boundary で集約されたかは
physics_rules change receipt から first-class に検証できませんでした。

## Options considered

- A: per-participant transport receipt の配列だけを維持する
- B: raw approval conversation transcript を collection log に保存する
- C: ordered participant list、ordered receipt digest set、bounded batch digest を
  `wms_approval_collection_receipt` に縮約する

## Decision

**C** を採択。

`bounded-wms-approval-collection-v1` を fixed profile とし、
`participant-ordered-batch-digest-v1` の digest profile で
required participant order、receipt digest set、`max_batch_size=2` の batch digest を
physics_rules change receipt に束縛する。

## Consequences

- `wms-demo --json` は 3 participant の approval collection を返し、
  physics change の `approval_collection_digest` と同じ digest を共有する
- `interface.wms.v0` は `collect_approval_transport_receipts` operation を持ち、
  apply は complete collection receipt を要求する
- public schema / eval / tests は raw IMC payload ではなく digest-only collection を検証する

## Remaining scope

- distributed Council transport での approval fan-out は別 surface に分離する
- 実 multi-user engine の transaction log 統合は WMS engine adapter を持つ段階で再検討する

## Revisit triggers

- approval batch size を participant 数や jurisdiction ごとに可変化したくなった時
- remote authority transport 由来の approval receipt を WMS collection に直接混ぜる時
