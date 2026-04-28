---
date: 2026-04-28
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/07-reference-implementation/README.md
  - specs/interfaces/selfctor.gap_report.v0.idl
  - specs/schemas/gap_report.schema
  - evals/continuity/gap_report_scan_receipt.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - 2026-04-28_gap-report-surface-digest-manifest.md#gap-report-scan-continuity-ledger-binding
---

# Decision: gap-report scan receipt を continuity ledger evidence に束縛する

## Context

`self-construction-gap-report-scan-receipt-v1` は report digest と
truth-source surface manifest digest を返していたが、その all-zero 判定を
continuity ledger 側の event evidence として参照する digest/ref は持っていなかった。
そのため、automation gate が同じ scan receipt を後続 ledger event へ渡す際に、
raw report payload を保存せずに同一性を確認する reviewer-facing artifact が弱かった。

## Decision

`gap-report-scan-continuity-ledger-binding-v1` を scan receipt に追加する。
receipt は `continuity_event_ref`、`continuity_event_digest`、
`continuity_ledger_category=selfctor-gap-report-scan` を返し、
`report_digest` と `surface_manifest_digest`、counts、all-zero 判定を
同じ ledger event digest に束縛する。

raw report payload、raw scanned surface payload、raw continuity event payload は保存しない。

## Consequences

- `gap-report --json` は scan receipt だけで automation gate と continuity ledger evidence の対応を確認できる。
- public schema / IDL / continuity eval / IntegrityGuardian capability は同じ ledger binding profile を共有する。
- full test は continuity event digest の再計算を行い、schema drift と raw payload 保存を fail-closed で検出する。

## Revisit triggers

- 実際の `ContinuityLedger` append path へ gap-report scan event を永続化する時
- scan receipt を複数 repo / external registry response へ拡張する時
