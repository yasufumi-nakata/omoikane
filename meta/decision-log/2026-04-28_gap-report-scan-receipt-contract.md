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
---

# Decision: gap-report を digest-bound scan receipt へ昇格する

## Context

`gap-report --json` は open question、catalog coverage、truth-source future work、
decision-log frontier、implementation stub を all-zero にできるようになっていた。
ただし automation gate が読む出力全体は public schema と digest-bound receipt に
昇格しておらず、counts、prioritized task count、scan surface、all-zero 判定が
reviewer-facing artifact として固定されていなかった。

## Decision

`self-construction-gap-report-scan-receipt-v1` を追加し、`GapScanner.scan()` が
`scan_receipt` を返す。

receipt は report counts、prioritized task count、scan surface、all-zero 判定、
report digest、raw report payload 非保存 flag を束縛する。
`gap_report.schema` と `selfctor.gap_report.v0.idl` は CLI output を public contract
として固定し、continuity eval と IntegrityGuardian capability が同じ profile id を共有する。

## Consequences

- `gap-report --json` は all-zero だけでなく `scan_receipt.validation.ok=true` を返す。
- schema contract tests は CLI/runtime output を `gap_report.schema` に直接通す。
- catalog inventory は new schema / IDL / eval を entries に含め、次回以降の inventory drift を検出できる。
