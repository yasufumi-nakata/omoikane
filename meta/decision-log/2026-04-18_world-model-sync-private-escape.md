---
date: 2026-04-18
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/README.md
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - evals/interface/wms_private_reality_escape.yaml
status: decided
---

# Decision: WMS の private reality escape contract を reference runtime に固定する

## Context

`gap-report` は clean でしたが、reference runtime README には
「残る L6 interface protocol（IMC/WMS/EWA）の adapter」が残っていました。
特に WMS は docs で不整合時の退避規則まで具体化されている一方で、
runtime / CLI / eval / tests が存在せず、
shared reality から private reality へ退避できるという重要な安全境界が
実装で検証されていませんでした。

## Options considered

- A: WMS は docs-only のまま維持し、実装は IMC/EWA とまとめて後回しにする
- B: shared/private/mixed の mode、minor/major/malicious の 3 分類、
  private reality escape、guardian isolation に限定した bounded contract を追加する
- C: scenegraph 全文、physics simulation、distributed consensus 実装まで v0 に含める

## Decision

**B** を採択。

## Consequences

- `interface.wms.v0` を追加し、`snapshot / propose_diff / switch_mode / observe_violation`
  の 4 op を固定する
- `world_state.schema` と `wms_reconcile.schema` を追加し、
  `affected_object_ratio < 0.05` を minor / それ以上を major とする
- `wms-demo` を追加し、minor reconcile、major escape offer、
  malicious inject isolation、private reality escape honoring をまとめて検証する
- IMC/EWA は引き続き未実装だが、shared reality 退避路だけは runtime で担保される

## Revisit triggers

- shared reality の scenegraph や object diff を opaque hash ではなく構造化検証したくなった時
- time_rate 1.0 固定を解除し、substrate 間の速度差 negotiation を model 化する時
- Federation Council や distributed broker と接続して real external session を扱う時
