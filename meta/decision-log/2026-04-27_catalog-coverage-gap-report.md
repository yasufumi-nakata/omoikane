---
date: 2026-04-27
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/07-reference-implementation/README.md
  - specs/catalog.yaml
  - specs/interfaces/kernel.identity.v0.idl
  - src/omoikane/self_construction/gaps.py
  - tests/unit/test_gap_scanner.py
status: decided
---

# Decision: gap-report で uncataloged spec file を検出する

## Context

`specs/interfaces/kernel.identity.v0.idl` は実装済みで README inventory にも載っていたが、
`specs/catalog.yaml` の entries から抜けていた。
従来の `gap-report` は catalog entries が指す未作成ファイルと README inventory drift は
検出していた一方で、実装済み spec file が catalog に未登録の状態は all-zero に見えていた。

## Decision

`gap-report` に catalog coverage gap を追加し、
`specs/interfaces/*.idl` と `specs/schemas/*.{schema,yaml}` の実ファイルが
`specs/catalog.yaml` entries に未登録なら `catalog_coverage_gap_hits` として返す。
同時に `kernel.identity.v0.idl` を catalog の P1 interface entry に登録する。

## Consequences

- automation は README inventory と catalog entries の片方向差分だけでなく、
  実装済み spec file の catalog 登録漏れも next durable gap として拾える
- `gap-report --json` は `catalog_coverage_gap_count` /
  `catalog_coverage_gap_hits` を返し、現行 repo では all-zero を維持する
- identity lifecycle の schema / IDL / eval / guardian consumer 関係が catalog 上でも
  one closure point に揃う

## Revisit Triggers

- catalog entries を generated inventory に移す時
- schema / IDL 以外の spec artifact も catalog coverage 対象に広げる時
