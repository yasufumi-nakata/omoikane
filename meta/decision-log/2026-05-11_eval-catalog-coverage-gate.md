---
date: 2026-05-11
deciders: [yasufumi, codex-builder]
related_docs:
  - specs/catalog.yaml
  - src/omoikane/self_construction/gaps.py
  - specs/schemas/gap_report.schema
  - specs/interfaces/selfctor.gap_report.v0.idl
  - evals/continuity/gap_report_scan_receipt.yaml
status: decided
---

# Decision: eval YAML を catalog coverage gate に含める

## Context

`gap-report --json` は all-zero だったが、`evals/README.md` に列挙済みの
実在 eval YAML の一部が `specs/catalog.yaml` の `file:` entry に未登録だった。
既存 gate は `specs/interfaces` と `specs/schemas` の実装済みファイルだけを
catalog coverage として見ていたため、eval inventory と catalog の間の drift を
検出できなかった。

## Options considered

- A: 今回見つかった eval entry だけを `specs/catalog.yaml` に追加する
- B: eval YAML も catalog coverage gate に含め、未登録 eval を all-zero gate の外へ出す
- C: eval inventory は `evals/README.md` だけを正本とし、catalog 登録は任意にする

## Decision

B を採用する。`GapScanner` の catalog coverage scan を `evals/**/*.yaml` /
`evals/**/*.yml` まで広げ、実在 eval が `specs/catalog.yaml` に未登録なら
`catalog_coverage_gap_hits` として surfacing する。同時に今回見つかった 14 件の
eval entry を catalog に登録する。

## Consequences

- 実装済み eval を追加した時は、README inventory と catalog entry の両方が
  all-zero gate の対象になる。
- docs-only の評価記述だけではなく、reference runtime の検証 surface として
  catalog から consumers / rationale を追跡できる。
- BioData Transmitter、主観同一性、意識再現、thought content、完全人格再現の
  claim ceiling は変更しない。

## Revisit Triggers

- catalog が eval を正本として持たない軽量 index に分離される時
- eval YAML の階層を release package や external eval registry に移す時
