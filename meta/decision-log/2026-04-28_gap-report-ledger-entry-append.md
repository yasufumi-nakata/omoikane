---
date: 2026-04-28
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/07-reference-implementation/README.md
  - docs/02-subsystems/kernel/continuity-ledger.md
  - specs/interfaces/selfctor.gap_report.v0.idl
  - specs/schemas/gap_report.schema
  - specs/schemas/continuity_log_entry.schema
  - evals/continuity/gap_report_scan_receipt.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - 2026-04-28_gap-report-continuity-ledger-binding.md#actual-continuity-ledger-append
---

# Decision: gap-report scan event を ContinuityLedger append path に接続する

## Context

`gap-report --json` は `continuity_event_ref` と `continuity_event_digest` を返し、
report digest と surface manifest digest を ledger 用 evidence へ束縛していた。
ただしその evidence はまだ実際の `ContinuityLedger` entry として append されず、
automation gate が ledger head、entry hash、payload ref、署名 role を同じ receipt で
検証できなかった。

## Decision

`OmoikaneReferenceOS.generate_gap_report()` は scan receipt から作った digest-only event
payload を `selfctor-gap-report-scan` category の `ContinuityLedger` entry として append する。
entry は `selfctor.gap_report.scanned` event type と `self+guardian` 署名 role を持つ。

`gap_report.schema` は `continuity_ledger_entry_ref`、`continuity_ledger_entry_hash`、
`continuity_ledger_payload_ref`、`continuity_ledger_appended`、
`continuity_ledger_signature_roles` を public output として固定する。
raw report payload、raw scanned surface payload、raw continuity event payload は保存しない。

## Consequences

- `gap-report --json` の scan receipt は digest-bound event だけでなく実 ledger entry の存在も示せる。
- ContinuityLedger の category policy は `selfctor-gap-report-scan` を self + guardian 署名対象として扱う。
- IntegrityGuardian は all-zero gate の counts / surface digest / ledger entry append を同じ artifact で検証できる。
