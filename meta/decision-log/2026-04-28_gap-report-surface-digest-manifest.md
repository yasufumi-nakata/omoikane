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

# Decision: gap-report scan receipt は source surface digest manifest を束縛する

## Context

`gap-report --json` は all-zero 判定、counts、prioritized task count、report digest を
`scan_receipt` に固定していた。
ただし receipt が保持していた `scanned_surfaces` は pattern 名だけであり、
その run が実際にどの truth-source file content に基づいた all-zero 判定だったかを
後から digest-only に照合する証跡は不足していた。

## Options considered

- A: `scanned_surfaces` の pattern 名だけを維持する
- B: matched truth-source file ごとの `sha256` / `byte_length` を `scan_surface_digests` に追加し、manifest 全体を `surface_manifest_digest` で束縛する
- C: raw scanned source payload を receipt に保存する

## Decision

B を採用する。
`self-construction-gap-report-scan-receipt-v1` は、既存の report digest に加えて、
scan surface pattern、matched file path、SHA-256 digest、byte length を
`scan_surface_digests` に保持し、その ordered manifest を
`surface_manifest_digest` で固定する。

raw report payload と raw surface payload は保存しない。

## Consequences

- `gap-report --json` の scan receipt は all-zero 判定の根拠となった truth-source file set を digest-only に監査できる。
- public schema / IDL / continuity eval / IntegrityGuardian capability は同じ surface digest manifest contract を共有する。
- automation は report digest と surface manifest digest の両方を比較して、同じ all-zero 判定が同じ source content に由来するか確認できる。

## Revisit triggers

- scan 対象が repo-local file 以外の外部 registry や network response に広がる時
- surface digest manifest を continuity ledger event として永続化する時
